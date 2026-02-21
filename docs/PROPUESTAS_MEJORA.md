# Propuestas de mejora (sin romper el programa)

Este documento propone mejoras **incrementales** y de **bajo riesgo** para seguir mejorando calidad, mantenimiento y experiencia de uso sin cambiar el flujo principal.

## 1) Mejoras rápidas (1-2 días)

### 1.1 Logging básico en archivo
- Agregar logging centralizado (`logging`) con rotación a archivo (`logs/app.log`).
- Registrar: inicio/cierre de app, errores de scanner, errores de generación PDF, errores DB.
- Beneficio: diagnóstico más rápido cuando un usuario reporta "no anda".

### 1.2 Mensajes de error más accionables
- Estandarizar mensajes de error para usuario final:
  - "No se encontró scanner"
  - "No se pudo abrir la imagen"
  - "No se pudo escribir PDF"
- Incluir sugerencia concreta en cada mensaje (ej. "revisar permisos de carpeta").

### 1.3 Validaciones de entrada de paciente
- Validar formato de email y teléfono antes de guardar.
- Normalizar espacios y mayúsculas en nombre.
- Evita datos inconsistentes y reduce trabajo manual luego.

### 1.4 Backup automático de base de datos
- Crear copia de `podoscopio.db` al iniciar o cerrar sesión (ej. `backups/podoscopio_YYYYMMDD.db`).
- Mantener últimas N copias (por ejemplo 7).

## 2) Mejoras de estabilidad (1 semana)

### 2.1 Pruebas de integración mínimas
- Agregar tests para flujo completo:
  1) crear paciente,
  2) crear informe,
  3) generar PDF,
  4) eliminar paciente.
- Ya hay base de tests unitarios; esto suma confianza en el flujo real.

### 2.2 Migraciones explícitas de DB
- Agregar versión de esquema en tabla `meta`.
- Ejecutar migraciones por versión (v1->v2->v3) en vez de lógica implícita por columnas.
- Mejora compatibilidad entre instalaciones viejas y nuevas.

### 2.3 Timeouts y reintentos en scanner
- En lectura de scanner: timeout configurable + reintento acotado (2-3 intentos).
- Mostrar estado en UI durante espera.

## 3) Mejoras de arquitectura (sin reescribir todo)

### 3.1 Separar UI por módulos
- Dividir `PodoscopioApp` por pantallas/servicios:
  - `ui_inicio.py`
  - `ui_paciente.py`
  - `ui_estudio.py`
  - `services/report_service.py`
- Mantener API actual para no romper comportamiento.

### 3.2 Capa de servicio para casos de uso
- Encapsular lógica de negocio en servicios:
  - `crear_paciente_y_estudio`
  - `generar_reporte`
  - `eliminar_paciente_completo`
- UI queda más simple y testeable.

## 4) UX/operación clínica

### 4.1 Plantillas de observaciones
- Botones rápidos con frases frecuentes para diagnóstico/recomendaciones.
- Acelera carga de trabajo en consultorio.

### 4.2 Historial comparativo
- Vista de comparación entre estudios por fecha (actual vs previo).
- Métricas básicas: variación de apoyo, observaciones destacadas.

### 4.3 Exportación de datos
- Exportar CSV de pacientes + estudios para análisis externo.
- Útil para auditoría y respaldo.

## 5) Priorización sugerida

### Sprint A (seguro y rápido)
1. Logging + mensajes de error accionables.
2. Validaciones de entrada en paciente.
3. Backup automático de DB.

### Sprint B (estabilidad)
1. Tests de integración del flujo completo.
2. Timeouts/reintentos en scanner.
3. Migraciones explícitas de esquema.

### Sprint C (mantenibilidad)
1. Separación gradual de UI.
2. Capa de servicios de negocio.

---

## Propuesta concreta de siguiente paso (recomendado)
Implementar **Sprint A completo** en una sola entrega:
- no cambia flujo principal,
- reduce riesgo operativo,
- y mejora soporte en campo desde el día 1.

## 6) Próximas mejoras recomendadas (en base a uso real)

### 6.1 Gestión de temporales y almacenamiento
- Panel de mantenimiento con métricas: cantidad y tamaño total de `temp/scans` y `temp/legacy`.
- Limpieza programada configurable (ej. conservar 24h/72h) y opción de "conservar último estudio temporal".
- Compresión opcional de escaneos originales al guardar estudio para ahorrar disco en instalaciones con alto volumen.

### 6.2 Mejora visual de interfaz
- Filtro rápido por semáforo en historial (solo rojo/amarillo/verde).
- Tarjetas de estudio con densidad visual consistente: jerarquía tipográfica y badges de estado más grandes.
- Modo de alto contraste para consultorio con luz fuerte.

### 6.3 Precisión de medida y calibración
- Asistente guiado de calibración con patrón impreso (regla de 5 cm) y validación automática.
- Persistir perfiles de calibración por escáner (si hay más de un equipo).
- Diagnóstico de escala: mostrar en UI si la fuente de calibración fue DPI embebido o fallback geométrico.
