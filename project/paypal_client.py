from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
import configparser
import sys

class PayPalClient:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("site.cfg")

        self.client_id = config.get('PAYPAL', 'CLIENT_ID')
        self.client_secret = config.get('PAYPAL', 'SECRET')

        """Set up and return PayPal Python SDK environment with PayPal access credentials.
           This sample uses SandboxEnvironment. In production, use LiveEnvironment."""
        if config.get('DEFAULT', 'ENVIRONMENT') == 'development':
            self.environment = SandboxEnvironment(client_id=self.client_id, client_secret=self.client_secret)
        else:
            self.environment = LiveEnvironment(client_id=self.client_id, client_secret=self.client_secret)

        """ Returns PayPal HTTP client instance with environment that has access
            credentials context. Use this instance to invoke PayPal APIs, provided the
            credentials have access. """
        self.client = PayPalHttpClient(self.environment)