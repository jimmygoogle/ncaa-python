from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from ncaa import Ncaa
from project import YEAR

ncaa = Ncaa()
pool_blueprint = Blueprint('pool', __name__, template_folder='templates')

@pool_blueprint.route('/')
def index():
    if 1 == 2:
        return 'should redirect' 
        ##url_for('show_pool_form')
    else:
        return 'show something'


## routes for pool setup/switching
@pool_blueprint.route('/pool/')
@pool_blueprint.route('/pool/<string:pool_name>/')
def show_pool_form(pool_name=None):
    if pool_name:
        ## setting cookie and redirect to main page
        ncaa.setPoolName(pool_name)
        return redirect(url_for('index'))
    else:
        return render_template('pool.html', year=YEAR)

## set demo mode (portfolio)
@pool_blueprint.route('/demo')
def demo_mode():
    return redirect('/pool/butler')