import streamlit as st
from datetime import datetime
from supabase_client import obtener_supabase

from database import (
    crear_tablas,
    crear_consulta,
    obtener_consultas,
    cerrar_consulta,
    crear_nc_desde_consulta,
    obtener_notas,
    obtener_nota,
    actualizar_pi01,
    registrar_d02,
    obtener_historial
)
from supabase_database import (
    crear_consulta_supabase,
    obtener_consultas_supabase,
    cerrar_consulta_supabase,
    crear_nc_desde_consulta_supabase,
    obtener_notas_supabase,
    obtener_nota_supabase,
    actualizar_pi01_supabase,
    registrar_d02_supabase,
    obtener_historial_supabase
)

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Gestión de Notas de Cambio",
    page_icon="📋",
    layout="wide"
)

crear_tablas()
# =========================================================
# AUTENTICACIÓN MULTIUSUARIO
# =========================================================

supabase = obtener_supabase()

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "perfil" not in st.session_state:
    st.session_state.perfil = None


def iniciar_sesion(email, password):

    try:
        respuesta = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        usuario = respuesta.user

        if usuario is None:
            return False, "No fue posible iniciar sesión."

        perfil_respuesta = (
            supabase
            .table("perfiles")
            .select("*")
            .eq("id", str(usuario.id))
            .single()
            .execute()
        )

        perfil = perfil_respuesta.data

        if not perfil:
            supabase.auth.sign_out()
            return False, "El usuario no posee un perfil configurado."

        if not perfil["activo"]:
            supabase.auth.sign_out()
            return False, "El usuario se encuentra desactivado."

        st.session_state.usuario = {
            "id": str(usuario.id),
            "email": usuario.email
        }

        st.session_state.perfil = perfil

        return True, None

    except Exception as error:
        return False, str(error)


def cerrar_sesion():

    try:
        supabase.auth.sign_out()
    except:
        pass

    st.session_state.usuario = None
    st.session_state.perfil = None

    st.rerun()


# =========================================================
# LOGIN
# =========================================================

if st.session_state.usuario is None:

    st.title("Gestión de Notas de Cambio")

    st.subheader("Acceso al sistema")

    st.caption(
        "Ingrese con las credenciales asignadas al proyecto."
    )

    with st.form("form_login"):

        email = st.text_input(
            "Correo electrónico"
        )

        password = st.text_input(
            "Contraseña",
            type="password"
        )

        ingresar = st.form_submit_button(
            "Iniciar sesión",
            type="primary"
        )

        if ingresar:

            if not email or not password:

                st.error(
                    "Debe ingresar correo electrónico y contraseña."
                )

            else:

                correcto, error = iniciar_sesion(
                    email,
                    password
                )

                if correcto:
                    st.rerun()

                else:
                    st.error(
                        f"No fue posible iniciar sesión: {error}"
                    )

    st.stop()

# =========================================================
# VARIABLES DE NAVEGACIÓN
# =========================================================

if "nc_seleccionada" not in st.session_state:
    st.session_state.nc_seleccionada = None


# =========================================================
# MENÚ LATERAL
# =========================================================

st.sidebar.title("Gestión NC")
perfil = st.session_state.perfil
usuario = st.session_state.usuario

st.sidebar.success(
    f"👤 {perfil['nombre']}"
)

st.sidebar.write(
    f"**Rol:** {perfil['rol']}"
)

st.sidebar.write(
    f"**Proyecto:** {perfil['proyecto']}"
)

st.sidebar.caption(
    usuario["email"]
)

if st.sidebar.button(
    "Cerrar sesión"
):
    cerrar_sesion()

st.sidebar.divider()

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
    "Prototipo metodológico para la gestión "
    "de Notas de Cambio dentro de un entorno BIM."
)

# =========================================================
# INICIO
# =========================================================

