from datetime import datetime
from supabase_client import obtener_supabase


def crear_consulta_supabase(
    proyecto,
    titulo,
    descripcion,
    disciplina,
    ubicacion,
    origen,
    evidencia,
    usuario_id
):
    supabase = obtener_supabase()

    datos = {
        "proyecto": proyecto,
        "titulo": titulo,
        "descripcion": descripcion,
        "disciplina": disciplina,
        "ubicacion": ubicacion,
        "origen": origen,
        "evidencia": evidencia,
        "estado": "Pendiente D-01",
        "creado_por": usuario_id
    }

    respuesta = (
        supabase
        .table("consultas")
        .insert(datos)
        .execute()
    )

    if not respuesta.data:
        raise Exception("No fue posible crear la consulta.")

    registro = respuesta.data[0]

    codigo = f"CON-{registro['id']:03d}"

    (
        supabase
        .table("consultas")
        .update({
            "codigo": codigo
        })
        .eq("id", registro["id"])
        .execute()
    )

    return codigo


def obtener_consultas_supabase(proyecto):

    supabase = obtener_supabase()

    respuesta = (
        supabase
        .table("consultas")
        .select("*")
        .eq("proyecto", proyecto)
        .order("id", desc=True)
        .execute()
    )

    return respuesta.data
    # =========================================================
# CERRAR CONSULTA SIN GENERAR NC
# =========================================================

def cerrar_consulta_supabase(
    proyecto,
    codigo,
    respuesta
):
    supabase = obtener_supabase()

    (
        supabase
        .table("consultas")
        .update({
            "estado": "Consulta cerrada",
            "decision_d01": "No",
            "respuesta_cierre": respuesta
        })
        .eq("proyecto", proyecto)
        .eq("codigo", codigo)
        .execute()
    )


# =========================================================
# CREAR NC DESDE CONSULTA
# =========================================================

def crear_nc_desde_consulta_supabase(
    proyecto,
    codigo_consulta,
    tipo,
    usuario_id
):
    supabase = obtener_supabase()

    # Buscar consulta de origen
    respuesta_consulta = (
        supabase
        .table("consultas")
        .select("*")
        .eq("proyecto", proyecto)
        .eq("codigo", codigo_consulta)
        .single()
        .execute()
    )

    consulta = respuesta_consulta.data

    if not consulta:
        return None

    # Crear Nota de Cambio
    respuesta_nc = (
        supabase
        .table("notas_cambio")
        .insert({
            "proyecto": proyecto,
            "consulta_origen": codigo_consulta,
            "titulo": consulta["titulo"],
            "descripcion": consulta["descripcion"],
            "tipo": tipo,
            "disciplina": consulta["disciplina"],
            "ubicacion": consulta["ubicacion"],
            "origen": consulta["origen"],
            "estado": "Registrada",
            "estado_cde": "WIP",
            "responsable_actual": "Coordinador NC",
            "creado_por": usuario_id
        })
        .execute()
    )

    if not respuesta_nc.data:
        return None

    registro_nc = respuesta_nc.data[0]

    codigo_nc = f"NC-{registro_nc['id']:03d}"

    # Asignar código definitivo
    (
        supabase
        .table("notas_cambio")
        .update({
            "codigo": codigo_nc
        })
        .eq("id", registro_nc["id"])
        .execute()
    )

    # Actualizar consulta de origen
    (
        supabase
        .table("consultas")
        .update({
            "estado": "Convertida en Nota de Cambio",
            "decision_d01": "Sí",
            "nc_generada": codigo_nc
        })
        .eq("proyecto", proyecto)
        .eq("codigo", codigo_consulta)
        .execute()
    )

    # Registrar trazabilidad inicial
    (
        supabase
        .table("historial")
        .insert({
            "codigo_nc": codigo_nc,
            "proyecto": proyecto,
            "accion": "Creación de Nota de Cambio",
            "estado_anterior": None,
            "estado_nuevo": "Registrada",
            "ejecutado_por": usuario_id,
            "rol_ejecutor": "Coordinador NC",
            "detalle": f"Nota creada desde {codigo_consulta}"
        })
        .execute()
    )

    return codigo_nc


# =========================================================
# OBTENER NOTAS DE CAMBIO COMPARTIDAS
# =========================================================

def obtener_notas_supabase(proyecto):

    supabase = obtener_supabase()

    respuesta = (
        supabase
        .table("notas_cambio")
        .select("*")
        .eq("proyecto", proyecto)
        .order("id", desc=True)
        .execute()
    )

    return respuesta.data
    # =========================================================
# OBTENER UNA NOTA DE CAMBIO
# =========================================================

def obtener_nota_supabase(proyecto, codigo):

    supabase = obtener_supabase()

    respuesta = (
        supabase
        .table("notas_cambio")
        .select("*")
        .eq("proyecto", proyecto)
        .eq("codigo", codigo)
        .single()
        .execute()
    )

    return respuesta.data


# =========================================================
# ACTUALIZAR PI-01
# =========================================================

def actualizar_pi01_supabase(
    proyecto,
    codigo,
    originador,
    elemento_afectado,
    evidencia_inicial,
    referencia_fuente
):

    supabase = obtener_supabase()

    (
        supabase
        .table("notas_cambio")
        .update({
            "originador": originador,
            "elemento_afectado": elemento_afectado,
            "evidencia_inicial": evidencia_inicial,
            "referencia_fuente": referencia_fuente
        })
        .eq("proyecto", proyecto)
        .eq("codigo", codigo)
        .execute()
    )


# =========================================================
# REGISTRAR D-02
# =========================================================

def registrar_d02_supabase(
    proyecto,
    codigo,
    decision,
    observacion,
    responsable_tecnico,
    usuario_id,
    rol_usuario
):

    supabase = obtener_supabase()

    nota = obtener_nota_supabase(
        proyecto,
        codigo
    )

    if not nota:
        return False

    estado_anterior = nota["estado"]

    if decision == "Sí":

        nuevo_estado = "En análisis técnico"
        nuevo_responsable = responsable_tecnico

    else:

        nuevo_estado = "Registrada"
        nuevo_responsable = "Originador"

    (
        supabase
        .table("notas_cambio")
        .update({
            "decision_d02": decision,
            "observacion_d02": observacion,
            "fecha_d02": datetime.now().isoformat(),
            "estado": nuevo_estado,
            "responsable_actual": nuevo_responsable
        })
        .eq("proyecto", proyecto)
        .eq("codigo", codigo)
        .execute()
    )

    (
        supabase
        .table("historial")
        .insert({
            "codigo_nc": codigo,
            "proyecto": proyecto,
            "accion": "Decisión D-02",
            "estado_anterior": estado_anterior,
            "estado_nuevo": nuevo_estado,
            "ejecutado_por": usuario_id,
            "rol_ejecutor": rol_usuario,
            "detalle": (
                f"Información inicial suficiente: "
                f"{decision}. {observacion}"
            )
        })
        .execute()
    )

    return True


# =========================================================
# OBTENER HISTORIAL
# =========================================================

def obtener_historial_supabase(
    proyecto,
    codigo_nc
):

    supabase = obtener_supabase()

    respuesta = (
        supabase
        .table("historial")
        .select("*")
        .eq("proyecto", proyecto)
        .eq("codigo_nc", codigo_nc)
        .order("id", desc=True)
        .execute()
    )

    return respuesta.data