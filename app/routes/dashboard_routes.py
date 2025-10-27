# app/routes/dashboard_routes.py

from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required
import logging

# Importa os modelos e utils necessários
from app.models import Product, User
from app.utils import ROLES, role_required

# Cria o Blueprint para as rotas do dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@role_required([ROLES['1'], ROLES['2']]) # Protege a rota (Admin e Analista)
def get_dashboard_stats():
    """
    Retorna estatísticas agregadas para o painel de controle.
    """
    try:
        # 1. Card 1: NÚMERO DE PRODUTOS CADASTRADOS
        # .count_documents({}) é a forma mais eficiente de contar todos os documentos
        total_products = Product.collection().count_documents({})

        # 2. Card 2: ULTIMO PRODUTO APROVADO
        # Busca o último produto (.sort('_id', -1)) que tenha o status "aprovado"
        last_approved_product_doc = Product.collection().find_one(
            {"status": "aprovado"},
            sort=[('_id', -1)] # -1 significa ordem decrescente (o mais recente)
        )
        
        # Pega o nome do produto, ou define "Nenhum" se não encontrar
        last_approved_product_name = "Nenhum"
        if last_approved_product_doc:
            last_approved_product_name = last_approved_product_doc.get("nome_do_produto", "Nome não encontrado")

        # 3. Card 3: NÚMERO DE USUÁRIOS CADASTRADOS
        total_users = User.collection().count_documents({})

        # 4. Card 4: ULTIMO USUÁRIO CADASTRADO
        # Busca o último usuário cadastrado
        last_user_doc = User.collection().find_one(
            {},
            sort=[('_id', -1)]
        )
        
        last_registered_user_name = "Nenhum"
        if last_user_doc:
            last_registered_user_name = last_user_doc.get("username", "Nome não encontrado")

        # Monta a resposta JSON
        stats = {
            "total_products": total_products,
            "last_approved_product": last_approved_product_name,
            "total_users": total_users,
            "last_registered_user": last_registered_user_name
        }

        return jsonify(stats), 200

    except Exception as e:
        # Em caso de erro no banco de dados, retorna uma mensagem
        logging.error(f"Erro ao buscar estatísticas do dashboard: {e}")
        return jsonify({"msg": "Erro interno ao buscar estatísticas."}), 500