# app/routes/user_routes.py

from flask import request, jsonify, Blueprint
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

# Importa a classe User do módulo models
from app.models import User
# Importa o decorador role_required e a constante ROLES do módulo utils
from app.utils import ROLES, role_required

# user_routes.py (adições necessárias)
from flask_limiter.util import get_remote_address
from app.security_config import RATE_LIMITS, get_limiter_key, limiter


# Configurar o limiter após criar o blueprint
user_bp = Blueprint('user', __name__)

# Rota de registro de usuário
#CODIGO ANTES
'''
@user_bp.route('/register', methods=['POST'])
def register():
    """
    Registra um novo usuário na aplicação.
    Requer 'nome_do_usuario', 'email' e 'senha'. 'nivel' é opcional (padrão: VIEWER).
    Aceita campos adicionais como cpf, empresa, setor, data_de_nascimento, planta.
    """
    data = request.get_json()

    # Extrai os campos obrigatórios do JSON
    nome_do_usuario = data.get('nome_do_usuario') # ATUALIZADO: Usando 'nome_do_usuario'
    email = data.get('email')
    senha = data.get('senha')
'''
#CODIGO DEPOIS
#Sistema completo de validação e sanitização de dados de entrada.
import re
from email_validator import validate_email, EmailNotValidError

def validate_email_address(email):
    """Valida endereço de email"""
    try:
        v = validate_email(email)
        return v.email
    except EmailNotValidError:
        return None

def validate_password(password):
    """Valida força da senha"""
    # 🎯 CORREÇÃO: Adicionada verificação para senha vazia
    if not password or len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def sanitize_input(input_str, max_length=255):
    """Remove caracteres potencialmente perigosos e espaços em branco desnecessários"""
    if not input_str or not isinstance(input_str, str):
        return None
    cleaned = re.sub(r'[<>\(\)\&\|\;\`\$]', '', input_str)
    # 🎯 CORREÇÃO: Adicionado .strip() para remover espaços em branco
    return cleaned[:max_length].strip() if cleaned else None

@user_bp.route('/register', methods=['POST'])
@limiter.limit("2 per hour")  # Limita a 2 registros por hora por IP
def register():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Dados de requisição inválidos ou ausentes"}), 400

    # 1. Extrair os dados brutos primeiro
    nome_do_usuario_bruto = data.get('nome_do_usuario')
    email_bruto = data.get('email')
    senha = data.get('senha')

    # 2. Validar a força da senha antes de qualquer outra coisa
    if not validate_password(senha):
        return jsonify({"msg": "Senha deve ter pelo menos 8 caracteres com letras maiúsculas, minúsculas e números"}), 400

    # 3. Validar e-mail antes da validação genérica de campos obrigatórios
    email = validate_email_address(email_bruto)
    if not email:
        return jsonify({"msg": "Endereço de email inválido"}), 400

    # 4. Sanitizar o nome de usuário. Se a sanitização falhar, retorne um erro.
    nome_do_usuario = sanitize_input(nome_do_usuario_bruto)

    # Verificação extra: nome vazio ou contendo termos perigosos após sanitização
    termos_proibidos = ["script", "alert", "onload", "iframe", "img", "svg", "object"]
    if not nome_do_usuario or nome_do_usuario.lower() in termos_proibidos:
        return jsonify({"msg": "Nome de usuário inválido"}), 400


    # 5. Finalmente, faça a validação genérica dos campos obrigatórios
    if not nome_do_usuario or not email or not senha:
        return jsonify({"msg": "Nome de usuário, email e senha são obrigatórios"}), 400
    

    # Verificação de usuários já existentes
    existing_user_by_name = User.collection().find_one({"nome_do_usuario": nome_do_usuario})
    if existing_user_by_name:
        return jsonify({"msg": "Nome de usuário já existe"}), 409
    
    existing_user_by_email = User.collection().find_one({"email": email})
    if existing_user_by_email:
        return jsonify({"msg": "Email já está em uso"}), 409

    role = data.get('nivel', ROLES['3']) 
    if role not in ROLES.values():
        return jsonify({"msg": "Role inválido"}), 400

    # Extrai os campos adicionais do JSON
    cpf = data.get('cpf')
    empresa = data.get('empresa')
    setor = data.get('setor')
    data_de_nascimento = data.get('data_de_nascimento')
    planta = data.get('planta')

    # Gera o hash da senha antes de armazenar
    hashed_password = generate_password_hash(senha)

    # Cria uma nova instância de User e insere no banco de dados com todos os campos
    new_user = User(
        username=nome_do_usuario,
        email=email,
        password_hash=hashed_password,
        role=role,
        cpf=cpf,
        empresa=empresa,
        setor=setor,
        data_de_nascimento=data_de_nascimento,
        planta=planta
    )
    result = User.collection().insert_one(new_user.to_dict())
    new_user._id = result.inserted_id

    # Retorna uma resposta de sucesso
    return jsonify({
        "msg": "Usuário registrado com sucesso",
        "user": {
            "id": str(new_user._id),
            "nome_do_usuario": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "cpf": new_user.cpf,
            "empresa": new_user.empresa,
            "setor": new_user.setor,
            "data_de_nascimento": new_user.data_de_nascimento,
            "planta": new_user.planta
        }
    }), 201

