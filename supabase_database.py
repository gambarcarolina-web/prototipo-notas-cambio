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
    