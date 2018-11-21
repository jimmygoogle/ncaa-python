from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa import Ncaa
from project import YEAR

ncaa = Ncaa()
pool_blueprint = Blueprint('pool', __name__, template_folder='templates')

@pool_blueprint.route('/')
def index():
    '''Show index page'''
    if 1 == 2:
        return 'should redirect' 
        ##url_for('show_pool_form')
    else:
        return 'show something'

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
        return render_template('pool.html', year=YEAR, gui_js_only=1)

## set demo mode (portfolio)
@pool_blueprint.route('/demo')
def demo_mode():
    return redirect('/pool/butler')