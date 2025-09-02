# security_config.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request
import logging

def get_limiter_key():
    """
    Obtém chave única para rate limiting combinando IP e usuário quando disponível
    """
    current_user = getattr(request, 'current_user', None)
    if current_user and hasattr(current_user, 'username'):
        return f"{get_remote_address()}:{current_user.username}"
    return get_remote_address()

# Inicialização do limiter será feita no app principal
limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Para produção, use Redis ou MongoDB
    strategy="fixed-window",
    on_breach=lambda request_limit: logging.warning(
        f"Rate limit exceeded: {request_limit.key} - {request_limit.limit}"
    )
)

# Configurações específicas por rota
RATE_LIMITS = {
    'login': "5 per minute",
    'register': "3 per hour",
    'upload': "10 per hour",
    'general': "100 per hour"
}