# run.py
# ==============================================================================
# PONTO DE ENTRADA (ENTRYPOINT) DA APLICAÇÃO
# ------------------------------------------------------------------------------
# Este arquivo é responsável por criar e configurar a instância da aplicação Flask.
# - Em produção: O Gunicorn importa este arquivo e usa a variável 'app'.
# - Em desenvolvimento: Você executa 'python run.py' para iniciar o servidor local.
# ==============================================================================

# ---------------------------
# IMPORTS PADRÃO E DE LIBS
# ---------------------------
import os
import sys
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ---------------------------
# CONFIGURAÇÃO DO PATH
# ---------------------------
# Garante que os módulos da aplicação sejam encontrados corretamente.
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------
# IMPORTS DA APLICAÇÃO
# ---------------------------
from app import create_app
from app.security_config import init_security, limiter
from app.security_middleware import init_security_middleware


# ==============================================================================
# INICIALIZAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO
# (Esta seção é executada tanto pelo Gunicorn quanto localmente)
# ==============================================================================

# 1. CRIA A INSTÂNCIA DA APLICAÇÃO USANDO A FACTORY
# A variável 'app' é o que o Gunicorn procura e utiliza para servir a aplicação.
app = create_app()

# 2. INICIALIZA MÓDULOS DE SEGURANÇA E MIDDLEWARE
init_security(app)
app = init_security_middleware(app)

# 3. CONFIGURAÇÃO AVANÇADA DE CORS
# Define quais domínios (origins) podem acessar sua API e com quais regras.
# A origem permitida é lida da variável de ambiente 'ALLOWED_ORIGINS'.
CORS(app, resources={
    r"/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": [
            "X-RateLimit-Limit", 
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "X-RateLimit-Policy",
            "Retry-After"
        ],
        "supports_credentials": True,
        "max_age": 600
    }
})


# 4. MIDDLEWARE PARA ADICIONAR HEADERS DE SEGURANÇA E RATE LIMITING
# Esta função é executada após cada requisição, antes de enviar a resposta.
@app.after_request
def add_custom_headers(response):
    """Adiciona headers de segurança e de rate limiting em todas as respostas."""
    try:
        # Headers padrão de segurança
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Headers de Rate Limiting (se a requisição foi limitada)
        if hasattr(request, 'rate_limited') and request.rate_limited is not None:
            rate_limit = request.rate_limited
            response.headers['X-RateLimit-Limit'] = str(rate_limit.limit)
            response.headers['X-RateLimit-Remaining'] = str(rate_limit.remaining)
            response.headers['X-RateLimit-Reset'] = str(rate_limit.reset_at)
            
            # Tempo em segundos até o reset do limite
            reset_in_seconds = max(0, int(rate_limit.reset_at - time.time()))
            response.headers['Retry-After'] = str(reset_in_seconds)
        
        # Headers informativos da API
        response.headers['X-Application'] = 'QuimiDocs API'
        response.headers['X-API-Version'] = '1.0.0'
        
    except Exception as e:
        # Evita que um erro aqui quebre a aplicação. Apenas registra o log.
        logging.error(f"Erro ao adicionar headers customizados: {str(e)}")
    
    return response


# 5. HANDLER GLOBAL PARA ERROS DE RATE LIMITING (HTTP 429)
# Cria uma resposta JSON padronizada quando um usuário excede o limite.
@app.errorhandler(429)
def ratelimit_handler(e):
    """Retorna uma resposta JSON detalhada para erros de rate limiting."""
    retry_after = e.get_response().headers.get("Retry-After", 60)
    return jsonify({
        "error": "limite_de_requisicoes_excedido",
        "message": f"Você excedeu o limite de requisições. Tente novamente após {retry_after} segundos."
    }), 429


# 6. ROTAS GLOBAIS DA APLICAÇÃO
# Endpoints que não pertencem a um blueprint específico.

@app.route('/health', methods=['GET'])
@limiter.limit("30 per minute")
def health_check():
    """Endpoint de 'health check' para verificar se a API está no ar e saudável."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quimidocs-api"
    }), 200

@app.route('/rate-limits', methods=['GET'])
def get_rate_limits_info():
    """Endpoint informativo que descreve as políticas de rate limiting da API."""
    return jsonify({
        "info": "Esta API utiliza políticas de rate limiting para garantir a estabilidade.",
        "headers_de_referencia": {
            "X-RateLimit-Limit": "O limite total de requisições por janela de tempo.",
            "X-RateLimit-Remaining": "Quantas requisições ainda restam na janela atual.",
            "X-RateLimit-Reset": "O momento (timestamp) em que a janela será reiniciada.",
            "Retry-After": "Quantos segundos aguardar antes de tentar novamente (em respostas 429)."
        }
    }), 200


# ==============================================================================
# EXECUTOR PARA DESENVOLVIMENTO LOCAL
# (Esta seção é ignorada pelo Gunicorn em produção)
# ==============================================================================

if __name__ == '__main__':
    # Este bloco só é executado quando você roda o comando 'python run.py'.
    
    # Configura o sistema de logging para exibir informações no terminal.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Determina se a aplicação deve rodar em modo debug com base em variáveis de ambiente.
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1']
    
    # Uma trava de segurança para não rodar em modo debug em um ambiente de produção.
    if debug_mode and os.getenv('FLASK_ENV') == 'production':
        logging.warning("AVISO: Tentativa de rodar em modo DEBUG em ambiente de produção. Forçando DEBUG=False.")
        debug_mode = False
    
    # Inicia o servidor de desenvolvimento do Flask.
    app.run(
        debug=debug_mode,
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        use_reloader=debug_mode  # O reloader automático só funciona em modo debug.
    )