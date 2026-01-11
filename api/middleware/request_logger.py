import logging

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware:
    """Middleware that logs incoming request path and querystring for debugging.

    Enabled only when Django DEBUG is True (checked in settings) before adding to MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            qs = request.META.get('QUERY_STRING', '')
            full = None
            try:
                full = request.get_full_path()
            except Exception:
                full = None
            # Print to stdout as well to ensure visibility in development console
            msg = f"Incoming request: method={request.method} path={request.path} full_path={full} query={qs}"
            print(msg)
            logger.info(msg)
        except Exception:
            logger.exception("Failed to log incoming request")

        response = self.get_response(request)
        return response
