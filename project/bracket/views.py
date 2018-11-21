from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa import Ncaa

ncaa = Ncaa()
bracket_blueprint = Blueprint('bracket', __name__, template_folder='templates')

## show brackets for display or editing
@bracket_blueprint.route('/bracket/<string:user_token>/', methods=['GET'])
@bracket_blueprint.route('/bracket/<string:user_token>/e/', methods=['GET', 'POST'])
def user_bracket(user_token):
    print(request.method)
    #str(user_token)
    if request.method == 'POST':
        #request.values['xxx']
        #request.form['xxx']
        return "update user bracket %s %d times" % (user_token, 3) 
        #return "update user bracket %s" % user_token 
    else:
        return 'show bracket for updating' 
        
           # response = make_response(redirect(url_for('index')))
           # response.set_cookie('MarchMadnessPoolName', 'xxx', expires=(30 * 24 * 60 * 60 * 1000))
           # return response
           
           #if 'MarchMadnessPoolName' in session
           #session['MarchMadnessPoolName']
            
           # pool_name = request.cookies.get('MarchMadnessPoolName')
           # if pool_name:
    
    # session['MarchMadnessPoolName'] = 'xxxx'
    