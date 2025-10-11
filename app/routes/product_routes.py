# app/routes/product_routes.py
from flask import request, jsonify, Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required
import logging
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
import re
import json
from app.models import Product, User
from app.utils import ROLES, role_required, get_aws_client
import boto3, uuid, os
from datetime import datetime, timezone
import hashlib # 👈 Adicione esta linha para calcular o hash dos arquivos
from werkzeug.utils import secure_filename # 👈 Adicione esta linha para limpar nomes de arquivos

product_bp = Blueprint('product', __name__)

s3_client = None
s3_bucket_name = os.getenv("AWS_BUCKET_NAME")

# ============================================================
# HELPERS
# ============================================================

def _serialize_dt(value):
    if isinstance(value, datetime):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def _serialize_product(doc):
    if not doc:
        return {}

    p = dict(doc)

    # ID sempre como string
    p["id"] = str(p.get("_id"))
    p.pop("_id", None)

    # Datas
    if "created_at" in p:
        p["created_at"] = _serialize_dt(p["created_at"])
    if "updated_at" in p:
        p["updated_at"] = _serialize_dt(p["updated_at"])

    # Nome do criador
    created_by_user_id = p.get("created_by_user_id")
    if created_by_user_id:
        try:
            _oid = created_by_user_id if isinstance(created_by_user_id, ObjectId) else ObjectId(created_by_user_id)
            user = User.collection().find_one({"_id": _oid})
            if user:
                p["created_by"] = user.get("username") or user.get("name") or str(created_by_user_id)
            else:
                p["created_by"] = str(created_by_user_id)
        except Exception:
            p["created_by"] = str(created_by_user_id)

    # 🎯 CORREÇÃO FINAL: Garante que o campo original seja sempre uma string
    if "created_by_user_id" in p and p["created_by_user_id"]:
        p["created_by_user_id"] = str(p["created_by_user_id"])

    return p

# ============================================================
# TEST ROUTE
# ============================================================
@product_bp.route('/products/test', methods=['GET'])
def test_products():
    return jsonify({"msg": "API de produtos está ativa!"}), 200


# ============================================================
# NEXT PRODUCT CODE
# ============================================================
@product_bp.route('/products/next-code', methods=['GET'])
@role_required([ROLES['1'], ROLES['2']])
def get_next_product_code():
    try:
        last_product = Product.collection().find_one(sort=[('_id', -1)])
        last_code_number = 0

        if last_product and 'codigo' in last_product:
            match = re.search(r'FDS(\d+)', last_product['codigo'])
            if match:
                last_code_number = int(match.group(1))

        new_code_number = last_code_number + 1
        new_codigo = f"FDS{new_code_number:06d}"

        return jsonify({"next_code": new_codigo}), 200

    except Exception as e:
        return jsonify({"msg": f"Erro ao gerar o próximo código do produto: {str(e)}"}), 500

# =============================================================================
# ✅ PASSO 1: FUNÇÃO AUXILIAR PARA VALIDAR O NÚMERO CAS
# Esta função contém a lógica do algoritmo de soma de verificação.
# Colocá-la fora da rota torna o código mais limpo e reutilizável.
# =============================================================================
def is_valid_cas_number(cas_string: str) -> bool:
    """
    Valida um número CAS usando o algoritmo de soma de verificação.
    """
    # Verifica o formato (ex: 7732-18-5) usando expressão regular.
    if not re.match(r'^\d{2,7}-\d{2}-\d$', cas_string):
        return False

    # Remove os hífens para o cálculo.
    digits = cas_string.replace('-', '')
    check_digit = int(digits[-1])
    cas_digits_to_check = digits[:-1]

    # Aplica o algoritmo: soma ponderada dos dígitos.
    total_sum = 0
    for i, digit in enumerate(cas_digits_to_check[::-1]): # Itera da direita para a esquerda
        total_sum += int(digit) * (i + 1)
    
    # O resto da divisão por 10 deve ser igual ao dígito verificador.
    return (total_sum % 10) == check_digit


# ============================================================
# CREATE PRODUCT 
# ============================================================

