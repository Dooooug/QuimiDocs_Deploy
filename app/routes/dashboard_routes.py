# app/routes/dashboard_routes.py

from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required
import logging
from flask_cors import cross_origin

# Importa os modelos e utils necessários
from app.models import Product, User
from app.utils import ROLES, role_required

# Cria o Blueprint para as rotas do dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET', 'OPTIONS'])
@role_required([ROLES['1'], ROLES['2']])  # Protege a rota (Admin e Analista)
@cross_origin()  # 🔥 Permite CORS e responde automaticamente ao preflight OPTIONS

def get_dashboard_stats():
    """
    Retorna estatísticas agregadas para o painel de controle.
    """
    try:
        # 1. NÚMERO DE PRODUTOS CADASTRADOS
        total_products = Product.collection().count_documents({})

        # 2. ÚLTIMO PRODUTO APROVADO
        last_approved_product_doc = Product.collection().find_one(
            {"status": "aprovado"},
            sort=[('_id', -1)]
        )
        last_approved_product_name = (
            last_approved_product_doc.get("nome_do_produto", "Nome não encontrado")
            if last_approved_product_doc else "Nenhum"
        )

        # 3. NÚMERO DE USUÁRIOS CADASTRADOS
        total_users = User.collection().count_documents({})

        # 4. ÚLTIMO USUÁRIO CADASTRADO
        last_user_doc = User.collection().find_one({}, sort=[('_id', -1)])
        last_registered_user_name = (
            last_user_doc.get("username", "Nome não encontrado")
            if last_user_doc else "Nenhum"
        )

        stats = {
            "total_products": total_products,
            "last_approved_product": last_approved_product_name,
            "total_users": total_users,
            "last_registered_user": last_registered_user_name
        }

        return jsonify(stats), 200

    except Exception as e:
        logging.error(f"Erro ao buscar estatísticas do dashboard: {e}")
        return jsonify({"msg": "Erro interno ao buscar estatísticas."}), 500
