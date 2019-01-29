from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa_class import Ncaa

#ncaa = Ncaa()
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')

@admin_blueprint.route('/admin')
def admin():
    if 1 == 1:
        
        #req.params.userToken = process.env.ADMIN_TOKEN;
        return 'show admin page' 
        ##url_for('show_pool_form')
    else:
        return 'show something'
    