@product_bp.route('/products', methods=['POST'])
@role_required([ROLES['1'], ROLES['2']])
def create_product():
    current_user_id = get_jwt_identity()
    try:
        creator_user_id = ObjectId(current_user_id)
    except (InvalidId, TypeError):
        creator_user_id = str(current_user_id)

    # 1️⃣ Verificação dos dados recebidos
    if 'productData' not in request.form:
        return jsonify({"msg": "Dados do produto (productData) não encontrados no formulário."}), 400
    if 'file' not in request.files:
        return jsonify({"msg": "Nenhum arquivo (file) foi enviado."}), 400

    # 2️⃣ Converte os dados do formulário JSON → Python
    try:
        data = json.loads(request.form['productData'])
    except json.JSONDecodeError:
        return jsonify({"msg": "Formato de 'productData' é inválido."}), 400

    pdf_file = request.files['file']
    
    # 3️⃣ Validação de campos obrigatórios
    required_fields = ['nome_do_produto', 'fornecedor', 'estado_fisico', 'local_de_armazenamento', 'empresa']
    if any(field not in data or not data[field] for field in required_fields):
        return jsonify({
            "msg": "Campos obrigatórios faltando: nome_do_produto, fornecedor, estado_fisico, local_de_armazenamento e empresa."
        }), 400

    # =============================================================================
    # ✅ VALIDAÇÕES DE NEGÓCIO
    # =============================================================================
    product_name = data.get('nome_do_produto').strip()
    original_filename = pdf_file.filename
    filename_without_ext, _ = os.path.splitext(original_filename)

    if product_name.lower() != filename_without_ext.strip().lower():
        return jsonify({
            "msg": f"O nome do produto ('{product_name}') não corresponde ao nome do arquivo ('{filename_without_ext}')."
        }), 409

    if Product.collection().find_one({"nome_do_produto": {"$regex": f"^{re.escape(product_name)}$", "$options": "i"}}):
        return jsonify({"msg": f"Já existe um produto cadastrado com o nome '{product_name}'."}), 409

    try:
        sha256_hash = hashlib.sha256()
        for byte_block in iter(lambda: pdf_file.read(4096), b""):
            sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()
        pdf_file.seek(0)
        if Product.collection().find_one({"file_hash": file_hash}):
            return jsonify({"msg": "Este arquivo FDS já foi cadastrado para outro produto."}), 409
    except Exception as e:
        return jsonify({"msg": f"Erro ao processar o arquivo para verificação: {str(e)}"}), 500

    # 4️⃣ Geração do código do produto
    try:
        last_product = Product.collection().find_one(sort=[('_id', -1)])
        last_code_number = 0
        if last_product and 'codigo' in last_product:
            match = re.search(r'FDS(\d+)', last_product['codigo'])
            if match:
                last_code_number = int(match.group(1))
        new_code_number = last_code_number + 1
        new_codigo = f"FDS{new_code_number:06d}"
    except Exception as e:
        return jsonify({"msg": f"Erro ao gerar o código interno do produto: {str(e)}"}), 500

    # 5️⃣ Upload do PDF para o S3
    try:
        s3_key_from_s3, pdf_url_from_s3 = upload_to_s3(pdf_file, product_name)
    except Exception as e:
        return jsonify({"msg": f"Erro ao enviar arquivo para o S3: {str(e)}"}), 500

    # 6️⃣ Montagem do novo produto e VALIDAÇÃO DO NÚMERO CAS
    substancias = []
    if 'substancias' in data and isinstance(data['substancias'], list):
        for s in data['substancias']:
            cas_number = s.get('cas', '')
            substance_name = s.get('nome', 'Nome não informado')

            # Se um número CAS foi fornecido, ele DEVE ser válido.
            if cas_number and not is_valid_cas_number(cas_number):
                # Se for inválido, interrompe o processo e avisa o usuário.
                return jsonify({
                    "msg": f"O número CAS '{cas_number}' para a substância '{substance_name}' é inválido. Por favor, digite novamente."
                }), 400
            
            # Se a validação passou (ou o campo estava vazio), adiciona à lista.
            substancias.append({
                'nome': substance_name,
                'cas': cas_number,
                'concentracao': s.get('concentracao', ''),
            })

    new_product = Product(
        codigo=new_codigo,
        qtade_maxima_armazenada=data.get('qtade_maxima_armazenada'),
        nome_do_produto=product_name,
        fornecedor=data.get('fornecedor'),
        estado_fisico=data.get('estado_fisico'),
        local_de_armazenamento=data.get('local_de_armazenamento'),
        substancias=substancias,
        perigos_fisicos=data.get('perigos_fisicos', []),
        perigos_saude=data.get('perigos_saude', []),
        perigos_meio_ambiente=data.get('perigos_meio_ambiente', []),
        palavra_de_perigo=data.get('palavra_de_perigo'),
        categoria=data.get('categoria'),
        status=data.get('status') or 'pendente',
        created_by_user_id=creator_user_id,
        pdf_url=pdf_url_from_s3,
        pdf_s3_key=s3_key_from_s3,
        empresa=data.get('empresa'),
        file_hash=file_hash,
    )

    # 7️⃣ Inserção no MongoDB
    try:
        product_dict = new_product.to_dict()
        product_dict["created_at"] = datetime.now(timezone.utc)
        product_dict["updated_at"] = datetime.now(timezone.utc)
        result = Product.collection().insert_one(product_dict)
        new_product._id = result.inserted_id
        product_dict["_id"] = new_product._id
        serialized = _serialize_product(product_dict)

        return jsonify({
            "msg": f"{new_codigo} - {data.get('nome_do_produto')} cadastrado com sucesso!",
            "product": serialized,
            "id": serialized["id"]
        }), 201

    except Exception as e:
        return jsonify({"msg": f"Erro ao criar o produto: {str(e)}"}), 500
