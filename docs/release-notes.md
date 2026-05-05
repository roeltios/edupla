# Release Notes

## 2026-05-05

### Resumen

Esta version mejora el flujo de trabajo de calendario, fortalece la gestion de proyectos y recursos, y agrega documentacion operativa y tecnica del sistema.

### Novedades

- Calendario renovado:
  - vista por defecto en mes
  - celdas de dia simplificadas con contador de sesiones
  - vista por dia en modal al hacer click en una fecha
  - boton para agendar desde la vista por dia
  - boton para editar sesiones agendadas desde la vista por dia
- Proyectos:
  - mejoras en detalle de proyecto
  - edicion de planificacion por sesion
  - reorganizacion visual del contenido y recursos
- Recursos del proyecto:
  - nueva entidad persistente para recursos asociados a proyectos
  - soporte de creacion/edicion visual en formularios
- Rubricas:
  - mejoras de integracion con banco de rubricas
  - posibilidad de importar estructuras completas desde el banco

### Cambios tecnicos

- Nueva migracion para tabla de recursos de proyecto:
  - `c4e2f9b0a1d7_add_project_manual_resources_table.py`
- Nuevos documentos:
  - `README.md`
  - `docs/arquitectura.md`
  - `docs/operacion.md`
  - `docs/cambios-recientes.md`
- Se excluye `.cloudflared/` del versionado para evitar subir credenciales locales.

### Correcciones

- Ajustes de ancho y consistencia visual en dashboard y vistas principales.
- Correccion del flujo de vista semanal del calendario.
- Eliminacion de chips de `0 sesiones` para reducir ruido visual.
- Correccion de errores de estructura HTML en el dashboard.

### Impacto para usuarios

- Navegacion mas clara en calendario.
- Menos ruido visual en semana/mes.
- Mejor administracion de sesiones agendadas.
- Mejor soporte para documentar y operar el proyecto.
