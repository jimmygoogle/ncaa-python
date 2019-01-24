from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa import Ncaa
from project import YEAR

ncaa = Ncaa()
bracket_blueprint = Blueprint('bracket', __name__, template_folder='templates')

## show brackets for display or editing
#@bracket_blueprint.route('/bracket/', methods=['POST'], defaults={'user_token': None})
@bracket_blueprint.route('/bracket/<user_token>', methods=['GET', 'POST', 'PUT'])
def user_bracket(user_token):
 
    ''' Show the user bracket form '''

    pool_name = ncaa.get_pool_name()
    pool_status = ncaa.check_pool_status()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))
    
    ncaa.debug(f"user token is {user_token}")
    ncaa.debug(f"request is {request.method}")

    # user is submitting bracket data so process it and add it to the DB
    if request.method == 'POST':
        ncaa.process_user_bracket(action = 'add')
        return ''

    # update the user bracket
    elif request.method == 'PUT':
        ncaa.user_edit_token = user_token
        ncaa.process_user_bracket(action = 'update')
        return ''  
    # show bracket to user
    else:
        ## set the default action to view
        action = 'view'
        show_user_bracket_form = 0
        edit_type = 'add'

        if pool_status['normalBracket']['is_open']:
            bracket_type = 'normalBracket'
        elif pool_status['sweetSixteenBracket']['is_open']:
            bracket_type = 'sweetSixteenBracket'

        ## TODO check to see if pool open
        pool_is_open = 1
        #pool_status
        
        if 'action' in request.values and request.values['action'] == 'e' and pool_is_open:
            action = 'edit'
            show_user_bracket_form = 1
            edit_type = 'edit'
        
        # get user data (bracket and info) for display purposes
        data = ncaa.get_user_bracket_for_display(action = action, user_token = user_token, is_master = None)
        
        # add logic for setting display of user's winning pick
        data_team = ''
        data_pick = ''

        if 'pickCSS' in data['user_picks'][62]:
            data_pick = data['user_picks'][62]['pickCSS']
            data_team = str(data['user_picks'][62]['seedID']) + ' ' + data['user_picks'][62]['teamName']

        # render the bracket
        return render_template('bracket.html',
            pool_name = pool_name,
            year = YEAR,
            data_pick = data_pick,
            data_team = data_team,
            user_picks = data['user_picks'],
            team_data = data['team_data'],
            bracket_display_name = data['bracket_display_name'],
            show_user_bracket_form = show_user_bracket_form,
            user_data = data['user_info'],
            is_open = 1,
            edit_type = edit_type,
            bracket_type = bracket_type
        )

def show_open_bracket():
    ''' WIP ''' 