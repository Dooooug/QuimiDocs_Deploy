# tests/test_product_routes.py

import pytest
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from bson.objectid import ObjectId
from unittest.mock import MagicMock, ANY
from datetime import datetime, timezone

# Importar o blueprint que queremos testar
from app.routes.product_routes import product_bp
from app.utils import ROLES

# ============================================================
# SETUP DO AMBIENTE DE TESTE (Fixtures) - Sem alterações aqui
# ============================================================

@pytest.fixture
def app():
    """Cria e configura uma nova instância do app Flask para cada teste."""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'super-secret-test-key'
    app.config['TESTING'] = True
    
    JWTManager(app)
    app.register_blueprint(product_bp)
    
    return app

@pytest.fixture
def client(app):
    """Cria um cliente de teste para fazer requisições ao app."""
    return app.test_client()

@pytest.fixture
def mocker_db(mocker):
    """Fixture para mockar as coleções do MongoDB."""
    mock_product_collection = MagicMock()
    mocker.patch('app.models.Product.collection', return_value=mock_product_collection)
    
    mock_user_collection = MagicMock()
    mocker.patch('app.models.User.collection', return_value=mock_user_collection)
    
    return {
        'products': mock_product_collection,
        'users': mock_user_collection
    }

# ============================================================
# HELPERS DE AUTENTICAÇÃO - Sem alterações aqui
# ============================================================

def get_auth_headers(app, user_id):
    """Gera um token JWT e retorna os headers de autorização."""
    with app.app_context():
        access_token = create_access_token(identity=str(user_id))
    return {'Authorization': f'Bearer {access_token}'}

# ============================================================
# INÍCIO DOS TESTES CORRIGIDOS
# ============================================================

def test_create_product_success(client, app, mocker_db):
    """
    Testa se um produto é criado com sucesso por um usuário autorizado (Admin/Analista).
    """
    # --- Arrange (Preparação) ---
    user_id = ObjectId()
    headers = get_auth_headers(app, user_id)
    
    # 🎯 CORREÇÃO: Simula a busca do usuário pelo decorador @role_required.
    # Sem isso, o decorador não encontra o usuário e retorna 403 Forbidden.
    mocker_db['users'].find_one.return_value = {"_id": user_id, "role": ROLES['1']}

    mocker_db['products'].find_one.return_value = {'codigo': 'FDS000001'}
    mocker_db['products'].insert_one.return_value.inserted_id = ObjectId()
    
    new_product_data = {
        "nome_do_produto": "Produto de Teste",
        "fornecedor": "Fornecedor Teste",
        "estado_fisico": "Líquido",
        "local_de_armazenamento": "Armazém A",
        "empresa": "Empresa Teste"
    }
    
    # --- Act (Ação) ---
    response = client.post('/products', json=new_product_data, headers=headers)

    # --- Assert (Verificação) ---
    assert response.status_code == 201
    json_data = response.get_json()
    assert "produto cadastrado com sucesso" in json_data['msg']
    assert json_data['product']['codigo'] == 'FDS000002'


def test_create_product_missing_fields(client, app, mocker_db):
    """
    Testa se a API retorna erro 400 quando campos obrigatórios não são enviados.
    """
    # --- Arrange ---
    user_id = ObjectId()
    headers = get_auth_headers(app, user_id)
    
    # 🎯 CORREÇÃO: O decorador ainda é executado, mesmo que a requisição falhe depois.
    mocker_db['users'].find_one.return_value = {"_id": user_id, "role": ROLES['1']}
    
    incomplete_data = {"nome_do_produto": "Produto Incompleto"}

    # --- Act ---
    response = client.post('/products', json=incomplete_data, headers=headers)

    # --- Assert ---
    assert response.status_code == 400
    assert "Campos obrigatórios faltando" in response.get_json()['msg']


# 🎯 CORREÇÃO FINAL DOS TESTES QUE FALHAVAM
def test_list_products(client, app, mocker_db):
    logged_in_user_id = ObjectId()
    product_creator_id = ObjectId()
    headers = get_auth_headers(app, logged_in_user_id)
    
    # Esta rota precisa de 2 buscas: 1 do decorador, 1 do serializador
    mocker_db['users'].find_one.side_effect = [
        {"_id": logged_in_user_id, "role": ROLES['1']},
        {"_id": product_creator_id, "username": "criador_produto"}
    ]

    mock_products = [{"_id": ObjectId(), "nome_do_produto": "Produto A", "created_by_user_id": product_creator_id}]
    mocker_db['products'].find.return_value.sort.return_value = mock_products
    
    response = client.get('/products', headers=headers)

    assert response.status_code == 200
    assert response.get_json()[0]['created_by'] == 'criador_produto'

def test_get_product_by_id_found(client, app, mocker_db):
    logged_in_user_id = ObjectId()
    product_creator_id = ObjectId()
    product_id = ObjectId()
    headers = get_auth_headers(app, logged_in_user_id)
    
    # Esta rota também precisa de 2 buscas: 1 do decorador, 1 do serializador
    mocker_db['users'].find_one.side_effect = [
        {"_id": logged_in_user_id, "role": ROLES['1']},
        {"_id": product_creator_id, "username": "criador_produto"}
    ]
    
    mock_product = {"_id": product_id, "nome_do_produto": "Específico", "created_by_user_id": product_creator_id}
    mocker_db['products'].find_one.return_value = mock_product
    
    response = client.get(f'/products/{product_id}', headers=headers)
    
    assert response.status_code == 200
    assert response.get_json()['created_by'] == 'criador_produto'

def test_update_product_by_admin(client, app, mocker_db):
    admin_id = ObjectId()
    creator_id = ObjectId()
    product_id = ObjectId()
    headers = get_auth_headers(app, admin_id)
    
    # 🎯 A CORREÇÃO PRINCIPAL: Esta rota precisa de 3 buscas de usuário!
    mocker_db['users'].find_one.side_effect = [
        # 1. Chamada pelo decorador @role_required
        {"_id": admin_id, "role": ROLES['1']},
        # 2. Chamada pela lógica interna da rota update_product
        {"_id": admin_id, "role": ROLES['1']},
        # 3. Chamada pelo serializador _serialize_product
        {"_id": creator_id, "username": "antigo_criador"}
    ]
    
    original_product = {"_id": product_id, "nome_do_produto": "Original", "created_by_user_id": creator_id}
    update_data = {"nome_do_produto": "Atualizado"}
    mocker_db['products'].find_one.side_effect = [original_product, {**original_product, **update_data}]
    
    response = client.put(f'/products/{product_id}', json=update_data, headers=headers)

    assert response.status_code == 200
    assert response.get_json()['product']['created_by'] == "antigo_criador"

# Testes que já passavam
def test_get_product_by_id_not_found(client, app, mocker_db):
    user_id = ObjectId()
    product_id = ObjectId()
    headers = get_auth_headers(app, user_id)
    mocker_db['users'].find_one.return_value = {"_id": user_id, "role": ROLES['1']}
    mocker_db['products'].find_one.return_value = None
    response = client.get(f'/products/{product_id}', headers=headers)
    assert response.status_code == 404

def test_delete_product_by_admin(client, app, mocker_db):
    admin_id = ObjectId()
    product_id = ObjectId()
    headers = get_auth_headers(app, admin_id)
    mocker_db['users'].find_one.return_value = {"_id": admin_id, "role": ROLES['1']}
    mocker_db['products'].delete_one.return_value.deleted_count = 1
    response = client.delete(f'/products/{product_id}', headers=headers)
    assert response.status_code == 200