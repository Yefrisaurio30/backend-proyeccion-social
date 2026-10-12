from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.db.models import Q
from apps.actividad.models import RegistroActividad
from .models import Rol
from .serializers import (
    UsuarioActualSerializer,
    RegistroSerializer,
    UsuarioAdminSerializer,
    RolSerializer,
)
from .permissions import IsStaffOrHasRole as IsStaffOnly
from .permissions import SoloSuperadmin, es_superadmin

User = get_user_model()


class IsAdminUser(IsStaffOnly):
    def has_object_permission(self, request, view, obj):
        if not es_superadmin(request.user):
            return False
        if obj.pk == request.user.pk:
            return False
        # Solo un superusuario puede actuar sobre otro superusuario.
        if obj.is_superuser and not request.user.is_superuser:
            return False
        return True


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        identifier = request.data.get('username', request.data.get('email', '')).strip()
        password = request.data.get('password', '')
        remember = request.data.get('remember', True)
        if not identifier or not password:
            return Response(
                {'detail': 'Correo (o usuario) y contraseña son requeridos.'},
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
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'detail': 'La cuenta está desactivada. Contacte al administrador.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        if remember in (False, 'false', 'False', 0, '0', ''):
            request.session.set_expiry(0)
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.LOGIN,
            descripcion=f'{user.username} inició sesión',
            usuario=user,
        )
        return Response(UsuarioActualSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.LOGOUT,
            descripcion=f'{request.user.username} cerró sesión',
            usuario=request.user,
        )
        logout(request)
        return Response({'detail': 'Sesión cerrada.'})


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
            {'detail': 'Cuenta creada correctamente. Inicie sesión.', 'id': user.pk},
            status=status.HTTP_201_CREATED,
        )


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UsuarioAdminSerializer
    permission_classes = [IsStaffOnly]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['is_staff', 'is_active']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsStaffOnly()]
        return [SoloSuperadmin()]

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
        if (
            not request.user.is_superuser
            and user.roles_rel.filter(rol__nombre='Superadmin').exists()
        ):
            return Response(
                {'detail': 'Solo un superusuario puede eliminar a un Superadmin.'},
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
        if user.pk == request.user.pk:
            return Response(
                {'detail': 'No puede modificar su propia cuenta desde aqui.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {'detail': 'Solo un superusuario puede modificar a otro superusuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Compat DER: aceptar roles: ["Admin", ...] además de is_staff.
        # Solo roles existentes: no se crean al vuelo (S1).
        roles = request.data.get('roles')
        if isinstance(roles, list):
            from .models import Rol, UsuarioRol
            existentes = list(Rol.objects.filter(nombre__in=roles))
            if len(existentes) != len(set(roles)):
                return Response(
                    {'detail': 'Rol inexistente.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            UsuarioRol.objects.filter(usuario=user).exclude(rol__nombre__in=roles).delete()
            for rol in existentes:
                UsuarioRol.objects.get_or_create(usuario=user, rol=rol, defaults={'asignado_por': request.user})
            # sincroniza is_staff via señal
        return super().partial_update(request, *args, **kwargs)


class RolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsStaffOnly]


class AsignarRolView(APIView):
    permission_classes = [SoloSuperadmin]

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
        if usuario.pk == request.user.pk:
            return Response(
                {'detail': 'No puede modificar sus propios roles desde aqui.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if usuario.is_superuser and not request.user.is_superuser:
            return Response(
                {'detail': 'Solo un superusuario puede modificar a otro superusuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Solo roles existentes: no se crean al vuelo (S1).
        rol = Rol.objects.filter(nombre=rol_nombre).first()
        if rol is None:
            return Response({'detail': 'Rol inexistente.'}, status=status.HTTP_400_BAD_REQUEST)
        _, created = UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol, defaults={'asignado_por': request.user})
        return Response({'detail': 'Rol asignado.' if created else 'Ya tenía el rol.', 'rol': rol.nombre})

    def delete(self, request):
        from .models import UsuarioRol
        usuario_id = request.data.get('usuario')
        rol_nombre = request.data.get('rol')
        if usuario_id is not None and int(usuario_id) == request.user.pk:
            return Response(
                {'detail': 'No puede modificar sus propios roles desde aqui.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        UsuarioRol.objects.filter(usuario_id=usuario_id, rol__nombre=rol_nombre).delete()
        return Response({'detail': 'Rol retirado.'})