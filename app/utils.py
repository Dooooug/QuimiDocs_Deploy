# app/utils.py

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import functools
import logging
import os
import boto3

# Importa a classe User do módulo models
from app.models import User

# Define os papéis (roles) disponíveis na aplicação
ROLES = {
    '1': 'administrador',
    '2': 'analista',
    '3': 'visualizador'
}

def is_valid_objectid(oid):
    """Valida se o ID é um ObjectId válido do MongoDB."""
    try:
        ObjectId(str(oid))
        return True
    except Exception:
        return False

def role_required(required_roles):
    def decorator(fn):
        @functools.wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()

                if not current_user_id or not is_valid_objectid(current_user_id):
                    return jsonify({"msg": "Token inválido"}), 401
                
                user_collection = User.collection()
                if user_collection is None:
                    logging.error("A coleção de usuários não está inicializada. Verifique a conexão com o banco de dados na inicialização do app.")
                    return jsonify({"msg": "Erro de serviço: A conexão com o banco de dados não está disponível."}), 503

                user_data = user_collection.find_one(
                    {"_id": ObjectId(current_user_id)},
                    {"username": 1, "role": 1, "active": 1}
                )

                if not user_data:
                    return jsonify({"msg": "Usuário não encontrado"}), 404

                if not user_data.get('active', True):
                    return jsonify({"msg": "Usuário desativado"}), 403

                user_role = user_data.get('role')
                if not (
                    user_role in required_roles or
                    ROLES.get(str(user_role)) in required_roles
                ):
                    logging.warning(f"Tentativa de acesso não autorizado: {current_user_id}")
                    return jsonify({"msg": "Acesso negado: Nível de permissão insuficiente"}), 403

                return fn(*args, **kwargs)
            
            except Exception as e:
                logging.error(f"Erro inesperado na verificação de role: {str(e)}")
                return jsonify({"msg": "Erro de autorização"}), 500
        return wrapper
    return decorator

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