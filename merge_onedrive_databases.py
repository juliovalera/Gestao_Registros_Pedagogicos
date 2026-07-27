from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"

MAIN_DB = DATA_DIR / "gestao_registros_ciebp.db"
ONEDRIVE_DB = DATA_DIR / "gestao_registros_ciebp-WIN-MS60197RMTQ.db"

ESPACO_TODOS = "Todos os espaços"
PROFESSOR_TODOS = "Todos os professores"


def current_stamp() -> str:
    import datetime as dt

    return dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def has_column(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    return any(row[1] == column_name for row in conn.execute(f"PRAGMA table_info({table_name})"))


def ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    if not has_column(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]


def backup_file(path: Path, suffix: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"{path.stem}_{suffix}{path.suffix}"
    shutil.copy2(path, target)
    return target


def get_map(conn: sqlite3.Connection, table_name: str, key_col: str = "nome", value_col: str = "id") -> dict[str, int]:
    return {row[key_col]: row[value_col] for row in conn.execute(f"SELECT {value_col}, {key_col} FROM {table_name}").fetchall()}


def merge_reference_spaces(source: sqlite3.Connection, target: sqlite3.Connection) -> None:
    source_rows = rows_to_dicts(source.execute("SELECT nome, descricao, situacao FROM espacos ORDER BY id").fetchall())
    target_map = get_map(target, "espacos")
    for row in source_rows:
        if row["nome"] not in target_map:
            cursor = target.execute(
                "INSERT INTO espacos (nome, descricao, situacao) VALUES (?, ?, ?)",
                (row["nome"], row["descricao"], row["situacao"]),
            )
            target_map[row["nome"]] = int(cursor.lastrowid)


def merge_reference_occurrence_types(source: sqlite3.Connection, target: sqlite3.Connection) -> None:
    source_rows = rows_to_dicts(
        source.execute(
            "SELECT nome, descricao, nivel_gravidade_padrao, situacao FROM tipos_ocorrencia ORDER BY id"
        ).fetchall()
    )
    target_map = get_map(target, "tipos_ocorrencia")
    for row in source_rows:
        if row["nome"] not in target_map:
            cursor = target.execute(
                """
                INSERT INTO tipos_ocorrencia (nome, descricao, nivel_gravidade_padrao, situacao)
                VALUES (?, ?, ?, ?)
                """,
                (row["nome"], row["descricao"], row["nivel_gravidade_padrao"], row["situacao"]),
            )
            target_map[row["nome"]] = int(cursor.lastrowid)


def merge_reference_teachers(source: sqlite3.Connection, target: sqlite3.Connection) -> None:
    target_spaces = get_map(target, "espacos")
    source_rows = rows_to_dicts(
        source.execute(
            """
            SELECT p.*, e.nome AS espaco_principal_nome
            FROM professores p
            LEFT JOIN espacos e ON e.id = p.espaco_principal_id
            ORDER BY p.id
            """
        ).fetchall()
    )
    target_map = get_map(target, "professores", "nome_completo", "id")
    for row in source_rows:
        if row["nome_completo"] in target_map:
            continue
        espaco_principal_id = target_spaces.get(row.get("espaco_principal_nome"))
        cursor = target.execute(
            """
            INSERT INTO professores (
                nome_completo, nome_curto, area_atuacao, espaco_principal_id, situacao, vinculo,
                telefone_institucional, email_institucional, observacoes, data_cadastro, data_atualizacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["nome_completo"],
                row["nome_curto"],
                row["area_atuacao"],
                espaco_principal_id,
                row["situacao"],
                row["vinculo"],
                row["telefone_institucional"],
                row["email_institucional"],
                row["observacoes"],
                row["data_cadastro"],
                row["data_atualizacao"],
            ),
        )
        target_map[row["nome_completo"]] = int(cursor.lastrowid)


def merge_users(source: sqlite3.Connection, target: sqlite3.Connection) -> None:
    target_users = {row["nome_usuario"]: row for row in rows_to_dicts(target.execute("SELECT * FROM usuarios").fetchall())}
    for row in rows_to_dicts(source.execute("SELECT * FROM usuarios ORDER BY id").fetchall()):
        existing = target_users.get(row["nome_usuario"])
        if existing:
            continue
        cursor = target.execute(
            """
            INSERT INTO usuarios (
                nome_completo, nome_usuario, senha_hash, situacao, ultimo_login, data_cadastro, data_atualizacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["nome_completo"],
                row["nome_usuario"],
                row["senha_hash"],
                row["situacao"],
                row["ultimo_login"],
                row["data_cadastro"],
                row["data_atualizacao"],
            ),
        )
        target_users[row["nome_usuario"]] = {"id": int(cursor.lastrowid)}


def record_professor_label(row: sqlite3.Row, supports_all_professors: bool) -> str:
    if supports_all_professors and row["todos_professores"] == "sim":
        return PROFESSOR_TODOS
    return row["professor_nome"] or "-"


def source_inter_signatures(conn: sqlite3.Connection) -> dict[tuple, dict]:
    supports_all_professors = has_column(conn, "intercorrencias", "todos_professores")
    sql = """
        SELECT
            i.*,
            t.nome AS tipo_nome,
            e.nome AS espaco_nome,
            p.nome_completo AS professor_nome
        FROM intercorrencias i
        INNER JOIN tipos_ocorrencia t ON t.id = i.tipo_ocorrencia_id
        INNER JOIN espacos e ON e.id = i.espaco_id
        LEFT JOIN professores p ON p.id = i.professor_relacionado_id
        ORDER BY i.id
    """
    result = {}
    for row in conn.execute(sql).fetchall():
        record = dict(row)
        signature = (
            record["data"],
            record["hora"],
            record["tipo_nome"],
            record["espaco_nome"],
            PROFESSOR_TODOS if (supports_all_professors and record.get("todos_professores") == "sim") else (record.get("professor_nome") or "-"),
            (record["descricao_objetiva"] or "").strip(),
        )
        result[signature] = record
    return result


def source_rotina_signatures(conn: sqlite3.Connection) -> dict[tuple, dict]:
    sql = """
        SELECT
            r.*,
            COALESCE(e.nome, '') AS espaco_nome,
            (
                SELECT GROUP_CONCAT(p.nome_completo, ' | ')
                FROM rotinas_docentes_professores rp
                INNER JOIN professores p ON p.id = rp.professor_id
                WHERE rp.rotina_docente_id = r.id
                ORDER BY rp.ordem
            ) AS professores_nomes
        FROM rotinas_docentes r
        LEFT JOIN espacos e ON e.id = r.espaco_id
        ORDER BY r.id
    """
    result = {}
    for row in conn.execute(sql).fetchall():
        record = dict(row)
        if not record.get("professores_nomes"):
            fallback = conn.execute("SELECT nome_completo FROM professores WHERE id = ?", (record["professor_id"],)).fetchone()
            record["professores_nomes"] = fallback[0] if fallback else ""
        signature = (
            record["data"],
            record.get("hora_inicio") or "",
            record.get("hora_fim") or "",
            record["categoria"],
            record["titulo"],
            (record["descricao_atividade"] or "").strip(),
            record["professores_nomes"],
        )
        result[signature] = record
    return result


def copy_evidences(source: sqlite3.Connection, target: sqlite3.Connection, tipo_registro: str, source_id: int, target_id: int) -> int:
    rows = rows_to_dicts(
        source.execute(
            """
            SELECT nome_arquivo, dados, data_hora_registro
            FROM evidencias_registros
            WHERE tipo_registro = ? AND registro_id = ?
            ORDER BY id
            """,
            (tipo_registro, source_id),
        ).fetchall()
    )
    inserted = 0
    for row in rows:
        target.execute(
            """
            INSERT INTO evidencias_registros (tipo_registro, registro_id, nome_arquivo, dados, data_hora_registro)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tipo_registro, target_id, row["nome_arquivo"], sqlite3.Binary(row["dados"]), row["data_hora_registro"]),
        )
        inserted += 1
    return inserted


def merge_intercorrencias(source: sqlite3.Connection, target: sqlite3.Connection) -> tuple[int, int]:
    target_spaces = get_map(target, "espacos")
    target_teachers = get_map(target, "professores", "nome_completo", "id")
    target_types = get_map(target, "tipos_ocorrencia")
    target_sigs = set(source_inter_signatures(target).keys())
    source_records = source_inter_signatures(source)
    supports_all_professors = has_column(source, "intercorrencias", "todos_professores")

    inserted_records = 0
    inserted_evidences = 0
    for signature, row in source_records.items():
        if signature in target_sigs:
            continue
        professor_name = PROFESSOR_TODOS if (supports_all_professors and row.get("todos_professores") == "sim") else row.get("professor_nome")
        professor_id = None if professor_name in {None, "", PROFESSOR_TODOS} else target_teachers.get(professor_name)
        cursor = target.execute(
            """
            INSERT INTO intercorrencias (
                data, hora, tipo_ocorrencia_id, espaco_id, pessoas_relacionadas, professor_relacionado_id,
                todos_professores, descricao_objetiva, providencias_adotadas, encaminhado_para, nivel_gravidade,
                tags, observacoes, data_hora_registro, data_hora_atualizacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["data"],
                row["hora"],
                target_types[row["tipo_nome"]],
                target_spaces[row["espaco_nome"]],
                row["pessoas_relacionadas"],
                professor_id,
                "sim" if professor_name == PROFESSOR_TODOS else row.get("todos_professores", "não"),
                row["descricao_objetiva"],
                row["providencias_adotadas"],
                row["encaminhado_para"],
                row["nivel_gravidade"],
                row["tags"],
                row["observacoes"],
                row["data_hora_registro"],
                row["data_hora_atualizacao"],
            ),
        )
        target_id = int(cursor.lastrowid)
        inserted_records += 1
        inserted_evidences += copy_evidences(source, target, "intercorrencia", row["id"], target_id)
    return inserted_records, inserted_evidences


def merge_rotinas(source: sqlite3.Connection, target: sqlite3.Connection) -> tuple[int, int, int]:
    target_spaces = get_map(target, "espacos")
    target_teachers = get_map(target, "professores", "nome_completo", "id")
    target_sigs = set(source_rotina_signatures(target).keys())
    source_records = source_rotina_signatures(source)

    inserted_records = 0
    inserted_relations = 0
    inserted_evidences = 0
    for signature, row in source_records.items():
        if signature in target_sigs:
            continue

        source_prof_rows = rows_to_dicts(
            source.execute(
                """
                SELECT rp.ordem, p.nome_completo
                FROM rotinas_docentes_professores rp
                INNER JOIN professores p ON p.id = rp.professor_id
                WHERE rp.rotina_docente_id = ?
                ORDER BY rp.ordem
                """,
                (row["id"],),
            ).fetchall()
        )
        if source_prof_rows:
            professor_names = [item["nome_completo"] for item in source_prof_rows]
        else:
            fallback = source.execute("SELECT nome_completo FROM professores WHERE id = ?", (row["professor_id"],)).fetchone()
            professor_names = [fallback[0]] if fallback else []
        mapped_professor_ids = [target_teachers[name] for name in professor_names if name in target_teachers]
        if not mapped_professor_ids:
            continue

        primary_professor_id = mapped_professor_ids[0]
        espaco_id = target_spaces.get(row["espaco_nome"]) if row.get("espaco_nome") else None
        cursor = target.execute(
            """
            INSERT INTO rotinas_docentes (
                data, hora_inicio, hora_fim, categoria, professor_id, espaco_id, turma_ou_publico,
                titulo, descricao_atividade, objetivos, recursos_utilizados, encaminhamentos, tags,
                observacoes, data_hora_registro, data_hora_atualizacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["data"],
                row["hora_inicio"],
                row["hora_fim"],
                row["categoria"],
                primary_professor_id,
                espaco_id,
                row["turma_ou_publico"],
                row["titulo"],
                row["descricao_atividade"],
                row["objetivos"],
                row["recursos_utilizados"],
                row["encaminhamentos"],
                row["tags"],
                row["observacoes"],
                row["data_hora_registro"],
                row["data_hora_atualizacao"],
            ),
        )
        target_id = int(cursor.lastrowid)
        inserted_records += 1

        for ordem, professor_id in enumerate(mapped_professor_ids):
            target.execute(
                """
                INSERT INTO rotinas_docentes_professores (rotina_docente_id, professor_id, ordem)
                VALUES (?, ?, ?)
                """,
                (target_id, professor_id, ordem),
            )
            inserted_relations += 1
        inserted_evidences += copy_evidences(source, target, "rotina_docente", row["id"], target_id)
    return inserted_records, inserted_relations, inserted_evidences


def main() -> None:
    if not MAIN_DB.exists():
        raise FileNotFoundError(f"Banco principal não encontrado: {MAIN_DB}")
    if not ONEDRIVE_DB.exists():
        raise FileNotFoundError(f"Banco do OneDrive não encontrado: {ONEDRIVE_DB}")

    stamp = current_stamp()
    main_backup = backup_file(MAIN_DB, f"antes_merge_{stamp}")
    onedrive_backup = backup_file(ONEDRIVE_DB, f"fonte_merge_{stamp}")

    source = sqlite3.connect(ONEDRIVE_DB)
    source.row_factory = sqlite3.Row
    target = sqlite3.connect(MAIN_DB)
    target.row_factory = sqlite3.Row
    target.execute("PRAGMA foreign_keys = ON")

    try:
        target.execute("BEGIN IMMEDIATE")
        ensure_column(target, "intercorrencias", "todos_professores", "TEXT NOT NULL DEFAULT 'não'")
        merge_reference_spaces(source, target)
        merge_reference_occurrence_types(source, target)
        merge_reference_teachers(source, target)
        merge_users(source, target)

        inter_count, inter_evid = merge_intercorrencias(source, target)
        rot_count, rot_rel_count, rot_evid = merge_rotinas(source, target)

        target.commit()
        print("MERGE_OK")
        print(f"BACKUP_MAIN={main_backup}")
        print(f"BACKUP_SOURCE={onedrive_backup}")
        print(f"INTERCORRENCIAS_INSERIDAS={inter_count}")
        print(f"ROTINAS_INSERIDAS={rot_count}")
        print(f"RELACOES_ROTINAS_INSERIDAS={rot_rel_count}")
        print(f"EVIDENCIAS_INTER_INSERIDAS={inter_evid}")
        print(f"EVIDENCIAS_ROTINAS_INSERIDAS={rot_evid}")
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    main()
