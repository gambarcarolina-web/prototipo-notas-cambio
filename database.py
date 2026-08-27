import sqlite3

DB_NAME = "notas_cambio.db"


# =========================================================
# CONEXIÓN
# =========================================================

def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# APOYO PARA ACTUALIZAR LA BASE
# =========================================================

def agregar_columna_si_falta(tabla, columna, tipo):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [
        fila["name"]
        for fila in cursor.fetchall()
    ]

    if columna not in columnas:
        cursor.execute(
            f"ALTER TABLE {tabla} "
            f"ADD COLUMN {columna} {tipo}"
        )

    conn.commit()
    conn.close()


# =========================================================
# CREACIÓN / ACTUALIZACIÓN DE TABLAS
# =========================================================

def crear_tablas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            titulo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            disciplina TEXT NOT NULL,
            ubicacion TEXT NOT NULL,
            origen TEXT NOT NULL,
            evidencia TEXT,
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL,
            decision_d01 TEXT,
            respuesta_cierre TEXT,
            nc_generada TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_cambio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            consulta_origen TEXT,
            titulo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            tipo TEXT NOT NULL,
            disciplina TEXT NOT NULL,
            ubicacion TEXT NOT NULL,
            origen TEXT NOT NULL,
            fecha_registro TEXT NOT NULL,
            estado TEXT NOT NULL,
            estado_cde TEXT NOT NULL,
            responsable_actual TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_nc TEXT NOT NULL,
            fecha TEXT NOT NULL,
            accion TEXT NOT NULL,
            estado_anterior TEXT,
            estado_nuevo TEXT,
            responsable TEXT,
            detalle TEXT
        )
    """)

    conn.commit()
    conn.close()

    # Nuevos campos para PI-01 y D-02
    agregar_columna_si_falta(
        "notas_cambio",
        "originador",
        "TEXT"
    )

    agregar_columna_si_falta(
        "notas_cambio",
        "elemento_afectado",
        "TEXT"
    )

    agregar_columna_si_falta(
        "notas_cambio",
        "evidencia_inicial",
        "TEXT"
    )

    agregar_columna_si_falta(
        "notas_cambio",
        "referencia_fuente",
        "TEXT"
    )

    agregar_columna_si_falta(
        "notas_cambio",
        "decision_d02",
        "TEXT"
    )

    agregar_columna_si_falta(
        "notas_cambio",
        "observacion_d02",
        "TEXT"
    )

    agregar_columna_si_falta(
        "notas_cambio",
        "fecha_d02",
        "TEXT"
    )


# =========================================================
# CONSULTAS
# =========================================================

def crear_consulta(
    titulo,
    descripcion,
    disciplina,
    ubicacion,
    origen,
    evidencia,
    fecha
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO consultas (
            titulo,
            descripcion,
            disciplina,
            ubicacion,
            origen,
            evidencia,
            fecha,
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        titulo,
        descripcion,
        disciplina,
        ubicacion,
        origen,
        evidencia,
        fecha,
        "Pendiente D-01"
    ))

    id_consulta = cursor.lastrowid
    codigo = f"CON-{id_consulta:03d}"

    cursor.execute("""
        UPDATE consultas
        SET codigo = ?
        WHERE id = ?
    """, (
        codigo,
        id_consulta
    ))

    conn.commit()
    conn.close()

    return codigo


def obtener_consultas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM consultas
        ORDER BY id DESC
    """)

    registros = cursor.fetchall()
    conn.close()

    return [
        dict(registro)
        for registro in registros
    ]


