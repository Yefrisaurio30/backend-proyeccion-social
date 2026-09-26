from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PublicacionViewSet, PublicacionPublicViewSet, CategoriaViewSet

router = DefaultRouter()
router.register(r'publicaciones', PublicacionViewSet, basename='publicacion')
router.register(r'publicas', PublicacionPublicViewSet, basename='publicacion-publica')
router.register(r'categorias', CategoriaViewSet, basename='categoria')

urlpatterns = [
    path('', include(router.urls)),
]
