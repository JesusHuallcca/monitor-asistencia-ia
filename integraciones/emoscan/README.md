# EmoScan - Sistema de Reconocimiento de Emociones Faciales en Tiempo Real (FER)

**Versión integrada actual:** OpenCV + ONNX Runtime / FERPlus (ocho clases).
La arquitectura descrita más abajo es la documentación original del módulo.
Para ejecutar esta versión, seguir [LEEME_ONNX.md](LEEME_ONNX.md) y
[INTEGRACION_ASISTENCIA.md](INTEGRACION_ASISTENCIA.md); no se utilizan los pesos
TensorFlow/Keras antiguos. Las salidas se interpretan como expresiones estimadas.

Sistema interactivo para la detección, clasificación y análisis temporal de emociones faciales mediante Visión por Computadora y Deep Learning. Integra un backend en Flask con un modelo convolucional entrenado y una interfaz analítica moderna desarrollada con Chart.js.

---

## 1. Arquitectura del Sistema

* **Capa de Visión:** Detección de rostros basada en clasificadores en cascada Haar de OpenCV.
* **Capa de Inferencia:** Red Neuronal Convolucional (CNN) implementada con TensorFlow/Keras para clasificar 7 emociones: Happy, Sad, Angry, Neutral, Surprise, Fear, Disgust.
* **Backend de Servicio:** Servidor Flask con streaming multiproceso de video (`/video_feed`) y servicio REST para estadísticas (`/get_stats`).
* **Frontend y Analítica:** Dashboard reactivo en modo oscuro con visualización en tiempo real mediante gráfico tipo dona y monitor temporal de curvas.

---

## 2. Estructura del Proyecto

```text
EmoScan/
├── app.py                      # Servidor principal Flask y controladores
├── config.py                   # Configuración del entorno y parámetros de inferencia
├── main.py                     # Lógica de inferencia y procesamiento de imágenes
├── requirements.txt            # Dependencias del proyecto
├── models/
│   ├── facial_expression_model_weights.h5   # Pesos de la CNN
│   ├── haarcascade_frontalface_default.xml  # Clasificador frontal Haar
│   └── model_info.txt                       # Ficha técnica de los modelos
├── ui/
│   └── templates/
│       └── index.html          # Panel analítico y dashboard visual
└── logs/                       # Registros de sesiones analizadas
