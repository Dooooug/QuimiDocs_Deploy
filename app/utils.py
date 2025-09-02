# app/utils.py

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import functools
import logging

# Importa a classe User do módulo models (certifique-se que app/models.py está correto)
from app.models import User

# Define os papéis (roles) disponíveis na aplicação
ROLES = {
    'ADMIN': 'administrador',
    'ANALYST': 'analista',
    'VIEWER': 'visualizador'
}#Douglas uma sugestao as "roles" poderiam estar em um arquivo separado tipo config.py ou roles.py 
# ao inves de usar ADMIN, ANALYST, VIEWER poderia ser por numero tipo 1, 2, 3
# para facilitar a comparacao e economizar espaco no banco de dados e na transferencia de dados
#e obrigatorio ? nao, so uma sugestao que nao impacta nada


def is_valid_objectid(oid):
    """Valida se o ID é um ObjectId válido do MongoDB."""
    try:
        ObjectId(str(oid))
        return True
    except Exception:
        return False


#CODIGO ANTES
'''
def role_required(required_roles):
    """
    Decorador para verificar se o usuário autenticado tem um dos papéis necessários.
    """
    def decorator(fn):
        @functools.wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            
            # Busca os dados do usuário no MongoDB usando a classe User
            user_data = User.collection().find_one({"_id": ObjectId(current_user_id)})
            if not user_data:
                return jsonify({"msg": "Usuário não encontrado"}), 404
            
            # Converte o dicionário do MongoDB para um objeto User
            user = User.from_dict(user_data)

            # Verifica se o papel do usuário está entre os papéis requeridos
            if user.role not in required_roles:
                return jsonify({"msg": "Acesso negado: Nível de permissão insuficiente"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
'''

#CODIGO NOVO
#Sistema de autorização robusto com validação de token, verificação de usuário ativo e proteção contra informações sensíveis.
def role_required(required_roles):
    def decorator(fn):
        @functools.wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()
                
                #Validação robusta do ID do usuário
                if not current_user_id or not is_valid_objectid(current_user_id):
                    return jsonify({"msg": "Token inválido"}), 401
                
                #Busca usuário com projeção segura
                user_data = User.collection().find_one(
                    {"_id": ObjectId(current_user_id)},
                    {"username": 1, "role": 1, "active": 1}  #Apenas campos necessários
                )
                
                if not user_data:
                    return jsonify({"msg": "Usuário não encontrado"}), 404
                
                #Verifica se usuário está ativo
                if not user_data.get('active', True):
                    return jsonify({"msg": "Usuário desativado"}), 403
                
                #Verificação de autorização
                if user_data.get('role') not in required_roles:
                    logging.warning(f"Tentativa de acesso não autorizado: {current_user_id}")
                    return jsonify({"msg": "Acesso negado: Nível de permissão insuficiente"}), 403
                    
                return fn(*args, **kwargs)
            except Exception as e:
                logging.error(f"Erro na verificação de role: {str(e)}")
                return jsonify({"msg": "Erro de autorização"}), 500
        return wrapper
    return decorator