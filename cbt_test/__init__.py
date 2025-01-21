from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

loginManager = LoginManager()
db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ecd7aa86d7ed8e31449fff0fb4c124ed'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    
    db.init_app(app)
    bcrypt.init_app(app)
    loginManager.init_app(app)

    loginManager.login_view = 'main.login'
    loginManager.login_message_category = 'info'
        
    from cbt_test.routes import main
    app.register_blueprint(main)
    
    return app