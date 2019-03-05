from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.pool_class import Pool
from project.bracket_class import Bracket
from project.user_class import User
import datetime

bracket_blueprint = Blueprint('bracket', __name__, template_folder='templates')

## show brackets for display or editing
@bracket_blueprint.route('/bracket/<user_token>', methods=['GET', 'POST', 'PUT'])
def user_bracket(user_token):
    ''' Show the user bracket form '''

    bracket = Bracket()
    pool = Pool()
    user = User()
    
    # check to see if we are the admin/master bracket
    admin_user_token = user.get_admin_edit_token()
    is_admin = 0
    
    # if the user token equals the admin token
    if admin_user_token == user_token:
        is_admin = 1

    # check pool status
    pool_name = pool.get_pool_name()
    pool_status = pool.check_pool_status()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))
    
    year = datetime.datetime.now().year
    #bracket.debug(f"user token is {user_token} for {request.method}")

    # user is submitting bracket data so process it and add/update it in the DB
    if request.method == 'POST':
        return bracket.process_user_bracket(action = 'add', is_admin = None)

    # update the user bracket
    elif request.method == 'PUT':
        return bracket.process_user_bracket(action = 'update', edit_user_token = user_token, is_admin = is_admin)

    # show bracket to user
    else:
        ## set the default action to view
        action = 'view'
        show_user_bracket_form = 0
        edit_type = 'add'
        bracket_type = ''
        pool_is_open = 1

        # set bracket type based on open pool
        if pool_status['normalBracket']['is_open']:
            bracket_type = 'normalBracket'
        elif pool_status['sweetSixteenBracket']['is_open']:
            bracket_type = 'sweetSixteenBracket'
        else:
            pool_is_open = 0

        # the pools are always open for the admin user
        # i chose to do this here rather than make the if/elif/else more confusing
        if is_admin:
            pool_is_open = 1

        # we are trying to show a bracket for editing
        if 'action' in request.values and request.values['action'] == 'e':
            action = 'edit'
            edit_type = 'edit'

        # decide whether or not to allow the user to edit their bracket based on the pool close date/time
        show_user_bracket_form = 0

        if pool_is_open and action != 'view':
            show_user_bracket_form = 1   
        
        # get user data (bracket and info) for display purposes
        data = bracket.get_user_bracket_for_display(action = action, user_token = user_token, is_admin = is_admin)
        
        # add logic for setting display of user's winning pick
        data_team = ''
        data_pick = ''

        # add the winning pick
        # we need to account for the master bracket here as well as it wont have a winning pick until the tournament is over
        if 'pickCSS' in data['user_picks'][62]:
            data_pick = data['user_picks'][62]['pickCSS']
            data_team = str(data['user_picks'][62]['seedID']) + ' ' + data['user_picks'][62]['teamName']

        # render the bracket
        return render_template('bracket.html',
            pool_name = pool_name,
            year = year,
            data_pick = data_pick,
            data_team = data_team,
            user_picks = data['user_picks'],
            team_data = data['team_data'],
            bracket_display_name = data['bracket_display_name'],
            show_user_bracket_form = show_user_bracket_form,
            user_data = data['user_info'],
            is_open = pool_is_open,
            edit_type = edit_type,
            bracket_type = bracket_type,
            dates = bracket.get_start_dates()
        )