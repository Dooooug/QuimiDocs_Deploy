# app/__init__.py

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
import os

# Importações
from app.models import Product, User
from app.security_config import init_security
from app.routes.pdf_routes import init_services as init_pdf_services

db = None

def create_app(testing: bool = False):
    """
    Fábrica de criação da aplicação Flask, otimizada para DEV e PRODUÇÃO.
    """
    app = Flask(__name__)

    # ========================
    # CONFIGURAÇÕES BÁSICAS
    # ========================
    app.config['MONGO_DB_NAME'] = os.environ.get('MONGO_DB_NAME', 'quimicadocs_db')

    # Detecta ambiente (Render = produção, local = dev)
    env = os.environ.get('FLASK_ENV', 'production')

    if testing:
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret'
        app.config['JWT_SECRET_KEY'] = 'test_jwt_secret'
        app.config['MONGO_URI'] = "mongodb://localhost:27017/test_db"
        print("⚠️ Aplicação iniciada em modo de TESTE.")

    elif env == 'development':
        # 🔧 Modo desenvolvimento local
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret')
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret')
        app.config['MONGO_URI'] = os.environ.get(
            'MONGO_URI',
            'mongodb://localhost:27017/quimicadocs_db'
        )

    else:
        # 🔒 Modo produção (Render)
        try:
            app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
            app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
            app.config['MONGO_URI'] = os.environ['MONGO_URI']
        except KeyError as e:
            print(f"❌ ERRO: Variável de ambiente {e} não definida.")
            exit(1)

    # ========================
    # EXTENSÕES DO FLASK
    # ========================
    JWTManager(app)
    init_security(app)

    # ========================
    # CONFIGURAÇÃO DE CORS
    # ========================
    if env == 'development':
        allowed_origins = [
            "http://localhost:3000",
            "https://localhost:3000",
            "http://127.0.0.1:3000",
            "http://quimidocs:3000"
        ]
        CORS(app, resources={r"/*": {"origins": allowed_origins}})
        print(f"✅ CORS (DEV) habilitado para: {', '.join(allowed_origins)}")

    else:
        FRONTEND_URL_STRING = os.environ.get('FRONTEND_URL')
        if FRONTEND_URL_STRING:
            allowed_origins = [url.strip() for url in FRONTEND_URL_STRING.split(',')]
            CORS(app, resources={r"/*": {"origins": allowed_origins}})
            print(f"✅ CORS (PROD) habilitado para: {', '.join(allowed_origins)}")
        else:
            CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
            print("⚠️ FRONTEND_URL não definida — usando fallback localhost.")

    # ========================
    # CONEXÃO COM MONGODB
    # ========================
    global db
    if not testing:
        try:
            mongo_client = MongoClient(app.config['MONGO_URI'])
            db = mongo_client[app.config['MONGO_DB_NAME']]
            mongo_client.admin.command('ping')
            print("✅ Conexão com MongoDB estabelecida com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao conectar com MongoDB: {e}")
            exit(1)

    # ========================
    # ROTAS / BLUEPRINTS
    # ========================
    with app.app_context():
        init_pdf_services()

    from app.routes.user_routes import user_bp
    from app.routes.product_routes import product_bp
    from app.routes.pdf_routes import pdf_bp
    from app.routes.dashboard_routes import dashboard_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    @app.route('/')
    def home():
        return "Backend da QuimiDocs funcionando perfeitamente!"

    return app
