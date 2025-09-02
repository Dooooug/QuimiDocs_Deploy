from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
import os

# Importa as classes Product e User
from app.models import Product, User
# Importa inicialização de segurança e limiter
from app.security_config import init_security, limiter


# Variável global para a instância do banco de dados MongoDB
# Esta variável será acessada pelos métodos .collection() das suas classes de modelo
db = None

def create_app():
    app = Flask(__name__)

    # Configurações do Flask com valores padrão para evitar erros
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['MONGO_DB_NAME'] = os.environ.get('MONGO_DB_NAME', 'quimicadocs_db')

    # Inicializa JWT
    jwt = JWTManager(app)

    # Inicializa rate limiting com o app
    init_security(app)  

    # Conexão com o MongoDB
    try:
        mongo_client = MongoClient(app.config['MONGO_URI'])
        global db
        db = mongo_client[app.config['MONGO_DB_NAME']]
        print("Conexão MongoDB estabelecida com sucesso.")
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        exit(1)

    # Configuração do CORS para permitir requisições do frontend
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

    # Importa e registra os Blueprints
    from app.routes.user_routes import user_bp
    from app.routes.product_routes import product_bp
    from app.routes.pdf_routes import pdf_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(pdf_bp)

    # Rota inicial
    @app.route('/')
    def home():
        return "Aplicação Flask funcionando"

    return app
