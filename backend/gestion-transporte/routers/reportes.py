"""Reportes: consultas de 3 o más tablas relacionadas, sin IDs, con envío por correo.

- Abordajes: registros_abordaje + estudiantes + rutas + vehiculos + conductores
- Ausencias: ausencias + estudiantes + acudientes + rutas

Cada rol ve solo lo suyo (mismas reglas de alcance que el resto de la app).
El PDF y el Excel los genera el frontend; este módulo entrega los datos y
envía por correo el archivo ya generado.
"""
import base64
import binascii
import os
import re
import smtplib
import ssl
from datetime import date, datetime, time, timedelta
from email.message import EmailMessage
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import permiso
from database import get_db
from models import (
    Acudiente, Ausencia, Conductor, Estudiante, RegistroAbordaje, Ruta, Vehiculo,
)
from scope import es_admin, ids_estudiantes, ids_rutas

router = APIRouter(prefix="/reportes", tags=["Reportes"])
CLAVE = "reportes"
MAX_FILAS = 5000
MAX_ADJUNTO = 8 * 1024 * 1024  # 8 MB
CORREO_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------- utilidades ----------------

def _rutas_permitidas(db, usuario, ruta_id):
    """None = sin filtro (todas). Lista = solo esas rutas."""
    visibles = ids_rutas(db, usuario)
    if ruta_id is None:
        return visibles
    if visibles is not None and ruta_id not in visibles:
        return [-1]
    return [ruta_id]


def _limites(desde: Optional[date], hasta: Optional[date]):
    ini = datetime.combine(desde, time.min) if desde else None
    fin = datetime.combine(hasta + timedelta(days=1), time.min) if hasta else None
    return ini, fin


def _texto(valor) -> str:
    return "" if valor is None else str(valor)


def _nombre(nombre, apellido) -> str:
    return f"{_texto(nombre)} {_texto(apellido)}".strip()


# ---------------- opciones de los filtros ----------------

@router.get("/opciones")
def opciones(db: Session = Depends(get_db), usuario=Depends(permiso(CLAVE))):
    consulta = db.query(Ruta).filter(Ruta.status == "Activo")
    visibles = ids_rutas(db, usuario)
    if visibles is not None:
        consulta = consulta.filter(Ruta.id.in_(visibles or [-1]))
    rutas = [{"id": r.id, "nombre": r.nombre} for r in consulta.order_by(Ruta.nombre)]

    tipos = [t[0] for t in db.query(RegistroAbordaje.tipo).distinct().order_by(RegistroAbordaje.tipo)]
    atenciones = [a[0] for a in db.query(Ausencia.atencion).distinct().order_by(Ausencia.atencion)]
    return {
        "rutas": rutas,
        "tipos": tipos or ["Subida", "Bajada"],
        "atenciones": atenciones or ["Pendiente"],
    }


# ---------------- reporte 1: abordajes ----------------

@router.get("/abordajes")
def reporte_abordajes(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    ruta_id: Optional[int] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario=Depends(permiso(CLAVE)),
):
    consulta = (
        db.query(
            RegistroAbordaje.fecha_hora,
            Estudiante.nombre, Estudiante.apellido, Estudiante.grado,
            Ruta.nombre,
            Vehiculo.placa,
            Conductor.nombre, Conductor.apellido,
            RegistroAbordaje.tipo,
        )
        .select_from(RegistroAbordaje)
        .join(Estudiante, RegistroAbordaje.estudiante_id == Estudiante.id)
        .join(Ruta, RegistroAbordaje.ruta_id == Ruta.id)
        .join(Vehiculo, Ruta.vehiculo_id == Vehiculo.id)
        .join(Conductor, Ruta.conductor_id == Conductor.id)
        .filter(RegistroAbordaje.status == "Activo")
    )

    ini, fin = _limites(desde, hasta)
    if ini:
        consulta = consulta.filter(RegistroAbordaje.fecha_hora >= ini)
    if fin:
        consulta = consulta.filter(RegistroAbordaje.fecha_hora < fin)
    if tipo:
        consulta = consulta.filter(RegistroAbordaje.tipo == tipo)

    rutas_ok = _rutas_permitidas(db, usuario, ruta_id)
    if rutas_ok is not None:
        consulta = consulta.filter(RegistroAbordaje.ruta_id.in_(rutas_ok or [-1]))
    if not es_admin(usuario) and usuario.rol.nombre in ("Acudiente", "Estudiante"):
        consulta = consulta.filter(
            RegistroAbordaje.estudiante_id.in_(ids_estudiantes(db, usuario) or [-1])
        )

    filas = [
        [
            f[0].strftime("%d/%m/%Y %H:%M"),
            _nombre(f[1], f[2]),
            _texto(f[3]),
            _texto(f[4]),
            _texto(f[5]),
            _nombre(f[6], f[7]),
            _texto(f[8]),
        ]
        for f in consulta.order_by(RegistroAbordaje.fecha_hora.desc()).limit(MAX_FILAS).all()
    ]
    return {
        "tipo": "abordajes",
        "titulo": "Reporte de abordajes",
        "columnas": ["Fecha y hora", "Estudiante", "Grado", "Ruta", "Placa", "Conductor", "Tipo"],
        "filas": filas,
        "total": len(filas),
    }


