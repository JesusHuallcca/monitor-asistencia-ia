# Resguardo local de EmoScan y recuperación

Antes de cambiar de rama se revisó el estado, se verificó que `segmentacion`
coincidía entre ramas y se guardaron 32 archivos seleccionados en un stash local.
Se verificó el contenido de los 32 archivos contra sus hashes previos, admitiendo
únicamente la normalización LF/CRLF de Git para archivos de texto.

- Rama de origen: `integracion-emoscan`.
- Rama actual del trabajo de Parte 3: `parte-3-segmentacion`.
- Mensaje: `resguardo-emoscan-antes-parte3-2026-10-26`.
- Referencia estable: `3949fd59ab553975ad9e0ad4d477af833e04e28a`.

El resguardo incluye código, documentación, pruebas, configuración de ejemplo,
el modelo ONNX y la fotografía pública de NASA documentada. No incluye `.env`,
entornos virtuales, claves reales, imágenes privadas, cachés ni archivos
generados/temporales. `.env`, los entornos, `integraciones/o.pb` y
`integraciones/emoscan/resultado_prueba.jpg` / `.json` permanecieron localmente
sin modificarse. No se borraron ni sobrescribieron para cambiar de rama.

El stash se conserva; no se aplicó ni eliminó. No se crearon commits en las
ramas ni se ejecutó push. Git implementa internamente el stash con objetos de
resguardo, distintos de un commit añadido a la historia de la rama.

## Volver a EmoScan sin perder la ampliación de Parte 3

Los archivos experimentales actuales son nuevos y no están comprometidos en Git.
Los archivos no rastreados no quedan asociados a una rama solo por cambiarla.
Antes de regresar, proteger también esta carpeta:

```powershell
git status --short
git stash push --include-untracked --message "resguardo-parte3-experimental" -- segmentacion/experimental_expresiones
git stash list --format="%H %s"
git switch integracion-emoscan
git stash apply 3949fd59ab553975ad9e0ad4d477af833e04e28a
git status --short
```

La orden de Parte 3 incluye sus nuevos CSV y gráficos sintéticos; su `.gitignore`
excluye cachés y copias temporales de demostración. No usar `git stash -a`.
Verificar que el resguardo de Parte 3 termine correctamente antes del `switch`.

Se usa `apply`, no `pop`, para conservar el respaldo de EmoScan. No hace falta
que sea `stash@{0}`: al crear otro stash cambian los índices, pero la referencia
completa de EmoScan sigue identificando el mismo contenido.

Para recuperar después la ampliación de Parte 3, proteger primero cualquier
cambio pendiente de EmoScan, volver a `parte-3-segmentacion` y aplicar el hash
correspondiente a `resguardo-parte3-experimental` que muestre `git stash list`.
No aplicar dos veces el mismo stash ni forzar conflictos con reset/clean.

Los stashes son locales: no son un respaldo remoto y no se enviaron a GitHub.
