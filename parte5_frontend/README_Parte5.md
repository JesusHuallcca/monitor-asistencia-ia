# Parte 5 – Frontend: Indicadores ML en la Web

**Responsable:** Integrante E  
**Independiente:** Sí (100 %). No necesita backend ni las otras partes para funcionar.

---

## Qué incluye esta carpeta

| Archivo | Descripción |
|---------|-------------|
| `indicadores_ml.html` | Página completa con KPIs, predicción, segmentación, gráfico y tabla de estadísticas |
| `mock_indicadores.json` | Datos de ejemplo (estadística, regresión, K-Means, tendencia) |
| `README_Parte5.md` | Este archivo |

---

## Cómo ejecutarlo (2 formas)

### Opción A – Servidor local (recomendado)

Desde esta carpeta:

```bash
cd parte5_frontend
python -m http.server 8080
```

Luego abre en el navegador:

```
http://localhost:8080/indicadores_ml.html
```

### Opción B – Live Server (VS Code / Cursor)

Clic derecho en `indicadores_ml.html` → **Open with Live Server**.

> **Importante:** No abras el HTML con doble clic (file://). El navegador bloquea la lectura del JSON por seguridad. Usa siempre un servidor local.

---

## Qué se ve en la página

1. **4 cards de KPIs** – media emocional, predicción de asistencia, segmento actual, sesiones analizadas  
2. **Bloque de predicción** – valor %, intervalo de confianza, R², features usadas  
3. **Segmentación K-Means** – barras de distribución de los 3 segmentos  
4. **Gráfico de línea** – asistencia vs emoción positiva por día (Chart.js)  
5. **Tabla de estadística básica** – media, mediana, varianza, desviación, probabilidades  

---

## Cómo conectar después a las APIs reales

Cuando las Partes 1, 2 y 3 tengan endpoints, cambia **una sola línea** en el `<script>` de `indicadores_ml.html`:

```js
// Antes (mock):
const URL_DATOS = "mock_indicadores.json";

// Después (API real):
const URL_DATOS = "http://127.0.0.1:8000/api/ml/indicadores";
```

El JSON de la API debe tener la misma estructura que `mock_indicadores.json` (o adaptar el JavaScript).

---

## Requisitos del curso que cubre esta parte

- ✅ Ver los indicadores a nivel web aplicados en una empresa (OBLIGATORIO)  
- ✅ La predicción de la línea se mostrará en la web como un indicador (OBLIGATORIO)  
- ✅ Librerías Python NumPy en web aplicado a la empresa (vía JSON/API)  
- ✅ Proyecto web final funcional (listo para el video de 5 min)  

---

## Capturas para el video / entrega

1. Abre la página con el servidor local.  
2. Toma 2–3 capturas de pantalla mostrando:  
   - Las 4 cards de KPIs  
   - El bloque de predicción al 81 %  
   - El gráfico de tendencia  
3. Guárdalas en una carpeta `capturas_dashboard/` (opcional).

---

## Criterio de aceptación (individual)

- La página se abre en el navegador.  
- Muestra al menos 3 indicadores numéricos y un gráfico.  
- Usa datos del JSON mock.  
- Queda lista para cambiar solo la URL cuando existan los endpoints reales.
