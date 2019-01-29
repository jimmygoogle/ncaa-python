#from project import app, flask_session
#
#if __name__ == '__main__':
#    app.config['SESSION_TYPE'] = 'filesystem'
#
#    flask_session.init_app(app)
#    
#    app.debug = True
#    app.run(host='0.0.0.0')


from project import create_app

create_app().run(host='0.0.0.0', port=5000, debug=True)