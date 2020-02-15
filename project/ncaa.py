import sys
import configparser

class Ncaa(object):
    
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.paypal_client_id = config.get('PAYPAL', 'CLIENT_ID')
        pass

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
