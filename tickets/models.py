from django.db import models
from django.contrib.auth.models import User

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    peso_prioridad = models.IntegerField(default=1)

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)
    departamento = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return self.usuario.username


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    horas_sla = models.IntegerField(default=24)

    def __str__(self):
        return self.nombre


class Ticket(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        PRIORIZADO = "PRIORIZADO", "Priorizado"
        AGENDADO = "AGENDADO", "Agendado"
        EN_PROGRESO = "EN_PROGRESO", "En progreso"
        RESUELTO = "RESUELTO", "Resuelto"
        CERRADO = "CERRADO", "Cerrado"

    solicitante = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name="tickets")
    asignado_a = models.ForeignKey(Empleado, on_delete=models.PROTECT, null=True, blank=True, related_name="asignados")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTO)
    prioridad = models.IntegerField(default=3)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    vence_en = models.DateTimeField(null=True, blank=True)
    es_proyecto = models.BooleanField(default=False, help_text="Marcar si es proyecto a futuro")
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.titulo} ({self.get_estado_display()})"


class Comentario(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(Empleado, on_delete=models.PROTECT)
    mensaje = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.autor} en {self.ticket}"


class Adjunto(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="adjuntos")
    archivo = models.FileField(upload_to="adjuntos/")
    subido_por = models.ForeignKey(Empleado, on_delete=models.PROTECT)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjunto de {self.ticket.titulo}"


class Reunion(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="reunion")
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    id_evento_outlook = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"Reunión para {self.ticket.titulo}"


class Evaluacion(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="evaluacion")
    puntaje = models.IntegerField()  # 1 a 5
    comentario = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluación de {self.ticket}"


class OrdenKanban(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    columna = models.CharField(max_length=20, choices=Ticket.Estado.choices, default=Ticket.Estado.ABIERTO)
    posicion = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.ticket.titulo} en {self.columna}"
