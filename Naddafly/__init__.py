from json import JSONEncoder

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_swagger_ui import get_swaggerui_blueprint
import datetime

app = Flask(__name__ , static_folder='static')
app.config['JWT_SECRET_KEY'] = '7e2c0a1fa3ee02906ca29f4a'

app.config['SECRET_KEY'] = '7e2c0a1fa3ee02906ca29f4a'

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Naddafly.db'
app.config['SQLALCHEMY_POOL_SIZE'] = 200  
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
app.json_encoder = JSONEncoder
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

SWAGGER_URL = '/swagger'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "NADDAFLY"
    },
   
)

app.register_blueprint(swaggerui_blueprint)

# app.run()
from Naddafly import routes

with app.app_context():
    db.create_all()
