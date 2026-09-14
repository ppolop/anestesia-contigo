# RAG mínimo viable — Anestesia Contigo

Aplicación Streamlit para recuperar localmente, mediante TF-IDF, fragmentos de un corpus perioperatorio validado. No requiere una clave de OpenAI ni envía preguntas a un servicio externo. La respuesta visible es el fragmento recuperado y siempre muestra fuente, fase, categoría, nivel de riesgo y fecha de revisión.

## Estructura

- `corpus/`: documentos Markdown con metadatos.
- `build_index.py`: fragmenta los documentos, conserva metadatos y crea `data/index.pkl` con un índice TF-IDF local.
- `local_retriever.py`: indexación y búsqueda local sin API externa.
- `app.py`: buscador documental, rutas guiadas y respuesta con fuente recuperada.

## Ejecución

1. Cree un entorno virtual e instale dependencias: `pip install -r requirements.txt`.
2. Ejecute `python build_index.py`.
3. Inicie: `streamlit run app.py`.

## Pruebas antes del demo

- Ejecute las pruebas sin conexión: `PYTHONPATH=. python -m unittest discover -s tests -v`.
- Después de crear el índice local, ejecute `python evaluate_index.py` para probar las 40 preguntas de aceptación. El comando falla si una fuente/fecha falta, la ruta de alto riesgo no escala, un tema fuera de alcance no se rechaza o el fragmento recuperado no coincide con el esperado.

## Reglas de seguridad implementadas

- No hay generación libre sin fuente: la respuesta es el fragmento mejor recuperado.
- La fuente recuperada se muestra junto a la respuesta.
- Un umbral mínimo de similitud evita contestar cuando el corpus no tiene evidencia suficiente.
- Preguntas con signos de urgencia recuperan la ruta de alarma; solicitudes de cambio de insulina, anticoagulantes, antiagregantes o GLP-1 recuperan una ruta de escalamiento, sin prescribir. Tos, congestión, fiebre u otros síntomas nuevos antes del procedimiento se escalan a valoración preanestésica.
- Los documentos de alto riesgo mantienen sus límites de seguridad y rutas de escalamiento.
- La interfaz incluye bienvenida, rutas para ansiedad, síntomas, preparación, medicamentos, anestesia y recuperación, respuesta con fuente/fecha y el botón **“Agendar Cita con mi Médico Anestesiólogo”**.
- El corpus no debe recibir datos identificables de pacientes.

## Validación antes de demo

Pruebe consultas sobre ayuno, diabetes, GLP-1, anticoagulantes, anestesia, recuperación y urgencias. Confirme que la fuente coincide con la respuesta y que las preguntas individuales se redirigen al equipo tratante.
