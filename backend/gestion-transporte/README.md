# Gestión de Transporte Escolar (RutaEscolar)

API FastAPI + frontend Svelte (Vite) + PostgreSQL. Roles: Administrador, Conductor, Acudiente, Estudiante.

```text
gestion-transporte-api/
├── routers/         # un archivo por entidad (misma estructura de la clase 1)
├── models.py        # tablas (todas con created, updated y status)
├── schemas.py       # validación y respuestas
├── auth.py          # JWT + permisos leídos de roles_modulos
├── scope.py         # qué datos ve cada rol
├── routers/reportes.py  # reportes (abordajes y ausencias) y envío por correo
├── utils.py         # ayudas compartidas (baja lógica, etc.)
├── seed.py          # roles, módulos, permisos y datos de ejemplo
├── main.py
└── (el frontend está en ../../frontend)
```

## Lo nuevo (indicaciones del profesor)

- **Tablas `modulos` y `roles_modulos`**: el menú de cada rol y sus permisos (crear/editar/eliminar) salen de la base de datos.
- **`created`, `updated` y `status` en TODAS las tablas.** Eliminar = `status = 'Inactivo'` (no se borra la fila).
- **Login con JWT** y selector de rol (`POST /auth/login`).
- **Conductor**: reporta *fallas del vehículo* (`/fallas-vehiculo`) y ve las *ausencias* avisadas por los acudientes.
- **Acudiente**: reporta *ausencias* de sus hijos y ve abordajes y alertas de vehículos de sus rutas.
- Cambios de nombre: la situación operativa del vehículo es `vehiculos.disponibilidad`; el campo común de baja lógica de todas las tablas es `status`.

### Funcionamiento entre roles
1. Conductor registra un abordaje → acudiente y estudiante lo ven.
2. Acudiente/estudiante reporta ausencia → el conductor la ve y la marca "Vista por conductor" → el acudiente ve el cambio.
3. Conductor reporta una falla → el administrador la pone "En revisión" (el vehículo pasa a *Mantenimiento*) o "Resuelta" → acudientes y estudiantes de esa ruta ven la alerta.

## Desarrollo local

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # y configura DATABASE_URL y JWT_SECRET
python seed.py --reset        # crea tablas y carga datos (BORRA las tablas del proyecto)
uvicorn main:app --reload
```

Módulos nuevos en una base que ya existe (sin borrar datos): `python agregar_tablero.py` y `python agregar_reportes.py`.

Frontend: `cd ../../frontend`, copia `.env.example` a `.env`, `npm install`, `npm run dev`.

Cuentas de prueba (el login pide también el rol): `admin@rutaescolar.co / Admin2026*`;
los demás usuarios usan `Ruta2026*` (el seed imprime un correo de ejemplo por rol).

## Nube

1. `python seed.py --reset` apuntando al `DATABASE_URL` de la base en la nube (Supabase/Postgres).
2. Render: variables `DATABASE_URL`, `CORS_ORIGINS` (URL del frontend, sin barra final), `JWT_SECRET` y, para enviar reportes por correo, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` y `SMTP_PASSWORD`.
3. Frontend: `VITE_API_URL=https://tu-api.onrender.com`, `npm run build` y publica `frontend/dist` (Netlify).

## Organización interna del backend

- `app/models/`: definiciones de modelos SQLAlchemy por ahora agrupadas en `__init__.py`.
- `app/repositories/`: repositorios de acceso a datos con operaciones reutilizables.
- `models.py`: módulo de compatibilidad para mantener funcionando los imports de los routers existentes.

Los repositorios nuevos no cambian por sí solos los endpoints existentes; permiten migrarlos gradualmente sin alterar las rutas públicas.
