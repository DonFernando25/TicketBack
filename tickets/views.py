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
from django.utils.timezone import now
from rest_framework.decorators import action


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

    # CREAR TICKET
    def perform_create(self, serializer):
        empleado = self.request.user.empleado
        categoria = serializer.validated_data["categoria"]

        # Calcular prioridad con IA simple
        prioridad = heuristic_priority(
            peso_rol=empleado.rol.peso_prioridad,
            horas_sla=categoria.horas_sla,
            descripcion=serializer.validated_data["descripcion"]
        )

        # Fecha actual
        creado = datetime.now(timezone.utc)

        # Si es proyecto, no aplica SLA
        if not serializer.validated_data.get("es_proyecto", False):
            vence = calcular_vencimiento(creado, categoria.horas_sla)
        else:
            vence = None

        serializer.save(
            solicitante=empleado,
            prioridad=prioridad,
            vence_en=vence,
            es_proyecto=serializer.validated_data.get("es_proyecto", False)
        )
    
    @action(detail=True, methods=["post"])
    def agendar(self, request, pk=None):
        ticket = self.get_object()
        inicio = parse_datetime(request.data.get("inicio"))
        fin = parse_datetime(request.data.get("fin"))
        asunto = f"Asistencia TI - {ticket.titulo}"

        evento_id = crear_evento_asistencia(
            asunto,
            inicio.isoformat(),
            fin.isoformat(),
            [ticket.solicitante.usuario.email, "soporte@tudominio.com"]
        )

        # Guarda la reunión en tu modelo si tienes campo para eso
        ticket.reunion.inicio = inicio
        ticket.reunion.fin = fin
        ticket.reunion.id_evento_outlook = evento_id
        ticket.estado = Ticket.Estado.AGENDADO
        ticket.save()

        return Response({"mensaje": "Reunión creada", "evento_id": evento_id})


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


#ACTUALIZAR TICKET (para registrar fecha de cierre)
def perform_update(self, serializer):
    ticket = serializer.save()

    # Si el ticket pasa a RESUELTO o CERRADO, registrar fecha de cierre
    if ticket.estado in [Ticket.Estado.RESUELTO, Ticket.Estado.CERRADO] and not ticket.fecha_cierre:
        ticket.fecha_cierre = now()
        ticket.save()

    #calcular duración del ticket
@action(detail=True, methods=["get"])
def duracion(self, request, pk=None):
    ticket = self.get_object()
    if ticket.fecha_cierre:
        delta = ticket.fecha_cierre - ticket.creado_en
        horas = round(delta.total_seconds() / 3600, 2)
        return Response({"duracion_horas": horas})
    else:
        return Response({"mensaje": "El ticket aún no ha sido cerrado."})
    


