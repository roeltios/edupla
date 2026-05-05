# Cambios recientes

## Calendario

- Vista por defecto en `month`.
- Celdas de dia simplificadas:
  - muestran solo contador de sesiones (si hay sesiones).
  - click en dia abre modal "Vista por dia" con horarios.
- En la vista por dia:
  - boton `Agendar sesion`.
  - boton `Editar` por sesion agendada.
- Se corrigio estructura HTML de vista semanal que causaba layout roto.

## Proyectos

- Se reforzo la experiencia en `manual_detail` para planificacion por sesion.
- Edicion de filas en `ManualSessionPlan`.
- Ajustes visuales para consistencia de anchos de contenedores.

## Recursos de proyecto

- Soporte para `ProjectManualResource` con tabla dedicada.
- Migracion creada:
  - `migrations/versions/c4e2f9b0a1d7_add_project_manual_resources_table.py`

## Rubricas

- Integracion de banco de rubricas para importar dimensiones completas.
- Mejoras de flujo de creacion/edicion en interfaces relacionadas.

## Terminologia UI

- Ajustes de textos visibles para usar "Proyecto/Proyectos" en lugar de "Manual/Manuales" donde aplica.