# ---------------- reporte 2: ausencias ----------------

@router.get("/ausencias")
def reporte_ausencias(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    ruta_id: Optional[int] = None,
    atencion: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario=Depends(permiso(CLAVE)),
):
    consulta = (
        db.query(
            Ausencia.fecha,
            Estudiante.nombre, Estudiante.apellido,
            Acudiente.nombre, Acudiente.apellido, Acudiente.telefono,
            Ruta.nombre,
            Ausencia.motivo,
            Ausencia.atencion,
        )
        .select_from(Ausencia)
        .join(Estudiante, Ausencia.estudiante_id == Estudiante.id)
        .join(Acudiente, Estudiante.acudiente_id == Acudiente.id)
        .outerjoin(Ruta, Ausencia.ruta_id == Ruta.id)
        .filter(Ausencia.status == "Activo")
    )

    if desde:
        consulta = consulta.filter(Ausencia.fecha >= desde)
    if hasta:
        consulta = consulta.filter(Ausencia.fecha <= hasta)
    if atencion:
        consulta = consulta.filter(Ausencia.atencion == atencion)

    rutas_ok = _rutas_permitidas(db, usuario, ruta_id)
    if rutas_ok is not None:
        consulta = consulta.filter(Ausencia.ruta_id.in_(rutas_ok or [-1]))
    if not es_admin(usuario) and usuario.rol.nombre in ("Acudiente", "Estudiante"):
        consulta = consulta.filter(
            Ausencia.estudiante_id.in_(ids_estudiantes(db, usuario) or [-1])
        )

    filas = [
        [
            f[0].strftime("%d/%m/%Y"),
            _nombre(f[1], f[2]),
            _nombre(f[3], f[4]),
            _texto(f[5]),
            _texto(f[6]) or "Sin ruta",
            _texto(f[7]),
            _texto(f[8]),
        ]
        for f in consulta.order_by(Ausencia.fecha.desc()).limit(MAX_FILAS).all()
    ]
    return {
        "tipo": "ausencias",
        "titulo": "Reporte de ausencias",
        "columnas": ["Fecha", "Estudiante", "Acudiente", "Teléfono acudiente", "Ruta", "Motivo", "Atención"],
        "filas": filas,
        "total": len(filas),
    }


# ---------------- envío por correo ----------------

class EnvioReporte(BaseModel):
    destinatario: str
    asunto: str = "Reporte de Gestión de Transporte Escolar"
    mensaje: str = ""
    nombre_archivo: str
    contenido_base64: str


@router.post("/enviar")
def enviar_reporte(datos: EnvioReporte, usuario=Depends(permiso(CLAVE))):
    host = os.getenv("SMTP_HOST")
    cuenta = os.getenv("SMTP_USER")
    clave = os.getenv("SMTP_PASSWORD")
    if not (host and cuenta and clave):
        raise HTTPException(
            503,
            "El envío por correo no está configurado en el servidor "
            "(faltan SMTP_HOST, SMTP_USER y SMTP_PASSWORD en el .env).",
        )

    destinatario = datos.destinatario.strip()
    if not CORREO_VALIDO.match(destinatario):
        raise HTTPException(422, "El correo del destinatario no es válido.")

    nombre = re.sub(r"[^A-Za-z0-9._-]", "_", datos.nombre_archivo)[:80]
    if nombre.lower().endswith(".pdf"):
        tipo = ("application", "pdf")
    elif nombre.lower().endswith(".xlsx"):
        tipo = ("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        raise HTTPException(422, "Solo se pueden enviar archivos PDF o Excel (.xlsx).")

    try:
        contenido = base64.b64decode(datos.contenido_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "El archivo adjunto no es válido.")
    if not contenido or len(contenido) > MAX_ADJUNTO:
        raise HTTPException(422, "El archivo está vacío o supera los 8 MB.")

    mensaje = EmailMessage()
    mensaje["From"] = os.getenv("SMTP_FROM", cuenta)
    mensaje["To"] = destinatario
    mensaje["Subject"] = " ".join(datos.asunto.split())[:150] or "Reporte"
    cuerpo = datos.mensaje.strip()
    firma = (
        f"Reporte generado por {usuario.nombre_completo} ({usuario.rol.nombre}) "
        "desde Gestión de Transporte Escolar."
    )
    mensaje.set_content(f"{cuerpo}\n\n{firma}" if cuerpo else firma)
    mensaje.add_attachment(contenido, maintype=tipo[0], subtype=tipo[1], filename=nombre)

    puerto = int(os.getenv("SMTP_PORT", "587"))
    try:
        if puerto == 465:
            with smtplib.SMTP_SSL(host, puerto, context=ssl.create_default_context(), timeout=20) as s:
                s.login(cuenta, clave)
                s.send_message(mensaje)
        else:
            with smtplib.SMTP(host, puerto, timeout=20) as s:
                s.starttls(context=ssl.create_default_context())
                s.login(cuenta, clave)
                s.send_message(mensaje)
    except (smtplib.SMTPException, OSError):
        raise HTTPException(
            502, "No se pudo enviar el correo. Revisa la configuración SMTP del servidor."
        )
    return {"mensaje": f"Reporte enviado a {destinatario}"}
