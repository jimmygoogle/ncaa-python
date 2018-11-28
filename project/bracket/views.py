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

    ncaa.debug(request.method)
    #str(user_token)
    if request.method == 'POST':
        #request.values['xxx']
        #request.form['xxx']
        return "update user bracket %s %d times" % (user_token, 3) 
        #return "update user bracket %s" % user_token 
    else:
        
        data = ncaa.get_user_bracket_for_display(user_token=user_token)

        return render_template('bracket.html',
            pool_name = pool_name,
            year = YEAR,
            user_picks = data['user_picks'],
            team_data = data['team_data'],
            bracket_display_name = data['bracket_display_name']
        )
        
           # response = make_response(redirect(url_for('index')))
           # response.set_cookie('MarchMadnessPoolName', 'xxx', expires=(30 * 24 * 60 * 60 * 1000))
           # return response
           
           #if 'MarchMadnessPoolName' in session
           #session['MarchMadnessPoolName']
            
           # pool_name = request.cookies.get('MarchMadnessPoolName')
           # if pool_name:
    
    # session['MarchMadnessPoolName'] = 'xxxx'
    