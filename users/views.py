import allauth
from allauth.account.utils import complete_signup
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from rest_auth.app_settings import create_token
from rest_auth.models import TokenModel
from rest_auth.registration.app_settings import register_permission_classes
from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.registration.views import RegisterView
from rest_auth.serializers import JWTSerializer, TokenSerializer
from rest_auth.utils import import_callable
from rest_framework import viewsets, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from django.conf import  settings
from users.models import CustomUser
from users.serializers import UserSerializer, JWTSerializerCustom


# Create your views here.
class UserModelViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        data['password'] = make_password(data['password'])
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RegisterView_(RegisterView):
    serializer_class = RegisterSerializer
    permission_classes = register_permission_classes()
    token_model = TokenModel


    def get_response_data(self, user):
        if allauth.account.app_settings.EMAIL_VERIFICATION == \
                allauth.account.app_settings.EmailVerificationMethod.MANDATORY:
            return {'detail': _('Verification e-mail sent.')}

        if getattr(settings, 'REST_USE_JWT', False):
            data = {
                'user': user,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
            }
            return JWTSerializerCustom(data, context=self.get_serializer_context()).data
        elif getattr(settings, 'REST_SESSION_LOGIN', False):
            return None
        else:
            return TokenSerializer(user.auth_token, context=self.get_serializer_context()).data


    def perform_create(self, serializer):
        user = serializer.save(self.request)
        if allauth.account.app_settings.EMAIL_VERIFICATION != \
                allauth.account.app_settings.EmailVerificationMethod.MANDATORY:
            if getattr(settings, 'REST_USE_JWT', False):
                self.access_token, self.refresh_token = jwt_encode(user)
            elif not getattr(settings, 'REST_SESSION_LOGIN', False):
                # Session authentication isn't active either, so this has to be
                #  token authentication
                create_token(self.token_model, user, serializer)

        complete_signup(
            self.request._request, user,
            allauth.account.app_settings.EMAIL_VERIFICATION,
            None,
        )
        return user

def jwt_encode(user):
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
    rest_auth_serializers = getattr(settings, 'REST_AUTH_SERIALIZERS', {})

    JWTTokenClaimsSerializer = rest_auth_serializers.get(
        'JWT_TOKEN_CLAIMS_SERIALIZER',
        TokenObtainPairSerializer,
    )

    TOPS = import_callable(JWTTokenClaimsSerializer)
    refresh = TOPS.get_token(user)
    return refresh.access_token, refresh