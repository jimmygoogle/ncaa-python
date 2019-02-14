from flask import Blueprint, request, render_template, url_for, redirect, jsonify, g
from project.ncaa_class import Ncaa
from project.pool_class import Pool
from project.bracket_class import Bracket
import datetime

pool = Pool()
bracket = Bracket()
pool_blueprint = Blueprint('pool', __name__, template_folder='templates')

@pool_blueprint.route('/')
def index():
    '''Show master bracket (if pool is closed) or show a bracket for user submission (if pool is open)'''
    
    pool_name = pool.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))
    else:
        year = datetime.datetime.now().year
        pool_status = pool.check_pool_status()
        
        # bracket is open for submissions so get bracket page
        if pool_status['any']['is_open']:
            
            # set the bracket type
            bracket_type = 'normalBracket'
            
            if pool_status['sweetSixteenBracket'] == 1:
                bracket_type = 'sweetSixteenBracket'
                
            # set the bracket edit type
            edit_type = 'add'

            # render the bracket
            return render_template('bracket.html',
                pool_name = pool_name,
                year = year,
                data_team = '',
                data_pick = '',
                user_data = [{}],
                user_picks = bracket.get_empty_picks(),
                team_data = bracket.get_base_teams(),
                show_user_bracket_form = 1,
                is_open = 1,
                edit_type = edit_type,
                bracket_type = bracket_type
            )
        
        # the pool is closed so show the master bracket
        else:
            data = bracket.get_master_bracket_data()

            # render the bracket
            return render_template('bracket.html',
                pool_name = pool_name,
                year = year,
                data_team = '',
                data_pick = '',
                user_data = [],
                user_picks = data['user_picks'],
                team_data = data['team_data'],
                show_user_bracket_form = 0,
                is_open = 0,
            )

## routes for pool setup/switching
@pool_blueprint.route('/pool', methods=['GET', 'POST'])
@pool_blueprint.route('/pool/<string:pool_name>', methods=['GET'])
def show_pool_form(pool_name=None):
    '''Show pool form for user to enter their pool name'''

    # user posted a pool name to check or switch to
    if request.method == 'POST':
       pool_name = request.form['poolName']
       result = pool.validate_pool_name(pool_name)
       
       return jsonify(result)

    else:
        if pool_name is not None and pool_name != '':
            ## validate, set session and redirect to main page
            result = pool.validate_pool_name(pool_name)
            return redirect(url_for('pool.index'))
        else:
            return render_template('pool.html', 
                is_open = 1
            )

## set demo mode (portfolio)
@pool_blueprint.route('/demo')
def demo_mode():
    return redirect('/pool/butler')