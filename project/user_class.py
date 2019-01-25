from project.pool_class import Pool
from project import session, app, YEAR
import re

class User(Pool):
    '''User class to get/set information for a user that is tied to their pool. A user (email) can exist in multiple pools'''

    def __init__(self):
        super().__init__()
        self.user_edit_token = ''

    def set_user_edit_token(self, **kwargs):
        '''
        Creates a token string to be encoded from the time, pool name, user email, username, bracket type and display type.
        This combo ensures a unique token for every user
        '''
        
        token = [str(time.time()), session['pool_name'], kwargs['email_address'], kwargs['username'], kwargs['bracket_type_name'], 'edit'];
        return self.set_token('.'.join(token))
    
    def set_user_display_token(self, **kwargs):
        '''
        Creates a token string to be encoded from the time, pool name, user email, username, bracket type and display type.
        This combo ensures a unique token for every user
        '''
        
        token = [str(time.time()), session['pool_name'], kwargs['email_address'], kwargs['username'], kwargs['bracket_type_name'], 'display'];
        return self.set_token('.'.join(token))
    
    def set_token(self, string):
        '''Creates an md5 hash from string parameter'''

        h = hashlib.new('ripemd160')
        h.update(string.encode('utf-8'))
        return h.hexdigest()
    
    def set_user_bracket_name(self, username):
        '''
        Fixes the usernmame for display.
        
        If the username doesnt end in an 's' append one for the bracket name
        ex: Jim -> Jim's
        ex: Balls stays Balls'
        '''
        
        # get rid of spaces at the end of the user name and append '
        username = re.sub(r'\s+$', '', username)
        username += "'"

        # append 's' at the end of the string if the string doesnt already end with "'s"
        if not re.search(r"s'$", username):
            username += 's'

        return username

    def update_user_data(self):
        '''
            Add/update the user information
            Ex: email, username, etc
        '''

        edit_type = request.values['edit_type']

        # add/edit user data
        if edit_type == 'add':
            user_id = self.insert_new_user()
        else:
           user_id = self.update_user()
           
        return user_id
   
    def insert_new_user(self, **kwargs):
        '''Insert new user to DB'''
        
        bracket_type_name = request.values['bracket_type_name']
        email_address = request.values['email_address']
        username = request.values['username']
        first_name = request.values['first_name']
        tie_breaker_points = request.values['tie_breaker_points']

        # setup user tokens
        display_token = self.set_user_display_token(
            email_address = email_address,
            username = username,
            bracket_type_name = bracket_type_name
        )

        edit_token = self.set_user_edit_token(
            email_address = email_address,
            username = username,
            bracket_type_name = bracket_type_name
        )
        
        self.user_edit_token = edit_token

        pool_name = self.get_pool_name()

        user_id = self.db.insert(proc='InsertUser', params=[
            pool_name,
            username,
            email_address,
            tie_breaker_points,
            first_name,
            edit_token, 
            display_token,
            bracket_type_name
        ])
        
        return user_id
        
    def update_user(self, **kwargs):
        '''Update the user information based on their edit token value'''
      
        edit_token = self.user_edit_token
        bracket_type_name = request.values['bracket_type_name']
        email_address = request.values['email_address']
        username = request.values['username']
        first_name = request.values['first_name']
        tie_breaker_points = request.values['tie_breaker_points']

        user_id = self.db.update(proc='UpdateUser', params=[
            edit_token,
            username,
            email_address,
            tie_breaker_points,
            first_name
          ])

        # clear out the user's picks
        self.db.insert(proc='ResetBracket', params=[user_id])

        return user_id