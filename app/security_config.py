# app/security_config.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import has_request_context, jsonify
import logging
import os


def get_limiter_key():
    """
    Gera uma chave única para identificar o cliente no rate limiting.
    
    - Se não houver contexto de request (ex.: scripts internos), retorna 'global'.
    - Se houver usuário autenticado via JWT, usa o ID do usuário + IP.
    - Caso contrário, usa apenas o endereço IP do cliente.
    """
    if not has_request_context():
        return "global"
    
    try:
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
    except Exception:
        current_user_id = None
    
    if current_user_id:
        return f"{get_remote_address()}:{current_user_id}"
    
    return get_remote_address()


# ✅ Agora sim: instanciamos o limiter depois que get_limiter_key existe
limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'),
    strategy="fixed-window"
)


def init_security(app):
    """
    Inicializa segurança:
    - Conecta o limiter ao Flask
    - Configura logging de segurança
    - Registra handlers globais
    """
    limiter.init_app(app)  # conecta limiter ao Flask
    setup_security_logging()
    register_error_handlers(app)
    logging.info("Security middleware initialized")


def rate_limit_breach_handler(request_limit):
    """
    Handler disparado quando o rate limit é excedido.
    Apenas registra o evento no log.
    """
    client_ip = get_remote_address()
    logging.warning(
        f"Rate limit exceeded - IP: {client_ip}, "
        f"Endpoint: {request_limit.endpoint}, "
        f"Limit: {request_limit.limit}"
    )


def setup_security_logging():
    """
    Configura logging específico para eventos de segurança.
    - Cria diretório de logs se não existir.
    - Salva logs críticos em logs/security.log.
    """
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    security_handler = logging.FileHandler('logs/security.log')
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    ))
    
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.propagate = False


def register_error_handlers(app):
    """
    Registra handlers globais de erro no Flask.
    - 429: Limite de requisições excedido
    """
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "error": "Limite de requisições excedido",
            "message": "Muitas requisições em um curto período. Tente novamente mais tarde.",
            "retry_after": 60  # tempo sugerido para retry
        }), 429


# Limites específicos por rota (podem ser aplicados nos decorators @limiter.limit)
RATE_LIMITS = {
    'login': "5 per minute",
    'register': "3 per hour", 
    'upload': "10 per hour",
    'delete': "5 per hour",
    'general': "100 per hour",
    'health': "30 per minute"
}
