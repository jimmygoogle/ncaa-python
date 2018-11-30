from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa import Ncaa
from project import YEAR

ncaa = Ncaa()
bracket_blueprint = Blueprint('bracket', __name__, template_folder='templates')

## show brackets for display or editing
@bracket_blueprint.route('/bracket/<string:user_token>/')
#@bracket_blueprint.route('/bracket/<string:user_token>/e', methods=['GET', 'POST'])
def user_bracket(user_token):

    pool_name = ncaa.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))

    # user is submitting bracket data
    if request.method == 'POST':
        #request.values['xxx']
        #request.form['xxx']
        return "update user bracket %s %d times" % (user_token, 3) 

    # show bracket to user
    else:
        data = ncaa.get_user_bracket_for_display(user_token = user_token, is_master = None)
        
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
            bracket_display_name = data['bracket_display_name']
        )
    