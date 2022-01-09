from flask import Flask

app = Flask(__name__, template_folder='template', static_url_path='/pfad')
app.secret_key = "superSecretKey"

from app import routes

app.config.from_object('config')