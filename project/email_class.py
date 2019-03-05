from flask import request, render_template, current_app
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import datetime
from . import celery

@celery.task()
def send_confirmation_email(**kwargs):
    '''Send the user a confirmation email with a link to edit their picks'''

    with current_app.app_context():
        config = configparser.ConfigParser()
        config.read("site.cfg")

        sender_email = config.get('EMAIL', 'MAIL_USER')
        password = config.get('EMAIL', 'MAIL_PASS')
        
        message = MIMEMultipart("alternative")

        pool_name = kwargs['pool_name'].upper()
        year = datetime.datetime.now().year
        receiver_email = kwargs['email_address']

        message["Subject"] = '\U0001F3C0' + f" Welcome to the {str(year)} {pool_name} March Madness Pool"
        message["From"] = config.get('EMAIL', 'MAIL_FROM')
        message["To"] = receiver_email

        # generate template
        content = MIMEText(get_email_confirmation_template(
            year = year,
            info_email = config.get('EMAIL', 'INFO_EMAIL'),
            pool_name = pool_name,
            user_edit_token = kwargs['token'],
            username = kwargs['username'],
            pool_status = kwargs['pool_status'],
            bracket_type_name = kwargs['bracket_type_name'],
            url = kwargs['url']
        ), 'html')
        message.attach(content)
        
        # create gmail connection and send
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )

def get_email_confirmation_template(**kwargs):
    '''Build email template for confirmation email'''

    pool_status = kwargs['pool_status']
    bracket_type_name = kwargs['bracket_type_name']

    return render_template('email.html',
        pool_name = kwargs['pool_name'],
        year = kwargs['year'],
        username = kwargs['username'],
        email = kwargs['info_email'],
        closing_date_time = pool_status[bracket_type_name]['closing_date_time'],
        edit_url = kwargs['url'] + 'bracket/' + kwargs['user_edit_token'] + '?action=e'
    )
