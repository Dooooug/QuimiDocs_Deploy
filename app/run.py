# run.py (versão completa com headers de rate limiting)

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from app.security_config import init_security, limiter
from app.security_middleware import init_security_middleware

app = create_app()

# ✅ Inicializar configurações de segurança
init_security(app)

# ✅ Inicializar middleware de segurança
app = init_security_middleware(app)

# ✅ Configuração de CORS
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

# ✅ 7. HEADERS DE RATE LIMITING NAS RESPOSTAS
@app.after_request
def add_rate_limit_headers(response):
    """
    Adiciona headers de rate limiting em todas as respostas
    Isso ajuda os clientes a entenderem os limites e quando podem fazer novas requisições
    """
    try:
        # Headers padrão de segurança (já existiam)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # ✅ NOVO: Headers de Rate Limiting
        if hasattr(request, 'rate_limited'):
            # Headers padrão do Flask-Limiter
            rate_limit = request.rate_limited
            
            response.headers['X-RateLimit-Limit'] = str(rate_limit.limit)
            response.headers['X-RateLimit-Remaining'] = str(rate_limit.remaining)
            response.headers['X-RateLimit-Reset'] = str(rate_limit.reset_at)
            
            # ✅ Headers adicionais informativos
            response.headers['X-RateLimit-Policy'] = f"{rate_limit.limit};w=3600"
            
            # Calcular tempo até reset em segundos
            reset_in = max(0, int(rate_limit.reset_at - time.time()))
            response.headers['Retry-After'] = str(reset_in)
            
        else:
            # ✅ Headers mesmo quando não está rate limited
            # Para ajudar clientes a entenderem os limites gerais
            response.headers['X-RateLimit-Limit'] = '200'
            response.headers['X-RateLimit-Remaining'] = '199'  # Será atualizado dinamicamente
            response.headers['X-RateLimit-Policy'] = '200 per day, 50 per hour'
        
        # ✅ Header para identificar a aplicação
        response.headers['X-Application'] = 'QuimiDocs API'
        response.headers['X-API-Version'] = '1.0.0'
        
    except Exception as e:
        # Em caso de erro, não quebrar a resposta
        logging.error(f"Error adding rate limit headers: {str(e)}")
    
    return response

# ✅ Handler global para erros de rate limiting
@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Handler personalizado para erros de rate limiting
    Retorna informações detalhadas sobre o limite excedido
    """
    # Obter informações do rate limiting
    rate_limit_info = getattr(e, 'description', {})
    
    response = jsonify({
        "error": "limite_de_requisicoes_excedido",
        "message": "Muitas requisições em um curto período de tempo.",
        "detail": "O limite de requisições foi excedido para este recurso.",
        "retry_after": rate_limit_info.get('retry_after', 60),
        "limit": rate_limit_info.get('limit', '50 per hour'),
        "documentation": "https://api.quimidocs.com/docs/rate-limiting"
    })
    
    response.status_code = 429
    
    # ✅ Adicionar headers específicos para erro 429
    reset_time = int(time.time() + rate_limit_info.get('retry_after', 60))
    response.headers['X-RateLimit-Limit'] = rate_limit_info.get('limit', '50 per hour')
    response.headers['X-RateLimit-Reset'] = str(reset_time)
    response.headers['Retry-After'] = str(rate_limit_info.get('retry_after', 60))
    response.headers['X-RateLimit-Scope'] = 'ip'  # ou 'user' para limites por usuário
    
    return response

# ✅ Health check global com rate limiting
@app.route('/health', methods=['GET'])
@limiter.limit("30 per minute")
def health_check():
    """Endpoint de health check global da aplicação"""
    from datetime import datetime
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quimidocs-api",
        "version": "1.0.0",
        "rate_limits": {
            "daily": 200,
            "hourly": 50,
            "login": "5 per minute",
            "register": "3 per hour",
            "upload": "10 per hour"
        }
    }), 200

# ✅ NOVO: Endpoint para verificar limites atuais
@app.route('/rate-limits', methods=['GET'])
def get_rate_limits_info():
    """
    Retorna informações sobre os limites de rate limiting da aplicação
    Útil para clientes entenderem os limites antes de fazer requisições
    """
    return jsonify({
        "rate_limits": {
            "global": {
                "daily": "200 requests per day",
                "hourly": "50 requests per hour"
            },
            "endpoints": {
                "login": "5 requests per minute",
                "register": "3 requests per hour",
                "upload": "10 requests per hour",
                "delete": "5 requests per hour",
                "health": "30 requests per minute"
            },
            "policies": {
                "scope": "IP-based with user differentiation when authenticated",
                "storage": os.getenv('REDIS_URL', 'memory://').split('://')[0],
                "strategy": "fixed-window"
            },
            "headers": {
                "X-RateLimit-Limit": "Total limit for the time window",
                "X-RateLimit-Remaining": "Remaining requests in current window",
                "X-RateLimit-Reset": "Unix timestamp when limits reset",
                "Retry-After": "Seconds to wait after rate limit exceeded"
            }
        }
    }), 200

if __name__ == '__main__':
    import time  # ✅ Import necessário para time.time()
    import logging
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    if debug_mode and os.getenv('FLASK_ENV') == 'production':
        print("⚠️  AVISO: Debug mode não deve ser usado em produção!")
        debug_mode = False
    
    app.run(
        debug=debug_mode,
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        threaded=True,
        use_reloader=debug_mode
    )