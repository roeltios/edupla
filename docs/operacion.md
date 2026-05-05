# Operacion y despliegue

## Entorno local

```bash
source venv/bin/activate
flask db upgrade
flask run
```

## Variables de entorno

- `DATABASE_URL`: conexion a PostgreSQL.
- `SECRET_KEY`: clave Flask.
- `APP_ENV`: `development` o `production`.

## Migraciones

```bash
flask db migrate -m "mensaje"
flask db upgrade
```

## Datos base

```bash
flask seed-reference-data
```

## Usuario administrador

```bash
flask create-user
```

## Cloudflare Tunnel (opcional)

La carpeta `.cloudflared/` se considera local y no se versiona.

Pasos tipicos:

1. Instalar `cloudflared`.
2. Autenticar en Cloudflare.
3. Crear tunel.
4. Configurar ingress a `http://localhost:5000`.

## Incidencias comunes

### Puerto 5000 ocupado

```bash
fuser -k 5000/tcp
flask run
```

### Cambios no visibles

- Verificar proceso activo de Flask.
- Recargar navegador de forma forzada.
- Revisar logs del servidor.

### Error en migracion

- Validar `DATABASE_URL`.
- Confirmar estado de revision actual:

```bash
flask db current
flask db history
```
