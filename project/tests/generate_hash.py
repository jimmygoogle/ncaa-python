import hashlib, binascii, sys, configparser
 
def hash_password(password):
    '''Hash a password for admin'''

    config = configparser.ConfigParser()
    config.read("site.cfg")
        
    salt = config.get('DEFAULT', 'ADMIN_LOGIN_SALT').encode('utf-8')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

pw = hash_password(sys.argv[0])
print(f"password is {pw}")