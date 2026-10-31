# Publicación e integración de Parte 7

La publicación de desarrollo fue autorizada después del informe de auditoría. Los informes anteriores son instantáneas históricas, no una aprobación de producción.

## Alcance de publicación
Se conservan las cinco fases y el rediseño SENATI. Se retiran literales JWT, clave facial y respaldo de contraseña del árbol actual. El Blueprint pide secretos al operador. No se modifica la configuración real de Render, MySQL ni claves en uso.

La historia Git pública anterior todavía contiene los valores antiguos: su retiro del árbol no los revoca. Se requiere rotación coordinada y recuperación facial comprobada. Nunca cambiar la clave facial sin preservar descifrado de datos y respaldos anteriores.

La rama de integración se preparará sobre origin/main, separada de esta entrega. La publicación de desarrollo no declara aprobada la integración ni autoriza un despliegue.

Los resultados, decisiones, conflictos y procedimientos finales se documentarán en este archivo y en el Pull Request.

El health público es ahora liveness mínimo sin consultar MySQL ni exponer configuración. Los errores generales no devuelven excepciones internas. Esto no sustituye readiness protegido ni la rotación de secretos.

Pruebas previas a publicación: backend Parte 7, 260 aprobadas; 509 comprobaciones Chrome, voz simulada y conversación aprobadas. Los resultados globales anteriores siguen siendo bloqueos de integración, no se declaran resueltos por publicar desarrollo.

## Evidencia de Fase A

Se verificaron las seis suites Chrome de Parte 7, con 509 comprobaciones, más voz simulada y conversación contextual. La suite backend tiene 260 pruebas aprobadas. Se publicará desarrollo preservando los bloqueos históricos de la suite global para resolverlos en la rama de integración.