# Rota de login (sem alterações necessárias aqui para este problema)
@user_bp.route('/login', methods=['POST'])
@limiter.limit(RATE_LIMITS['login'])  # Limita a 5 tentativas de login por minuto por IP
def login():
    """
    Autentica um usuário e retorna um token de acesso JWT.
    Requer 'email' e 'senha'.
    """
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    if not email or not senha:
        return jsonify({"msg": "Email e senha são obrigatórios"}), 400

    # Busca o usuário no banco de dados pelo email
    user_data = User.collection().find_one({"email": email})

    # Verifica se o usuário existe e se a senha está correta
    if not user_data or not check_password_hash(user_data['password_hash'], senha):
        return jsonify({"msg": "Email ou senha inválidos"}), 401
    
    # Converte o dicionário do MongoDB para um objeto User
    user = User.from_dict(user_data)

    # Cria um token de acesso JWT com a identidade do usuário (ID do MongoDB)
    access_token = create_access_token(identity=str(user._id))
    return jsonify(access_token=access_token, user={'id': str(user._id), 'username': user.username, 'email': user.email, 'role': user.role}), 200

# --- Rotas CRUD para Usuários (Administrador) ---


# Get User by ID (sem alterações necessárias aqui para este problema)
@user_bp.route('/users', methods=['GET'])
@role_required([ROLES['1']])
def get_users():
    users_cursor = User.collection().find({})
    users_list = []
    for user_data in users_cursor:
        user = User.from_dict(user_data)
        users_list.append({
            "id": str(user._id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "cpf": user.cpf, # <--- Certifique-se que esses campos estão aqui
            "empresa": user.empresa,
            "setor": user.setor,
            "data_de_nascimento": user.data_de_nascimento,
            "planta": user.planta,
            # Adicione 'created_at' e 'last_access' se seu modelo e rota de login/registro os tiverem
            # "created_at": user.created_at.isoformat() if user.created_at else None,
            # "last_access": user.last_access.isoformat() if user.last_access else None,
        })
    return jsonify(users_list), 200

# Update User (sem alterações necessárias aqui para este problema, mas se 'planta' e outros campos
# também pudessem ser atualizados, eles precisariam ser adicionados aqui)

@user_bp.route('/users/<user_id>', methods=['PUT'])
@role_required([ROLES['1']])
def update_user(user_id):
    """
    Atualiza um usuário existente pelo ID. Apenas para administradores.
    """
    try:
        user_data_from_db = User.collection().find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"msg": "ID de usuário inválido"}), 400

    if not user_data_from_db:
        return jsonify({"msg": "Usuário não encontrado"}), 404

    # 🔑 Tentar obter o JSON, e retornar 400 se for nulo ou inválido
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"msg": "Dados de requisição inválidos ou ausentes"}), 400

    update_data = {}

    # Mapeamento do payload para os campos do banco de dados
    payload_to_db_map = {
        'nome_do_usuario': 'username',
        'email': 'email',
        'nivel': 'role',
        'senha': 'password_hash',
        'cpf': 'cpf',
        'empresa': 'empresa',
        'setor': 'setor',
        'data_de_nascimento': 'data_de_nascimento',
        'planta': 'planta'
    }

    # Processar cada campo no payload
    for payload_key, db_key in payload_to_db_map.items():
        if payload_key in data:
            if db_key == 'email':
                # Validação e verificação de e-mail duplicado
                email_bruto = data.get('email')
                email_validado = validate_email_address(email_bruto)
                if not email_validado:
                    return jsonify({"msg": "Endereço de email inválido"}), 400

                existing_user_with_email = User.collection().find_one({
                    "email": email_validado,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_user_with_email:
                    return jsonify({"msg": "Email já está em uso por outro usuário"}), 409
                update_data['email'] = email_validado

            elif db_key == 'role':
                # Validação de 'role'
                if data['nivel'] not in ROLES.values():
                    return jsonify({"msg": "Role inválido"}), 400
                update_data['role'] = data['nivel']

            elif db_key == 'password_hash':
                # Hashing da senha
                update_data['password_hash'] = generate_password_hash(data['senha'])
            
            else:
                update_data[db_key] = data[payload_key]

    if not update_data:
        return jsonify({"msg": "Nenhum dado para atualizar"}), 400

    User.collection().update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated_user_data = User.collection().find_one({"_id": ObjectId(user_id)})
    updated_user = User.from_dict(updated_user_data)

    return jsonify({
        "msg": "Usuário atualizado com sucesso",
        "user": {
            "id": str(updated_user._id),
            "nome_do_usuario": updated_user.username,
            "email": updated_user.email,
            "role": updated_user.role,
            "cpf": updated_user.cpf,
            "empresa": updated_user.empresa,
            "setor": updated_user.setor,
            "data_de_nascimento": updated_user.data_de_nascimento,
            "planta": updated_user.planta
        }
    }), 200


# Delete User (sem alterações necessárias aqui para este problema)
@user_bp.route('/users/<user_id>', methods=['DELETE'])
@role_required([ROLES['1']])
def delete_user(user_id):
    """
    Deleta um usuário pelo ID. Apenas para administradores.
    """
    try:
        result = User.collection().delete_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"msg": "ID de usuário inválido"}), 400
        
    if result.deleted_count == 0:
        return jsonify({"msg": "Usuário não encontrado"}), 404
    return jsonify({"msg": "Usuário deletado com sucesso"}), 200
