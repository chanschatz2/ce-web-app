from flask import Flask

def create_app():
    app = Flask(__name__)
    # session key
    #app.config["SECRET KEY"] = "secret key"
    app.secret_key = "secret key"

    from .views import views
    from .data_input import data_input
    from .analysis import analysis

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(data_input, url_prefix="/")
    app.register_blueprint(analysis, url_prefix="/")

    return app