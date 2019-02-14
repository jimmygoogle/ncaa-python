from flask import request, render_template, jsonify, g
from project import session
from project.ncaa_class import Ncaa
from project.pool_class import Pool
from project.user_class import User
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import datetime

class Email(Ncaa):
    
    def __init__(self):
        self.__pool = Pool()
        self.__user = User()
        
    def send_confirmation_email(self, **kwargs):
        '''Send the user a confirmation email with a link to edit their picks'''
        
        config = configparser.ConfigParser()
        config.read("site.cfg")

        sender_email = config.get('EMAIL', 'MAIL_USER')
        receiver_email = request.values['email_address']
        password = config.get('EMAIL', 'MAIL_PASS')
        
        message = MIMEMultipart("alternative")

        year = datetime.datetime.now().year
        pool_name = self.__pool.get_pool_name().upper()

        message["Subject"] = '\U0001F3C0' + f" Welcome to the {str(year)} {pool_name} March Madness Pool"
        message["From"] = config.get('EMAIL', 'MAIL_FROM')
        message["To"] = receiver_email

        content = MIMEText(self.get_email_confirmation_template(year = year, config = config, pool_name = pool_name, user_edit_token = kwargs['token']), 'html')
        message.attach(content)
        
        # create gmail connection and send
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )

        return 1
    
    def get_email_confirmation_template(self, **kwargs):
        '''Build email template for confirmation email'''

        config = kwargs['config']
        year = kwargs['year']
        pool_name = kwargs['pool_name']
        token = kwargs['user_edit_token']

        pool_status = self.__pool.check_pool_status()
        bracket_type_name = request.values['bracket_type_name']

        return render_template('email.html',
            pool_name = pool_name,
            year = year,
            username = request.values['username'],
            email = config.get('EMAIL', 'INFO_EMAIL'),
            closing_date_time = pool_status[bracket_type_name]['closing_date_time'],
            edit_url = request.url_root + 'bracket/' + token + '?action=e'
        )

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
