from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import UserModelViewSet, RegisterView_

user_router = DefaultRouter()
user_router.register(r'users', viewset=UserModelViewSet, basename='Users')

urlpatterns = [
    path('api/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/jwt/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path(r'^', include('django.contrib.auth.urls')),

    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', RegisterView_.as_view(), name='register')
]

users_urlpatterns = [*user_router.urls, *urlpatterns]
