# app/routes/pdf_routes.py

# ============================================================
# IMPORTS
# ============================================================
import os
import logging
import re
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import boto3
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
from flask_jwt_extended import get_jwt_identity
from bson.objectid import ObjectId
from bson.errors import InvalidId
from app.models import User, Product
from app.utils import ROLES, role_required
from app.security_config import limiter

load_dotenv()

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================
class SensitiveDataFilter(logging.Filter):
    """Filtro para remover informações sensíveis dos logs"""
    def filter(self, record):
        if hasattr(record, 'msg'):
            sensitive_patterns = [
                r'(aws_access_key_id|aws_secret_access_key|password|token|secret)=[^&\s]*',
                r'(\bAKIA[0-9A-Z]{16}\b)',
                r'(\b[0-9a-fA-F]{40}\b)',
                r'(mongo_uri|mongodb\+srv://)[^@\s]*@[^\s]*'
            ]
            for pattern in sensitive_patterns:
                record.msg = re.sub(pattern, r'\1=***', str(record.msg))
        return True

# Configurar logging com filtro de segurança
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

for handler in logging.getLogger().handlers:
    handler.addFilter(SensitiveDataFilter())

# ============================================================
# BLUEPRINT E CONEXÕES GLOBAIS
# ============================================================
pdf_bp = Blueprint("pdf", __name__)
CORS(pdf_bp, resources={r"/*": {"origins": "*"}})

# Variáveis globais que serão inicializadas pela função init_services
# Elas começam como None e recebem as conexões ativas quando o app inicia.
s3_client = None
s3_bucket_name = os.getenv("AWS_BUCKET_NAME")
pdf_metadata_collection = None


# ============================================================
# FUNÇÃO DE INICIALIZAÇÃO DOS SERVIÇOS (NOVA FUNÇÃO)
# ============================================================
def init_services():
    """
    Inicializa as conexões com MongoDB e AWS S3.
    Esta função é chamada uma vez quando a aplicação Flask é iniciada.
    """
    # A palavra-chave 'global' nos permite modificar as variáveis declaradas fora desta função.
    global s3_client, pdf_metadata_collection
    
    logging.info("Inicializando conexões com serviços externos (MongoDB, S3)...")

    # 1. Conexão com AWS S3: Só tenta conectar se ainda não houver um cliente.
    if not s3_client:
        s3_client = get_aws_client('s3')
        if s3_client:
            logging.info("Cliente AWS S3 inicializado com sucesso.")
        else:
            logging.error("Falha ao inicializar o cliente AWS S3. Verifique as credenciais e configurações no .env.")

    # 2. Conexão com MongoDB: Só tenta conectar se a coleção não estiver definida.
    if not pdf_metadata_collection:
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB_NAME")

        if not mongo_uri or not db_name:
            logging.error("MONGO_URI ou MONGO_DB_NAME não encontrados nas variáveis de ambiente.")
            return

        try:
            mongo_client = MongoClient(mongo_uri)
            db = mongo_client[db_name]
            # Define a coleção específica que usaremos para os metadados dos PDFs.
            pdf_metadata_collection = db.pdf_metadata
            logging.info(f"Conectado ao MongoDB no banco de dados '{db_name}' com sucesso.")
        except Exception as e:
            logging.error(f"Não foi possível conectar ao MongoDB: {e}")

# ============================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================

def is_valid_objectid(id_str):
    """Valida se uma string é um ObjectId válido"""
    try:
        ObjectId(id_str)
        return True
    except (InvalidId, TypeError):
        return False

def get_aws_client(service_name):
    """Obtém cliente AWS de forma segura"""
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    if not all([aws_access_key_id, aws_secret_access_key, aws_region]):
        logging.error("Configuração AWS incompleta")
        return None
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        return session.client(service_name)
    except Exception as e:
        logging.error(f"Erro ao inicializar cliente AWS: {type(e).__name__}")
        return None

# ============================================================
# ROTAS
# ============================================================

