# Arquitectura

## Capas

- Presentacion: templates Jinja en `templates/`.
- Aplicacion: handlers y reglas en `routes.py`.
- Datos: modelos SQLAlchemy en `models.py`.
- Infra Flask: app factory + extensiones en `app.py` y `extensions.py`.

## Modelos principales

- `User`: usuarios del sistema (`admin`, `teacher`).
- `ProjectManual`: proyecto educativo principal.
- `ProjectManualResource`: recursos asociados al proyecto.
- `ManualSessionPlan`: plan de sesiones por proyecto.
- `ProjectManualSchedule`: sesiones calendarizadas por usuario.
- `ProjectRubric` + `ProjectRubricCriterion`: rubricas del proyecto.
- `RubricBankItem`: banco reutilizable de criterios.

## Relacion funcional clave

1. Se crea o edita un proyecto (`ProjectManual`).
2. Se define su plan de sesiones (`ManualSessionPlan`).
3. Se calendariza en `/dashboard` generando `ProjectManualSchedule`.
4. Se evalua con rubricas del proyecto o del banco.

## Rutas relevantes

- Auth:
  - `/auth/login`
  - `/auth/logout`
- Calendario:
  - `/dashboard`
  - `/dashboard/sessions/create`
  - `/dashboard/sessions/<id>/update`
  - `/dashboard/sessions/<id>/delete`
- Proyectos:
  - `/manuals`
  - `/manuals/new`
  - `/manuals/<id>`
  - `/manuals/<id>/edit`
- Rubricas:
  - `/rubrics/bank`
  - `/rubrics/bank/new`
  - `/rubrics/bank/<id>/edit`

## Notas de UI del calendario

- Se evita sobrecargar celdas del calendario.
- El dia muestra solo contador de sesiones (si > 0).
- Click en dia abre modal de detalle por horarios.
- Desde ese detalle se permite agendar o editar.
