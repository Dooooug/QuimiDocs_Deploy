# tests/test_init_app.py

import pytest
from unittest.mock import MagicMock

# Importa a função que queremos testar
from app.__init__app import create_default_admin_user
# Importa o dicionário ROLES para o teste
from app.utils import ROLES

# Mock para a classe User para que não precisemos de um banco de dados real
@pytest.fixture
def mock_user_collection(mocker):
    """Fixture que mocka a coleção de usuários do MongoDB."""
    mock_collection = MagicMock()
    # Intercepta a chamada a User.collection() e retorna nosso mock
    mocker.patch('app.models.User.collection', return_value=mock_collection)
    return mock_collection

def test_create_admin_when_user_already_exists(mock_user_collection, mocker):
    """
    Testa o cenário em que o usuário administrador já existe.
    Verifica se nenhuma inserção é feita.
    """
    # Arrange (Preparação)
    # Mock para o logging para podermos verificar as mensagens
    mock_logging_info = mocker.patch('app.__init__app.logging.info')
    
    # Configuramos o find_one para retornar um usuário, simulando que ele já existe
    mock_user_collection.find_one.return_value = {"email": "admin@example.com"}

    # Act (Ação)
    create_default_admin_user()

    # Assert (Verificação)
    # Garante que a busca no banco foi feita uma vez
    mock_user_collection.find_one.assert_called_once()
    
    # Garante que a inserção de um novo usuário NÃO foi chamada
    mock_user_collection.insert_one.assert_not_called()
    
    # Garante que a mensagem de log correta foi exibida
    mock_logging_info.assert_called_with("Usuário administrador padrão já existe. Nenhuma ação necessária.")

def test_create_admin_when_user_does_not_exist(mock_user_collection, mocker):
    """
    Testa o cenário em que o usuário administrador não existe.
    Verifica se um novo usuário é criado e inserido.
    """
    # Arrange (Preparação)
    mock_logging_info = mocker.patch('app.__init__app.logging.info')
    mock_hash_password = mocker.patch('app.__init__app.generate_password_hash')
    
    # Configuramos o find_one para retornar None, simulando que o usuário não existe
    mock_user_collection.find_one.return_value = None

    # Act (Ação)
    create_default_admin_user()

    # Assert (Verificação)
    # Garante que a busca no banco foi feita
    mock_user_collection.find_one.assert_called_once()
    
    # Garante que a função para gerar o hash da senha foi chamada
    mock_hash_password.assert_called_once()
    
    # Garante que a função de inserir um novo usuário foi chamada uma vez
    mock_user_collection.insert_one.assert_called_once()
    
    # Garante que a mensagem de sucesso foi logada
    mock_logging_info.assert_any_call("Usuário administrador padrão criado com sucesso.")

def test_create_admin_handles_exception(mock_user_collection, mocker):
    """
    Testa o cenário em que ocorre um erro no banco de dados.
    Verifica se o erro é capturado e logado.
    """
    # Arrange (Preparação)
    mock_logging_error = mocker.patch('app.__init__app.logging.error')
    
    # Configuramos o find_one para simular uma exceção do banco de dados
    mock_user_collection.find_one.side_effect = Exception("Erro de conexão com o banco")

    # Act (Ação)
    create_default_admin_user()

    # Assert (Verificação)
    # Garante que a mensagem de erro foi logada
    mock_logging_error.assert_called_once()
    # Podemos verificar se a mensagem contém o texto esperado
    log_message = mock_logging_error.call_args[0][0]
    assert "Erro ao criar usuário administrador" in log_message