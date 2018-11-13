from project import app
 
if __name__ == '__main__':
    app.debug = True
    ## key from os.urandom(24)
    app.secret_key = 'Q\xa7\x91\xfa\\\xc0\xf9\xc3\xa0\x85\x92\xd7\xacQ\xbe\xae\x06%\x03Dl\x96OC'
    app.run(host='0.0.0.0')


