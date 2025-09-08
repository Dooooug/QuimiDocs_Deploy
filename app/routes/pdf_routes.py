import os
import logging
import re
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import boto3
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import uuid
from flask_jwt_extended import get_jwt_identity
from bson.objectid import ObjectId
from bson.errors import InvalidId

# Importa as classes User e Product
from app.models import User, Product
# Importa o decorador role_required e a constante ROLES
from app.utils import ROLES, role_required
# Importa o limiter centralizado
from app.security_config import limiter

load_dotenv()

# ============================================================
# CONFIGURAÇÃO DE LOGGING COM FILTRO DE SEGURANÇA
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
# BLUEPRINT
# ============================================================

pdf_bp = Blueprint("pdf", __name__)
CORS(pdf_bp, resources={r"/*": {"origins": "*"}})

# Conexões globais (MongoDB e AWS S3)
s3_client = None
s3_bucket_name = os.getenv("AWS_BUCKET_NAME")
pdf_metadata_collection = None

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

@pdf_bp.route('/upload', methods=['POST'])
@role_required([ROLES['1']])
@limiter.limit("10 per hour")  # Limite de 10 uploads por hora por admin
def upload_file():
    """
    Upload de arquivos PDF para S3 e armazenamento de metadados no MongoDB
    """
    logging.info("Recebendo requisição de upload de arquivo...")

    if s3_client is None or s3_bucket_name is None:
        return jsonify({"error": "Configuração do AWS S3 inválida"}), 500

    if pdf_metadata_collection is None:
        return jsonify({"error": "Configuração do MongoDB inválida"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    try:
        original_file_name = file.filename
        file_extension = os.path.splitext(original_file_name)[1]
        unique_s3_file_name = f"{uuid.uuid4()}{file_extension}"
        file_key = f"uploads/{unique_s3_file_name}"

        s3_client.upload_fileobj(file, s3_bucket_name, file_key)

        file_url = f"https://{s3_bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_key}"

        current_user_id = get_jwt_identity()
        if not is_valid_objectid(current_user_id):
            return jsonify({"error": "Erro de autenticação"}), 401

        pdf_document_metadata = {
            "original_filename": original_file_name,
            "s3_file_key": file_key,
            "url": file_url,
            "uploaded_at": datetime.utcnow(),
            "uploaded_by_user_id": ObjectId(current_user_id)
        }

        insert_result = pdf_metadata_collection.insert_one(pdf_document_metadata)

        return jsonify({
            "message": "Arquivo enviado com sucesso",
            "url": file_url,
            "s3_file_key": file_key,
            "id": str(insert_result.inserted_id),
            "original_filename": original_file_name
        }), 200

    except boto3.exceptions.S3UploadFailedError:
        return jsonify({"error": "Erro ao enviar arquivo"}), 500
    except Exception as e:
        logging.error(f"Erro inesperado: {type(e).__name__}")
        return jsonify({"error": "Erro interno do servidor"}), 500

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
            "timestamp": datetime.utcnow().isoformat(),
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
