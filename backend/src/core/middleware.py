import logging
from rest_framework.authentication import TokenAuthentication

logger = logging.getLogger('request_logger')

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.token_auth = TokenAuthentication()

    def __call__(self, request):
        user_auth_tuple = self.token_auth.authenticate(request)
        if user_auth_tuple is not None:
            request.user, _ = user_auth_tuple

        response = self.get_response(request)

        user = (
            request.user.username
            if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated
            else 'anonymous'
        )

        ip = self.get_client_ip(request)

        logger.info('', extra={
            'user': user,
            'ip': ip,
            'path': request.path,
            'status': response.status_code
        })

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')