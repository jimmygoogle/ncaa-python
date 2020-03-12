from flask import request, render_template, current_app
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import datetime
from . import celery
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

@celery.task()
def send_confirmation_email(**kwargs):
    '''Send the user a confirmation email with a link to edit their picks'''

    with current_app.app_context():
        config = configparser.ConfigParser()
        config.read("site.cfg")

        pool_name = kwargs['pool_name'].upper()
        year = datetime.datetime.now().year

        content= get_email_confirmation_template(
            year = year,
            info_email = config.get('EMAIL', 'INFO_EMAIL'),
            pool_name = pool_name,
            user_edit_token = kwargs['token'],
            username = kwargs['username'],
            pool_status = kwargs['pool_status'],
            bracket_type_name = kwargs['bracket_type_name'],
            bracket_type_label = kwargs['bracket_type_label'],
            url = kwargs['url']
        )

        message = Mail(
            from_email = config.get('EMAIL', 'MAIL_FROM'),
            to_emails = kwargs['email_address'],
            subject = '\U0001F3C0' + f" Welcome to the {str(year)} {pool_name} March Madness Pool",
            html_content = content
        )
        try:
            # send email through sendgrid
            sg = SendGridAPIClient(config.get('EMAIL', 'SEND_API_KEY'))
            response = sg.send(message)
        except Exception as e:
            print(e.message)

def get_email_confirmation_template(**kwargs):
    '''Build email template for confirmation email'''

    pool_status = kwargs['pool_status']
    bracket_type_name = kwargs['bracket_type_name']
    bracket_type_label = kwargs['bracket_type_label']
    edit_token = kwargs['user_edit_token']
    url = kwargs['url']

    return render_template('email.html',
        pool_name = kwargs['pool_name'],
        year = kwargs['year'],
        username = kwargs['username'],
        email = kwargs['info_email'],
        closing_date_time = pool_status[bracket_type_name]['closing_date_time'],
        edit_url = f"{url}bracket/{bracket_type_label}/{edit_token}?action=e"
    )
