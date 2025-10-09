import os, msal, requests

def obtener_token():
    app = msal.ConfidentialClientApplication(
        os.getenv("MS_CLIENT_ID"),
        authority=f"https://login.microsoftonline.com/{os.getenv('MS_TENANT_ID')}",
        client_credential=os.getenv("MS_CLIENT_SECRET"),
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token["access_token"]

def crear_evento_asistencia(asunto, inicio_iso, fin_iso, asistentes):
    token = obtener_token()
    payload = {
        "subject": asunto,
        "start": {"dateTime": inicio_iso, "timeZone": "America/Santiago"},
        "end": {"dateTime": fin_iso, "timeZone": "America/Santiago"},
        "attendees": [{"emailAddress": {"address": e}, "type": "required"} for e in asistentes],
    }
    r = requests.post(
        "https://graph.microsoft.com/v1.0/users/<correo_servicio>/events",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=15
    )
    r.raise_for_status()
    return r.json().get("id")
