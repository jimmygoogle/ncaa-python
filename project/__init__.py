from flask import Flask, request, session, g

def create_app(is_testing=None):
    
    app = Flask(__name__, instance_relative_config=True)

    from project.mysql_python import MysqlPython
    from project.mongo import Mongo
    
    with app.app_context():
    
        if is_testing is None:
            #set up DB connection
            db = MysqlPython()
            db.get_db()
            
            #set up mongo connection
            mongo = Mongo()
            mongo.get_db()

            # setup session
            from flask_session import Session
            flask_session = Session()
            app.config['SESSION_TYPE'] = 'filesystem'
            flask_session.init_app(app)
    
    if __name__ == '__main__':
        app.debug = True
        app.run(host='0.0.0.0')

    # import
    from project.pool.views import pool_blueprint
    from project.standings.views import standings_blueprint
    from project.bracket.views import bracket_blueprint
    from project.polls.views import polls_blueprint
    from project.admin.views import admin_blueprint
    
    # register the blueprints
    app.register_blueprint(pool_blueprint)
    app.register_blueprint(standings_blueprint)
    app.register_blueprint(bracket_blueprint)
    app.register_blueprint(polls_blueprint)
    app.register_blueprint(admin_blueprint)

    return app