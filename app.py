import streamlit as st

st.set_page_config(
    page_title="Gestión de Notas de Cambio",
    layout="wide"
)

st.title("Gestión de Notas de Cambio")

st.write("Prototipo funcional de la metodología")
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Gestión de Notas de Cambio",
    page_icon="📋",
    layout="wide"
)

# =========================================================
# DATOS TEMPORALES
# =========================================================

if "consultas" not in st.session_state:
    st.session_state.consultas = []

if "notas_cambio" not in st.session_state:
    st.session_state.notas_cambio = []

if "contador_consulta" not in st.session_state:
    st.session_state.contador_consulta = 1

if "contador_nc" not in st.session_state:
    st.session_state.contador_nc = 1


# =========================================================
# FUNCIONES
# =========================================================

def crear_id_consulta():
    codigo = f"CON-{st.session_state.contador_consulta:03d}"
    st.session_state.contador_consulta += 1
    return codigo


def crear_id_nc():
    codigo = f"NC-{st.session_state.contador_nc:03d}"
    st.session_state.contador_nc += 1
    return codigo


# =========================================================
# MENÚ
# =========================================================

st.sidebar.title("Gestión NC")

pagina = st.sidebar.radio(
    "Navegación",
    [
        "Inicio",
        "Nueva consulta",
        "Consultas",
        "Notas de Cambio",
        "Configuración"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Prototipo metodológico para la gestión de "
    "Notas de Cambio dentro de un entorno BIM."
)


# =========================================================
# INICIO
# =========================================================

if pagina == "Inicio":

    st.title("Gestión de Notas de Cambio")
    st.caption("Panel general del proyecto")

    total_consultas = len(st.session_state.consultas)
    total_nc = len(st.session_state.notas_cambio)

    registradas = sum(
        1 for nc in st.session_state.notas_cambio
        if nc["estado"] == "Registrada"
    )

    cerradas = sum(
        1 for consulta in st.session_state.consultas
        if consulta["estado"] == "Consulta cerrada"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Consultas", total_consultas)

    with col2:
        st.metric("Notas de Cambio", total_nc)

    with col3:
        st.metric("NC registradas", registradas)

    with col4:
        st.metric("Consultas cerradas", cerradas)

    st.divider()

    st.subheader("Actividad reciente")

    if not st.session_state.consultas:
        st.info("Todavía no existen registros.")

    else:
        for consulta in reversed(st.session_state.consultas[-5:]):
            st.write(
                f"**{consulta['id']}** · "
                f"{consulta['titulo']} · "
                f"{consulta['estado']}"
            )


# =========================================================
# NUEVA CONSULTA
# =========================================================

elif pagina == "Nueva consulta":

    st.title("Nueva consulta")

    st.write(
        "Registre una situación detectada que pueda "
        "tener impacto contractual."
    )

    st.caption(
        "En esta etapa la situación todavía no constituye "
        "formalmente una Nota de Cambio."
    )

    with st.form("form_nueva_consulta"):

        titulo = st.text_input(
            "Título *"
        )

        descripcion = st.text_area(
            "Descripción de la situación *"
        )

        disciplina = st.selectbox(
            "Disciplina *",
            [
                "Seleccionar",
                "Arquitectura",
                "Estructura",
                "Sanitaria",
                "Eléctrica",
                "Climatización",
                "Otra"
            ]
        )

        ubicacion = st.text_input(
            "Ubicación *",
            placeholder="Ej.: Fachada Norte - Nivel 2"
        )

        origen = st.selectbox(
            "Origen *",
            [
                "Seleccionar",
                "Obra",
                "Mandante",
                "Diseño",
                "Especialidad",
                "Coordinación",
                "Otro"
            ]
        )

        evidencia = st.file_uploader(
            "Evidencia inicial",
            type=["pdf", "png", "jpg", "jpeg"]
        )

        enviar = st.form_submit_button(
            "Registrar consulta"
        )

        if enviar:

            if (
                not titulo
                or not descripcion
                or disciplina == "Seleccionar"
                or not ubicacion
                or origen == "Seleccionar"
            ):

                st.error(
                    "Complete todos los campos obligatorios."
                )

            else:

                nueva_consulta = {
                    "id": crear_id_consulta(),
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "disciplina": disciplina,
                    "ubicacion": ubicacion,
                    "origen": origen,
                    "evidencia": evidencia.name if evidencia else None,
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "estado": "Pendiente D-01",
                    "decision_d01": None,
                    "respuesta_cierre": None,
                    "nc_generada": None
                }

                st.session_state.consultas.append(
                    nueva_consulta
                )

                st.success(
                    f"Consulta {nueva_consulta['id']} "
                    "registrada correctamente."
                )


# =========================================================
# CONSULTAS
# =========================================================

elif pagina == "Consultas":

    st.title("Consultas registradas")

    st.caption(
        "D-01 · Determinar si corresponde iniciar "
        "una Nota de Cambio."
    )

    if not st.session_state.consultas:

        st.info(
            "Todavía no existen consultas registradas."
        )

    else:

        for i, consulta in enumerate(st.session_state.consultas):

            with st.expander(
                f"{consulta['id']} · "
                f"{consulta['titulo']} · "
                f"{consulta['estado']}"
            ):

                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Disciplina:** {consulta['disciplina']}"
                    )
                    st.write(
                        f"**Ubicación:** {consulta['ubicacion']}"
                    )
                    st.write(
                        f"**Origen:** {consulta['origen']}"
                    )

                with col2:
                    st.write(
                        f"**Fecha:** {consulta['fecha']}"
                    )
                    st.write(
                        f"**Estado:** {consulta['estado']}"
                    )

                    if consulta["evidencia"]:
                        st.write(
                            f"**Evidencia:** "
                            f"{consulta['evidencia']}"
                        )

                st.write("**Descripción**")
                st.write(consulta["descripcion"])

                st.divider()

                if consulta["estado"] == "Pendiente D-01":

                    st.subheader(
                        "D-01 · ¿Corresponde iniciar "
                        "una Nota de Cambio?"
                    )

                    decision = st.radio(
                        "¿La situación puede modificar "
                        "el alcance contractual?",
                        [
                            "Seleccionar",
                            "Sí",
                            "No"
                        ],
                        key=f"decision_{i}"
                    )

                    # -----------------------------------
                    # SI CORRESPONDE NC
                    # -----------------------------------

                    if decision == "Sí":

                        st.info(
                            "Seleccione la clasificación "
                            "preliminar de la Nota de Cambio."
                        )

                        tipo_nc = st.selectbox(
                            "Tipo preliminar",
                            [
                                "Seleccionar",
                                "AO - Aumento de obra",
                                "DO - Disminución de obra",
                                "CM - Cambio de materialidad"
                            ],
                            key=f"tipo_{i}"
                        )

                        if st.button(
                            "Formalizar Nota de Cambio",
                            key=f"crear_nc_{i}"
                        ):

                            if tipo_nc == "Seleccionar":

                                st.error(
                                    "Seleccione el tipo "
                                    "preliminar de NC."
                                )

                            else:

                                nuevo_id_nc = crear_id_nc()

                                nueva_nc = {
                                    "id": nuevo_id_nc,
                                    "consulta_origen": consulta["id"],
                                    "titulo": consulta["titulo"],
                                    "descripcion": consulta["descripcion"],
                                    "tipo": tipo_nc,
                                    "disciplina": consulta["disciplina"],
                                    "ubicacion": consulta["ubicacion"],
                                    "origen": consulta["origen"],
                                    "fecha_registro": datetime.now().strftime(
                                        "%d/%m/%Y %H:%M"
                                    ),
                                    "estado": "Registrada",
                                    "estado_cde": "WIP",
                                    "responsable_actual": "Coordinador NC"
                                }

                                st.session_state.notas_cambio.append(
                                    nueva_nc
                                )

                                consulta["estado"] = (
                                    "Convertida en Nota de Cambio"
                                )

                                consulta["decision_d01"] = "Sí"
                                consulta["nc_generada"] = nuevo_id_nc

                                st.success(
                                    f"Se creó correctamente "
                                    f"{nuevo_id_nc}."
                                )

                                st.rerun()

                    # -----------------------------------
                    # NO CORRESPONDE NC
                    # -----------------------------------

                    elif decision == "No":

                        respuesta = st.text_area(
                            "Respuesta o fundamento de cierre",
                            key=f"respuesta_{i}"
                        )

                        if st.button(
                            "Responder y cerrar consulta",
                            key=f"cerrar_{i}"
                        ):

                            if not respuesta:

                                st.error(
                                    "Debe registrar una respuesta "
                                    "o fundamento."
                                )

                            else:

                                consulta["estado"] = "Consulta cerrada"
                                consulta["decision_d01"] = "No"
                                consulta["respuesta_cierre"] = respuesta

                                st.success(
                                    "La consulta fue cerrada "
                                    "sin generar una Nota de Cambio."
                                )

                                st.rerun()

                else:

                    if consulta["decision_d01"] == "Sí":

                        st.success(
                            f"D-01: Sí corresponde NC. "
                            f"Registro generado: "
                            f"{consulta['nc_generada']}"
                        )

                    elif consulta["decision_d01"] == "No":

                        st.info(
                            "D-01: No corresponde iniciar "
                            "una Nota de Cambio."
                        )

                        st.write(
                            "**Respuesta de cierre:**"
                        )

                        st.write(
                            consulta["respuesta_cierre"]
                        )


# =========================================================
# NOTAS DE CAMBIO
# =========================================================

elif pagina == "Notas de Cambio":

    st.title("Notas de Cambio")

    st.caption(
        "Registro Único de Nota de Cambio (RNC)"
    )

    if not st.session_state.notas_cambio:

        st.info(
            "Todavía no existen Notas de Cambio."
        )

    else:

        for nc in reversed(st.session_state.notas_cambio):

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [2, 1, 1]
                )

                with col1:

                    st.subheader(
                        f"{nc['id']} · {nc['titulo']}"
                    )

                    st.write(
                        f"**Tipo:** {nc['tipo']}"
                    )

                    st.write(
                        f"**Disciplina:** "
                        f"{nc['disciplina']}"
                    )

                    st.write(
                        f"**Ubicación:** "
                        f"{nc['ubicacion']}"
                    )

                with col2:

                    st.metric(
                        "Estado NC",
                        nc["estado"]
                    )

                with col3:

                    st.metric(
                        "Estado CDE",
                        nc["estado_cde"]
                    )

                st.write(
                    f"**Responsable actual:** "
                    f"{nc['responsable_actual']}"
                )

                st.caption(
                    f"Originada desde "
                    f"{nc['consulta_origen']} · "
                    f"{nc['fecha_registro']}"
                )


# =========================================================
# CONFIGURACIÓN
# =========================================================

elif pagina == "Configuración":

    st.title("Configuración")

    st.write(
        "En esta sección se administrarán posteriormente:"
    )

    st.markdown(
        """
        - Usuarios
        - Roles
        - Disciplinas
        - Permisos
        - Parámetros del proyecto
        """
    )
    