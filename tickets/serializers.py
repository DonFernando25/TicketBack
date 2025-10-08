from rest_framework import serializers
from .models import (
    Rol, Empleado, Categoria, Ticket, Comentario,
    Adjunto, Reunion, Evaluacion, OrdenKanban
)
from django.contrib.auth.models import User


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = "__all__"


class EmpleadoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    rol = RolSerializer(read_only=True)

    class Meta:
        model = Empleado
        fields = "__all__"


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class ComentarioSerializer(serializers.ModelSerializer):
    autor = EmpleadoSerializer(read_only=True)

    class Meta:
        model = Comentario
        fields = "__all__"
        read_only_fields = ["autor", "creado_en"]


class EvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluacion
        fields = "__all__"
        read_only_fields = ["creado_en"]


class TicketSerializer(serializers.ModelSerializer):
    solicitante = EmpleadoSerializer(read_only=True)
    asignado_a = EmpleadoSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ["creado_en", "actualizado_en", "vence_en"]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Usado para creación rápida de ticket."""
    class Meta:
        model = Ticket
        fields = ["titulo", "descripcion", "categoria"]


class OrdenKanbanSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenKanban
        fields = "__all__"
