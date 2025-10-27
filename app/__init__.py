# app/__init__.py

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
import os

# Importações continuam as mesmas
from app.models import Product, User
from app.security_config import init_security
from app.routes.pdf_routes import init_services as init_pdf_services

db = None

def create_app(testing: bool = False):
    """
    Fábrica de criação da aplicação Flask, otimizada para produção e deploy.
    """
    app = Flask(__name__)

    # ========================
    # CONFIGURAÇÕES BÁSICAS
    # ========================
    app.config['MONGO_DB_NAME'] = os.environ.get('MONGO_DB_NAME', 'quimicadocs_db')

    if testing:
        # Configurações para ambiente de teste permanecem as mesmas
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret'
        app.config['JWT_SECRET_KEY'] = 'test_jwt_secret'
        app.config['MONGO_URI'] = "mongodb://localhost:27017/test_db"
        print("⚠️  Aplicação iniciada em modo de TESTE.")
    else:
        # <<< MUDANÇA 1: Tornando os segredos obrigatórios em produção >>>
        try:
            app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
            app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
            app.config['MONGO_URI'] = os.environ['MONGO_URI']
        except KeyError as e:
            print(f"❌ ERRO: A variável de ambiente {e} não foi definida!")
            print("❌ A aplicação não pode iniciar sem as configurações de segurança.")
            exit(1) # Encerra a aplicação se uma chave estiver faltando

    # ========================
    # EXTENSÕES DO FLASK
    # ========================
    JWTManager(app)
    init_security(app)

    # <<< CORREÇÃO CRÍTICA DO CORS PARA MÚLTIPLAS ORIGENS >>>
    if not testing:
        # Pega a string de URLs do FRONTEND_URL configurada no Render (ex: "url1,url2")
        FRONTEND_URL_STRING = os.environ.get('FRONTEND_URL')
        
        if FRONTEND_URL_STRING:
            # 1. Divide a string pela vírgula (','), transformando em uma lista.
            # 2. .strip() remove quaisquer espaços em branco de cada URL.
            allowed_origins = [url.strip() for url in FRONTEND_URL_STRING.split(',')]
            
            # 3. Passa a lista de origens para a configuração do CORS.
            CORS(app, resources={r"/*": {"origins": allowed_origins}})
            print(f"✅ CORS configurado para aceitar requisições de: {', '.join(allowed_origins)}")
        else:
            # Fallback para localhost se a variável não for definida (bom para debug)
            CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
            print("⚠️ AVISO: FRONTEND_URL não definida. CORS configurado para localhost.")

    # ========================
    # CONEXÃO COM MONGODB
    # ========================
    global db
    if not testing:
        try:
            mongo_client = MongoClient(app.config['MONGO_URI'])
            db = mongo_client[app.config['MONGO_DB_NAME']]
            # O ping() é uma boa forma de validar a conexão imediatamente.
            mongo_client.admin.command('ping')
            print("✅ Conexão com MongoDB estabelecida e validada com sucesso.")
        except Exception as e:
            print(f"❌ Erro fatal ao conectar ou validar o MongoDB: {e}")
            exit(1)
    else:
        db = None

    # O restante do seu código está perfeito e não precisa de alterações!
    with app.app_context():
        init_pdf_services()
    
    from app.routes.user_routes import user_bp
    from app.routes.product_routes import product_bp
    from app.routes.pdf_routes import pdf_bp
    from app.routes.dashboard_routes import dashboard_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(dashboard_bp)

    @app.route('/')
    def home():
        return "Backend da QuimiDocs funcionando perfeitamente!"

    return app