@pdf_bp.route('/upload/<product_id>', methods=['POST'])
@role_required([ROLES['1']])
@limiter.limit("10 per hour")
def upload_file(product_id):
    """
    Upload de arquivos PDF para S3, armazenamento de metadados no MongoDB
    e associação do PDF ao produto especificado.
    """
    logging.info(f"Recebendo requisição de upload para o produto ID: {product_id}")

    # Validação inicial do ID do produto
    if not is_valid_objectid(product_id):
        return jsonify({"error": "ID de produto inválido"}), 400

    if s3_client is None or s3_bucket_name is None:
        logging.error("Configuração do AWS S3 inválida no momento da requisição.")
        return jsonify({"error": "Configuração do serviço de armazenamento inválida"}), 500

    if pdf_metadata_collection is None or Product.collection() is None:
        logging.error("Configuração do MongoDB inválida no momento da requisição.")
        return jsonify({"error": "Configuração do banco de dados inválida"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    try:
        # 1. Upload para o S3 (como já estava)
        original_file_name = file.filename
        file_extension = os.path.splitext(original_file_name)[1]
        unique_s3_file_name = f"{uuid.uuid4()}{file_extension}"
        file_key = f"uploads/{unique_s3_file_name}"

        s3_client.upload_fileobj(file, s3_bucket_name, file_key)

        file_url = f"https://{s3_bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_key}"

        # 2. Criação dos metadados (como já estava)
        current_user_id = get_jwt_identity()
        if not is_valid_objectid(current_user_id):
            return jsonify({"error": "Erro de autenticação"}), 401
        
        # ALTERAÇÃO 2: Adicionamos o ID do produto aos metadados para referência futura.
        pdf_document_metadata = {
            "original_filename": original_file_name,
            "s3_file_key": file_key,
            "url": file_url,
            "uploaded_at": datetime.now(timezone.utc),
            "uploaded_by_user_id": ObjectId(current_user_id),
            "associated_product_id": ObjectId(product_id) 
        }

        insert_result = pdf_metadata_collection.insert_one(pdf_document_metadata)
        
        # ALTERAÇÃO 3: Atualizar o documento do produto com a URL do PDF.
        # Esta é a etapa crucial que estava faltando.
        update_result = Product.collection().update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {
                "pdf_url": file_url,
                "pdf_s3_key": file_key,
                "pdf_metadata_id": insert_result.inserted_id,
                "updated_at": datetime.now(timezone.utc)
            }}
        )

        # Se nenhum produto foi encontrado com o ID fornecido
        if update_result.matched_count == 0:
            logging.warning(f"Upload bem-sucedido, mas produto com ID {product_id} não foi encontrado para associação.")
            # Opcional: deletar o arquivo do S3 e os metadados se o produto não existe
            s3_client.delete_object(Bucket=s3_bucket_name, Key=file_key)
            pdf_metadata_collection.delete_one({"_id": insert_result.inserted_id})
            return jsonify({"error": "Produto não encontrado"}), 404

        return jsonify({
            "message": "Arquivo enviado e associado ao produto com sucesso",
            "url": file_url,
            "s3_file_key": file_key,
            "id": str(insert_result.inserted_id)
        }), 200

    except Exception as e:
        # Melhoramos o log de erro para nos dar mais detalhes sobre o que falhou
        logging.error(f"Erro inesperado no upload: {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro interno no servidor ao processar o arquivo."}), 500


@pdf_bp.route('/pdfs', methods=['GET'])
@role_required([ROLES['1'], ROLES['2'], ROLES['3']])
@limiter.limit("30 per minute")
def get_pdfs():
    """
    Lista PDFs associados a produtos
    """
    logging.info("Listando PDFs disponíveis...")

    if Product.collection() is None:
        return jsonify({"error": "Configuração da coleção de produtos inválida"}), 500

    current_user_id_str = get_jwt_identity()
    if not is_valid_objectid(current_user_id_str):
        return jsonify({"error": "Erro de autenticação"}), 401

    try:
        current_user_data = User.collection().find_one(
            {"_id": ObjectId(current_user_id_str)},
            {"username": 1, "role": 1, "active": 1}
        )

        if not current_user_data or not current_user_data.get('active', True):
            return jsonify({"error": "Usuário não autorizado"}), 403

        current_user = User.from_dict(current_user_data)

        query_filter = {"pdf_url": {"$exists": True, "$ne": None}}
        projection = {}

        if current_user.role == ROLES['3']:
            query_filter["status"] = "aprovado"
            projection = {
                "_id": 1,
                "nome_do_produto": 1,
                "qtade_maxima_armazenada": 1,
                "pdf_url": 1
            }
        elif current_user.role == ROLES['2']:
            query_filter["$or"] = [
                {"status": "aprovado"},
                {"created_by_user_id": current_user_id_str}
            ]
        # ADMIN=1 vê todos

        products_with_pdfs = []
        products_cursor = Product.collection().find(query_filter, projection)

        for p_data in products_cursor:
            p_data['_id'] = str(p_data['_id'])
            if 'pdf_url' in p_data:
                p_data['url_download'] = p_data.pop('pdf_url')
            products_with_pdfs.append(p_data)

        return jsonify(products_with_pdfs), 200

    except Exception as e:
        logging.error(f"Erro ao buscar PDFs: {type(e).__name__}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@pdf_bp.route('/pdfs/<pdf_id>', methods=['DELETE'])
@role_required([ROLES['1']])
@limiter.limit("5 per hour")
def delete_pdf(pdf_id):
    """
    Deleta um PDF do S3 e seus metadados no MongoDB
    """
    if not is_valid_objectid(pdf_id):
        return jsonify({"error": "ID inválido"}), 400

    try:
        pdf_data = pdf_metadata_collection.find_one({"_id": ObjectId(pdf_id)})
        if not pdf_data:
            return jsonify({"error": "PDF não encontrado"}), 404

        if s3_client and 's3_file_key' in pdf_data:
            try:
                s3_client.delete_object(Bucket=s3_bucket_name, Key=pdf_data['s3_file_key'])
            except Exception as e:
                logging.error(f"Erro ao deletar do S3: {type(e).__name__}")

        result = pdf_metadata_collection.delete_one({"_id": ObjectId(pdf_id)})

        if result.deleted_count == 0:
            return jsonify({"error": "PDF não encontrado"}), 404

        return jsonify({"message": "PDF deletado com sucesso"}), 200

    except Exception as e:
        logging.error(f"Erro ao deletar PDF: {type(e).__name__}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@pdf_bp.route('/health', methods=['GET'])
@limiter.limit("10 per minute")
def health_check():
    """
    Verifica a saúde do serviço de PDFs
    """
    try:
        if pdf_metadata_collection:
            pdf_metadata_collection.find_one()

        if s3_client and s3_bucket_name:
            s3_client.head_bucket(Bucket=s3_bucket_name)

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "mongodb": "connected" if pdf_metadata_collection else "disconnected",
                "aws_s3": "connected" if s3_client else "disconnected"
            }
        }), 200

    except Exception as e:
        logging.error(f"Health check failed: {type(e).__name__}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Service unavailable"
        }), 503