# ============================================================
# LIST PRODUCTS
# ============================================================
@product_bp.route('/products', methods=['GET'])
@role_required([ROLES['1'], ROLES['2']])
def list_products():
    try:
        status_filter = request.args.get('status')
        query = {}
        if status_filter:
            query['status'] = status_filter

        cursor = Product.collection().find(query).sort([('_id', -1)])
        products = [_serialize_product(doc) for doc in cursor]

        return jsonify(products), 200

    except Exception as e:
        return jsonify({"msg": f"Erro ao listar produtos: {str(e)}"}), 500


# ============================================================
# GET PRODUCT BY ID
# ============================================================
#COMENTADO CODIGO ANTES
#@product_bp.route('/products/<product_id>', methods=['GET'])
#@role_required([ROLES['ADMIN'], ROLES['ANALYST']])
#def get_product(product_id):
#    try:
#        _id = ObjectId(product_id)
#    except Exception:
#        return jsonify({"msg": "ID do produto inválido."}), 400
#

#Adicionada validação robusta de ObjectId para prevenir NoSQL injection. codigo novo
def is_valid_objectid(id_str):
    """Valida se uma string é um ObjectId válido"""
    try:
        ObjectId(id_str)
        return True
    except:
        return False

@product_bp.route('/products/<product_id>', methods=['GET'])
@role_required([ROLES['1'], ROLES['2']])
def get_product(product_id):
    if not is_valid_objectid(product_id):
        return jsonify({"msg": "ID do produto inválido."}), 400

    try:
        # 🎯 CORREÇÃO: Adicionamos a definição da variável `_id`
        _id = ObjectId(product_id)
        doc = Product.collection().find_one({"_id": _id})
        if not doc:
            return jsonify({"msg": "Produto não encontrado."}), 404

        return jsonify(_serialize_product(doc)), 200

    except Exception as e:
        return jsonify({"msg": f"Erro ao buscar produto: {str(e)}"}), 500


