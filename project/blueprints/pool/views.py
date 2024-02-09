from flask import Blueprint, request, render_template, url_for, redirect, jsonify, g
from project.pool import Pool
from project.bracket import Bracket
import datetime
import configparser

pool = Pool()
bracket = Bracket()
pool_blueprint = Blueprint('pool', __name__, template_folder='templates')
year = datetime.datetime.now().year

@pool_blueprint.route('/')
def index():
    '''Show master bracket (if pool is closed) or show a bracket for user submission (if pool is open)'''
    pool_name = pool.get_pool_name()

    if pool_name is None:
        # for now redirect to a working pool
        return redirect('/pool/butler')
        # return redirect(url_for('pool.show_pool_form'))
    else:
        pool_status = pool.check_pool_status()

        # scoring_info
        scoring_info = pool.get_pool_round_score()

        # bracket is open for submissions so get bracket page
        if pool_status['any']['is_open']:
            # set the bracket type
            if pool_status['sweetSixteenBracket']['is_open'] == 1:
                bracket_type = 'sweetSixteenBracket'
                bracket_type_label = 'sweet'
                user_picks = bracket.get_master_bracket_data()['user_picks']
            else:
                user_picks = bracket.get_empty_picks()
                bracket_type = 'normalBracket'
                bracket_type_label = 'full'

            # set the bracket edit type
            edit_type = 'add'

            # render the bracket
            return render_template('bracket.html',
                pool_name = pool_name,
                year = year,
                data_team = '',
                data_pick = '',
                user_data = [{}],
                user_picks = user_picks,
                team_data = bracket.get_base_teams(),
                show_user_bracket_form = 1,
                is_open = 1,
                edit_type = edit_type,
                bracket_type = bracket_type,
                bracket_type_label = bracket_type_label,
                dates = bracket.get_start_dates(),
                upset_bonus_data = '{}',
                scoring_info = scoring_info,
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
                dates = bracket.get_start_dates(),
                requires_payment = 0,
                scoring_info = scoring_info,
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

## show pricing
@pool_blueprint.route('/pricing')
def pricing():
    config = configparser.ConfigParser()
    config.read("site.cfg")

    return render_template('pricing.html',
        year = year,
        contact_email = config.get('EMAIL', 'CONTACT_US')
    )

## show contact form
@pool_blueprint.route('/contact', methods=['GET', 'POST'])
def contact():
    # user posted question
    if request.method == 'POST':
        # send contact request
        pool.send_contact_email(
            request = request.form
        )
        return render_template('contact.html', year = year)
    else:
        return render_template('contact.html', year = year)
