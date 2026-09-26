from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Perfil, Rol

User = get_user_model()


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion', 'fechaCreacion']
        read_only_fields = ['id', 'fechaCreacion']


class UsuarioActualSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'is_active', 'date_joined',
            'roles', 'permisos',
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return list(obj.roles_rel.values_list('rol__nombre', flat=True))

    def get_permisos(self, obj):
        return list(
            obj.roles_rel.values_list('rol__permisos_rel__permiso__codename', flat=True).distinct()
        )


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    nombre_completo = serializers.CharField(max_length=35, required=False, allow_blank=True, default='')
    tipo_afiliacion = serializers.ChoiceField(
        choices=Perfil.TipoAfiliacion.choices,
        required=False,
        default=Perfil.TipoAfiliacion.COMUNIDAD,
    )
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True, default='')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('El nombre de usuario ya esta en uso.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('El correo ya esta registrado.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Las contrasenas no coinciden.'})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        nombre = validated_data.pop('nombre_completo', '').strip()
        tipo = validated_data.pop('tipo_afiliacion', Perfil.TipoAfiliacion.COMUNIDAD)
        telefono = validated_data.pop('telefono', '')
        first_name, _, last_name = nombre.partition(' ')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name[:150],
            last_name=last_name[:150],
        )
        Perfil.objects.create(
            usuario=user,
            tipo_afiliacion=tipo,
            telefono=telefono,
        )
        return user


class UsuarioAdminSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'is_active', 'date_joined', 'last_login',
            'roles',
        ]
        read_only_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_superuser', 'date_joined', 'last_login', 'roles',
        ]

    def get_roles(self, obj):
        return list(obj.roles_rel.values_list('rol__nombre', flat=True))