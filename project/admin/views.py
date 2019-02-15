from flask import Blueprint, request, render_template, redirect
from project.ncaa_class import Ncaa
from project.admin_class import Admin
from project.bracket_class import Bracket

admin = Admin()
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')

@admin_blueprint.route('/admin/new', methods=['GET', 'POST'])
def intialize_bracket():
    
    '''Show/update 64 teams for bracket'''
    
    # setup bracket
    if request.method == 'POST':
        admin = Admin()
        
        if 'team_data' in request.values:
            return admin.initialize_new_bracket()
        else:
            return admin.setup__start_dates_for_display()

    # show the game/team form
    else:
        return render_template('blank_bracket.html')


@admin_blueprint.route('/admin/master')
def edit_admin_bracket():
    
    '''Show/update master bracket'''
    
    admin = Admin()
    token = admin.get_edit_token()

    url = request.url_root + f"bracket/{token}?action=e"  
    return redirect(url)