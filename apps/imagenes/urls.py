from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImagenViewSet

router = DefaultRouter()
router.register(r'imagenes', ImagenViewSet, basename='imagen')

urlpatterns = [
    path('', include(router.urls)),
]
