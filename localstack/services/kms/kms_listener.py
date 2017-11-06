import logging
import base64
from six.moves.urllib import parse as urlparse
from localstack.utils.common import short_uid, to_str
from localstack.services.generic_proxy import ProxyListener
from requests.models import Response

# mappings for SNS topic subscriptions
SNS_SUBSCRIPTIONS = {}

# set up logger
LOGGER = logging.getLogger(__name__)


class ProxyListenerKMS(ProxyListener):

    def forward_request(self, method, path, data, headers):

        if method == 'POST' and path == '/':
            req_data = urlparse.parse_qs(to_str(data))
            req_action = req_data['Action'][0]

            if req_action == 'Encrypt':
                return make_response(req_action, content=encrypt(req_data))
            elif req_action == 'Decrypt':
                return make_response(req_action, content=decrypt(req_data))

        return True

    def return_response(self, method, path, data, headers, response):
        # This method is executed by the proxy after we've already received a
        # response from the backend, hence we can utilize the "reponse" variable here
        if method == 'POST' and path == '/':
            req_data = urlparse.parse_qs(to_str(data))
            req_action = req_data['Action'][0]
            print(req_action)


# instantiate listener
UPDATE_KMS = ProxyListenerKMS()


def encrypt(raw):
    return base64.b64encode(raw)


def decrypt(enc):
    return base64.b64decode(enc)


def make_response(op_name, content=''):
    response = Response()
    if not content:
        content = '<MessageId>%s</MessageId>' % short_uid()
    response._content = """<{op_name}Response xmlns="http://sns.amazonaws.com/doc/2010-03-31/">
        <{op_name}Result>
            {content}
        </{op_name}Result>
        <ResponseMetadata><RequestId>{req_id}</RequestId></ResponseMetadata>
        </{op_name}Response>""".format(op_name=op_name, content=content, req_id=short_uid())
    response.status_code = 200
    return response


def make_error(message, code=400, code_string='InvalidParameter'):
    response = Response()
    response._content = """<ErrorResponse xmlns="http://sns.amazonaws.com/doc/2010-03-31/"><Error>
        <Type>Sender</Type>
        <Code>{code_string}</Code>
        <Message>{message}</Message>
        </Error><RequestId>{req_id}</RequestId>
        </ErrorResponse>""".format(message=message, code_string=code_string, req_id=short_uid())
    response.status_code = code
    return response
