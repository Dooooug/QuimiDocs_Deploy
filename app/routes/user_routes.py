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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from security_config import limiter, RATE_LIMITS, get_limiter_key



limiter = Limiter(key_func=get_remote_address)


# Configurar o limiter após criar o blueprint
user_bp = Blueprint('user', __name__)
limiter.limit(RATE_LIMITS['login'])(user_bp)  # Limite geral para o blueprint


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
        return v["email"]
    except EmailNotValidError:
        return None

def validate_password(password):
    """Valida força da senha"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def sanitize_input(input_str, max_length=255):
    """Remove caracteres potencialmente perigosos"""
    if not input_str or not isinstance(input_str, str):
        return None
    cleaned = re.sub(r'[<>\(\)\&\|\;\`\$]', '', input_str)
    return cleaned[:max_length] if cleaned else None

@user_bp.route('/register', methods=['POST'])
@limiter.limit("2 per hour")  # Limita a 2 registros por hora por IP
def register():
    data = request.get_json()
    
    # ✅ Validação e sanitização de entrada
    nome_do_usuario = sanitize_input(data.get('nome_do_usuario'))
    email = validate_email_address(data.get('email'))
    senha = data.get('senha')
    
    if not nome_do_usuario or not email or not senha:
        return jsonify({"msg": "Dados inválidos"}), 400
        
    if not validate_password(senha):
        return jsonify({"msg": "Senha deve ter pelo menos 8 caracteres com letras maiúsculas, minúsculas e números"}), 400

    # Extrai o nível (role) do JSON. Se não for fornecido, usa VIEWER como padrão.
    # Mantém a lógica de role conforme solicitado, mas extrai da chave 'nivel'
    role = data.get('nivel', ROLES['VIEWER']) 

    # Extrai os campos adicionais do JSON
    cpf = data.get('cpf')
    empresa = data.get('empresa')
    setor = data.get('setor')
    data_de_nascimento = data.get('data_de_nascimento')
    planta = data.get('planta')

    # Validação dos campos obrigatórios
    if not nome_do_usuario or not email or not senha: # ATUALIZADO: Validando 'nome_do_usuario'
        return jsonify({"msg": "Nome de usuário, email e senha são obrigatórios"}), 400

    # Verifica se o nome de usuário já existe
    if User.collection().find_one({"nome_do_usuario": nome_do_usuario}): # ATUALIZADO: Busca por 'nome_do_usuario'
        return jsonify({"msg": "Nome de usuário já existe"}), 409
    
    # Verifica se o email já existe
    if User.collection().find_one({"email": email}):
        return jsonify({"msg": "Email já está em uso"}), 409

    # Valida se o papel fornecido é um dos papéis permitidos
    if role not in ROLES.values():
        return jsonify({"msg": "Role inválido"}), 400

    # Gera o hash da senha antes de armazenar
    hashed_password = generate_password_hash(senha)

    # Cria uma nova instância de User e insere no banco de dados com todos os campos
    new_user = User(
        username=nome_do_usuario, # Mapeia 'nome_do_usuario' do frontend para 'username' no modelo
        email=email,
        password_hash=hashed_password,
        role=role,
        cpf=cpf, # NOVO: Adiciona o campo cpf
        empresa=empresa, # NOVO: Adiciona o campo empresa
        setor=setor, # NOVO: Adiciona o campo setor
        data_de_nascimento=data_de_nascimento, # NOVO: Adiciona o campo data_de_nascimento
        planta=planta # NOVO: Adiciona o campo planta
    )
    result = User.collection().insert_one(new_user.to_dict())
    new_user._id = result.inserted_id # Atribui o ID gerado pelo MongoDB ao objeto

    # Retorna uma resposta de sucesso
    return jsonify({
        "msg": "Usuário registrado com sucesso",
        "user": {
            "id": str(new_user._id),
            "nome_do_usuario": new_user.username, # Retorna como nome_do_usuario para consistência com o frontend
            "email": new_user.email,
            "role": new_user.role,
            "cpf": new_user.cpf, # NOVO: Inclui cpf na resposta
            "empresa": new_user.empresa, # NOVO: Inclui empresa na resposta
            "setor": new_user.setor, # NOVO: Inclui setor na resposta
            "data_de_nascimento": new_user.data_de_nascimento, # NOVO: Inclui data_de_nascimento na resposta
            "planta": new_user.planta # NOVO: Inclui planta na resposta
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
@role_required([ROLES['ADMIN']])
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
@role_required([ROLES['ADMIN']])
def update_user(user_id):
    """
    Atualiza um usuário existente pelo ID. Apenas para administradores.
    Permite atualizar 'username', 'email', 'senha' e 'role'.
    """
    try:
        user_data_from_db = User.collection().find_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"msg": "ID de usuário inválido"}), 400

    if not user_data_from_db:
        return jsonify({"msg": "Usuário não encontrado"}), 404

    data = request.get_json()
    update_data = {}

    # ATUALIZADO: Mapeia 'nome_do_usuario' do frontend para 'username' no backend
    if 'nome_do_usuario' in data:
        update_data['username'] = data['nome_do_usuario']
    
    if 'email' in data:
        # Opcional: Adicionar validação para email duplicado ao atualizar, excluindo o próprio usuário
        existing_user_with_email = User.collection().find_one({"email": data['email'], "_id": {"$ne": ObjectId(user_id)}})
        if existing_user_with_email:
            return jsonify({"msg": "Email já está em uso por outro usuário"}), 409
        update_data['email'] = data['email']
    
    # ATUALIZADO: Mapeia 'nivel' do frontend para 'role' no backend
    if 'nivel' in data:
        if data['nivel'] not in ROLES.values():
            return jsonify({"msg": "Role inválido"}), 400
        update_data['role'] = data['nivel'] # Usa 'nivel' do frontend
    
    if 'senha' in data:
        update_data['password_hash'] = generate_password_hash(data['senha'])

    # NOVO: Adiciona campos adicionais para atualização, se presentes na requisição
    if 'cpf' in data:
        update_data['cpf'] = data['cpf']
    if 'empresa' in data:
        update_data['empresa'] = data['empresa']
    if 'setor' in data:
        update_data['setor'] = data['setor']
    if 'data_de_nascimento' in data:
        update_data['data_de_nascimento'] = data['data_de_nascimento']
    if 'planta' in data:
        update_data['planta'] = data['planta']


    if update_data:
        User.collection().update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        updated_user_data = User.collection().find_one({"_id": ObjectId(user_id)})
        updated_user = User.from_dict(updated_user_data)
        
        # Constrói a resposta com os dados atualizados, incluindo os novos campos
        response_user_data = {
            "id": str(updated_user._id),
            "nome_do_usuario": updated_user.username, 
            "email": updated_user.email,
            "role": updated_user.role,
            "cpf": updated_user.cpf, # Inclui cpf
            "empresa": updated_user.empresa, # Inclui empresa
            "setor": updated_user.setor, # Inclui setor
            "data_de_nascimento": updated_user.data_de_nascimento, # Inclui data_de_nascimento
            "planta": updated_user.planta # Inclui planta
        }

        return jsonify({
            "msg": "Usuário atualizado com sucesso",
            "user": response_user_data
        }), 200
    else:
        return jsonify({"msg": "Nenhum dado para atualizar"}), 400

# Delete User (sem alterações necessárias aqui para este problema)
@user_bp.route('/users/<user_id>', methods=['DELETE'])
@role_required([ROLES['ADMIN']])
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
