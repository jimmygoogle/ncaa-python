from flask import Flask, request, session, g
from celery import Celery
from project.mysql_python import MysqlPython
from project.mongo import Mongo
import configparser

config = configparser.ConfigParser()
config.read("site.cfg")

# setup redis
redis_host = config.get('REDIS', 'REDIS_HOST')
redis_port = config.get('REDIS', 'REDIS_PORT')
redis_url = f"redis://{redis_host}:{redis_port}/0"

celery = Celery(__name__, broker=redis_url)

db = MysqlPython()
mongo = Mongo()

def create_app(is_testing=None, celery_app=None):
    app = Flask(__name__)

    with app.app_context():    
        if is_testing is None:
            # dont load the DB stuff for celery
            if celery_app is None:
                # set up mysql connection
                db.get_db()
            
                # set up mongo connection
                mongo.get_db()

            # setup session
            from flask_session import Session
            flask_session = Session()
            app.config['SESSION_TYPE'] = 'filesystem'
            flask_session.init_app(app)

            # setup celery
            app.config['CELERY_BROKER_URL'] = redis_url
            app.config['CELERY_RESULT_BACKEND'] = redis_url
            celery.conf.update(app.config)
  
            # close the DB connections
            @app.teardown_request
            def teardown_request(response_or_exc):
                db.close_db()
                mongo.close_db()        
   
    if __name__ == '__main__':
        app.debug = True
        app.run(host='0.0.0.0', port=5000)

    # import blue prints
    from project.blueprints.pool.views import pool_blueprint
    from project.blueprints.standings.views import standings_blueprint
    from project.blueprints.bracket.views import bracket_blueprint
    from project.blueprints.polls.views import polls_blueprint
    from project.blueprints.admin.views import admin_blueprint
    
    # register the blueprints
    app.register_blueprint(pool_blueprint)
    app.register_blueprint(standings_blueprint)
    app.register_blueprint(bracket_blueprint)
    app.register_blueprint(polls_blueprint)
    app.register_blueprint(admin_blueprint)
    
    return app
