from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from apps.actividad.models import RegistroActividad
from .models import Rol
from .serializers import (
    UsuarioActualSerializer,
    RegistroSerializer,
    UsuarioAdminSerializer,
    RolSerializer,
)

User = get_user_model()


from .permissions import IsStaffOrHasRole as IsStaffOnly


class IsAdminUser(IsStaffOnly):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_superuser
            and obj.pk != request.user.pk
            and not obj.is_superuser
        )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('username', request.data.get('email', '')).strip()
        password = request.data.get('password', '')
        remember = request.data.get('remember', True)
        if not identifier or not password:
            return Response(
                {'detail': 'Correo (o usuario) y contrasena son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username = identifier
        if '@' in identifier:
            try:
                username = User.objects.get(email__iexact=identifier).username
            except User.DoesNotExist:
                username = identifier
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Credenciales invalidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'detail': 'La cuenta esta desactivada. Contacte al administrador.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        if remember in (False, 'false', 'False', 0, '0', ''):
            request.session.set_expiry(0)
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.LOGIN,
            descripcion=f'{user.username} inicio sesion',
            usuario=user,
        )
        return Response(UsuarioActualSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.LOGOUT,
            descripcion=f'{request.user.username} cerro sesion',
            usuario=request.user,
        )
        logout(request)
        return Response({'detail': 'Sesion cerrada.'})


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UsuarioActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioActualSerializer(request.user).data)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'detail': 'Cuenta creada correctamente. Inicie sesion.', 'id': user.pk},
            status=status.HTTP_201_CREATED,
        )


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UsuarioAdminSerializer
    permission_classes = [IsStaffOnly]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['is_staff', 'is_active']
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsStaffOnly()]
        return [IsStaffOnly()]

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        is_staff = self.request.query_params.get('is_staff')
        if is_staff in ('true', 'false'):
            qs = qs.filter(is_staff=is_staff == 'true')
        is_active = self.request.query_params.get('is_active')
        if is_active in ('true', 'false'):
            qs = qs.filter(is_active=is_active == 'true')
        return qs

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {'detail': 'No puede eliminar su propia cuenta desde aqui.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser:
            return Response(
                {'detail': 'No puede eliminar a otro superusuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        username = user.username
        user.delete()
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.ELIMINAR,
            descripcion=f'Se elimino el usuario "{username}"',
            modelo='User',
            usuario=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk and 'is_active' in request.data and request.data['is_active'] is False:
            return Response(
                {'detail': 'No puede desactivar su propia cuenta desde aqui.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Compat DER: aceptar roles: ["Admin", ...] además de is_staff
        roles = request.data.get('roles')
        if isinstance(roles, list):
            from .models import Rol, UsuarioRol
            UsuarioRol.objects.filter(usuario=user).exclude(rol__nombre__in=roles).delete()
            for nombre in roles:
                rol, _ = Rol.objects.get_or_create(nombre=nombre, defaults={'descripcion': nombre})
                UsuarioRol.objects.get_or_create(usuario=user, rol=rol, defaults={'asignado_por': request.user})
            # sincroniza is_staff via señal
        return super().partial_update(request, *args, **kwargs)


class RolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsStaffOnly]
    pagination_class = None


class AsignarRolView(APIView):
    permission_classes = [IsStaffOnly]

    def post(self, request):
        from .models import Rol, UsuarioRol
        usuario_id = request.data.get('usuario')
        rol_nombre = request.data.get('rol')
        if not usuario_id or not rol_nombre:
            return Response({'detail': 'usuario y rol son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            usuario = User.objects.get(pk=usuario_id)
        except User.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        rol, _ = Rol.objects.get_or_create(nombre=rol_nombre, defaults={'descripcion': rol_nombre})
        _, created = UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol, defaults={'asignado_por': request.user})
        return Response({'detail': 'Rol asignado.' if created else 'Ya tenía el rol.', 'rol': rol.nombre})

    def delete(self, request):
        from .models import UsuarioRol
        usuario_id = request.data.get('usuario')
        rol_nombre = request.data.get('rol')
        UsuarioRol.objects.filter(usuario_id=usuario_id, rol__nombre=rol_nombre).delete()
        return Response({'detail': 'Rol retirado.'})