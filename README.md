# Edupla

Plataforma Flask para planificacion de proyectos educativos, calendario docente, recursos y rubricas.

## Caracteristicas principales

- Gestion de proyectos (`/manuals`) con contenido markdown, recursos y rubricas.
- Banco de rubricas reutilizables (`/rubrics/bank`).
- Calendario docente semanal/mensual (`/dashboard`) con sesiones agendadas.
- Vista por dia desde calendario:
  - El dia muestra solo cantidad de sesiones.
  - Click en el dia abre modal con detalle horario.
  - Desde esa vista se puede agendar y editar sesiones.
- Administracion de usuarios (`/users`) con roles `admin` y `teacher`.

## Stack tecnico

- Python + Flask
- SQLAlchemy + Alembic (`flask db ...`)
- Jinja templates + Tailwind CSS (CDN)
- PostgreSQL (recomendado para desarrollo y produccion)

## Estructura del proyecto

- `app.py`: factory Flask y comandos CLI.
- `config.py`: configuracion por entorno.
- `extensions.py`: inicializacion de `db`, `migrate`, `csrf`.
- `models.py`: modelos de dominio.
- `routes.py`: endpoints y logica de negocio.
- `templates/`: vistas HTML.
- `migrations/`: historial Alembic.
- `docs/`: documentacion funcional y operativa.

## Requisitos

- Python 3.11+ (recomendado 3.12)
- PostgreSQL
- `pip`

## Configuracion local

1. Crear entorno virtual e instalar dependencias.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configurar variables de entorno.

```bash
cp .env.example .env
```

Valores minimos en `.env`:

- `DATABASE_URL=postgresql://USER:PASSWORD@localhost/edupla_db`
- `SECRET_KEY=...`
- `APP_ENV=development`

3. Ejecutar migraciones.

```bash
flask db upgrade
```

4. Sembrar datos de referencia (opcional).

```bash
flask seed-reference-data
```

5. Crear usuario inicial (opcional).

```bash
flask create-user
```

6. Levantar servidor.

```bash
flask run
```

## Flujos clave

### Calendario

- Ruta: `/dashboard`
- Vista por defecto: `month`
- Vista `week` y `month` muestran chips de sesiones solo si el dia tiene sesiones.
- Click en dia abre modal "Vista por dia".
- Desde ese modal:
  - listado de sesiones del dia
  - boton `Agendar sesion`
  - boton `Editar` por sesion

### Proyectos

- Ruta: `/manuals`
- Detalle: `/manuals/<id>`
- Incluye:
  - contenido markdown renderizado
  - recursos del proyecto
  - planificacion por sesion
  - rubricas del proyecto

## Comandos utiles

```bash
# Ver estado de rutas
flask routes

# Aplicar nuevas migraciones
flask db upgrade

# Crear migracion
flask db migrate -m "descripcion"
```

## Seguridad y buenas practicas

- No subir `.env` ni credenciales de tuneles (`.cloudflared/`).
- Revisar `SECRET_KEY` fuerte en produccion.
- Ejecutar con WSGI server en produccion (gunicorn/uwsgi), no `flask run`.

## Documentacion adicional

- `docs/arquitectura.md`
- `docs/operacion.md`
- `docs/cambios-recientes.md`
