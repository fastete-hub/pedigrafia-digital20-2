# Estado actual: depuración y próximos pasos recomendados

## Resumen corto
- **No hace falta una depuración masiva** del programa completo ahora mismo.
- **Sí conviene depuración focalizada** en 3 áreas clínicas críticas:
  1. segmentación de huella (falsos positivos/fondo),
  2. calibración automática (consistencia entre dispositivos y lotes),
  3. estabilidad del escáner en campo (tiempos y errores intermitentes).

---

## ¿Es necesario seguir depurando el código?

### Lo que hoy está razonablemente bien
- La base de datos está más robusta (validación de updates, cierre idempotente, FK activas).
- El flujo PDF es más estable y tiene pruebas.
- Hay cobertura de tests para utilidades, servicios y flujo de integración básico.
- Scanner ya tiene reintentos y configuración por parámetros.

### Lo que aún requiere depuración selectiva
- **Segmentación de huella**: aunque mejoró, en algunos escenarios sigue entrando ruido periférico o faltando talón/metatarso.
- **Calibración**: priorizar DPI ayuda, pero en la práctica clínica pueden existir variaciones por drivers/WIA o metadatos inconsistentes.
- **Comparabilidad entre sesiones**: se necesitan controles de calidad para evitar que diferencias de captura se interpreten como diferencias clínicas reales.

> Conclusión: no hace falta “refactor total”, sí una etapa breve de **QA clínico técnico** con casos reales.

---

## Mejoras que haría a continuación (priorizadas)

## 1) Control de calidad de captura (alto impacto)
- Mostrar un "check de calidad" antes de aceptar estudio:
  - porcentaje de huella detectada,
  - huella cortada en bordes,
  - relación área izquierda/derecha atípica.
- Si falla, sugerir recapturar antes de guardar.

## 2) Alertas con severidad (alto impacto clínico)
- Mantener alertas actuales, pero añadir niveles:
  - `verde`: dentro de rango,
  - `amarillo`: desviación moderada,
  - `rojo`: desviación marcada.
- Mostrar semáforo en UI y en PDF.

## 3) Calibración híbrida robusta (alto impacto métrico)
- Estrategia sugerida:
  1. DPI metadata (cuando sea confiable),
  2. fallback geométrico A4,
  3. fallback manual asistido (una sola vez por equipo).
- Guardar un "factor de calibración por dispositivo" para no recalibrar seguido.

## 4) Comparativo visual (alto valor para seguimiento)
- Además del comparativo textual, agregar:
  - superposición anterior vs actual,
  - mapa de diferencia,
  - resumen de cambios principales por zona.

## 5) Perfil de parámetros por modo (Tinta/Digital) (consistencia)
- Mantener pipelines separados (como ahora) y exponer presets:
  - `Digital suave`, `Digital detalle`,
  - `Tinta conservador`, `Tinta intenso`.

---

## Propuesta concreta de trabajo (2 iteraciones)

### Iteración 1 (rápida)
- Semáforo de alertas en UI + PDF.
- Check de calidad de captura antes de guardar.
- Registro de motivo cuando se recaptura (para auditar fallos de escaneo).

### Iteración 2 (clínica)
- Calibración híbrida con factor por dispositivo.
- Comparativo visual entre estudios.
- Reporte de tendencia por paciente (últimos N estudios).

---

## Señales para decidir si seguir depurando

Si observás alguno de estos síntomas en uso real, **sí conviene seguir depurando**:
- más de 1 recaptura cada 5 pacientes,
- diferencias de medida >10% sin cambio clínico esperable,
- necesidad frecuente de borrado manual para limpiar fondo,
- quejas de mapas "manchados" en más de 20% de estudios.

Si esos síntomas son bajos, conviene pasar a mejoras funcionales (comparativos, alertas visuales, reportes).
