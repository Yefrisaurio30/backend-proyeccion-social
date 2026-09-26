from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComentarioViewSet

router = DefaultRouter()
router.register(r'comentarios', ComentarioViewSet, basename='comentario')

urlpatterns = [
    path('', include(router.urls)),
]
