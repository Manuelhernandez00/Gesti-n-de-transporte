# Gestión de Transporte Escolar (RutaEscolar)

Aplicación web y móvil para gestionar el transporte escolar: rutas, estudiantes, abordajes,
ausencias y fallas de vehículos. Roles: **Administrador, Conductor, Acudiente y Estudiante**,
cada uno con su propio menú y sus propios datos.

## Tecnologías

| Parte | Tecnología |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, JWT |
| Base de datos | PostgreSQL (Neon) |
| Frontend | Svelte 5 + Vite |
| Móvil (APK) | Capacitor (carpeta `frontend/android`, compilación con GitHub Actions) |
| Tablero | Power BI publicado en la web, mostrado con un `<iframe>` |
| Reportes | PDF (jsPDF) y Excel (ExcelJS), con envío por correo (SMTP) |

## Estructura

```text
gestion-transporte/
├── backend/gestion-transporte/   API: routers/, models, auth.py, scope.py, seed.py
├── frontend/                     Svelte + Vite (src/components, src/lib) y Capacitor (android/)
├── .github/workflows/android.yml Compilación del APK
├── render.yaml                   Servicio del backend en Render
└── netlify.toml                  Build del frontend en Netlify
```

## Módulos destacados

- **Tablero:** el módulo muestra el tablero de Power BI (4 indicadores, 6 gráficos y 2 filtros) con un
  `<iframe>`. El vínculo está en `frontend/src/components/Tablero.svelte`.
- **Reportes:** dos informes (Abordajes y Ausencias) con filtros de rango de fechas, ruta y estado/tipo.
  No muestran IDs, unen 4 o más tablas, se visualizan en pantalla, se exportan a PDF o Excel con
  formato (encabezado, pie, colores) y se envían por correo. El Administrador ve todo y el Conductor
  solo sus rutas.

## Ejecutar localmente (Windows)

Requisitos: **Python 3.12 o 3.13** (versiones muy nuevas pueden no tener paquetes precompilados) y **Node.js LTS**.

### 1. Backend

```powershell
cd backend\gestion-transporte
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # y completa DATABASE_URL, CORS_ORIGINS y JWT_SECRET
python -m uvicorn main:app --reload --port 8000
```

Comprueba en `http://127.0.0.1:8000/docs`. Si `pip install -r requirements.txt` falla por `pyyaml`
(falta un compilador de C++), instala solo lo necesario:

```powershell
pip install fastapi uvicorn SQLAlchemy python-dotenv psycopg2-binary PyJWT
```

### 2. Base de datos

- **Base nueva y vacía:** `python seed.py` crea tablas, roles, módulos y datos de ejemplo.
  `python seed.py --reset` **borra** las tablas del proyecto antes: no lo uses en una base con datos.
- **Base que ya existe:** registra los módulos nuevos sin borrar nada:

```powershell
python agregar_tablero.py
python agregar_reportes.py
```

Después cierra sesión y vuelve a entrar para ver el menú.

### 3. Frontend

```powershell
cd frontend
npm install
copy .env.example .env          # VITE_API_URL=http://localhost:8000
npm run dev
```

Abre `http://localhost:5173`. Si Vite falla al cargar una librería nueva:
`Remove-Item -Recurse -Force node_modules\.vite` y `npm run dev -- --force`.

## Variables de entorno

| Variable | Dónde | Para qué |
|---|---|---|
| `DATABASE_URL` | Backend / Render | Conexión a PostgreSQL |
| `CORS_ORIGINS` | Backend / Render | URL(s) del frontend permitidas |
| `JWT_SECRET` | Backend / Render | Firma de sesiones |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Backend / Render | Envío de reportes por correo (opcional) |
| `VITE_API_URL` | Frontend / Netlify | URL pública de la API, sin barra final |

## Publicación

- **Render (backend):** `render.yaml` declara `rootDir: backend/gestion-transporte`. En *Environment* configura
  las variables de la tabla. `CORS_ORIGINS` debe incluir la URL exacta de Netlify.
- **Netlify (frontend):** el `netlify.toml` usa `base = "frontend"`, comando `npm run build` y carpeta `dist`.
  Define `VITE_API_URL` con la URL pública del backend en Render.
- **APK:** el flujo `.github/workflows/android.yml` compila la app Android con Capacitor.

## Seguridad

- El archivo `.env` real **no se sube** al repositorio (está en `.gitignore`); `.env.example` solo lleva valores de ejemplo.
- Si una contraseña o clave se subió o se compartió por error, cámbiala (en Neon, en Google, etc.) y actualiza
  las variables locales y las de Render.
- El tablero de Power BI se publica con "Publicar en la web": cualquiera con el enlace puede verlo.
  Usa solo datos de ejemplo.

## Pruebas

`backend/gestion-transporte/pruebas_api.py` contiene las pruebas de la API. Úsalo con una base **local de pruebas**.
