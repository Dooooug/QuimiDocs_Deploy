# init_app.py

import os
from werkzeug.security import generate_password_hash
from app.models import User
from app.utils import ROLES
import time
import pymongo
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dados do usuário administrador padrão
DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin_123')

def create_default_admin_user():
    """
    Cria um usuário administrador padrão se ele não existir no banco de dados.
    """
    # ... (código do script, conforme o exemplo da resposta anterior) ...
    # Lógica de conexão, verificação e criação do usuário
    
    # Exemplo:
    try:
        user_exists = User.collection().find_one({"email": DEFAULT_ADMIN_EMAIL})
        if user_exists:
            logging.info("Usuário administrador padrão já existe. Nenhuma ação necessária.")
            return

        hashed_password = generate_password_hash(DEFAULT_ADMIN_PASSWORD)
        new_user = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hashed_password,
            role=ROLES['ADMIN']
        )
        User.collection().insert_one(new_user.to_dict())
        logging.info("Usuário administrador padrão criado com sucesso.")
        logging.info(f"Detalhes: Email: {DEFAULT_ADMIN_EMAIL}, Senha: {DEFAULT_ADMIN_PASSWORD}")
    except Exception as e:
        logging.error(f"Erro ao criar usuário administrador: {e}")

if __name__ == "__main__":
    create_default_admin_user()