"""Agrega el módulo "Tablero" a la base de datos que YA existe (Neon).

NO borra nada y se puede ejecutar varias veces sin duplicar.
Da acceso al Administrador y al Conductor.

Uso (con el venv activado y el .env configurado):
    python agregar_tablero.py
"""
import models as m
from database import SessionLocal

# (rol, etiqueta del menú; None = usa el nombre del módulo)
PERMISOS = [
    ("Administrador", None),
    ("Conductor", "Mi tablero"),
]


def main():
    db = SessionLocal()
    try:
        modulo = db.query(m.Modulo).filter(m.Modulo.clave == "tablero").first()
        if not modulo:
            orden = db.query(m.Modulo).count() + 1
            modulo = m.Modulo(nombre="Tablero", clave="tablero", icono="📊", orden=orden)
            db.add(modulo)
            db.flush()
            print("Módulo 'tablero' creado.")
        else:
            modulo.status = "Activo"
            print("El módulo 'tablero' ya existía.")

        for nombre_rol, etiqueta in PERMISOS:
            rol = db.query(m.Rol).filter(m.Rol.nombre == nombre_rol).first()
            if not rol:
                print(f"  (el rol '{nombre_rol}' no existe, se omite)")
                continue
            permiso = db.query(m.RolModulo).filter(
                m.RolModulo.rol_id == rol.id, m.RolModulo.modulo_id == modulo.id
            ).first()
            if permiso:
                permiso.status = "Activo"
                print(f"  {nombre_rol}: ya tenía el permiso.")
            else:
                db.add(m.RolModulo(
                    rol_id=rol.id, modulo_id=modulo.id, etiqueta=etiqueta,
                    puede_crear=False, puede_editar=False, puede_eliminar=False,
                ))
                print(f"  {nombre_rol}: permiso agregado.")
        db.commit()
        print("Listo. Cierra sesión y vuelve a entrar para ver el menú.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
