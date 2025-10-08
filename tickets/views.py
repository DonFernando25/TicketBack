from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timezone
from .models import (
    Rol, Empleado, Categoria, Ticket, Comentario, Evaluacion, OrdenKanban
)
from .serializers import (
    RolSerializer, EmpleadoSerializer, CategoriaSerializer, TicketSerializer,
    TicketCreateSerializer, ComentarioSerializer, EvaluacionSerializer, OrdenKanbanSerializer
)
from .priority import heuristic_priority, calcular_vencimiento


# -------- PERMISOS ---------
class EsPropietarioOTI(permissions.BasePermission):
    """
    Permite acceso a:
      - Empleado: solo sus tickets
      - TI y Admin: todos
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "empleado"):
            emp = request.user.empleado
            if emp.rol.nombre.lower() == "ti":
                return True
            return obj.solicitante == emp
        return False


# -------- VISTAS PRINCIPALES ---------

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [permissions.IsAdminUser]


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().select_related("solicitante", "asignado_a", "categoria")
    permission_classes = [permissions.IsAuthenticated, EsPropietarioOTI]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["estado", "categoria", "asignado_a", "solicitante", "prioridad", "creado_en"]
    ordering_fields = ["creado_en", "prioridad"]
    search_fields = ["titulo", "descripcion"]

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        empleado = self.request.user.empleado
        categoria = serializer.validated_data["categoria"]

        # 🔹 Calcular prioridad heurística
        prioridad = heuristic_priority(
            peso_rol=empleado.rol.peso_prioridad,
            horas_sla=categoria.horas_sla,
            descripcion=serializer.validated_data["descripcion"]
        )

        # 🔹 Calcular fecha de vencimiento (SLA)
        creado = datetime.now(timezone.utc)
        vence = calcular_vencimiento(creado, categoria.horas_sla)

        # 🔹 Guardar el ticket con los campos calculados
        serializer.save(
            solicitante=empleado,
            prioridad=prioridad,
            vence_en=vence
        )


class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        empleado = self.request.user.empleado
        serializer.save(autor=empleado)


class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrdenKanbanViewSet(viewsets.ModelViewSet):
    queryset = OrdenKanban.objects.all()
    serializer_class = OrdenKanbanSerializer
    permission_classes = [permissions.IsAuthenticated]
