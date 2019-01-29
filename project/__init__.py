from flask import Flask, request, session, g

def create_app(test_config=None):
    
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py')
    
    from project.mysql_python import MysqlPython
    import datetime
    with app.app_context():
        db = MysqlPython()
        db.get_db()
        
        # set some global variables
        g.year = datetime.datetime.now().year

    from flask_session import Session
    flask_session = Session()
    app.config['SESSION_TYPE'] = 'filesystem'
    flask_session.init_app(app)
    
    if __name__ == '__main__':
        app.debug = True
        app.run(host='0.0.0.0')
    

    
    from project.pool.views import pool_blueprint
    from project.standings.views import standings_blueprint
    from project.bracket.views import bracket_blueprint
    from project.admin.views import admin_blueprint
    
    # register the blueprints
    app.register_blueprint(pool_blueprint)
    app.register_blueprint(standings_blueprint)
    app.register_blueprint(bracket_blueprint)
    app.register_blueprint(admin_blueprint)

    return app