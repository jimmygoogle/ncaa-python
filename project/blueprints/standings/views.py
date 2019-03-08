from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect, g
from project.standings import Standings
from project.pool import Pool
import datetime

pool = Pool()
standings = Standings()
standings_blueprint = Blueprint('standings', __name__, template_folder='templates')

@standings_blueprint.route('/standings/<pool_type>')
def show_standings(pool_type):
    
    pool_name = pool.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))

    bracket_type = 'normal'
    if pool_type == 'sweetsixteen':
        bracket_type = 'sweetSixteen'
    
    ## get standings data and calculate scores
    (data, has_games_left) = standings.get_standings(bracket_type=bracket_type)

    return render_template('standings.html',
        year = datetime.datetime.now().year,
        data = data, 
        has_games_left = has_games_left,
        pool_name = pool_name,
    )
