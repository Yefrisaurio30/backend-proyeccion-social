from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SolicitudViewSet, PublicSolicitudCreateView

router = DefaultRouter()
router.register(r'solicitudes', SolicitudViewSet, basename='solicitud')

urlpatterns = [
    path('solicitudes/nueva/', PublicSolicitudCreateView.as_view(), name='solicitud-create'),
    path('', include(router.urls)),
]