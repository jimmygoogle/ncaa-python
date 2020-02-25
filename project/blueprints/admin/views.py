from flask import Blueprint, request, render_template, redirect, url_for, flash
from project.ncaa import Ncaa
from project.admin import Admin
from project.bracket import Bracket

admin = Admin()
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')

@admin_blueprint.route('/admin', methods=['GET', 'POST'])
def admin_login():
    '''Show/process admin login'''

    admin = Admin()

    # handle login
    if request.method == 'POST':
        error = None

        # if we tried to log in
        if admin.process_admin_login():
            return show_admin_page()
        else:
            error = 'Really?!'
            show_admin_login_page(error)

    # show login or menu page
    else:
        # show login form
        if not admin.is_logged_in():
            return show_admin_login_page(None)
    
        # show admin menu
        else:
            return show_admin_page()

def show_admin_page():
    '''Show the admin page'''
    
    return render_template('admin_menu.html')

def show_admin_login_page(error = None):
    '''Show the admin login page'''
    
    return render_template('login.html', error = error)


@admin_blueprint.route('/admin/new', methods=['GET', 'POST'])
def intialize_bracket():
    '''Show/update 64 teams for bracket'''
    
    admin = Admin()
    
    if not admin.is_logged_in():
        return redirect(url_for('admin.admin_login'))

    # setup bracket
    if request.method == 'POST':
        if 'team_data' in request.values:
            return admin.initialize_new_bracket()
        elif 'game_dates' in request.values:
            return admin.setup_game_start_dates_for_display()
        elif 'pool_dates' in request.values:
            return admin.setup_pool_open_close_dates()

    # show the game/team form
    else:
        return render_template('blank_bracket.html')


@admin_blueprint.route('/admin/master')
def edit_admin_bracket():
    '''Show/update master bracket'''
    
    admin = Admin()
    
    if not admin.is_logged_in():
        return redirect(url_for('admin.admin_login'))

    token = admin.get_edit_token()

    url = request.url_root + f"bracket/full/{token}?action=e"  
    return redirect(url)

  
@admin_blueprint.route('/admin/pool', methods=['GET', 'POST'])
def add_pools():
    '''Add new pools'''

    admin = Admin()
    
    if not admin.is_logged_in():
        return redirect(url_for('admin.admin_login'))

    # add new pool
    if request.method == 'POST':
        return admin.add_new_pool()

    # show add pool form
    else:
        return render_template('add_pool.html')
    
    
@admin_blueprint.route('/admin/polls')
def reset_polls():
    '''Reset Top 25 polls data'''
    
    admin = Admin()
    admin.reset_and_pull_poll_data()
    
    # check for errors better
    flash('Poll data has been reset')
    return show_admin_page()

