# tests/test_security_middleware.py

import pytest
import time
import json
from flask import Flask
from unittest.mock import MagicMock
from werkzeug.test import Client
from app.security_middleware import SecurityMiddleware

# --- Fixtures de Configuração ---

@pytest.fixture
def dummy_app():
    """Cria uma aplicação Flask mínima apenas para ser 'embrulhada' pelo middleware."""
    app = Flask(__name__)
    @app.route('/')
    def index():
        return "OK", 200
    return app

@pytest.fixture
def middleware(dummy_app):
    """Inicializa uma instância do nosso middleware para cada teste."""
    # Passamos o app.wsgi_app, que é a parte que o middleware manipula
    return SecurityMiddleware(dummy_app.wsgi_app)

@pytest.fixture
def client(middleware):
    """Cria um cliente de teste que faz requisições diretamente ao middleware."""
    # Usamos o Client do Werkzeug para interagir no nível do WSGI
    return Client(middleware)

# --- Início dos Testes ---

def test_normal_request_passes(client):
    """Testa se uma requisição normal, sem suspeitas, passa pelo middleware."""
    # Arrange: Headers normais
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Act: Faz a requisição
    response = client.get('/', headers=headers)
    
    # Assert: A resposta deve ser da aplicação Flask (200 OK)
    assert response.status_code == 200
    assert response.data == b"OK"

def test_blocked_ip_is_rejected(client, middleware):
    """Testa se um IP previamente bloqueado é rejeitado com status 429."""
    # Arrange: Bloqueia manualmente um IP
    test_ip = '192.168.1.100'
    middleware.blocked_ips[test_ip] = time.time() + 60  # Bloqueado por 60s
    
    # Act: Faz uma requisição a partir do IP bloqueado
    response = client.get('/', environ_base={'REMOTE_ADDR': test_ip})
    
    # Assert: A resposta deve ser 429 Too Many Requests
    assert response.status_code == 429
    assert b"Acesso temporariamente bloqueado" in response.data

def test_block_expires_and_allows_request(client, middleware, mocker):
    """Testa se um IP é desbloqueado após o tempo de bloqueio expirar."""
    # Arrange: Bloqueia um IP em um tempo "passado"
    test_ip = '192.168.1.101'
    past_time = time.time() - 1000  # Um tempo bem no passado
    middleware.blocked_ips[test_ip] = past_time
    
    # Act: Faz uma requisição do IP que deveria estar desbloqueado
    response = client.get('/', environ_base={'REMOTE_ADDR': test_ip}, headers={'User-Agent': 'Valid User Agent'})
    
    # Assert: A requisição deve passar normalmente (200 OK)
    assert response.status_code == 200
    assert test_ip not in middleware.blocked_ips  # Verifica se o IP foi removido da lista de bloqueio

def test_missing_user_agent_is_suspicious(client):
    """Testa se uma requisição sem User-Agent é considerada suspeita (400 Bad Request)."""
    # Arrange: Nenhum header de User-Agent
    
    # Act: Faz a requisição
    response = client.get('/')
    
    # Assert: A resposta deve ser de atividade suspeita
    assert response.status_code == 400
    assert b"Atividade suspeita detectada" in response.data

def test_sql_injection_attempt_is_suspicious(client):
    """Testa se uma tentativa de SQL injection na URL é bloqueada."""
    # Arrange: Uma URL com padrão de SQL injection
    url_com_injecao = '/?user=admin%27%20OR%201=1;%20--'
    
    # Act: Faz a requisição
    response = client.get(url_com_injecao, headers={'User-Agent': 'Valid User Agent'})
    
    # Assert: A resposta deve ser de atividade suspeita
    assert response.status_code == 400
    assert b"Atividade suspeita detectada" in response.data

def test_ip_is_blocked_after_max_attempts(client, middleware):
    """Testa se um IP é bloqueado após atingir o número máximo de atividades suspeitas."""
    # Arrange
    test_ip = '192.168.1.102'
    # Força o middleware a usar um número baixo de tentativas para o teste
    middleware.MAX_FAILED_ATTEMPTS = 3
    
    # Act: Simula 3 atividades suspeitas (sem User-Agent)
    for _ in range(3):
        client.get('/', environ_base={'REMOTE_ADDR': test_ip})
        
    # Assert: O IP agora deve estar na lista de bloqueados
    assert test_ip in middleware.blocked_ips
    
    # Act 2: Uma quarta tentativa deve receber a resposta de bloqueio (429)
    response = client.get('/', environ_base={'REMOTE_ADDR': test_ip})
    assert response.status_code == 429
    assert b"Acesso temporariamente bloqueado" in response.data

def test_high_frequency_is_suspicious(client, middleware, mocker):
    """Testa se muitas requisições em pouco tempo são consideradas suspeitas."""
    # Arrange
    test_ip = '192.168.1.103'
    middleware.is_high_frequency = MagicMock(return_value=True) # Mockamos a função para simplificar o teste
    
    # Act
    response = client.get('/login', environ_base={'REMOTE_ADDR': test_ip}, headers={'User-Agent': 'Valid User Agent'})
    
    # Assert
    assert response.status_code == 400
    assert b"Atividade suspeita detectada" in response.data