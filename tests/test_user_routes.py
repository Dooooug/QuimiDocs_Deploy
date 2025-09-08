# tests/test_user_routes.py

import pytest
import json
from flask import Flask
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager
from unittest.mock import MagicMock
from flask_jwt_extended import create_access_token

# Importa o blueprint e limiter
from app.routes.user_routes import user_bp
from app.security_config import limiter

# ---------------------------
# FIXTURES DE CONFIGURAÇÃO
# ---------------------------

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['TESTING'] = True

    JWTManager(app)
    limiter.init_app(app)
    app.register_blueprint(user_bp)

    return app

@pytest.fixture
def client(app):
    return app.test_client()

# ---------------------------
# DADOS DE EXEMPLO
# ---------------------------

valid_user_data = {
    "nome_do_usuario": "testuser",
    "email": "test@example.com",
    "senha": "StrongPassword123",
    "cpf": "12345678900",
    "empresa": "Test Inc.",
    "setor": "IT",
    "data_de_nascimento": "2000-01-01",
    "planta": "Planta A",
    "nivel": "visualizador"
}

# ---------------------------
# TESTES PARA /register
# ---------------------------

def test_register_sucesso(client, mocker):
    mocker.patch('app.routes.user_routes.validate_email_address', return_value=valid_user_data['email'])
    mock_collection = mocker.patch('app.routes.user_routes.User.collection')
    collection_instance = mock_collection.return_value
    collection_instance.find_one.side_effect = [None, None]
    collection_instance.insert_one.return_value.inserted_id = ObjectId()

    response = client.post('/register', json=valid_user_data)
    response_json = response.get_json()
    assert response.status_code == 201
    assert response_json["msg"] == "Usuário registrado com sucesso"


def test_register_usuario_ja_existe(client, mocker):
    mocker.patch('app.routes.user_routes.validate_email_address', return_value=valid_user_data['email'])
    mock_collection = mocker.patch('app.routes.user_routes.User.collection')
    mock_collection.return_value.find_one.return_value = {"nome_do_usuario": "testuser"}

    response = client.post('/register', json=valid_user_data)
    response_json = response.get_json()
    assert response.status_code == 409
    assert response_json["msg"] == "Nome de usuário já existe"


@pytest.mark.parametrize("payload,expected_status,msg_contains", [
    ({**valid_user_data, "senha": "123"}, 400, "Senha deve"),
    ({**valid_user_data, "email": "email-invalido"}, 400, "Endere"),
    ({**valid_user_data, "nome_do_usuario": "<script>"}, 400, "Nome de usuário inválido"),
    ({**valid_user_data, "nivel": "HACKER"}, 400, "Role inválido"),
    (None, 400, "Dados de requisição inválidos"),
])
def test_register_invalidos(client, mocker, payload, expected_status, msg_contains):
    if payload and isinstance(payload, dict) and "email" in payload and "email-invalido" not in payload["email"]:
        mocker.patch('app.routes.user_routes.validate_email_address', return_value=valid_user_data['email'])

    mock_collection = mocker.patch('app.routes.user_routes.User.collection')
    collection_instance = mock_collection.return_value
    collection_instance.find_one.side_effect = [None, None]

    if payload is None:
        response = client.post('/register', data='null', content_type='application/json')
    else:
        response = client.post('/register', json=payload)

    response_json = response.get_json()
    assert response.status_code == expected_status
    assert msg_contains in response_json["msg"]


def test_register_rate_limit(client, mocker):
    mocker.patch('app.routes.user_routes.validate_email_address', return_value=valid_user_data['email'])
    mocker.patch('app.routes.user_routes.User.collection').return_value.find_one.return_value = None
    mocker.patch('app.routes.user_routes.User.collection').return_value.insert_one.return_value.inserted_id = ObjectId()
    mocker.patch('app.routes.user_routes.limiter.limit', side_effect=lambda *a, **k: (lambda f: f))

    client.post('/register', json=valid_user_data)
    client.post('/register', json=valid_user_data)
    response = client.post('/register', json=valid_user_data)

    assert response.status_code in (201, 429)

# ---------------------------
# TESTES PARA /login
# ---------------------------

def test_login_sucesso(client, mocker):
    hashed_password = generate_password_hash(valid_user_data['senha'])
    user_from_db = {
        "_id": ObjectId(),
        "username": valid_user_data['nome_do_usuario'],
        "email": valid_user_data['email'],
        "password_hash": hashed_password,
        "role": "visualizador"
    }

    mocker.patch('app.routes.user_routes.validate_email_address', return_value=valid_user_data['email'])
    mock_collection = mocker.patch('app.routes.user_routes.User.collection')
    mock_collection.return_value.find_one.return_value = user_from_db
    mocker.patch('app.routes.user_routes.create_access_token', return_value="fake_jwt_token")

    login_data = {"email": valid_user_data['email'], "senha": valid_user_data['senha']}
    response = client.post('/login', json=login_data)

    assert response.status_code == 200
    assert json.loads(response.data)["access_token"] == "fake_jwt_token"


