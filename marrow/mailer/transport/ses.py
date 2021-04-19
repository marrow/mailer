# encoding: utf-8

try:
    import boto3
    from botocore.exceptions import ClientError

except ImportError:
    raise ImportError("You must install the boto package to deliver mail via Amazon SES.")


__all__ = ['AmazonTransport']

log = __import__('logging').getLogger(__name__)


class AmazonTransport(object):  # pragma: no cover
    __slots__ = ('ephemeral', 'config', 'region', 'connection')

    def __init__(self, config):
        # Give our configuration aliases their proper names.
        config['aws_access_key_id'] = config.pop('id')
        config['aws_secret_access_key'] = config.pop('key')

        self.region = config.pop('region', "us-east-1")
        # boto throws an error if we leave this in the next line
        config.pop('use')
        config.pop('debug')
        # All other configuration directives are passed to connect_to_region.
        self.config = config
        self.connection = None

    def startup(self):
        self.connection = boto3.client('ses', region_name=self.region, **self.config)

    def deliver(self, message):
        try:
            destinations = [str(r) for r in message.recipients]
            response = self.connection.send_raw_email(
                RawMessage = {'Data': str(message)},
                Source = str(message.author),
                Destinations = destinations,
            )

            return (
                response.get('MessageId', 'messageId NOT FOUND'),
                response.get('RequestId', {}).get('ResponseMetadata')
            )

        except ClientError as e:
            raise  # TODO: Raise appropriate internal exception.
            # ['status', 'reason', 'body', 'request_id', 'error_code', 'error_message']

    def shutdown(self):
        # if self.connection:
        #     self.connection.close()

        self.connection = None
