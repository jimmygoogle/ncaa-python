from flask import Blueprint, request, render_template, url_for, redirect
from project.pool import Pool
from project.polls import Polls
import datetime

pool = Pool()
polls = Polls()
polls_blueprint = Blueprint('polls', __name__, template_folder='templates')

@polls_blueprint.route('/polls')
def index():
    '''Show Top 25 polls'''

    pool_name = pool.get_pool_name()

    if pool_name is None:
        return redirect(url_for('pool.show_pool_form'))
    else:
        # render the polls
        return render_template('polls.html',
            pool_name = pool_name,
            year = datetime.datetime.now().year,
            ap_rankings = polls.get_ap_poll_data(),
            usa_today_rankings = polls.get_usa_today_poll_data()
        )

