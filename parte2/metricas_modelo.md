# Métricas del Modelo — Parte 2

## Regresión Lineal Simple
| Métrica | Valor | Interpretación |
|---|---|---|
| R² | 0.1777 | El modelo explica el 17.8% de la varianza usando solo `confianza` |
| MAE | 12.26 pts | Error promedio de ±12 puntos en la predicción |
| MSE | 201.61 | Error cuadrático medio |

**Ecuación:** `puntaje = 23.89 × confianza + 54.55`

La regresión simple tiene un R² bajo porque la asistencia depende de múltiples factores, no solo de la confianza facial. Es el punto de partida esperado.

---

## Regresión Lineal Múltiple
| Métrica | Valor | Interpretación |
|---|---|---|
| R² | 0.7790 | Explica el 77.9% de la varianza con todas las features |
| MAE | 6.18 pts | Error promedio de ±6 puntos (mejora significativa) |
| MSE | 54.19 | Reducción de ~73% vs modelo simple |

### Coeficientes (estandarizados — mayor valor = mayor impacto)
| Feature | Coeficiente | Efecto |
|---|---|---|
| `hora_llegada` | -11.59 | Llegar tarde reduce mucho el puntaje (**más influyente**) |
| `happy` | -7.76 | Efecto compensado por otras emociones |
| `neutral` | -7.77 | Idem |
| `sad` | -7.21 | Tristeza reduce el puntaje |
| `angry` | -5.30 | Enojo reduce el puntaje |
| `confianza` | +4.03 | Alta confianza facial sube el puntaje |
| `liveness_score` | +2.16 | Anti-spoofing positivo sube el puntaje |
| `dia_semana` | +0.20 | Impacto mínimo |

### Limitaciones del modelo
- Dataset sintético de 200 filas; con datos reales del Monitor el R² puede variar
- La regresión lineal asume relación lineal entre variables; una relación no lineal podría mejorarse con Random Forest
- Los coeficientes de emociones tienen signo negativo por la normalización (suman 1); el efecto real es relativo entre emociones
