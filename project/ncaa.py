from project.mysql_python import MysqlPython
from flask import request, render_template
from project import session, app, YEAR
from collections import defaultdict
import asyncio
import sys
import hashlib
import time
import re
import ast
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Ncaa(object):
    
    def __init__(self):
        self.pool_name = ''
        
        self.db = MysqlPython()
    
    def set_pool_name(self, pool_name):
        '''Validate pool name and then set it for use in the application'''

        self.debug(f"inside set_pool_name with {pool_name}")
        result = self.db.query(proc='PoolInfo', params=[pool_name])
        self.debug(result)
        status = 0;
        # we found our pool so set a cookie
        if len(result):
            status = 1
            
            # set pool name in the session
            session['pool_name'] = pool_name
            self.debug(f"pool name is set in the session as {session['pool_name']}")

        return status
    
    def get_pool_name(self):
        '''Get the pool name from the session'''

        # try and get pool name from session
        pool_name = session.get('pool_name')
        self.debug(f"pool name is {pool_name}")
        
        return pool_name

    def check_pool_status(self, bracket_type=None):
        '''Get current pool status'''
        
        result = self.db.query(proc='PoolStatus')
        self.debug(result)
        status = {
            'normalBracket': {'is_open': result[0]['poolOpen'], 'closing_date_time': result[0]['poolCloseDateTime']},
            'sweetSixteenBracket': {'is_open': result[0]['sweetSixteenPoolOpen'], 'closing_date_time': result[0]['sweetSixteenCloseDateTime'] }
        }
        
        if bracket_type is None:
            return status
        else:
            return status[bracket_type]

    def get_standings(self, **kwargs):
        '''Get standings data for the pool'''

        bracket_type = kwargs['bracket_type'] + 'Bracket'        
        pool_name = self.get_pool_name()
        pool_status = self.check_pool_status(bracket_type)

        # set the round id to calculate the best possible score from
        round_id = 3
        if kwargs['bracket_type'] == 'normal':
            round_id = 1
        
        # calculate best possible score for each user 
        best_possible_data = self.db.query(proc='BestPossibleScore', params=[round_id])
        
        # get the remaining games
        remaining_teams_data = self.db.query(proc='RemainingTeams', params=[pool_name, bracket_type])   
        
        # fetch the user standings
        standings_data = self.db.query(proc='Standings', params=[pool_status['is_open'], pool_name, bracket_type])
        
        # get number of games played
        games_left = self.db.query(proc='AreThereGamesLeft', params=[])

        data = self.calculate_best_possible_scores(standings_data=standings_data, best_possible_data=best_possible_data, remaining_teams_data=remaining_teams_data)
        
        return (data, 1)

    def calculate_best_possible_scores(self, **kwargs):
        '''
        Calculate the best possible scores left for each user
        
        Some of the variable case names are mixed here as that is how they were previously coming from the DB, this can be addressed later
        
        '''

        standings_data = kwargs['standings_data']
        remaining_teams_data = kwargs['remaining_teams_data']

        # best possible data
        best_possible_data = kwargs['best_possible_data']
        best_possible_score = best_possible_data[0]['bestPossibleScore']
        adjusted_score = best_possible_data[0]['adjustedScore']

        # build standings lookup table
        array_index = 0;
        standings_lookup = defaultdict(dict)
        incorrect_picks = defaultdict(dict)
        
        self.debug(f"adjusted score is {adjusted_score}")
        self.debug(f"best possible score is {best_possible_score}")

        for data in standings_data:
            token = data['userDisplayToken']
            standings_lookup[token] = array_index
            incorrect_picks[token] = {}
            data['bestPossibleScore'] = adjusted_score

            array_index += 1
        
        self.debug(standings_data[0])
        self.debug(remaining_teams_data[0])
        
        # figure out the best possible score remaining for each user
        for data in remaining_teams_data:
            token = data['userDisplayToken']
            team_name = data['teamName']
            index = standings_lookup[token]
    
            # user pick is wrong so set the wrong team so we can follow it to the final four
            if data['userPick'] == 'incorrectPick':
                incorrect_picks[token][team_name] = 1;     
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']
    
            # this is an incorrect final four pick so decrement the total of correct teams left
            if data['userPick'] == '' and token in incorrect_picks and incorrect_picks[token][team_name]:
                standings_data[index]['bestPossibleScore'] -= data['gameRoundScore']

        return standings_data

    def get_user_bracket_for_display(self, **kwargs):
        '''Get standings data for the pool'''

        is_master = kwargs['is_master']
        user_token = kwargs['user_token']
        pool_name = self.get_pool_name()
        pool_status = self.check_pool_status()
        
        self.debug(f'Getting data for {user_token}')

        # calculate best possible score for each user
        user_data = []
        
        # if 
        if user_token is not None:
            user_picks = self.db.query(proc='UserDisplayBracket', params=[user_token])

            # set syling for incorrect picks
            incorrect_picks = {}
            for pick in user_picks:
                team_id = pick['teamID']

                if pick['pickCSS'] == 'incorrectPick':
                    incorrect_picks[team_id] = 1;

                if not pick['pickCSS'] and incorrect_picks[team_id]:
                    pick['pickCSS'] = 'incorrectPick'

        else:
            user_picks = self.db.query(proc='MasterBracket', params=[])

            # remove formatting
            for pick in user_picks:
                pick['pickCSS'] = ''

        # get the base teams (top 64)
        team_data = self.get_base_teams()

        # if we have a real user then get some additional info
        if user_token:
            user_info = self.db.query(proc='GetUserByDisplayToken', params=[user_token])
            bracket_display_name = self.set_user_bracket_name(user_info[0]['userName'])
        else:
            user_info = {}
            bracket_display_name = ''
 
        return {
            'team_data': team_data, 
            'user_picks': user_picks, 
            'user_info': user_info, 
            'bracket_display_name': bracket_display_name
        }
       
    def get_base_teams(self):
        '''Get base teams data for display'''
        
        return self.db.query(proc='GetBaseTeams', params=[])

    def get_empty_picks(self):
        '''
        Set empty user picks data for an empty bracket
        TODO: Fix this as it is really hacky
        '''
        
        empty_data = []
        for index in range(63):
            data = {
                'teamID': '',
                'seedID': '',
                'teamName': '',
                'pickCSS': '',
            }

            empty_data.append(data)
        
        return empty_data
    
    def get_master_bracket_data(self):
        '''Get master bracket data for display'''
        
        data = self.get_user_bracket_for_display(is_master = 1, user_token = None)
        return data
        
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

    async def process_user_bracket(self, **kwargs):
        '''Process the data the user submitted and add it to the DB'''
        
        # the speed was same as when it was synchronously so i decided to try something different
        tasks = [self.x(), self.send_confirmation_email()]
        await asyncio.gather(*tasks)

        # send confirmation email
        #self.send_confirmation_email()    
        pass

    async def x(self):
        '''xxx'''

        bracket_type_name = request.values['bracket_type_name']
        email_address = request.values['username']
        username = request.values['bracket_type_name']
        first_name = request.values['first_name']
        tie_breaker_points = request.values['tie_breaker_points']
        user_picks = request.values['user_picks']
        edit_type = request.values['edit_type']

        # add/edit user data
        if edit_type == 'add':
            user_id = self.insert_new_user()
        else:
           self.update_user() 

        # convert the picks string to a dictionary
        user_picks_dict = ast.literal_eval(user_picks)
        self.debug(user_picks_dict)
    
        # loop through the game data and insert it
        for game_id in user_picks_dict:
            team_id = user_picks_dict[game_id]

            # insert user's game' picks
            self.db.insert(proc='InsertBracketData', params=[
                user_id,
                team_id,
                game_id
            ])
    
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
      
        edit_token = request.values['edit_token']
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
        
    async def send_confirmation_email(self, **kwargs):
        '''Send the user a confirmation email with a link to edit their picks'''

        sender_email = app.config['MAIL_USER']
        receiver_email = "jim@jimandmeg.com"
        #request.values['email_address']
        password = app.config['MAIL_PASS']
        
        message = MIMEMultipart("alternative")

        message["Subject"] = '\U0001F3C0' + f" Welcome to the {str(YEAR)} {self.get_pool_name().upper()} March Madness Pool"
        message["From"] = app.config['MAIL_FROM']
        message["To"] = receiver_email

        content = MIMEText(self.get_email_template(), 'html')
        message.attach(content)
        
        # create gmail connection and send
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )

        return 1
    
    def get_email_template(self):
        '''Build email template'''

        pool_status = self.check_pool_status()
        bracket_type_name = request.values['bracket_type_name']
        self.debug('closing_date_time is ' + pool_status[bracket_type_name]['closing_date_time'])

        return render_template('email.html',
            pool_name = self.get_pool_name().upper(),
            year = YEAR,
            username = request.values['username'],
            email = app.config['ERROR_EMAIL'],
            closing_date_time = pool_status[bracket_type_name]['closing_date_time'],
            edit_url = request.url_root
        )

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)

