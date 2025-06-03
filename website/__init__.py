from flask import Flask, g
import psycopg2

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            host="db",  # since running in container, matches compose service name
                        # use "localhost" outside container
            database="ce_app",
            user="ce_user",
            password="password"
        )
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def create_app():
    app = Flask(__name__)

    #app.config["SECRET KEY"] = "secret key"
    app.secret_key = "secret key" # session key
    app.teardown_appcontext(close_db) # closes db on crash

    from .views import views
    from .data_input import data_input
    from .analysis import analysis

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(data_input, url_prefix="/")
    app.register_blueprint(analysis, url_prefix="/")

    return app