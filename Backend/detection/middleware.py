from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()

    def __call__(self, request):
        secure_paths = [
            # "/api/auth/upload",
            "/api/auth/history"
        ]
        if any(request.path.startswith(p) for p in secure_paths):
            try:
                user_auth_tuple = self.jwt_authenticator.authenticate(request)
                if user_auth_tuple is not None:
                    request.user, request.auth = user_auth_tuple
                else:
                    return JsonResponse({"error": "Authentication credentials were not provided."}, status=401)
            except (InvalidToken, AuthenticationFailed) as e:
                return JsonResponse({"error": str(e)}, status=401)

        return self.get_response(request)
