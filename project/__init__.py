from flask import Flask, request, session
from flask_session import Session
import datetime

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

flask_session = Session()

# set some global variables
YEAR = datetime.datetime.now().year

from project.pool.views import pool_blueprint
from project.standings.views import standings_blueprint
from project.bracket.views import bracket_blueprint
from project.admin.views import admin_blueprint

# register the blueprints
app.register_blueprint(pool_blueprint)
app.register_blueprint(standings_blueprint)
app.register_blueprint(bracket_blueprint)
app.register_blueprint(admin_blueprint)