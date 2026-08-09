import os
from flask import Flask, g, request, session
from dotenv import load_dotenv
from .database import banco, init_db

load_dotenv()

def create_app():
    app = Flask(__name__)

    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.secret_key = os.environ.get('SECRET_KEY')

    @app.before_request
    def carregar_fase_atual():
        endpoints_ignorados = ['static', 'geral.exibir_imagem_usuario']
        if request.endpoint in endpoints_ignorados:
            return

        resultado = banco.execute_query("SELECT fase FROM fase")
        print(resultado[0]['fase'])
        if resultado:
            session['fase'] = resultado[0]['fase']

    @app.teardown_appcontext
    def close_connection(exception):
        db_conn = g.pop('db', None)
        if db_conn is not None:
            db_conn.close()

    with app.app_context():
        init_db()

    from app.controllers.geral import geral_bp
    from app.controllers.admin import admin_bp
    from app.controllers.empresa import empresa_bp
    from app.controllers.candidato import candidato_bp

    app.register_blueprint(geral_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(empresa_bp)
    app.register_blueprint(candidato_bp)

    return app