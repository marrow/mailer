# encoding: utf-8

# TODO: Port: https://github.com/pankratiev/python-amazon-ses-api/blob/master/amazon_ses.py

try:
    from boto.ses import SESConnection

except ImportError:
    raise ImportError("You must install the boto package to deliver mail via Amazon SES.")


__all__ = ['AmazonTransport']

log = __import__('logging').getLogger(__name__)



class AmazonTransport(object): # pragma: no cover
    __slots__ = ('ephemeral', 'id', 'key', 'host', 'connection')
    
    def __init__(self, config):
        self.id = config.get('id')
        self.key = config.get('key')
        self.host = config.get('host', "email.us-east-1.amazonaws.com")
        self.connection = None
    
    def startup(self):
        self.connection = SESConnection(
                aws_access_key_id = self.id,
                aws_secret_access_key = self.key,
                host = self.host
            )
    
    def deliver(self, message):
        try:
            response = self.connection.send_raw_email(
                    source = message.author.encode(),
                    destinations = message.recipients.encode(),
                    raw_message = str(message)
                )
            
            return (
                    response['SendRawEmailResponse']['SendRawEmailResult']['MessageId'],
                    response['SendRawEmailResponse']['ResponseMetadata']['RequestId']
                )
        
        except SESConnection.ResponseError:
            raise # TODO: Raise appropriate internal exception.
            # ['status', 'reason', 'body', 'request_id', 'error_code', 'error_message']
    
    def shutdown(self):
        if self.connection:
            self.connection.close()
        
        self.connection = None
