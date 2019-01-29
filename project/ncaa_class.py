import sys

class Ncaa(object):
    
    def __init__(self):
        pass

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
