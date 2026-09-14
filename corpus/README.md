# Corpus RAG perioperatorio para pacientes adultos

Versión: 0.2 · Fecha: 2026-09-14 · Estado: demo con contactos y rutas locales incorporados.

Cada respuesta generada debe citar el documento recuperado, respetar su límite de seguridad y escalar cuando corresponda. No usar para diagnóstico, prescripción, ajuste de dosis, suspensión de fármacos ni autorización de un procedimiento.

Antes de producción: asignar responsable clínico nominal y validar la aplicación de los protocolos con la institución. El paquete incorpora como marco colombiano los *Lineamientos S.C.A.R.E. para una anestesia segura* (2023); este documento no sustituye protocolos clínicos institucionales específicos.

## Actualización 0.2

- Se añadió el marco S.C.A.R.E. a ayuno, diabetes y anticoagulantes.
- Se configuró `123` como línea única nacional de emergencias y `1234567890` como canal preanestésico del demo.
- Se creó un documento específico para el canal preanestésico y rutas de atención.
