from json import JSONEncoder

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_login import LoginManager

import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '7e2c0a1fa3ee02906ca29f4a'

app.config['SECRET_KEY'] = '7e2c0a1fa3ee02906ca29f4a'

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Naddafly.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
app.json_encoder = JSONEncoder
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"
from Naddafly import routes

with app.app_context():
    db.create_all()
