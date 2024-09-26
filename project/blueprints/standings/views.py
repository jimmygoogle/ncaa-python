from flask import Blueprint, request, render_template, url_for, flash, make_response, redirect, g
from flask_paginate import Pagination, get_page_parameter
from project.standings import Standings
from project.pool import Pool
import datetime

pool = Pool()
standings = Standings()
standings_blueprint = Blueprint('standings', __name__, template_folder='templates')

@standings_blueprint.route('/standings/<pool_type>')
def show_standings(pool_type):
    ''' Get the standings '''

    pool_name = pool.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))

    bracket_type = 'normal'
    if pool_type == 'sweetsixteen':
        bracket_type = 'sweetSixteen'

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = standings.users_per_page

    pppp = pool.check_pool_status(bracket_type + 'Bracket')
    pool_is_closed = 0
    if pppp['is_open'] == 0:
        pool_is_closed = 1

    ## get standings data and calculate scores
    (data, has_games_left) = standings.get_standings(
        bracket_type=bracket_type,
        page=page,
        per_page=per_page
    )
 
    # search = False
    # q = request.args.get('q')
    # if q:
    #     search = True
 
    pagination = Pagination(
        css_framework='bootstrap3',
        per_page=per_page,
        page=page,
        total=len(data),
        search=False,
        record_name='data',
        show_single_page=True
    )

    if page > 1:
        offset_start = (page - 1) * per_page
        offset_stop = page * per_page
    else:
        offset_start = 0
        offset_stop = per_page

    return render_template('standings.html',
        year=datetime.datetime.now().year,
        data=data[offset_start:offset_stop],
        has_games_left=has_games_left,
        pool_name=pool_name,
        pagination=pagination,
        per_page=per_page,
        pool_is_closed=pool_is_closed
    )