if pagina == "Inicio":

    st.title("Gestión de Notas de Cambio")
    st.caption("Panel general del proyecto")

    consultas = obtener_consultas_supabase(
        st.session_state.perfil["proyecto"]
    )

    notas = obtener_notas_supabase(
        st.session_state.perfil["proyecto"]
    )

    total_consultas = len(consultas)
    total_nc = len(notas)

    pendientes_d01 = sum(
        1 for c in consultas
        if c["estado"] == "Pendiente D-01"
    )

    en_analisis_tecnico = sum(
        1 for nc in notas
        if nc["estado"] == "En análisis técnico"
    )

    para_decision = sum(
        1 for nc in notas
        if nc["estado"] == "Para decisión"
    )

    cerradas = sum(
        1 for nc in notas
        if nc["estado"] == "Cerrada"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Consultas", total_consultas)

    with col2:
        st.metric("Pendientes D-01", pendientes_d01)

    with col3:
        st.metric("Notas de Cambio", total_nc)

    with col4:
        st.metric("Análisis técnico", en_analisis_tecnico)

    with col5:
        st.metric("Cerradas", cerradas)

    st.divider()

    st.subheader("Actividad reciente")

    if not notas:
        st.info("Todavía no existen Notas de Cambio.")

    else:
        for nc in notas[:5]:
            st.write(
                f"📋 **{nc['codigo']}** · "
                f"{nc['titulo']} · "
                f"{nc['estado']}"
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

    st.divider()

    with st.form("form_nueva_consulta"):

        titulo = st.text_input("Título *")

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

                nombre_evidencia = (
                    evidencia.name if evidencia else None
                )

                fecha = datetime.now().strftime(
                    "%d/%m/%Y %H:%M"
                )

                codigo = crear_consulta_supabase(
                    st.session_state.perfil["proyecto"],
                    titulo,
                    descripcion,
                    disciplina,
                    ubicacion,
                    origen,
                    nombre_evidencia,
                    st.session_state.usuario["id"]
                )

                st.success(
                    f"Consulta {codigo} registrada correctamente."
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

    st.divider()

    consultas = obtener_consultas_supabase(
        st.session_state.perfil["proyecto"]
    )

    if not consultas:

        st.info(
            "Todavía no existen consultas registradas."
        )

    else:

        for consulta in consultas:

            with st.expander(
                f"{consulta['codigo']} · "
                f"{consulta['titulo']} · "
                f"{consulta['estado']}"
            ):

                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Disciplina:** "
                        f"{consulta['disciplina']}"
                    )

                    st.write(
                        f"**Ubicación:** "
                        f"{consulta['ubicacion']}"
                    )

                    st.write(
                        f"**Origen:** "
                        f"{consulta['origen']}"
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

                # =========================================
                # D-01
                # =========================================

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
                        key=f"d01_{consulta['codigo']}"
                    )

                    if decision == "Sí":

                        tipo_nc = st.selectbox(
                            "Tipo preliminar de Nota de Cambio",
                            [
                                "Seleccionar",
                                "AO - Aumento de obra",
                                "DO - Disminución de obra",
                                "CM - Cambio de materialidad"
                            ],
                            key=f"tipo_{consulta['codigo']}"
                        )

                        if st.button(
                            "Formalizar Nota de Cambio",
                            key=f"crear_{consulta['codigo']}",
                            type="primary"
                        ):

                            if tipo_nc == "Seleccionar":

                                st.error(
                                    "Seleccione el tipo de NC."
                                )

                            else:

                                fecha = datetime.now().strftime(
                                    "%d/%m/%Y %H:%M"
                                )

                                codigo_nc = crear_nc_desde_consulta_supabase(
                                    st.session_state.perfil["proyecto"],
                                    consulta["codigo"],
                                    tipo_nc,
                                    st.session_state.usuario["id"]
                                )

                                st.success(
                                    f"Se creó {codigo_nc}."
                                )

                                st.rerun()

                    elif decision == "No":

                        respuesta = st.text_area(
                            "Respuesta o fundamento de cierre *",
                            key=f"respuesta_{consulta['codigo']}"
                        )

                        if st.button(
                            "Responder y cerrar consulta",
                            key=f"cerrar_{consulta['codigo']}"
                        ):

                            if not respuesta:

                                st.error(
                                    "Debe registrar un fundamento."
                                )

                            else:

                                cerrar_consulta_supabase(
                                    st.session_state.perfil["proyecto"],
                                    consulta["codigo"],
                                    respuesta
                                )

                                st.rerun()

                else:

                    if consulta["decision_d01"] == "Sí":

                        st.success(
                            "D-01 · Corresponde iniciar "
                            "una Nota de Cambio."
                        )

                        st.write(
                            f"**Registro generado:** "
                            f"{consulta['nc_generada']}"
                        )

                    elif consulta["decision_d01"] == "No":

                        st.info(
                            "D-01 · No corresponde iniciar NC."
                        )

                        st.write(
                            consulta["respuesta_cierre"]
                        )


# =========================================================
# NOTAS DE CAMBIO
# =========================================================

elif pagina == "Notas de Cambio":

    # =====================================================
    # LISTADO DE NC
    # =====================================================

    if st.session_state.nc_seleccionada is None:

        st.title("Notas de Cambio")

        st.caption(
            "Registro Único de Nota de Cambio (RNC)"
        )

        st.divider()

        notas = obtener_notas_supabase(
            st.session_state.perfil["proyecto"]
        )

        if not notas:

            st.info(
                "Todavía no existen Notas de Cambio."
            )

        else:

            for nc in notas:

                with st.container(border=True):

                    col1, col2, col3, col4 = st.columns(
                        [3, 1.3, 1.1, 1.2]
                    )

                    with col1:

                        st.subheader(
                            f"{nc['codigo']} · "
                            f"{nc['titulo']}"
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

                        st.write("**Estado NC**")

                        st.info(
                            nc["estado"]
                        )

                    with col3:

                        st.write("**Estado CDE**")

                        st.info(
                            nc["estado_cde"]
                        )

                    with col4:

                        st.write("**Responsable**")

                        st.write(
                            nc["responsable_actual"]
                        )

                        if st.button(
                            "Abrir expediente",
                            key=f"abrir_{nc['codigo']}",
                            type="primary"
                        ):

                            st.session_state.nc_seleccionada = (
                                nc["codigo"]
                            )

                            st.rerun()


    # =====================================================
    # EXPEDIENTE INDIVIDUAL
    # =====================================================

    else:

        codigo_nc = st.session_state.nc_seleccionada

        nc = obtener_nota_supabase(
            st.session_state.perfil["proyecto"],
            codigo_nc
        )

        if nc is None:

            st.error(
                "No fue posible encontrar la Nota de Cambio."
            )

        else:

            if st.button("← Volver al listado"):

                st.session_state.nc_seleccionada = None
                st.rerun()

            st.title(
                f"{nc['codigo']} · {nc['titulo']}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Estado NC",
                    nc["estado"]
                )

            with col2:
                st.metric(
                    "Estado CDE",
                    nc["estado_cde"]
                )

            with col3:
                st.metric(
                    "Responsable actual",
                    nc["responsable_actual"]
                )

            st.caption(
                f"Registro generado desde "
                f"{nc['consulta_origen']} · "
                f"{nc['fecha_registro']}"
            )

            st.divider()

            tabs = st.tabs(
                [
                    "Resumen",
                    "PI-01",
                    "PI-02",
                    "PI-03",
                    "PI-04",
                    "BIM",
                    "Documentos",
                    "Historial"
                ]
            )

            # =================================================
            # RESUMEN
            # =================================================

            with tabs[0]:

                st.subheader(
                    "Resumen de la Nota de Cambio"
                )

                col_a, col_b = st.columns(2)

                with col_a:

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

                    st.write(
                        f"**Origen:** "
                        f"{nc['origen']}"
                    )

                with col_b:

                    st.write(
                        f"**Consulta de origen:** "
                        f"{nc['consulta_origen']}"
                    )

                    st.write(
                        f"**Fecha de registro:** "
                        f"{nc['fecha_registro']}"
                    )

                    st.write(
                        f"**Responsable actual:** "
                        f"{nc['responsable_actual']}"
                    )

                st.write("**Descripción**")

                st.info(
                    nc["descripcion"]
                )


            # =================================================
            # PI-01
            # =================================================

            with tabs[1]:

                st.subheader(
                    "PI-01 · Registro inicial"
                )

                st.write(
                    "Información mínima necesaria para "
                    "formalizar y derivar la Nota de Cambio."
                )

                st.divider()

                # ---------------------------------------------
                # DATOS YA OBTENIDOS DEL REGISTRO
                # ---------------------------------------------

                st.markdown("#### Identificación")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.text_input(
                        "ID",
                        value=nc["codigo"],
                        disabled=True
                    )

                with c2:
                    st.text_input(
                        "Tipo",
                        value=nc["tipo"],
                        disabled=True
                    )

                with c3:
                    st.text_input(
                        "Fecha",
                        value=nc["fecha_registro"],
                        disabled=True
                    )

                st.text_input(
                    "Título",
                    value=nc["titulo"],
                    disabled=True
                )

                st.text_area(
                    "Descripción",
                    value=nc["descripcion"],
                    disabled=True
                )

                c4, c5 = st.columns(2)

                with c4:
                    st.text_input(
                        "Disciplina",
                        value=nc["disciplina"],
                        disabled=True
                    )

                with c5:
                    st.text_input(
                        "Ubicación",
                        value=nc["ubicacion"],
                        disabled=True
                    )

                st.divider()

                # ---------------------------------------------
                # COMPLETAR PI-01
                # ---------------------------------------------

                if nc["estado"] == "Registrada":

                    st.markdown(
                        "#### Completar antecedentes iniciales"
                    )

                    with st.form(
                        f"pi01_{nc['codigo']}"
                    ):

                        originador = st.text_input(
                            "Originador *",
                            value=nc["originador"] or ""
                        )

                        elemento_afectado = st.text_input(
                            "Elemento afectado",
                            value=nc["elemento_afectado"] or "",
                            placeholder=(
                                "Ej.: Revestimiento fachada norte"
                            )
                        )

                        evidencia_inicial = st.text_input(
                            "Evidencia inicial *",
                            value=nc["evidencia_inicial"] or "",
                            placeholder=(
                                "Ej.: Fotografía, croquis o documento"
                            )
                        )

                        referencia_fuente = st.text_input(
                            "Documento / modelo relacionado",
                            value=nc["referencia_fuente"] or "",
                            placeholder=(
                                "Ej.: Plano ARQ-105 Rev.01"
                            )
                        )

                        guardar_pi01 = st.form_submit_button(
                            "Guardar PI-01",
                            type="primary"
                        )

                        if guardar_pi01:

                            actualizar_pi01_supabase(
                                st.session_state.perfil["proyecto"],
                                nc["codigo"],
                                originador,
                                elemento_afectado,
                                evidencia_inicial,
                                referencia_fuente
                            )

                            st.success(
                                "PI-01 actualizado correctamente."
                            )

                            st.rerun()

                else:

                    st.success(
                        "PI-01 finalizado para esta etapa."
                    )

                    st.write(
                        f"**Originador:** "
                        f"{nc['originador'] or '—'}"
                    )

                    st.write(
                        f"**Elemento afectado:** "
                        f"{nc['elemento_afectado'] or '—'}"
                    )

                    st.write(
                        f"**Evidencia inicial:** "
                        f"{nc['evidencia_inicial'] or '—'}"
                    )

                    st.write(
                        f"**Referencia fuente:** "
                        f"{nc['referencia_fuente'] or '—'}"
                    )

                # ---------------------------------------------
                # CONTROL DE COMPLETITUD
                # ---------------------------------------------

                st.divider()

                st.markdown(
                    "#### Control de completitud PI-01"
                )

                faltantes = []

                if not nc["codigo"]:
                    faltantes.append("ID")

                if not nc["titulo"]:
                    faltantes.append("Título")

                if not nc["descripcion"]:
                    faltantes.append("Descripción")

                if not nc["tipo"]:
                    faltantes.append("Tipo")

                if not nc["disciplina"]:
                    faltantes.append("Disciplina")

                if not nc["ubicacion"]:
                    faltantes.append("Ubicación")

                if not nc["originador"]:
                    faltantes.append("Originador")

                if not nc["evidencia_inicial"]:
                    faltantes.append("Evidencia inicial")

                if faltantes:

                    st.warning(
                        "PI-01 aún presenta antecedentes "
                        "obligatorios pendientes:"
                    )

                    for campo in faltantes:
                        st.write(f"⚠️ {campo}")

                else:

                    st.success(
                        "PI-01 contiene la información "
                        "mínima obligatoria."
                    )

                # ---------------------------------------------
                # D-02
                # ---------------------------------------------

                if nc["estado"] == "Registrada":

                    st.divider()

                    st.subheader(
                        "D-02 · ¿Existe información mínima "
                        "suficiente para iniciar el análisis?"
                    )

                    decision_d02 = st.radio(
                        "Decisión del Coordinador NC",
                        [
                            "Seleccionar",
                            "Sí",
                            "No"
                        ],
                        key=f"d02_{nc['codigo']}"
                    )

                    observacion_d02 = st.text_area(
                        "Observación / fundamento",
                        key=f"obs_d02_{nc['codigo']}"
                    )

                    responsable_tecnico = st.selectbox(
                        "Responsable técnico",
                        [
                            "Seleccionar",
                            "Arquitectura",
                            "Ingeniería Estructural",
                            "Especialidad Sanitaria",
                            "Especialidad Eléctrica",
                            "Especialidad Climatización",
                            "Otro especialista"
                        ],
                        key=f"resp_tecnico_{nc['codigo']}"
                    )

                    if st.button(
                        "Registrar decisión D-02",
                        key=f"registrar_d02_{nc['codigo']}",
                        type="primary"
                    ):

                        if decision_d02 == "Seleccionar":

                            st.error(
                                "Debe seleccionar una decisión."
                            )

                        elif decision_d02 == "Sí" and faltantes:

                            st.error(
                                "No es posible aprobar D-02. "
                                "PI-01 posee información "
                                "obligatoria pendiente."
                            )

                        elif (
                            decision_d02 == "Sí"
                            and responsable_tecnico == "Seleccionar"
                        ):

                            st.error(
                                "Debe asignar un responsable técnico."
                            )

                        elif (
                            decision_d02 == "No"
                            and not observacion_d02
                        ):

                            st.error(
                                "Debe indicar qué antecedentes "
                                "deben complementarse."
                            )

                        else:

                            fecha = datetime.now().strftime(
                                "%d/%m/%Y %H:%M"
                            )

                            registrar_d02_supabase(
                                st.session_state.perfil["proyecto"],
                                nc["codigo"],
                                decision_d02,
                                observacion_d02,
                                responsable_tecnico,
                                st.session_state.usuario["id"],
                                st.session_state.perfil["rol"]
                            )

                            st.success(
                                "Decisión D-02 registrada."
                            )

                            st.rerun()


            # =================================================
            # PI-02
            # =================================================

            with tabs[2]:

                st.subheader(
                    "PI-02 · Antecedentes para solución técnica"
                )

                if nc["estado"] == "En análisis técnico":

                    st.success(
                        "Esta etapa se encuentra habilitada."
                    )

                    st.info(
                        "En el siguiente paso construiremos "
                        "los campos y D-03."
                    )

                else:

                    st.warning(
                        "PI-02 se habilita cuando D-02 "
                        "confirma que la información inicial "
                        "es suficiente."
                    )


            # =================================================
            # PI-03
            # =================================================

            with tabs[3]:

                st.subheader(
                    "PI-03 · Antecedentes contractuales "
                    "y económicos"
                )

                st.info(
                    "Se habilitará posteriormente."
                )


            # =================================================
            # PI-04
            # =================================================

            with tabs[4]:

                st.subheader(
                    "PI-04 · Decisión y cierre"
                )

                st.info(
                    "Se habilitará posteriormente."
                )


            # =================================================
            # BIM
            # =================================================

            with tabs[5]:

                st.subheader(
                    "Vinculación BIM"
                )

                st.write(
                    "Posteriormente vincularemos la NC "
                    "con el modelo y elemento BIM afectado."
                )

                st.text_input(
                    "Modelo",
                    disabled=True,
                    placeholder="Pendiente"
                )

                st.text_input(
                    "IFC GUID",
                    disabled=True,
                    placeholder="Pendiente"
                )


            # =================================================
            # DOCUMENTOS
            # =================================================

            with tabs[6]:

                st.subheader(
                    "Documentos vinculados"
                )

                st.info(
                    "La gestión documental y versiones "
                    "será incorporada posteriormente."
                )


            # =================================================
            # HISTORIAL
            # =================================================

            with tabs[7]:

                st.subheader(
                    "Historial y trazabilidad"
                )

                historial = obtener_historial_supabase(
                    st.session_state.perfil["proyecto"],
                    nc["codigo"]
                )

                if not historial:

                    st.info(
                        "Todavía no existen acciones "
                        "registradas en el historial."
                    )

                else:

                    for evento in historial:

                        with st.container(border=True):

                            st.write(
                                f"**{evento['accion']}**"
                            )

                            st.caption(
                                evento["fecha"]
                            )

                            st.write(
                                f"**Estado anterior:** "
                                f"{evento['estado_anterior'] or '—'}"
                            )

                            st.write(
                                f"**Estado nuevo:** "
                                f"{evento['estado_nuevo'] or '—'}"
                            )

                            st.write(
                                f"**Responsable:** "
                                f"{evento['responsable'] or '—'}"
                            )

                            if evento["detalle"]:
                                st.write(
                                    f"**Detalle:** "
                                    f"{evento['detalle']}"
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
    