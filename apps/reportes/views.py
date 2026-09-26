from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from apps.publicaciones.models import Publicacion
from apps.comentarios.models import Comentario
from apps.usuarios.permissions import IsStaffOrHasRole as IsStaffUser

User = get_user_model()


class DashboardView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        from datetime import timedelta
        from django.utils import timezone

        hace_30d = timezone.now() - timedelta(days=30)

        pub_by_estado = dict(
            Publicacion.objects.aggregate(
                total=Count('id'),
                borradores=Count('id', filter=Q(estado='BORRADOR')),
                en_revision=Count('id', filter=Q(estado='EN_REVISION')),
                publicadas=Count('id', filter=Q(estado='PUBLICADA')),
                archivadas=Count('id', filter=Q(estado='ARCHIVADA')),
                nuevas=Count('id', filter=Q(fechaCreacion__gte=hace_30d)),
            )
        )

        com_by_estado = dict(
            Comentario.objects.aggregate(
                total=Count('id'),
                pendientes=Count('id', filter=Q(estado='PENDIENTE')),
                aprobados=Count('id', filter=Q(estado='APROBADO')),
                rechazados=Count('id', filter=Q(estado='RECHAZADO')),
            )
        )

        total_usuarios = User.objects.count()

        mas_comentadas = (
            Publicacion.objects.annotate(num_comentarios=Count('comentarios'))
            .filter(num_comentarios__gt=0)
            .order_by('-num_comentarios')[:5]
            .values('id', 'titulo', 'num_comentarios')
        )

        recientes = (
            Publicacion.objects.select_related('usuario')
            .order_by('-fechaCreacion')[:5]
            .values('id', 'titulo', 'estado', 'fechaCreacion', 'usuario__username')
        )
        recientes = [
            {
                'id': r['id'],
                'titulo': r['titulo'],
                'estado': r['estado'],
                'fecha': r['fechaCreacion'],
                'autor': r['usuario__username'],
            }
            for r in recientes
        ]

        return Response({
            'publicaciones': pub_by_estado,
            'comentarios': com_by_estado,
            'usuarios': total_usuarios,
            'publicaciones_mas_comentadas': list(mas_comentadas),
            'publicaciones_recientes': recientes,
        })


# --- Reporte persistido (DER) ---

from rest_framework import viewsets
from .models import Reporte
from .serializers import ReporteSerializer


class ReporteViewSet(viewsets.ModelViewSet):
    queryset = Reporte.objects.select_related('creador').all()
    serializer_class = ReporteSerializer
    permission_classes = [IsStaffUser]

    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)
