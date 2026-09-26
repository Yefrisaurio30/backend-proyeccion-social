from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    LogoutView,
    UsuarioActualView,
    RegistroView,
    UsuarioViewSet,
    RolViewSet,
    AsignarRolView,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'roles', RolViewSet, basename='rol')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/register/', RegistroView.as_view(), name='auth-register'),
    path('auth/user/', UsuarioActualView.as_view(), name='auth-user'),
    path('roles/asignar/', AsignarRolView.as_view(), name='rol-asignar'),
    path('', include(router.urls)),
]