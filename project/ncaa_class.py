from project.mysql_python import MysqlPython
from flask import request, render_template, jsonify
from project import session, app, YEAR
#from collections import defaultdict
import sys
import hashlib
import time
#import re
import ast
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Ncaa(object):
    
    def __init__(self):
        self.db = MysqlPython()
        
    def send_confirmation_email(self, **kwargs):
        '''Send the user a confirmation email with a link to edit their picks'''

        sender_email = app.config['MAIL_USER']
        receiver_email = "jim@jimandmeg.com"
        #request.values['email_address']
        password = app.config['MAIL_PASS']
        
        message = MIMEMultipart("alternative")

        message["Subject"] = '\U0001F3C0' + f" Welcome to the {str(YEAR)} {self.get_pool_name().upper()} March Madness Pool"
        message["From"] = app.config['MAIL_FROM']
        message["To"] = receiver_email

        content = MIMEText(self.get_email_template(), 'html')
        message.attach(content)
        
        # create gmail connection and send
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )

        return 1
    
    def get_email_template(self):
        '''Build email template'''

        pool_status = self.check_pool_status()
        bracket_type_name = request.values['bracket_type_name']

        return render_template('email.html',
            pool_name = self.get_pool_name().upper(),
            year = YEAR,
            username = request.values['username'],
            email = app.config['ERROR_EMAIL'],
            closing_date_time = pool_status[bracket_type_name]['closing_date_time'],
            edit_url = request.url_root + 'bracket/' + self.user_edit_token + '?action=e'
        )

    def debug(self, *args, **kwargs):
        '''Helper method to print to console'''

        print(*args, file=sys.stderr, **kwargs)
