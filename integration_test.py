# integration_test.py (VERSÃO CORRIGIDA E MAIS ROBUSTA)

import requests
import pymongo
from bson.objectid import ObjectId
import time
from werkzeug.security import generate_password_hash

# --- CONFIGURAÇÕES ---
BASE_URL = "http://localhost:5000"
# ⚠️ ATENÇÃO: Use as mesmas credenciais do seu arquivo .env
MONGO_URI = "mongodb://admin_user:204314@localhost:27017/"
DB_NAME = "quimidocs"

# --- Dados para o teste ---
timestamp = int(time.time())
test_user_password = "StrongPassword123"
test_user = {
    "_id": ObjectId(), # Geramos o ID com antecedência
    "username": f"integ_user_{timestamp}",
    "email": f"integ_test_{timestamp}@test.com",
    "password_hash": generate_password_hash(test_user_password),
    "role": "administrador", # ✅ Garantimos a role correta
    "active": True
}
access_token = None
created_product_id = None

# --- Conecta ao MongoDB ---
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    # Limpa qualquer resquício de um teste anterior que possa ter falhado
    db.users.delete_one({"email": test_user["email"]})
    print("✅ Conexão com o MongoDB estabelecida com sucesso.")
except Exception as e:
    print(f"❌ Falha ao conectar com o MongoDB: {e}")
    exit()

print("\n🚀 INICIANDO TESTE DE INTEGRAÇÃO 🚀")

try:
    # 1. CRIAR USUÁRIO DIRETAMENTE NO BANCO
    print("\n[ETAPA 1/4] Inserindo usuário de teste diretamente no banco de dados...")
    db.users.insert_one(test_user)
    print(f"✅ Usuário '{test_user['username']}' inserido com a role '{test_user['role']}'.")

    # 2. FAZER LOGIN via API para obter token
    print("\n[ETAPA 2/4] Fazendo login via API...")
    login_data = {"email": test_user["email"], "senha": test_user_password}
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    assert response.status_code == 200, f"Falha no login! Status: {response.status_code}, Resposta: {response.text}"
    access_token = response.json()["access_token"]
    print("✅ Login bem-sucedido.")

    # 3. CRIAR PRODUTO via API
    print("\n[ETAPA 3/4] Criando produto via API...")
    product_data = {
        "nome_do_produto": f"Produto de Teste Integrado {timestamp}",
        "fornecedor": "Fornecedor de Integração",
        "estado_fisico": "Líquido",
        "local_de_armazenamento": "Armazém Central",
        "empresa": "Integration Tests Inc."
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/products", headers=headers, json=product_data)
    assert response.status_code == 201, f"Falha ao criar produto! Status: {response.status_code}, Resposta: {response.text}"
    created_product_id = response.json()["id"]
    print(f"✅ Produto '{product_data['nome_do_produto']}' criado.")

    # 4. VERIFICAR DIRETAMENTE NO BANCO DE DADOS
    print("\n[ETAPA 4/4] Verificando diretamente no MongoDB...")
    product_from_db = db.products.find_one({"_id": ObjectId(created_product_id)})
    
    assert product_from_db is not None, "Produto não encontrado no banco de dados!"
    assert product_from_db["nome_do_produto"] == product_data["nome_do_produto"], "O nome do produto no banco não corresponde!"
    print("✅ Verificação no MongoDB confirmada!")
    
    print("\n🎉 SUCESSO! A integração entre o Backend e o Banco de Dados está funcionando perfeitamente! 🎉")

except AssertionError as e:
    print(f"\n❌ FALHA NO TESTE DE INTEGRAÇÃO: {e}")

finally:
    # --- Limpeza dos dados de teste ---
    print("\n🧹 Iniciando limpeza...")
    if created_product_id:
        db.products.delete_one({"_id": ObjectId(created_product_id)})
        print("🧹 Produto de teste removido.")
    
    # Usamos o _id que já temos para garantir a remoção
    db.users.delete_one({"_id": test_user["_id"]})
    print("🧹 Usuário de teste removido.")
    client.close()
    print("🧹 Limpeza concluída.")