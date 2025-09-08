# tests/test_pdf_routes.py

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from bson.objectid import ObjectId
from unittest.mock import MagicMock, ANY
import io

# Importar o blueprint e as dependências
from app.routes.pdf_routes import pdf_bp
from app.utils import ROLES

@pytest.fixture
def app():
    """Cria e configura uma nova instância do app Flask para cada teste."""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'super-secret-test-key'
    app.config['TESTING'] = True
    
    JWTManager(app)
    app.register_blueprint(pdf_bp)
    
    return app

@pytest.fixture
def client(app):
    """Cria um cliente de teste para fazer requisições ao app."""
    return app.test_client()

@pytest.fixture
def mocker_aws_and_db(mocker):
    """Fixture para mockar o cliente S3 e as coleções do MongoDB."""
    mock_s3_client = MagicMock()
    mocker.patch('app.routes.pdf_routes.boto3.Session.client', return_value=mock_s3_client)
    
    mock_pdf_metadata_collection = MagicMock()
    mock_user_collection = MagicMock()
    mock_product_collection = MagicMock()
    
    mocker.patch('app.routes.pdf_routes.pdf_metadata_collection', mock_pdf_metadata_collection)
    mocker.patch('app.models.User.collection', return_value=mock_user_collection)
    mocker.patch('app.models.Product.collection', return_value=mock_product_collection)
    
    mocker.patch('app.routes.pdf_routes.s3_client', mock_s3_client)
    mocker.patch('app.routes.pdf_routes.s3_bucket_name', 'test-bucket')
    
    return {
        's3': mock_s3_client,
        'pdf_metadata': mock_pdf_metadata_collection,
        'users': mock_user_collection,
        'products': mock_product_collection
    }

def get_auth_headers(app, user_id, role):
    """Gera um token JWT e retorna os headers de autorização."""
    with app.app_context():
        # O argumento 'role' não é usado para criar o token, mas é útil manter
        # para clareza no código de teste.
        access_token = create_access_token(identity=str(user_id))
    return {'Authorization': f'Bearer {access_token}'}

# ============================================================
# INÍCIO DOS TESTES CORRIGIDOS
# ============================================================

def test_upload_file_success(client, app, mocker_aws_and_db):
    """Testa se um admin consegue fazer upload de um arquivo PDF com sucesso."""
    admin_id = ObjectId()
    headers = get_auth_headers(app, admin_id, ROLES['1'])
    
    # 🎯 CORREÇÃO: Informa ao mock que o usuário é um administrador.
    mocker_aws_and_db['users'].find_one.return_value = {"_id": admin_id, "role": ROLES['1']}
    
    mocker_aws_and_db['pdf_metadata'].insert_one.return_value.inserted_id = ObjectId()
    
    file_data = {'file': (io.BytesIO(b"fake pdf content"), 'test.pdf')}

    response = client.post('/upload', data=file_data, headers=headers, content_type='multipart/form-data')

    assert response.status_code == 200
    assert "Arquivo enviado com sucesso" in response.get_json()['message']

def test_upload_file_no_file(client, app, mocker_aws_and_db):
    """Testa a resposta de erro quando nenhum arquivo é enviado."""
    admin_id = ObjectId()
    headers = get_auth_headers(app, admin_id, ROLES['1'])
    
    # 🎯 CORREÇÃO: Informa ao mock que o usuário é um administrador.
    mocker_aws_and_db['users'].find_one.return_value = {"_id": admin_id, "role": ROLES['1']}
    
    response = client.post('/upload', data={}, headers=headers, content_type='multipart/form-data')
    
    assert response.status_code == 400
    assert "Nenhum arquivo enviado" in response.get_json()['error']

def test_get_pdfs_as_viewer(client, app, mocker_aws_and_db):
    """Testa se um usuário 'visualizador' vê apenas produtos aprovados com PDF."""
    viewer_id = ObjectId()
    headers = get_auth_headers(app, viewer_id, ROLES['3'])
    
    mocker_aws_and_db['users'].find_one.return_value = {
        "_id": viewer_id, "role": ROLES['3'], "active": True
    }
    
    mock_products = [{"_id": ObjectId(), "nome_do_produto": "PDF Aprovado", "status": "aprovado", "pdf_url": "http://s3.com/aprovado.pdf"}]
    mocker_aws_and_db['products'].find.return_value = mock_products
    
    response = client.get('/pdfs', headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['nome_do_produto'] == 'PDF Aprovado'