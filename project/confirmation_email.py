from flask import request, render_template, current_app
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import datetime
import os
import boto3
from . import celery

@celery.task()
def send_confirmation_email(**kwargs):
    '''Send the user a confirmation email with a link to edit their picks'''

    with current_app.app_context():
        pool_name = kwargs['pool_name'].upper()
        year = datetime.datetime.now().year

        config = configparser.ConfigParser()
        config.read("site.cfg")

        content = get_email_confirmation_template(
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

        send_email(
            config = config,
            content = content,
            email_address = kwargs['email_address'],
            subject = '\U0001F3C0' + f" Welcome to the {str(year)} {pool_name} March Madness Pool",
            from_email_address = config.get('EMAIL', 'MAIL_FROM')
        )

@celery.task()
def send_contact_us_email(**kwargs):
    '''Send contact request email to admin'''

    with current_app.app_context():
        config = configparser.ConfigParser()
        config.read("site.cfg")

        send_email(
            config = config,
            content = kwargs['message'],
            email_address = config.get('EMAIL', 'INFO_EMAIL'),
            subject = 'Contact request',
            from_email_address = kwargs['email_address']
        )

def send_email(**kwargs):
        try:
            config = kwargs['config']
            charset = 'UTF-8'

            ses_client = boto3.client(
                'ses',
                aws_access_key_id = config.get('AWS', 'ACCESS_KEY'),
                aws_secret_access_key = config.get('AWS', 'SECRET_KEY'),
                region_name = 'us-east-1'
            )

            ses_client.send_email(
                Destination={
                    "ToAddresses": [
                        kwargs['email_address']
                    ],
                },
                Message={
                    "Body": {
                        "Html": {
                            "Charset": charset,
                            "Data": kwargs['content'],
                        }
                    },
                    "Subject": {
                        "Charset": charset,
                        "Data": kwargs['subject'],
                    },
                },
                Source=kwargs['from_email_address'],
            )
        except Exception as e:
            print(e)

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

