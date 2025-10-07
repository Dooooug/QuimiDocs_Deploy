# tests/test_security_config.py

import pytest
from flask import Flask, jsonify
import logging
from unittest.mock import MagicMock

# Importa as funções e objetos que queremos testar
from app.security_config import (
    get_limiter_key,
    init_security,
    setup_security_logging,
    register_error_handlers,
    limiter 
)

# --- Fixture de Configuração ---

@pytest.fixture
def app():
    """Cria uma instância básica do Flask para os testes."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    return app

# --- Testes para get_limiter_key ---

def test_get_limiter_key_no_request_context():
    """Testa se a chave é 'global' quando não há contexto de requisição."""
    assert get_limiter_key() == "global"

def test_get_limiter_key_with_ip_only(app, mocker):
    """Testa se a chave é o IP quando não há identidade JWT."""
    mocker.patch('app.security_config.get_remote_address', return_value="127.0.0.1")
    
    with app.test_request_context():
        # 🎯 CORREÇÃO: Apontamos para o local correto da função.
        mocker.patch('flask_jwt_extended.get_jwt_identity', side_effect=Exception("No token"))
        assert get_limiter_key() == "127.0.0.1"

def test_get_limiter_key_with_jwt_identity(app, mocker):
    """Testa se a chave combina IP e user_id quando há identidade JWT."""
    mocker.patch('app.security_config.get_remote_address', return_value="127.0.0.1")
    
    with app.test_request_context():
        # 🎯 CORREÇÃO: Apontamos para o local correto da função.
        mocker.patch('flask_jwt_extended.get_jwt_identity', return_value='testuser')
        assert get_limiter_key() == "127.0.0.1:testuser"

# --- Testes para as funções de inicialização (sem alterações) ---

def test_init_security(app, mocker):
    """Testa se a função init_security chama as outras funções de configuração."""
    mock_limiter_init = mocker.patch('app.security_config.limiter.init_app')
    mock_setup_logging = mocker.patch('app.security_config.setup_security_logging')
    mock_register_handlers = mocker.patch('app.security_config.register_error_handlers')
    
    init_security(app)
    
    mock_limiter_init.assert_called_once_with(app)
    mock_setup_logging.assert_called_once()
    mock_register_handlers.assert_called_once_with(app)

def test_setup_security_logging_creates_directory(mocker):
    """Testa se a função de log tenta criar o diretório 'logs' se ele não existir."""
    mocker.patch('os.path.exists', return_value=False)
    mock_makedirs = mocker.patch('os.makedirs')
    mocker.patch('logging.FileHandler')
    mocker.patch('logging.getLogger')
    
    setup_security_logging()
    
    mock_makedirs.assert_called_once_with('logs')

def test_setup_security_logging_skips_creation_if_exists(mocker):
    """Testa se a função de log NÃO tenta criar o diretório se ele já existir."""
    mocker.patch('os.path.exists', return_value=True)
    mock_makedirs = mocker.patch('os.makedirs')
    mocker.patch('logging.FileHandler')
    mocker.patch('logging.getLogger')
    
    setup_security_logging()
    
    mock_makedirs.assert_not_called()

def test_ratelimit_handler_is_registered(app):
    """Testa de forma integrada se o handler de erro 429 está funcionando."""
    limiter.init_app(app)
    register_error_handlers(app)
    
    @app.route("/limited")
    @limiter.limit("1 per second")
    def limited_route():
        return "Success"

    client = app.test_client()
    
    response1 = client.get("/limited")
    assert response1.status_code == 200
    
    response2 = client.get("/limited")
    assert response2.status_code == 429
    
    json_data = response2.get_json()
    assert "Limite de requisições excedido" in json_data["error"]

# Adicione esta função ao final do arquivo tests/test_security_config.py

def test_rate_limit_breach_handler_logs_warning(mocker):
    """🎯 Testa se o handler de violação de limite registra um aviso no log."""
    # Arrange (Preparação)
    # Criamos um "espião" para a função logging.warning
    mock_logging_warning = mocker.patch('app.security_config.logging.warning')
    
    # Mock para o get_remote_address, já que o handler o utiliza
    mocker.patch('app.security_config.get_remote_address', return_value="192.168.1.100")

    # Criamos um objeto falso para simular o 'request_limit' que a função recebe
    mock_request_limit = MagicMock()
    mock_request_limit.endpoint = "/login"
    mock_request_limit.limit = "5 per minute"

    # Importa a função que estamos testando
    from app.security_config import rate_limit_breach_handler

    # Act (Ação)
    rate_limit_breach_handler(mock_request_limit)

    # Assert (Verificação)
    # Verificamos se logging.warning foi chamado exatamente uma vez
    mock_logging_warning.assert_called_once()
    
    # Opcional: verificar se a mensagem de log contém os detalhes corretos
    log_message = mock_logging_warning.call_args[0][0] # Pega o primeiro argumento da chamada
    assert "Rate limit exceeded" in log_message
    assert "IP: 192.168.1.100" in log_message
    assert "Endpoint: /login" in log_message

    