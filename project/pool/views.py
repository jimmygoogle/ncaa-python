from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa import Ncaa
from project import YEAR

ncaa = Ncaa()
pool_blueprint = Blueprint('pool', __name__, template_folder='templates')

@pool_blueprint.route('/')
def index():
    '''Show master bracket (if pool is closed) or show a bracket for user submission (if pool is open)'''
    
    pool_name = ncaa.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))
    else:
        pool_status = ncaa.check_pool_status()
        
        # bracket is open for submissions so get bracket page
        if pool_status['normalBracket']['is_open'] or pool_status['sweetSixteenBracket']['is_open']:
            
            # set the bracket type
            bracket_type = 'normalBracket'
            
            if pool_status['sweetSixteenBracket'] == 1:
                bracket_type = 'sweetSixteenBracket'
                
            # set the bracket edit type
            edit_type = 'add'

            # render the bracket
            return render_template('bracket.html',
                pool_name = pool_name,
                year = YEAR,
                data_team = '',
                data_pick = '',
                user_data = [{}],
                user_picks = ncaa.get_empty_picks(),
                team_data = ncaa.get_base_teams(),
                show_user_bracket_form = 1,
                is_open = 1,
                edit_type = edit_type,
                bracket_type = bracket_type
            )
        
        # show the master bracket
        else:
            data = ncaa.get_master_bracket_data()

            # render the bracket
            return render_template('bracket.html',
                pool_name = pool_name,
                year = YEAR,
                data_team = '',
                data_pick = '',
                user_data = [],
                user_picks = data['user_picks'],
                team_data = data['team_data'],
                show_user_bracket_form = 1,
                is_open = 1,
            )

## routes for pool setup/switching
@pool_blueprint.route('/pool', methods=['GET', 'POST'])
@pool_blueprint.route('/pool/<string:pool_name>', methods=['GET'])
def show_pool_form(pool_name=None):
    '''Show pool form for user to enter their pool name'''

    # user posted a pool name to check or switch to
    if request.method == 'POST':
       pool_name = request.form['poolName']

    ncaa.debug(f"pool name in show_pool_form is {pool_name}")

    if pool_name is not None and pool_name != '':
        ncaa.debug(f"yo {pool_name}")
        ## set session and redirect to main page
        ncaa.set_pool_name(pool_name)
        return redirect(url_for('pool.index'))
    else:
        return render_template('pool.html', 
            year = YEAR,
            is_open = 0
        )

## set demo mode (portfolio)
@pool_blueprint.route('/demo')
def demo_mode():
    return redirect('/pool/butler')