# ============================================================
# UPDATE PRODUCT (VERSÃO CORRIGIDA)
# ============================================================
@product_bp.route('/products/<product_id>', methods=['PUT'])
@role_required([ROLES['1'], ROLES['2']])
def update_product(product_id):
    current_user_id = get_jwt_identity()
    try:
        _id = ObjectId(product_id)
        current_oid = ObjectId(current_user_id)
    except Exception:
        return jsonify({"msg": "ID inválido."}), 400

    # 1. 🔄 ALTERAÇÃO PRINCIPAL: Ler dados do formulário multipart
    # Em vez de request.get_json(), lemos o campo 'productData' do formulário
    # e o convertemos de uma string JSON para um dicionário Python.
    try:
        data = json.loads(request.form['productData'])
    except (KeyError, json.JSONDecodeError):
        return jsonify({"msg": "Dados do produto (productData) não encontrados ou em formato inválido."}), 400

    try:
        doc = Product.collection().find_one({"_id": _id})
        if not doc:
            return jsonify({"msg": "Produto não encontrado."}), 404

        # ... (Sua lógica de permissão continua a mesma e está correta) ...
        user_role = User.collection().find_one({"_id": current_oid}, {"role": 1})
        role_value = user_role.get("role") if user_role else None

        if role_value == ROLES['2']:
            if str(doc.get("created_by_user_id")) != str(current_oid):
                return jsonify({"msg": "Você não tem permissão para editar este produto."}), 403
            if doc.get("status") == "aprovado":
                return jsonify({"msg": "Produto aprovado não pode ser editado por analista."}), 403

        # Prepara o documento de atualização com os dados recebidos do formulário
        fields_allowed = {
            'qtade_maxima_armazenada', 'nome_do_produto', 'fornecedor', 'estado_fisico', 
            'local_de_armazenamento', 'substancias', 'perigos_fisicos', 'perigos_saude', 
            'perigos_meio_ambiente', 'palavra_de_perigo', 'categoria', 'empresa'
        }
        update_doc = {k: v for k, v in data.items() if k in fields_allowed}

        # 2. 📂 ADIÇÃO: Lógica para tratar o upload de um novo arquivo
        # Verificamos se um novo arquivo foi enviado na requisição.
        if 'file' in request.files:
            pdf_file = request.files['file']
            # Garante que o arquivo tem um nome e não está vazio
            if pdf_file and pdf_file.filename != '':
                # Lógica para fazer upload do novo arquivo para o S3
                # (Você precisará deletar o antigo se a sua regra de negócio exigir)
                # Exemplo:
                # delete_from_s3(doc.get('pdf_s3_key')) # Deleta o antigo
                s3_key, pdf_url = upload_to_s3(pdf_file, update_doc['nome_do_produto'])
                
                # Adiciona as novas URLs ao documento de atualização
                update_doc['pdf_url'] = pdf_url
                update_doc['pdf_s3_key'] = s3_key

        # 3. ➕ ADIÇÃO: Lógica de status (se o admin estiver editando)
        # Permite que o admin altere o status na mesma requisição de edição.
        if role_value == ROLES['1'] and 'status' in data:
            if data['status'] in {"aprovado", "rejeitado", "pendente"}:
                update_doc['status'] = data['status']

        update_doc["updated_at"] = datetime.now(timezone.utc)

        Product.collection().update_one({"_id": _id}, {"$set": update_doc})

        updated = Product.collection().find_one({"_id": _id})
        return jsonify({
            "msg": "Produto atualizado com sucesso.",
            "product": _serialize_product(updated)
        }), 200

    except Exception as e:
        # Adiciona logging para depuração no futuro
        current_app.logger.error(f"Erro ao atualizar produto {_id}: {e}")
        return jsonify({"msg": f"Erro ao atualizar produto: {str(e)}"}), 500


