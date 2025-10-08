from datetime import timedelta

# Palabras disparadoras
KEYWORDS = {
    "bloqueado": -2,
    "bloqueada": -2,
    "producción": -2,
    "no funciona": -1,
    "error crítico": -3,
    "urgente": -3,
    "falla": -1,
    "caído": -2,
}

def heuristic_priority(peso_rol: int, horas_sla: int, descripcion: str) -> int:
    """
    Calcula la prioridad de forma heurística:
      - Base media = 3
      - Menor número = más urgente
      - Se ajusta según peso del rol y palabras clave
    """
    prioridad = 3  # base media

    # Mientras más importante el rol, más urgente
    prioridad -= min(2, peso_rol // 2)

    # Palabras clave en descripción
    texto = descripcion.lower()
    for palabra, delta in KEYWORDS.items():
        if palabra in texto:
            prioridad += delta

    # Limitar a rango 1–5
    prioridad = max(1, min(5, prioridad))
    return prioridad


def calcular_vencimiento(creado_en, horas_sla: int):
    """Devuelve la fecha de vencimiento del ticket según el SLA."""
    return creado_en + timedelta(hours=horas_sla)
