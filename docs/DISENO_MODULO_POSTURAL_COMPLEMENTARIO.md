# Diseño concreto: Módulo Postural Complementario (no obligatorio)

## Objetivo
Agregar un **módulo opcional** al sistema de pedigrafía digital para análisis postural estático por foto
(frente, lateral, espalda), sin alterar el flujo actual del estudio plantar.

- El estudio plantar sigue funcionando igual.
- El módulo postural se activa solo si el profesional lo desea.
- El profesional puede marcar puntos/líneas manualmente y el sistema calcula ángulos/desviaciones.

---

## 1) Alcance funcional (MVP)

### 1.1 Vistas posturales soportadas
- **Frente (plano frontal)**
- **Lateral (plano sagital)**
- **Espalda (plano posterior/frontal posterior)**

### 1.2 Flujo de uso
1. Abrir paciente (como hoy).
2. Entrar a estudio (como hoy).
3. Nueva sección opcional: `📸 Análisis Postural (Complementario)`.
4. Cargar foto (o 3 fotos) por vista.
5. Marcar puntos anatómicos sugeridos (manual) y/o trazar líneas manuales.
6. Calibrar escala con una referencia conocida (regla/marker en foto).
7. Obtener mediciones automáticas (ángulos + desviaciones lineales) y semáforo postural.
8. Guardar como complemento del estudio actual.

> Si el profesional no usa esta sección, el estudio se guarda exactamente como hoy.

---

## 2) Reglas biomecánicas de referencia (base configurable)

> **Nota clínica**: estos umbrales son de **screening orientativo** para evaluación estática.
> No reemplazan diagnóstico profesional ni evaluación funcional completa.

### 2.1 Plano frontal (frente/espalda)

#### A) Inclinación de hombros (línea acromion izq-der vs horizontal)
- Normal: `<= 2°`
- Moderado: `> 2° y <= 5°`
- Marcado: `> 5°`

#### B) Inclinación pélvica (línea EIAS izq-der vs horizontal)
- Normal: `<= 2°`
- Moderado: `> 2° y <= 5°`
- Marcado: `> 5°`

#### C) Alineación de rodillas (centro rótula respecto a plomada)
- Normal: desvío relativo bajo
- Moderado / marcado: según distancia a eje de referencia en mm o % de ancho pélvico

### 2.2 Plano sagital (lateral)

#### A) Cabeza adelantada (trago respecto a plomada por acromion)
- Normal: `<= 15 mm`
- Moderado: `> 15 mm y <= 30 mm`
- Marcado: `> 30 mm`

#### B) Tronco (acromion–trocánter vs vertical)
- Normal: `<= 3°`
- Moderado: `> 3° y <= 7°`
- Marcado: `> 7°`

#### C) Inclinación pélvica sagital (EIAS–EIPS aproximada si se marca)
- Umbral por defecto orientativo: `8° a 15°`

---

## 3) Biblioteca de protocolos (automática y editable)

Se recomienda una biblioteca por `vista + objetivo` con:

- puntos requeridos,
- líneas a construir,
- métricas derivadas,
- umbrales de semáforo,
- textos sugeridos para observación/recomendación.

### 3.1 Protocolo ejemplo: `frontal_basico_v1`
- Puntos: `acromion_izq`, `acromion_der`, `eias_izq`, `eias_der`
- Métricas:
  - `angulo_hombros_horizontal`
  - `angulo_pelvis_horizontal`
- Reglas:
  - verde / amarillo / rojo con umbrales descritos.

### 3.2 Protocolo ejemplo: `lateral_basico_v1`
- Puntos: `trago`, `acromion`, `trocanter`, `maleolo_lateral`
- Métricas:
  - `desvio_cabeza_mm` (trago a plomada por acromion)
  - `angulo_tronco_vertical`

### 3.3 Protocolo ejemplo: `posterior_basico_v1`
- Puntos: `acromion_izq`, `acromion_der`, `eips_izq`, `eips_der`, `calcaneo_izq`, `calcaneo_der`
- Métricas:
  - nivelación escapular/pélvica
  - valgo/varo retropié orientativo

---

## 4) Diseño técnico de datos

## 4.1 Entidades nuevas (propuesta)

### Tabla `postura_estudios`
- `id`
- `informe_id` (FK a estudio plantar)
- `fecha`
- `vista` (`frente|lateral|espalda`)
- `imagen_path`
- `escala_px_por_mm`
- `protocolo`
- `puntos_json`
- `lineas_json`
- `metricas_json`
- `alertas_json`
- `obs_postural`

### JSON `puntos_json`
```json
[
  {"name": "acromion_izq", "x": 412.4, "y": 288.1},
  {"name": "acromion_der", "x": 790.2, "y": 295.7}
]
```

### JSON `metricas_json`
```json
{
  "angulo_hombros_horizontal_deg": 2.1,
  "angulo_pelvis_horizontal_deg": 1.8,
  "desvio_cabeza_mm": 12.4
}
```

---

## 5) Arquitectura sugerida (agregado, no intrusivo)

Nuevos servicios:
- `services/posture_rules_service.py`
  - Biblioteca de protocolos biomecánicos + umbrales.
- `services/posture_analysis_service.py`
  - Cálculo geométrico de ángulos/desvíos desde puntos.
- `services/posture_report_service.py`
  - Resumen textual + semáforo + exportación PDF complementaria.

Nueva UI opcional:
- `ui_postura.py` (o sección en `main_mejorado.py` inicialmente).

Integración mínima:
- Botón secundario en estudio: `📸 Postura (Opcional)`.
- Guardado desacoplado del estudio plantar.

---

## 6) UX concreta

### 6.1 Controles
- Selector de vista: `Frente | Lateral | Espalda`
- Selector de protocolo: `Frontal Básico`, `Lateral Básico`, `Posterior Básico`
- Botones:
  - `Cargar Foto`
  - `Calibrar escala`
  - `Agregar punto`
  - `Calcular`
  - `Guardar complemento`

### 6.2 Modo manual prioritario
- El profesional define puntos y líneas.
- El sistema calcula ángulos/desvíos automáticamente.
- Semáforo y texto sugerido aparecen como ayuda editable.

---

## 7) PDF complementario postural (opcional)

Sección adicional en PDF comparativo o PDF propio:
- Foto anotada por vista
- Tabla de métricas
- Semáforo por métrica
- Evolución temporal si hay más de un estudio postural

---

## 8) Roadmap por fases (sin romper flujo actual)

### Fase A (2-3 semanas)
- Carga foto + puntos manuales + cálculo geométrico básico
- 3 protocolos básicos (frente/lateral/espalda)
- Guardado en BD y resumen en UI

### Fase B (2 semanas)
- Semáforo configurable por protocolo
- PDF complementario postural
- Comparativo postural entre estudios

### Fase C (futuro)
- Dinámica por video: selección de frames clave manuales
- Métricas de marcha en 2D

---

## 9) Riesgos y mitigación

- **Variabilidad de captura**: incluir checklist (distancia, altura cámara, marcador de escala).
- **Errores por mal marcado**: permitir editar puntos y recalcular.
- **Sobreinterpretación clínica**: mensajes de screening, no diagnóstico automático.

---

## 10) Criterio de aceptación del MVP

- Permite analizar 1 foto por vista con puntos manuales.
- Calcula al menos 3 métricas por vista.
- Guarda y reabre resultados por paciente.
- No bloquea ni altera guardado del estudio plantar si no se usa.

