from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)  # Email ile kullanıcıyı bul
            if user.check_password(password):  # Şifreyi doğrula
                return user
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        
from django.conf import settings
from django.utils.timezone import now
from rest_framework_simplejwt.tokens import RefreshToken

class JWTCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # AUTH_COOKIE'yi settings'ten al
        self.auth_cookie_name = getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE', 'access_token')

    def __call__(self, request):
        # Çerezlerden access token'ı al ve Authorization header'a ekle
        access_token = request.COOKIES.get(self.auth_cookie_name)
        if access_token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        response = self.get_response(request)

        # Kullanıcı anonimse yeni token üretme
        if request.user is None or not request.user.is_authenticated:
            return response

        # Eğer kullanıcının oturumu açıksa yeni token oluştur
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)

        # Access token'ı çereze yaz
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value=access_token,
            expires=now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure=True,  # HTTPS için True olmalı
            httponly=True,  # JS erişemesin
            samesite="None"
        )

        # Refresh token'ı çereze yaz
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            expires=now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
            secure=True,
            httponly=True,
            samesite="None"
        )

        return response