def cerrar_consulta(codigo, respuesta):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE consultas
        SET
            estado = ?,
            decision_d01 = ?,
            respuesta_cierre = ?
        WHERE codigo = ?
    """, (
        "Consulta cerrada",
        "No",
        respuesta,
        codigo
    ))

    conn.commit()
    conn.close()


# =========================================================
# CREAR NOTA DE CAMBIO
# =========================================================

def crear_nc_desde_consulta(
    codigo_consulta,
    tipo,
    fecha
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM consultas
        WHERE codigo = ?
    """, (
        codigo_consulta,
    ))

    consulta = cursor.fetchone()

    if consulta is None:
        conn.close()
        return None

    cursor.execute("""
        INSERT INTO notas_cambio (
            consulta_origen,
            titulo,
            descripcion,
            tipo,
            disciplina,
            ubicacion,
            origen,
            fecha_registro,
            estado,
            estado_cde,
            responsable_actual,
            evidencia_inicial
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        consulta["codigo"],
        consulta["titulo"],
        consulta["descripcion"],
        tipo,
        consulta["disciplina"],
        consulta["ubicacion"],
        consulta["origen"],
        fecha,
        "Registrada",
        "WIP",
        "Coordinador NC",
        consulta["evidencia"]
    ))

    id_nc = cursor.lastrowid
    codigo_nc = f"NC-{id_nc:03d}"

    cursor.execute("""
        UPDATE notas_cambio
        SET codigo = ?
        WHERE id = ?
    """, (
        codigo_nc,
        id_nc
    ))

    cursor.execute("""
        UPDATE consultas
        SET
            estado = ?,
            decision_d01 = ?,
            nc_generada = ?
        WHERE codigo = ?
    """, (
        "Convertida en Nota de Cambio",
        "Sí",
        codigo_nc,
        codigo_consulta
    ))

    # Primera entrada del historial
    cursor.execute("""
        INSERT INTO historial (
            codigo_nc,
            fecha,
            accion,
            estado_anterior,
            estado_nuevo,
            responsable,
            detalle
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        codigo_nc,
        fecha,
        "Creación de Nota de Cambio",
        None,
        "Registrada",
        "Coordinador NC",
        f"Nota creada desde {codigo_consulta}"
    ))

    conn.commit()
    conn.close()

    return codigo_nc


# =========================================================
# CONSULTAR NOTAS
# =========================================================

def obtener_notas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM notas_cambio
        ORDER BY id DESC
    """)

    registros = cursor.fetchall()

    conn.close()

    return [
        dict(registro)
        for registro in registros
    ]


def obtener_nota(codigo):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM notas_cambio
        WHERE codigo = ?
    """, (
        codigo,
    ))

    registro = cursor.fetchone()

    conn.close()

    if registro:
        return dict(registro)

    return None


# =========================================================
# PI-01
# =========================================================

def actualizar_pi01(
    codigo,
    originador,
    elemento_afectado,
    evidencia_inicial,
    referencia_fuente
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notas_cambio
        SET
            originador = ?,
            elemento_afectado = ?,
            evidencia_inicial = ?,
            referencia_fuente = ?
        WHERE codigo = ?
    """, (
        originador,
        elemento_afectado,
        evidencia_inicial,
        referencia_fuente,
        codigo
    ))

    conn.commit()
    conn.close()


# =========================================================
# D-02
# =========================================================

def registrar_d02(
    codigo,
    decision,
    observacion,
    responsable_tecnico,
    fecha
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT estado
        FROM notas_cambio
        WHERE codigo = ?
    """, (
        codigo,
    ))

    registro = cursor.fetchone()

    if registro is None:
        conn.close()
        return

    estado_anterior = registro["estado"]

    if decision == "Sí":

        nuevo_estado = "En análisis técnico"
        nuevo_responsable = responsable_tecnico

    else:

        nuevo_estado = "Registrada"
        nuevo_responsable = "Originador"

    cursor.execute("""
        UPDATE notas_cambio
        SET
            decision_d02 = ?,
            observacion_d02 = ?,
            fecha_d02 = ?,
            estado = ?,
            responsable_actual = ?
        WHERE codigo = ?
    """, (
        decision,
        observacion,
        fecha,
        nuevo_estado,
        nuevo_responsable,
        codigo
    ))

    cursor.execute("""
        INSERT INTO historial (
            codigo_nc,
            fecha,
            accion,
            estado_anterior,
            estado_nuevo,
            responsable,
            detalle
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        codigo,
        fecha,
        "Decisión D-02",
        estado_anterior,
        nuevo_estado,
        "Coordinador NC",
        (
            f"Información inicial suficiente: "
            f"{decision}. {observacion}"
        )
    ))

    conn.commit()
    conn.close()


# =========================================================
# HISTORIAL
# =========================================================

def obtener_historial(codigo_nc):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM historial
        WHERE codigo_nc = ?
        ORDER BY id DESC
    """, (
        codigo_nc,
    ))

    registros = cursor.fetchall()

    conn.close()

    return [
        dict(registro)
        for registro in registros
    ]
    