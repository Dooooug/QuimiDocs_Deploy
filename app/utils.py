# app/utils.py

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import functools
import logging

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