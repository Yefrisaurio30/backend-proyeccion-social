from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardView, ReporteViewSet

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')

urlpatterns = [
    path('reportes/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]
