import django_filters
from .models import Publicacion


class PublicacionFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='Busqueda por texto',
    )
    programa = django_filters.CharFilter(field_name='programa_nombre', lookup_expr='icontains', label='Programa')
    fecha_desde = django_filters.DateFilter(
        field_name='fechaPublicacion',
        lookup_expr='gte',
        label='Fecha publicacion desde',
    )
    fecha_hasta = django_filters.DateFilter(
        field_name='fechaPublicacion',
        lookup_expr='lte',
        label='Fecha publicacion hasta',
    )

    class Meta:
        model = Publicacion
        fields = {
            'estado': ['exact'],
            'categoria': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        if not value:
            return queryset
        query = (
            Q(titulo__icontains=value)
            | Q(resumen__icontains=value)
            | Q(contenido__icontains=value)
            | Q(programa_nombre__icontains=value)
            | Q(programa_codigo__icontains=value)
            | Q(coordinador_nombre__icontains=value)
        )
        return queryset.filter(query)


class PublicacionPublicFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='Busqueda por texto',
    )

    class Meta:
        model = Publicacion
        fields = {
            'categoria': ['exact'],
            'estado': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        if not value:
            return queryset
        return queryset.filter(
            Q(titulo__icontains=value)
            | Q(resumen__icontains=value)
            | Q(contenido__icontains=value)
        )
