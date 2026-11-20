# Gestión de Transporte Escolar — estructura reorganizada

Se conservó el código funcional de la API y del frontend; únicamente se reorganizaron las carpetas para seguir el patrón `backend/<proyecto>` y `frontend/<proyecto>` del repositorio Tutorías-Taller2.

## Estructura

- `backend/gestion-transporte/`: API FastAPI, modelos, esquemas y routers.
- `frontend/gestion_transporte_web/`: aplicación Svelte + Vite.
- `render.yaml`: servicio de Render configurado con `rootDir` para la nueva ubicación.
- `frontend/gestion_transporte_web/netlify.toml`: build de Netlify para Vite.

## Ejecutar localmente

### API (Python)

1. Abre una terminal en `backend/gestion-transporte`.
2. Crea y activa un entorno virtual. En Windows: `py -m venv venv` y `venv\Scripts\Activate.ps1`.
3. Instala dependencias: `pip install -r requirements.txt`.
4. Copia `.env.example` a `.env` y configura `DATABASE_URL`, `CORS_ORIGINS` y `JWT_SECRET`.
5. Ejecuta: `uvicorn main:app --reload --port 8000`.
6. Documentación: `http://127.0.0.1:8000/docs`.

### Frontend

1. Abre otra terminal en `frontend/gestion_transporte_web`.
2. Ejecuta `npm install`.
3. Copia `.env.example` a `.env` y configura `VITE_API_URL=http://localhost:8000`.
4. Ejecuta `npm run dev`.

## Publicación en Render y Netlify

- **Render:** el `render.yaml` declara `rootDir: backend/gestion-transporte`. Configura `DATABASE_URL` con la URL de PostgreSQL, `JWT_SECRET` como secreto largo y `CORS_ORIGINS` con la URL exacta de Netlify y los orígenes locales que necesites. Si Render ya está configurado manualmente, actualiza el Root Directory a `backend/gestion-transporte` y revisa el comando de inicio.
- **Netlify:** establece Base directory en `frontend/gestion_transporte_web`, Build command `npm run build` y Publish directory `dist`. Define `VITE_API_URL` con la URL pública real del backend en Render (sin barra final).
- La URL real del frontend de Netlify no se puede deducir de forma fiable del código; usa el dominio actual de tu proyecto en `CORS_ORIGINS`.

## Importante sobre credenciales

Los archivos `.env` reales no se incluyeron por seguridad. Configura las variables en el entorno local y en los paneles de Render/Netlify. Si las credenciales que estaban en el ZIP se subieron a GitHub o se compartieron, rota la contraseña de la base de datos y cualquier secreto JWT.

## Verificación

El archivo `pruebas_api.py` se conservó para las pruebas existentes. La estructura se reorganizó sin renombrar los módulos Python ni los endpoints, para mantener las importaciones y rutas actuales.
