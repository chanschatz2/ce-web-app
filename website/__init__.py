import os
from flask import Flask, g
import psycopg2
from dotenv import load_dotenv

load_dotenv() # load env variables

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
        )
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def create_app():
    app = Flask(__name__)

    #app.config["SECRET KEY"] = "secret_key"
    app.secret_key = os.environ.get("FLASK_SECRET_KEY")
    app.teardown_appcontext(close_db) # closes db on crash

    from .views import views
    from .data_input import data_input
    from .analysis import analysis

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(data_input, url_prefix="/")
    app.register_blueprint(analysis, url_prefix="/")

    return app