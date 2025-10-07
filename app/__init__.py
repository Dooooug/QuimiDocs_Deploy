from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
import os

# Importa os modelos
from app.models import Product, User
# Importa inicialização de segurança e rate limiter
from app.security_config import init_security

# A importação está correta!
from app.routes.pdf_routes import init_services as init_pdf_services 

# Variável global para a instância do banco de dados MongoDB
db = None

def create_app(testing: bool = False):
    """
    Fábrica de criação da aplicação Flask.
    """
    app = Flask(__name__)

    # ========================
    # CONFIGURAÇÕES BÁSICAS
    # ========================
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt_secret')
    app.config['MONGO_DB_NAME'] = os.environ.get('MONGO_DB_NAME', 'quimicadocs_db')

    if testing:
        app.config['TESTING'] = True
        app.config['MONGO_URI'] = "mongodb://localhost:27017/test_db"
        print("⚠️ Aplicação iniciada em modo de TESTE.")
    else:
        app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

    # ========================
    # EXTENSÕES DO FLASK
    # ========================
    JWTManager(app)
    init_security(app)
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

    # ========================
    # CONEXÃO COM MONGODB
    # ========================
    global db
    if not testing:
        try:
            mongo_client = MongoClient(app.config['MONGO_URI'])
            db = mongo_client[app.config['MONGO_DB_NAME']]
            print("✅ Conexão MongoDB estabelecida com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao conectar ao MongoDB: {e}")
            exit(1)
    else:
        db = None

    # ==========================================================
    # ALTERAÇÃO NECESSÁRIA: INICIALIZAÇÃO DE SERVIÇOS EXTERNOS
    # ==========================================================
    # É crucial chamar a função aqui para inicializar a conexão S3.
    with app.app_context():
        init_pdf_services()
    
    # ========================
    # BLUEPRINTS
    # ========================
    from app.routes.user_routes import user_bp
    from app.routes.product_routes import product_bp
    from app.routes.pdf_routes import pdf_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(pdf_bp)

    # ========================
    # ROTA INICIAL
    # ========================
    @app.route('/')
    def home():
        return "Aplicação Flask funcionando"

    return app