# ============================================================
# UPDATE STATUS
# ============================================================
@product_bp.route('/products/<product_id>/status', methods=['PUT'])
@role_required([ROLES['1']])
def update_product_status(product_id):
    try:
        _id = ObjectId(product_id)
    except Exception:
        return jsonify({"msg": "ID do produto inválido."}), 400

    data = request.get_json() or {}
    status = (data.get("status") or "").strip().lower()

    if status not in {"aprovado", "rejeitado", "pendente"}:
        return jsonify({"msg": "Status inválido. Use: aprovado, rejeitado ou pendente."}), 400

    try:
        result = Product.collection().update_one(
            {"_id": _id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            return jsonify({"msg": "Produto não encontrado."}), 404

        updated = Product.collection().find_one({"_id": _id})
        return jsonify({
            "msg": f"Status atualizado para '{status}' com sucesso.",
            "product": _serialize_product(updated)
        }), 200

    except Exception as e:
        return jsonify({"msg": f"Erro ao atualizar status do produto: {str(e)}"}), 500


# ============================================================
# DELETE PRODUCT (VERSÃO APRIMORADA)
# ============================================================
@product_bp.route('/products/<product_id>', methods=['DELETE'])
@role_required([ROLES['1']])
def delete_product(product_id):
    try:
        _id = ObjectId(product_id)
    except Exception:
        return jsonify({"msg": "ID do produto inválido."}), 400

    try:
        # 1. Encontrar o produto ANTES de apagar
        product_to_delete = Product.collection().find_one({"_id": _id})

        if not product_to_delete:
            return jsonify({"msg": "Produto não encontrado."}), 404

        # 2. Verificar se há um arquivo no S3 para apagar
        s3_key = product_to_delete.get("pdf_s3_key")
        if s3_key:
            try:
                # Inicializa o cliente S3 (pode ser global ou dentro da função)
                s3 = boto3.client("s3")
                bucket_name = os.getenv("AWS_BUCKET_NAME")
                
                # 3. Mandar o comando para apagar o objeto do S3
                s3.delete_object(Bucket=bucket_name, Key=s3_key)
                logging.info(f"Arquivo {s3_key} excluído do S3 com sucesso.")

            except Exception as s3_error:
                # Se der erro ao apagar do S3, logamos o erro mas continuamos
                # para apagar do DB. Ou você pode optar por parar a operação aqui.
                logging.error(f"Erro ao excluir arquivo {s3_key} do S3: {s3_error}")
                # return jsonify({"msg": "Erro ao remover arquivo associado no S3."}), 500

        # 4. Apagar o registro do MongoDB
        result = Product.collection().delete_one({"_id": _id})
        
        # Esta verificação se torna um pouco redundante se já fizemos o find_one, mas é segura
        if result.deleted_count == 0:
            return jsonify({"msg": "Produto não encontrado no momento da exclusão final."}), 404
            
        return jsonify({"msg": "Produto e arquivo associado foram excluídos com sucesso."}), 200

    except Exception as e:
        return jsonify({"msg": f"Erro ao excluir produto: {str(e)}"}), 500

# ==============================================================================
# ROTA PARA GERAR LINK DE DOWNLOAD/VISUALIZAÇÃO DE FDS
# ==============================================================================

# O decorator @product_bp.route define a URL e o método HTTP para esta função.
# A URL será /products/<product_id>/download, onde <product_id> é uma variável.
# O decorator @jwt_required() protege a rota, exigindo que o usuário esteja autenticado com um token JWT válido.
@product_bp.route('/products/<product_id>/download', methods=['GET'])
@jwt_required()
def download_fds(product_id):
    """
    Gera um link temporário (presigned URL) para o arquivo PDF do produto no S3.
    Este link permite o download ou a visualização pública por um tempo limitado,
    forçando o navegador a tentar exibir o arquivo em vez de baixá-lo.
    """
    # O bloco try...except captura qualquer erro inesperado que possa ocorrer,
    # evitando que o servidor quebre e retornando uma mensagem de erro amigável.
    try:
        # 1. VALIDAÇÃO DO PRODUTO
        # ========================
        
        # Busca a identidade do usuário (geralmente o ID) a partir do token JWT.
        user_id = get_jwt_identity()

        # Busca no banco de dados (MongoDB) o documento do produto pelo seu ID.
        # ObjectId(product_id) converte a string da URL para o formato de ID do MongoDB.
        product = Product.collection().find_one({"_id": ObjectId(product_id)})

        # Se nenhum produto for encontrado com o ID fornecido, retorna um erro 404 (Não Encontrado).
        if not product:
            return jsonify({"msg": "Produto não encontrado"}), 404

        # 2. VERIFICAÇÃO DO ARQUIVO PDF
        # ==============================

        # Pega o caminho (chave) do arquivo PDF armazenado no S3 a partir do documento do produto.
        file_key = product.get("pdf_s3_key")

        # Se o produto não tiver uma chave de PDF associada, significa que não há arquivo para baixar.
        if not file_key:
            return jsonify({"msg": "Arquivo FDS não encontrado para este produto"}), 404

        # 3. INICIALIZAÇÃO DO CLIENTE S3
        # ===============================
        
        # A variável s3_client é global. Verificamos se ela já foi inicializada.
        global s3_client
        if not s3_client:
            # Se não foi, chama a função auxiliar para criar um novo cliente S3.
            s3_client = get_aws_client('s3')
            # Se a inicialização falhar (ex: credenciais erradas), loga um erro e retorna uma resposta 500.
            if not s3_client:
                logging.error("Falha ao inicializar o cliente AWS S3 no momento da requisição.")
                return jsonify({"msg": "Erro interno: Serviço de armazenamento não configurado"}), 500

        # 4. GERAÇÃO DO LINK TEMPORÁRIO (PRESIGNED URL)
        # ===============================================

        # Loga uma informação útil no console do servidor para depuração.
        logging.info(f"Gerando presigned URL para bucket '{s3_bucket_name}' e chave '{file_key}'")

        # Esta é a função principal que pede ao S3 para criar uma URL de acesso temporário.
        presigned_url = s3_client.generate_presigned_url(
            # O método 'get_object' especifica que a URL será usada para buscar (visualizar/baixar) um objeto.
            ClientMethod='get_object',
            # 'Params' contém os detalhes do pedido que será feito quando a URL for acessada.
            Params={
                'Bucket': s3_bucket_name,  # O nome do seu bucket no S3.
                'Key': file_key,          # O caminho completo do arquivo dentro do bucket.
                
                # ✅ ALTERAÇÃO PRINCIPAL: Controle de como o arquivo é apresentado.
                # 'ResponseContentDisposition': 'inline' instrui o S3 a dizer ao navegador
                # para tentar ABRIR/EXIBIR o arquivo na própria aba, em vez de forçar o download.
                'ResponseContentDisposition': 'inline',

                # 'ResponseContentType': 'application/pdf' garante que o navegador saiba que
                # o arquivo é um PDF, ajudando-o a usar o visualizador correto.
                'ResponseContentType': 'application/pdf'
            },
            # Define o tempo de validade do link em segundos. Aqui, 600 segundos = 10 minutos.
            ExpiresIn=600
        )

        # 5. RETORNO DA RESPOSTA
        # =======================

        # Retorna a URL gerada em um objeto JSON. O front-end espera uma chave chamada "download_url".
        # O status 200 (OK) indica que a operação foi bem-sucedida.
        return jsonify({"download_url": presigned_url}), 200

    # Captura qualquer exceção não tratada que possa ter ocorrido.
    except Exception as e:
        # Loga o erro completo no console do servidor para análise posterior.
        logging.error(f"Erro inesperado ao gerar link temporário: {e}", exc_info=True)
        # Retorna uma mensagem de erro genérica para o usuário com status 500 (Erro Interno do Servidor).
        return jsonify({"msg": "Erro interno ao processar a solicitação de download"}), 500



def upload_to_s3(file_obj, product_name): # 👈 Alteramos o segundo argumento
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    bucket_name = os.getenv("AWS_BUCKET_NAME")
    
    # ✅ NOVO: Lógica para criar um nome de arquivo seguro a partir do nome do produto
    # Ex: "Óleo Lubrificante / XPTO" -> "oleo_lubrificante_xpto"
    clean_name = secure_filename(product_name).replace(' ', '_').lower()
    
    # Adicionamos um sufixo único para evitar qualquer chance de colisão de nomes
    unique_suffix = str(uuid.uuid4())[:8] 
    
    # O nome do arquivo final será algo como: "oleo_lubrificante_xpto_a1b2c3d4.pdf"
    unique_filename = f"{clean_name}_{unique_suffix}.pdf"
    
    key = f"uploads/{unique_filename}"

    s3.upload_fileobj(file_obj, bucket_name, key)

    url = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{key}"
    return key, url


