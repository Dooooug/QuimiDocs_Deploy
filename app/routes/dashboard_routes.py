# app/routes/dashboard_routes.py

from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required
import logging
from flask_cors import cross_origin
from bson.objectid import ObjectId # Importação útil se precisarmos de conversão

# Importa os modelos e utils necessários
from app.models import Product, User
from app.utils import ROLES, role_required

# Cria o Blueprint para as rotas do dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET', 'OPTIONS'])
@cross_origin()  # 🔥 Permite CORS e responde automaticamente ao preflight OPTIONS
@jwt_required()
@role_required([ROLES['1'], ROLES['2']])  # Protege a rota (Admin e Analista)
def get_dashboard_stats():
    """
    Retorna estatísticas agregadas e dados para gráficos para o painel de controle.
    """
    try:
        # --- ESTATÍSTICAS SIMPLES (JÁ EXISTENTES) ---
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

        # --- DADOS PARA GRÁFICOS (NOVAS AGREGAÇÕES) ---

        # 5. GRÁFICO: Contagem de Produtos por Status
        # Usamos o pipeline de agregação do MongoDB
        product_status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        # O resultado será uma lista como: [{"_id": "aprovado", "count": 50}, {"_id": "pendente", "count": 10}, ...]
        products_by_status = list(Product.collection().aggregate(product_status_pipeline))


        # 6. GRÁFICO: Contagem de Usuários por Role/Cargo
        user_role_pipeline = [
            {"$group": {"_id": "$role", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        # O resultado será uma lista como: [{"_id": "Admin", "count": 5}, {"_id": "Analista", "count": 20}, ...]
        users_by_role = list(User.collection().aggregate(user_role_pipeline))


        # --- ESTRUTURA FINAL DOS DADOS ---
        stats = {
            # Estatísticas Simples
            "total_products": total_products,
            "last_approved_product": last_approved_product_name,
            "total_users": total_users,
            "last_registered_user": last_registered_user_name,
            
            # Dados para Gráficos
            "products_by_status": products_by_status,
            "users_by_role": users_by_role
        }

        return jsonify(stats), 200

    except Exception as e:
        logging.error(f"Erro ao buscar estatísticas do dashboard: {e}")
        return jsonify({"msg": "Erro interno ao buscar estatísticas."}), 500