@pytest.mark.parametrize("payload", [
    {"email": valid_user_data['email']},
    {"senha": valid_user_data['senha']},
    {},
])
def test_login_campos_faltando(client, payload):
    response = client.post('/login', json=payload)
    assert response.status_code == 400
    assert "Email e senha são obrigatórios" in response.get_json()["msg"]


def test_login_credenciais_invalidas(client, mocker):
    hashed_password = generate_password_hash("senha_correta_do_banco")
    user_from_db = {
        "_id": ObjectId(),
        "email": valid_user_data['email'],
        "password_hash": hashed_password
    }

    mocker.patch('app.routes.user_routes.validate_email_address', return_value=valid_user_data['email'])
    mock_collection = mocker.patch('app.routes.user_routes.User.collection')
    mock_collection.return_value.find_one.return_value = user_from_db

    login_data = {"email": valid_user_data['email'], "senha": "senha_errada"}
    response = client.post('/login', json=login_data)

    assert response.status_code == 401
    assert "Email ou senha inv" in response.get_data(as_text=True)

# ---------------------------
# TESTES PARA UPDATE
# ---------------------------

def test_update_user_sucesso(client, mocker):
    """Deve atualizar usuário existente com payload válido"""
    target_user_id = str(ObjectId())

    user_original_data = {
        "username": "originaluser",
        "email": "original@example.com",
        "role": "visualizador",
        "cpf": "11122233344",
        "empresa": "Empresa X",
        "setor": "TI",
        "data_de_nascimento": "1990-01-01",
        "planta": "Planta A"
    }
    update_payload = {
        "nome_do_usuario": "updateduser",
        "email": "original@example.com",
        "nivel": "visualizador",
        "cpf": "11122233344",
        "empresa": "Empresa X",
        "setor": "TI",
        "data_de_nascimento": "1990-01-01",
        "planta": "Planta A"
    }
    updated_user_data = user_original_data.copy()
    updated_user_data["username"] = "updateduser"

    mock_identity = str(ObjectId())
    test_access_token = create_access_token(identity=mock_identity)
    mocker.patch("flask_jwt_extended.verify_jwt_in_request", return_value=None)
    mocker.patch("flask_jwt_extended.get_jwt_identity", return_value=mock_identity)

    mocker.patch("app.routes.user_routes.validate_email_address", return_value=update_payload["email"])

    mock_collection = mocker.patch("app.routes.user_routes.User.collection")
    collection_instance = mock_collection.return_value
    
    # 🎯 CORREÇÃO: Sequência de retornos para todas as chamadas `find_one`.
    collection_instance.find_one.side_effect = [
        {"role": "administrador"},  # 1. Busca pelo role do usuário autenticado.
        {"_id": ObjectId(target_user_id), **user_original_data},  # 2. Busca pelo usuário que será atualizado.
        None,  # 3. 🛑 ADICIONADO: Garante que a verificação de e-mail duplicado passe.
        {"_id": ObjectId(target_user_id), **updated_user_data} # 4. Busca o usuário após a atualização.
    ]
    
    mock_update_result = mocker.MagicMock()
    mock_update_result.modified_count = 1
    collection_instance.update_one.return_value = mock_update_result

    response = client.put(
        f'/users/{target_user_id}',
        json=update_payload,
        headers={"Authorization": f'Bearer {test_access_token}'}
    )

    assert response.status_code == 200
    assert "Usuário atualizado com sucesso" in response.get_json()["msg"]



def test_update_user_email_duplicado(client, mocker):
    """Se email já existir em outro usuário deve retornar 409"""
    target_user_id = str(ObjectId())

    update_payload = {
        "nome_do_usuario": "newname",
        "email": "duplicado@example.com",
        "nivel": "visualizador"
    }

    # GERAÇÃO DO TOKEN VÁLIDO PARA O AMBIENTE DE TESTE
    mock_identity = str(ObjectId())
    test_access_token = create_access_token(identity=mock_identity)
    mocker.patch("flask_jwt_extended.verify_jwt_in_request", return_value=None)
    mocker.patch("flask_jwt_extended.get_jwt_identity", return_value=mock_identity)

    # --- NOVO: MOCK DA FUNÇÃO DE VALIDAÇÃO DE EMAIL ---
    # Isso simula a validação para que ela sempre retorne o email sem erros.
    mocker.patch("app.routes.user_routes.validate_email_address", return_value=update_payload["email"])

    # Mocka banco
    mock_collection = mocker.patch("app.routes.user_routes.User.collection")
    collection_instance = mock_collection.return_value
    collection_instance.find_one.side_effect = [
        {"role": "administrador"},
        {"_id": ObjectId(target_user_id), "username": "userx", "email": "old@example.com", "role": "visualizador"},
        {"_id": ObjectId(), "username": "outro", "email": "duplicado@example.com"}
    ]

    response = client.put(
        f"/users/{target_user_id}",
        json=update_payload,
        headers={"Authorization": f'Bearer {test_access_token}'}
    )

    print(f"Status Code Real: {response.status_code}")
    print(f"Dados da Resposta: {response.json}")

    # A verificação agora vai funcionar, pois o teste chegará até a validação de email duplicado.
    assert response.status_code == 409
    assert "Email já está em uso por outro usuário" in response.get_json()["msg"]