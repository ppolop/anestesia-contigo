from __future__ import annotations

from pathlib import Path

import streamlit as st

from local_retriever import hybrid_search, load_local_index
from rag_core import assess_risk, corpus_route

INDEX_PATH = Path("data/index.pkl")
MIN_SIMILARITY = 0.25

ROUTES = {
    "Tengo miedo o ansiedad": "Tengo miedo de despertarme durante la cirugía, sentir dolor o no poder moverme.",
    "Tengo síntomas nuevos": "Tengo tos, congestión o fiebre antes de mi cirugía.",
    "Me preparo": "¿Qué debo saber sobre ayuno, agua y alimentos antes del procedimiento?",
    "Uso medicamentos": "Uso medicamentos antes de mi procedimiento, ¿qué información debo llevar?",
    "Quiero entender la anestesia": "¿Qué debo saber sobre los tipos de anestesia y la vigilancia durante la cirugía?",
    "Estoy en recuperación": "¿Qué puedo sentir al despertar después de la anestesia?",
}

st.set_page_config(page_title="Anestesia Contigo", page_icon="🩺", layout="centered")
st.title("Anestesia Contigo")
st.subheader("Orientación general antes y después de anestesia")
st.write("Seleccione una ruta o escriba una pregunta. Las respuestas se recuperan únicamente del corpus clínico validado.")
st.warning("Esta aplicación no diagnostica, no decide si una cirugía puede realizarse y no prescribe ni modifica medicamentos, dosis ni ayuno. No incluya datos personales.")

if st.button("Agendar Cita con mi Médico Anestesiólogo", type="primary", use_container_width=True):
    st.info("**Canal preanestésico del demo:** 1234567890")
    st.error("**Emergencia:** marque **123** en Colombia si hay dificultad para respirar, dolor en el pecho, desmayo, sangrado importante, confusión creciente o debilidad súbita.")

st.markdown("### ¿Qué necesita hoy?")
for left, right in zip(list(ROUTES.items())[::2], list(ROUTES.items())[1::2]):
    col_a, col_b = st.columns(2)
    for column, (label, prompt) in ((col_a, left), (col_b, right)):
        if column.button(label, use_container_width=True):
            st.session_state["suggested_question"] = prompt

can_search = INDEX_PATH.exists()
if not INDEX_PATH.exists():
    st.info("El índice local aún no está construido. Ejecute `python build_index.py` después de validar y cargar el corpus.")


@st.cache_resource
def get_index():
    return load_local_index(INDEX_PATH)


def render_source(item: dict) -> None:
    st.markdown("#### Fuente recuperada")
    st.markdown(f"**{item['fuente']}**")
    if item.get("url_fuente") and not item["url_fuente"].startswith("["):
        st.markdown(f"[Abrir fuente]({item['url_fuente']})")
    st.caption(f"Fase: {item['fase']} · Categoría: {item['categoría']} · Riesgo: {item['riesgo']} · Revisión: {item['fecha']}")


def answer(question: str) -> None:
    with st.chat_message("user"):
        st.write(question)

    index = get_index()
    risk = assess_risk(question)
    if risk == "emergencia":
        st.error("Esta situación requiere una ruta de urgencias. El chat no puede evaluarla.")
        best, matches = corpus_route(index, "POST-ALARM"), []
    elif risk == "medicación_alto_riesgo":
        st.warning("No se darán cambios de medicamentos ni dosis. Esta decisión requiere un plan individual.")
        text = question.lower()
        prefix = "PRE-DM" if "insulina" in text or "diabetes" in text else "PRE-GLP" if "semaglut" in text or "tirzep" in text or "glp" in text else "PRE-ANTICOAG"
        best = corpus_route(index, prefix) or corpus_route(index, "PRE-MED")
        matches = []
    elif risk == "síntomas_preoperatorios":
        st.warning("La aplicación no puede confirmar la causa de los síntomas ni decidir si el procedimiento puede realizarse.")
        best, matches = corpus_route(index, "PRE-SINTOMAS"), []
    elif risk == "fuera_de_alcance":
        best, matches = None, []
    else:
        matches = hybrid_search(index, question, limit=3)
        best = matches[0] if matches and matches[0]["score"] >= MIN_SIMILARITY else None

    with st.chat_message("assistant"):
        if not best:
            st.markdown("No encontré información suficiente y validada en el corpus para responder esta pregunta.")
            st.markdown("**Siguiente paso:** agende cita con su médico anestesiólogo o use el canal preanestésico del demo: **1234567890**.")
            return
        st.markdown("### Información recuperada del corpus")
        st.write(best["text"])
        st.info("Información educativa para adultos. La valoración e indicaciones individuales corresponden a su médico anestesiólogo.")
        if risk == "síntomas_preoperatorios":
            st.markdown("**Siguiente paso:** contacte a su médico anestesiólogo o al canal preanestésico: **1234567890**.")
        elif risk == "emergencia":
            st.markdown("**Siguiente paso:** marque **123** en Colombia o contacte inmediatamente a la institución.")
        render_source(best)
        if risk == "general" and len(matches) > 1:
            with st.expander("Otros fragmentos recuperados"):
                for item in matches[1:]:
                    st.markdown(f"**{item['fuente']}**")
                    st.write(item["text"])


suggested = st.session_state.pop("suggested_question", None)
question = st.chat_input("Escriba una pregunta general", disabled=not can_search)
if suggested and can_search:
    answer(suggested)
elif question:
    answer(question)
