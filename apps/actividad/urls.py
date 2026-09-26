from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegistroActividadViewSet

router = DefaultRouter()
router.register(r'registros', RegistroActividadViewSet, basename='registro-actividad')

urlpatterns = [
    path('', include(router.urls)),
]
