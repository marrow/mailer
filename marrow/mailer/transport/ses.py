# encoding: utf-8

try:
    import boto.ses 
    from boto.ses import SESConnection

except ImportError:
    raise ImportError("You must install the boto package to deliver mail via Amazon SES.")


__all__ = ['AmazonTransport']

log = __import__('logging').getLogger(__name__)



class AmazonTransport(object): # pragma: no cover
    __slots__ = ('ephemeral', 'config', 'region', 'connection')
    
    def __init__(self, config):
        # Give our configuration aliases their proper names.
        config['aws_access_key_id'] = config.pop('id')
        config['aws_secret_access_key'] = config.pop('key')
        
        self.region = config.pop('region', "us-east-1")
        config.pop('use') #boto throws an error if we leave this in the next line
        self.config = config  # All other configuration directives are passed to connect_to_region.
        self.connection = None
    
    def startup(self):
        self.connection = boto.ses.connect_to_region(self.region, **self.config)
    
    def deliver(self, message):
        try:
            destinations = [r.encode(encoding='utf-8') for r in message.recipients]
            response = self.connection.send_raw_email(str(message), message.author.encode(), destinations)
            
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
