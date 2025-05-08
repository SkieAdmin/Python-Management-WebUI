class CsrfExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Mark the request as exempt from CSRF protection
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response
