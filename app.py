from project import app, flask_session

if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'

    flask_session.init_app(app)
    
    app.debug = True
    app.run(host='0.0.0.0')