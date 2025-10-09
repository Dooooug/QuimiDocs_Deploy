# app/routes/product_routes.py
from flask import request, jsonify, Blueprint
from flask_jwt_extended import get_jwt_identity
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
import re
import json
from app.models import Product, User
from app.utils import ROLES, role_required
import boto3, uuid, os
from datetime import datetime, timezone

product_bp = Blueprint('product', __name__)

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

    # 4️⃣ Geração do código do produto (antes do upload!)
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

    # 5️⃣ Upload real do PDF para o S3
    try:
        s3_key_from_s3, pdf_url_from_s3 = upload_to_s3(pdf_file, new_codigo)
    except Exception as e:
        return jsonify({"msg": f"Erro ao enviar arquivo para o S3: {str(e)}"}), 500

    # 6️⃣ Montagem do novo produto com a URL real do S3
    substancias = []
    if 'substancias' in data and isinstance(data['substancias'], list):
        for s in data['substancias']:
            substancias.append({
                'nome': s.get('nome', ''),
                'cas': s.get('cas', ''),
                'concentracao': s.get('concentracao', ''),
            })

    new_product = Product(
        codigo=new_codigo,
        qtade_maxima_armazenada=data.get('qtade_maxima_armazenada'),
        nome_do_produto=data.get('nome_do_produto'),
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
        pdf_url=pdf_url_from_s3,      # ✅ URL real do S3
        pdf_s3_key=s3_key_from_s3,    # ✅ Caminho real dentro do bucket
        empresa=data.get('empresa'),
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
# UPDATE PRODUCT
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

    data = request.get_json() or {}

    try:
        doc = Product.collection().find_one({"_id": _id})
        if not doc:
            return jsonify({"msg": "Produto não encontrado."}), 404

        user_role = User.collection().find_one({"_id": current_oid}, {"role": 1})
        role_value = user_role.get("role") if user_role else None

        if role_value == ROLES['2']:
            if str(doc.get("created_by_user_id")) != str(current_oid):
                return jsonify({"msg": "Você não tem permissão para editar este produto."}), 403
            if doc.get("status") == "aprovado":
                return jsonify({"msg": "Produto aprovado não pode ser editado por analista."}), 403

        fields_allowed = {
            'qtade_maxima_armazenada',
            'nome_do_produto',
            'fornecedor',
            'estado_fisico',
            'local_de_armazenamento',
            'substancias',
            'perigos_fisicos',
            'perigos_saude',
            'perigos_meio_ambiente',
            'palavra_de_perigo',
            'categoria',
            'pdf_url',
            'pdf_s3_key',
            'empresa'
        }

        update_doc = {k: v for k, v in data.items() if k in fields_allowed}
        update_doc["updated_at"] = datetime.now(timezone.utc)

        Product.collection().update_one({"_id": _id}, {"$set": update_doc})

        updated = Product.collection().find_one({"_id": _id})
        return jsonify({
            "msg": "Produto atualizado com sucesso.",
            "product": _serialize_product(updated)
        }), 200

    except Exception as e:
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
# DELETE PRODUCT
# ============================================================
@product_bp.route('/products/<product_id>', methods=['DELETE'])
@role_required([ROLES['1']])
def delete_product(product_id):
    try:
        _id = ObjectId(product_id)
    except Exception:
        return jsonify({"msg": "ID do produto inválido."}), 400

    try:
        result = Product.collection().delete_one({"_id": _id})
        if result.deleted_count == 0:
            return jsonify({"msg": "Produto não encontrado."}), 404
        return jsonify({"msg": "Produto excluído com sucesso."}), 200
    except Exception as e:
        return jsonify({"msg": f"Erro ao excluir produto: {str(e)}"}), 500



def upload_to_s3(file_obj, filename_prefix):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    bucket_name = os.getenv("AWS_BUCKET_NAME")
    unique_name = f"{filename_prefix}_{uuid.uuid4()}.pdf"
    key = f"uploads/{unique_name}"

    s3.upload_fileobj(file_obj, bucket_name, key)

    url = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{key}"
    return key, url
