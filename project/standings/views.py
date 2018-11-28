from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect
from project.ncaa import Ncaa
from project import YEAR

ncaa = Ncaa()
standings_blueprint = Blueprint('standings', __name__, template_folder='templates')

@standings_blueprint.route('/standings/<string:sweet_sixteen>/')
@standings_blueprint.route('/standings/')
def show_standings(sweet_sixteen=None):
    
    pool_name = ncaa.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))

    bracket_type = 'normal'
    if sweet_sixteen:
        bracket_type = 'sweetSixteen'
    
    ## get standings data and calculate scores
    (data, has_games_left) = ncaa.get_standings(bracket_type=bracket_type)
    
    ncaa.debug(f"we have games left? {has_games_left}")
    
    return render_template('standings.html',
        year = YEAR,
        data = data, 
        has_games_left = has_games_left
    )
