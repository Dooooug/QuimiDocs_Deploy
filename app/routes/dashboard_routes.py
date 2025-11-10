# app/routes/dashboard_routes.py

from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required
import logging
from flask_cors import cross_origin
# Importa os modelos e utils necessários
from app.models import Product, User # Manter 'User' se for necessário para 'role_required', mas os dados de estatística serão removidos
from app.utils import ROLES, role_required
import traceback

# Cria o Blueprint para as rotas do dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET', 'OPTIONS'])
@cross_origin()
@jwt_required()
@role_required([ROLES['1'], ROLES['2']])
def get_dashboard_stats():
    """
    Retorna estatísticas agregadas e dados para gráficos para o painel de controle,
    focando em dados de Produto conforme o novo layout (2 Cards + 5 Gráficos).
    """
    try:
        # --- ESTATÍSTICAS SIMPLES (CARDS MANTIDOS) ---
        
        # 1. NÚMERO DE PRODUTOS CADASTRADOS (Card 1)
        total_products = Product.collection().count_documents({})
        
        # 2. ÚLTIMO PRODUTO APROVADO (Card 2)
        # Nota: O layout atual usa "Último Produto Aprovado". Se você quiser "Último Produto Cadastrado",
        # basta remover o filtro {"status": "aprovado"}. Mantendo o original por segurança.
        last_approved_product_doc = Product.collection().find_one(
            {"status": "aprovado"},
            sort=[('_id', -1)]
        )
        last_approved_product_name = (
            last_approved_product_doc.get("nome_do_produto", "Nome não encontrado")
            if last_approved_product_doc else "Nenhum"
        )
        
            
        # --- DADOS PARA GRÁFICOS (5 GRÁFICOS RESTANTES) ---

        # 1. GRÁFICO: Contagem de Produtos por Status
        product_status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        products_by_status = list(Product.collection().aggregate(product_status_pipeline))

        # 2. GRÁFICO: QTADE DE PRODUTOS CADASTRADOS POR EMPRESA
        products_by_company_pipeline = [
            {"$group": {"_id": "$empresa", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        products_by_company = list(Product.collection().aggregate(products_by_company_pipeline))
        
        # 3. GRÁFICO: QUANTIDADE DE PRODUTOS POR GHS
        products_by_pictogram_pipeline = [
            # 1. Combina os arrays e garante que cada perigo seja contado apenas uma vez por produto
            {"$project": {
                "todos_os_perigos": {
                    "$setUnion": [
                        {"$ifNull": ["$perigos_fisicos", []]},
                        {"$ifNull": ["$perigos_saude", []]},
                        {"$ifNull": ["$perigos_meio_ambiente", []]}
                    ]
                }
            }},
            # 2. Desconstrói o array 'todos_os_perigos' para contar cada perigo individualmente
            {"$unwind": "$todos_os_perigos"},
            # 3. Agrupa pelo nome do perigo e conta
            {"$group": {"_id": "$todos_os_perigos", "count": {"$sum": 1}}},
            # 4. Renomeia o campo _id para 'pictograma' e remove o _id antigo
            {"$project": {"_id": 0, "pictograma": "$_id", "quantidade_produtos": "$count"}},
            # 5. Ordena pela quantidade em ordem decrescente (opcional)
            {"$sort": {"quantidade_produtos": -1}}
        ]
        products_by_pictogram = list(Product.collection().aggregate(products_by_pictogram_pipeline))
        
        # 4. GRÁFICO: ESTADO FÍSICO (Pizza)
        physical_state_pipeline = [
            {"$group": {"_id": "$estado_fisico", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        products_by_physical_state = list(Product.collection().aggregate(physical_state_pipeline))

        # 5. GRÁFICO: CLASSIFICAÇÃO DE PERIGO POR PRODUTO
        danger_classification_pipeline = [
            # 1. Cria campos booleanos para indicar a presença de cada tipo de perigo.
            #    Um produto é contado na categoria se o array respectivo não for vazio.
            {"$addFields": {
                "is_perigo_fisico": {
                    "$cond": [{"$gt": [{"$size": {"$ifNull": ["$perigos_fisicos", []]}}, 0]}, 1, 0]
                },
                "is_perigo_saude": {
                    "$cond": [{"$gt": [{"$size": {"$ifNull": ["$perigos_saude", []]}}, 0]}, 1, 0]
                },
                "is_perigo_meio_ambiente": {
                    "$cond": [{"$gt": [{"$size": {"$ifNull": ["$perigos_meio_ambiente", []]}}, 0]}, 1, 0]
                },
            }},

            # 2. Agrupa (acumula) a soma total de produtos que possuem cada tipo de perigo.
            #    Como só há um grupo (null), ele soma os indicadores (1 ou 0) de todos os documentos.
            {"$group": {
                "_id": None, # Agrupa todos os documentos em um só resultado
                "Físico": {"$sum": "$is_perigo_fisico"},
                "À Saúde": {"$sum": "$is_perigo_saude"},
                "Ao Meio Ambiente": {"$sum": "$is_perigo_meio_ambiente"},
            }},

            # 3. Reestrutura para o formato de array (Labels e Data)
            #    Este formato é ideal para ser consumido por um gráfico de barras simples no frontend.
            {"$project": {
                "_id": 0,
                "dados": [
                    {"tipo": "Físico", "quantidade": "$Físico"},
                    {"tipo": "À Saúde", "quantidade": "$À Saúde"},
                    {"tipo": "Ao Meio Ambiente", "quantidade": "$Ao Meio Ambiente"},
                ]
            }},

            # 4. Desconstrói o array "dados" para ter um documento por categoria (opcional, mas limpa a saída)
            {"$unwind": "$dados"},

            # 5. Finaliza e Projeta os campos finais (tipo, quantidade)
            {"$project": {
                "_id": 0,
                "tipo": "$dados.tipo",
                "quantidade": "$dados.quantidade",
            }}
        ]

        danger_classification = list(Product.collection().aggregate(danger_classification_pipeline))
        # 6. GRÁFICO: Quantidade Armazenada por Empresa por Estado Físico
        storage_by_company_and_state_pipeline = [
            # 1. Pré-filtragem e Conversão (Essencial)
            {"$match": {
                "quantidade_armazenada": {"$exists": True, "$ne": None}
            }},
            {"$addFields": {
                # Tenta converter para número, tratando strings numéricas.
                # Se for string vazia ou falhar, usa 0 (Zero).
                "quantidade_armazenada_num": {
                    "$convert": {
                        "input": "$quantidade_armazenada",
                        "to": "double",
                        "onError": 0,
                        "onNull": 0
                    }
                }
            }},
            # 2. Agrupamento Principal
            {"$group": {
                "_id": {"empresa": "$empresa", "estado": "$estado_fisico"}, 
                "total_quantidade": {"$sum": "$quantidade_armazenada_num"} # Usa o campo convertido
            }},
            # 3. Ordenação
            {"$sort": {"_id.empresa": 1, "total_quantidade": -1}},

            # 4. Reestruturação para o Gráfico de Barras Agrupadas (OPCIONAL, mas muito útil)
            # Este passo agrupa todos os estados físicos sob a mesma empresa.
            {"$group": {
                "_id": "$_id.empresa", 
                "estados": {
                    "$push": {
                        "estado_fisico": "$_id.estado",
                        "quantidade": "$total_quantidade"
                    }
                }
            }},
            # 5. Renomear e Finalizar
            {"$project": {
                "_id": 0,
                "empresa": "$_id",
                "dados_por_estado": "$estados"
            }}
        ]

        storage_by_company_and_state = list(Product.collection().aggregate(storage_by_company_and_state_pipeline))


        # --- ESTRUTURA FINAL DOS DADOS ---
        stats = {
            # Estatísticas Simples
            "total_products": total_products,
            "last_approved_product": last_approved_product_name,
            
            # Dados para Gráficos
            "products_by_status": products_by_status, 
            "products_by_company": products_by_company, 
            "products_by_pictogram": products_by_pictogram, 
            "products_by_physical_state": products_by_physical_state, 
            "storage_by_company_and_state": storage_by_company_and_state,
            "danger_classification": danger_classification 
        }

        return jsonify(stats), 200

    except Exception as e:
        # ---------------------------------------
        # Resposta de Erro (Onde o 500 é capturado)
        # ---------------------------------------
        
        # 1. IMPRESSÃO CRÍTICA NO LOG DO SERVIDOR (O que você precisa ver)
        # Isso imprimirá o rastreamento completo do erro no seu console de execução do Python.
        print(f"\n--- ERRO CRÍTICO NA ROTA /dashboard/stats ---\n")
        traceback.print_exc()
        print(f"Mensagem de Erro: {e}")
        print(f"\n-----------------------------------------------\n")
        
        # 2. Retorna uma resposta 500 JSON para o cliente
        return jsonify({
            "status": "error",
            "message": f"Erro interno ao processar estatísticas: {str(e)}",
            "detail": traceback.format_exc().splitlines()[-1] # Retorna a última linha do erro
        }), 500 # Define o código de status HTTP para 500