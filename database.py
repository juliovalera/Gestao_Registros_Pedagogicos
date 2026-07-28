"""Camada de acesso ao banco SQLite local."""

from __future__ import annotations

import datetime as dt
import shutil
import sqlite3
from pathlib import Path

from models import (
    ESPACOS_INICIAIS,
    ESPACO_TODOS,
    GRAVIDADE_ORDEM,
    PROFESSORES_EXEMPLO,
    PROFESSOR_TODOS,
    ROTINA_DOCENTE_CATEGORIAS,
    TIPOS_OCORRENCIA_INICIAIS,
)
from utils import (
    BACKUP_DIR,
    DB_PATH,
    clean_optional,
    current_date_iso,
    current_time_hm,
    current_timestamp,
    ensure_directories,
    hash_password,
    verify_password,
)


class DatabaseManager:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or DB_PATH)

    def connect(self) -> sqlite3.Connection:
        ensure_directories()
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize_database(self) -> None:
        ensure_directories()
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    chave TEXT PRIMARY KEY,
                    valor TEXT
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_completo TEXT NOT NULL,
                    nome_usuario TEXT NOT NULL UNIQUE,
                    senha_hash TEXT NOT NULL,
                    situacao TEXT NOT NULL DEFAULT 'ativo',
                    ultimo_login TEXT,
                    data_cadastro TEXT NOT NULL,
                    data_atualizacao TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS espacos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    descricao TEXT,
                    situacao TEXT NOT NULL DEFAULT 'ativo'
                );

                CREATE TABLE IF NOT EXISTS professores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_completo TEXT NOT NULL,
                    nome_curto TEXT NOT NULL,
                    area_atuacao TEXT,
                    espaco_principal_id INTEGER,
                    situacao TEXT NOT NULL DEFAULT 'ativo',
                    vinculo TEXT NOT NULL DEFAULT 'efetivo',
                    telefone_institucional TEXT,
                    email_institucional TEXT,
                    observacoes TEXT,
                    data_cadastro TEXT NOT NULL,
                    data_atualizacao TEXT NOT NULL,
                    FOREIGN KEY (espaco_principal_id) REFERENCES espacos(id) ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tipos_ocorrencia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    descricao TEXT,
                    nivel_gravidade_padrao TEXT,
                    situacao TEXT NOT NULL DEFAULT 'ativo'
                );

                CREATE TABLE IF NOT EXISTS intercorrencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    tipo_ocorrencia_id INTEGER NOT NULL,
                    espaco_id INTEGER NOT NULL,
                    contexto_atuacao TEXT,
                    pessoas_relacionadas TEXT,
                    professor_relacionado_id INTEGER,
                    descricao_objetiva TEXT NOT NULL,
                    providencias_adotadas TEXT,
                    encaminhado_para TEXT,
                    nivel_gravidade TEXT,
                    tags TEXT,
                    observacoes TEXT,
                    data_hora_registro TEXT NOT NULL,
                    data_hora_atualizacao TEXT NOT NULL,
                    FOREIGN KEY (tipo_ocorrencia_id) REFERENCES tipos_ocorrencia(id) ON UPDATE CASCADE,
                    FOREIGN KEY (espaco_id) REFERENCES espacos(id) ON UPDATE CASCADE,
                    FOREIGN KEY (professor_relacionado_id) REFERENCES professores(id) ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ausencias_professores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    ausencia_integral TEXT NOT NULL DEFAULT 'não',
                    hora_inicio TEXT,
                    hora_fim TEXT,
                    professor_id INTEGER NOT NULL,
                    espaco_id INTEGER NOT NULL,
                    contexto_atuacao TEXT,
                    turma_ou_grupo_afetado TEXT,
                    tipo_ausencia TEXT NOT NULL,
                    havia_comunicacao_previa TEXT,
                    houve_substituicao TEXT,
                    impacto_observado TEXT,
                    providencia_tomada TEXT,
                    observacoes TEXT,
                    data_hora_registro TEXT NOT NULL,
                    data_hora_atualizacao TEXT NOT NULL,
                    FOREIGN KEY (professor_id) REFERENCES professores(id) ON UPDATE CASCADE,
                    FOREIGN KEY (espaco_id) REFERENCES espacos(id) ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS rotinas_docentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    hora_inicio TEXT,
                    hora_fim TEXT,
                    categoria TEXT NOT NULL,
                    professor_id INTEGER NOT NULL,
                    espaco_id INTEGER,
                    contexto_atuacao TEXT,
                    turma_ou_publico TEXT,
                    titulo TEXT NOT NULL,
                    descricao_atividade TEXT NOT NULL,
                    objetivos TEXT,
                    recursos_utilizados TEXT,
                    encaminhamentos TEXT,
                    tags TEXT,
                    observacoes TEXT,
                    data_hora_registro TEXT NOT NULL,
                    data_hora_atualizacao TEXT NOT NULL,
                    FOREIGN KEY (professor_id) REFERENCES professores(id) ON UPDATE CASCADE,
                    FOREIGN KEY (espaco_id) REFERENCES espacos(id) ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS rotinas_docentes_professores (
                    rotina_docente_id INTEGER NOT NULL,
                    professor_id INTEGER NOT NULL,
                    ordem INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (rotina_docente_id, professor_id),
                    FOREIGN KEY (rotina_docente_id) REFERENCES rotinas_docentes(id) ON DELETE CASCADE,
                    FOREIGN KEY (professor_id) REFERENCES professores(id) ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS evidencias_registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_registro TEXT NOT NULL,
                    registro_id INTEGER NOT NULL,
                    nome_arquivo TEXT NOT NULL,
                    dados BLOB NOT NULL,
                    data_hora_registro TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_intercorrencias_data ON intercorrencias(data);
                CREATE INDEX IF NOT EXISTS idx_intercorrencias_tipo ON intercorrencias(tipo_ocorrencia_id);
                CREATE INDEX IF NOT EXISTS idx_intercorrencias_professor ON intercorrencias(professor_relacionado_id);
                CREATE INDEX IF NOT EXISTS idx_intercorrencias_espaco ON intercorrencias(espaco_id);
                CREATE INDEX IF NOT EXISTS idx_ausencias_data ON ausencias_professores(data);
                CREATE INDEX IF NOT EXISTS idx_ausencias_professor ON ausencias_professores(professor_id);
                CREATE INDEX IF NOT EXISTS idx_ausencias_espaco ON ausencias_professores(espaco_id);
                CREATE INDEX IF NOT EXISTS idx_rotinas_data ON rotinas_docentes(data);
                CREATE INDEX IF NOT EXISTS idx_rotinas_professor ON rotinas_docentes(professor_id);
                CREATE INDEX IF NOT EXISTS idx_rotinas_espaco ON rotinas_docentes(espaco_id);
                CREATE INDEX IF NOT EXISTS idx_rotinas_categoria ON rotinas_docentes(categoria);
                CREATE INDEX IF NOT EXISTS idx_rotinas_rel_professor ON rotinas_docentes_professores(professor_id);
                CREATE INDEX IF NOT EXISTS idx_evidencias_tipo_registro ON evidencias_registros(tipo_registro, registro_id);
                """
            )
            self._ensure_column(conn, "ausencias_professores", "ausencia_integral", "TEXT NOT NULL DEFAULT 'não'")
            self._ensure_column(conn, "intercorrencias", "todos_professores", "TEXT NOT NULL DEFAULT 'não'")
            self._ensure_column(conn, "intercorrencias", "contexto_atuacao", "TEXT")
            self._ensure_column(conn, "ausencias_professores", "contexto_atuacao", "TEXT")
            self._ensure_column(conn, "rotinas_docentes", "contexto_atuacao", "TEXT")
            self._seed_reference_data(conn)
            self._seed_sample_data(conn)
            self._migrate_rotinas_docentes_professores(conn)

    def _ensure_column(self, conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
        if column_name not in columns:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def _migrate_rotinas_docentes_professores(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO rotinas_docentes_professores (rotina_docente_id, professor_id, ordem)
            SELECT id, professor_id, 0
            FROM rotinas_docentes
            WHERE professor_id IS NOT NULL
            """
        )

    def has_any_user(self) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()
            return bool(row["total"])

    def create_user(self, full_name: str, username: str, password: str) -> int:
        if self.has_any_user():
            existing = self.get_user_by_username(username)
            if existing:
                raise ValueError("Já existe um usuário com esse nome de login.")
        now = current_timestamp()
        username = username.strip().lower()
        full_name = full_name.strip()
        if not full_name or not username or not password:
            raise ValueError("Nome, usuário e senha são obrigatórios.")
        password_hash = hash_password(password)
        with self.connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO usuarios (
                        nome_completo, nome_usuario, senha_hash, situacao, data_cadastro, data_atualizacao
                    )
                    VALUES (?, ?, ?, 'ativo', ?, ?)
                    """,
                    (full_name, username, password_hash, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Já existe um usuário com esse nome de login.") from exc
            return int(cursor.lastrowid)

    def get_user_by_username(self, username: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE lower(nome_usuario) = lower(?)",
                (username.strip(),),
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def authenticate_user(self, username: str, password: str) -> dict | None:
        user = self.get_user_by_username(username)
        if not user or user["situacao"] != "ativo":
            return None
        if not verify_password(password, user["senha_hash"]):
            return None
        with self.connect() as conn:
            conn.execute(
                "UPDATE usuarios SET ultimo_login = ?, data_atualizacao = ? WHERE id = ?",
                (current_timestamp(), current_timestamp(), user["id"]),
            )
        return self.get_user_by_id(user["id"])

    def change_user_password(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado.")
        if not verify_password(current_password, user["senha_hash"]):
            raise ValueError("A senha atual informada não confere.")
        with self.connect() as conn:
            conn.execute(
                "UPDATE usuarios SET senha_hash = ?, data_atualizacao = ? WHERE id = ?",
                (hash_password(new_password), current_timestamp(), user_id),
            )

    def _seed_reference_data(self, conn: sqlite3.Connection) -> None:
        conn.executemany(
            """
            INSERT OR IGNORE INTO espacos (nome, descricao, situacao)
            VALUES (?, ?, 'ativo')
            """,
            ESPACOS_INICIAIS,
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO tipos_ocorrencia (nome, descricao, nivel_gravidade_padrao, situacao)
            VALUES (?, ?, ?, 'ativo')
            """,
            TIPOS_OCORRENCIA_INICIAIS,
        )

    def _seed_sample_data(self, conn: sqlite3.Connection) -> None:
        seeded = conn.execute("SELECT valor FROM metadata WHERE chave = 'sample_data_seeded'").fetchone()
        if seeded:
            return

        espacos = self._name_to_id_map(conn, "espacos")
        now = current_timestamp()
        for index, professor in enumerate(PROFESSORES_EXEMPLO):
            espaco_id = list(espacos.values())[index % len(espacos)] if espacos else None
            conn.execute(
                """
                INSERT INTO professores (
                    nome_completo, nome_curto, area_atuacao, espaco_principal_id,
                    situacao, vinculo, telefone_institucional, email_institucional,
                    observacoes, data_cadastro, data_atualizacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    professor["nome_completo"],
                    professor["nome_curto"],
                    professor["area_atuacao"],
                    espaco_id,
                    professor["situacao"],
                    professor["vinculo"],
                    clean_optional(professor["telefone_institucional"]),
                    clean_optional(professor["email_institucional"]),
                    clean_optional(professor["observacoes"]),
                    now,
                    now,
                ),
            )

        professor_map = {
            row["nome_completo"]: row["id"]
            for row in conn.execute("SELECT id, nome_completo FROM professores").fetchall()
        }
        tipos = self._name_to_id_map(conn, "tipos_ocorrencia")
        if professor_map and espacos and tipos:
            conn.execute(
                """
                INSERT INTO intercorrencias (
                    data, hora, tipo_ocorrencia_id, espaco_id, contexto_atuacao, pessoas_relacionadas,
                    professor_relacionado_id, descricao_objetiva, providencias_adotadas,
                    encaminhado_para, nivel_gravidade, tags, observacoes,
                    data_hora_registro, data_hora_atualizacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_date_iso(),
                    current_time_hm(),
                    tipos["Registro preventivo"],
                    next(iter(espacos.values())),
                    "CIEBP",
                    "grupo do 9º ano",
                    next(iter(professor_map.values())),
                    "Registro fictício inicial criado para demonstrar o uso do sistema.",
                    "Sem providência adicional no momento.",
                    "Coordenação, se necessário.",
                    "Baixo",
                    "exemplo, teste",
                    "Este registro pode ser editado ou excluído posteriormente.",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO ausencias_professores (
                    data, ausencia_integral, hora_inicio, hora_fim, professor_id, espaco_id, contexto_atuacao,
                    turma_ou_grupo_afetado, tipo_ausencia, havia_comunicacao_previa,
                    houve_substituicao, impacto_observado, providencia_tomada,
                    observacoes, data_hora_registro, data_hora_atualizacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_date_iso(),
                    "não",
                    "08:00",
                    "08:50",
                    next(iter(professor_map.values())),
                    next(iter(espacos.values())),
                    "CIEBP",
                    "turma visitante",
                    "atraso",
                    "não sei",
                    "não",
                    "Início da atividade adiado até a chegada do responsável pelo espaço.",
                    "Registro e comunicação à coordenação.",
                    "Exemplo inicial para testes do módulo de ausências.",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO rotinas_docentes (
                    data, hora_inicio, hora_fim, categoria, professor_id, espaco_id, contexto_atuacao,
                    turma_ou_publico, titulo, descricao_atividade, objetivos,
                    recursos_utilizados, encaminhamentos, tags, observacoes,
                    data_hora_registro, data_hora_atualizacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_date_iso(),
                    "09:00",
                    "10:30",
                    ROTINA_DOCENTE_CATEGORIAS[1],
                    next(iter(professor_map.values())),
                    next(iter(espacos.values())),
                    "CIEBP",
                    "turma visitante",
                    "Planejamento inicial de oficina",
                    "Organização do planejamento de uma aula/oficina para uso demonstrativo do sistema.",
                    "Estruturar sequência didática e registrar a rotina do professor.",
                    "Notebook, roteiro de aula e materiais do espaço.",
                    "Material reservado para continuidade da atividade.",
                    "planejamento, exemplo",
                    "Registro fictício inicial para testes do módulo de rotinas docentes.",
                    now,
                    now,
                ),
            )

        conn.execute(
            "INSERT OR REPLACE INTO metadata (chave, valor) VALUES ('sample_data_seeded', ?)",
            (now,),
        )

    def _name_to_id_map(self, conn: sqlite3.Connection, table_name: str) -> dict[str, int]:
        rows = conn.execute(f"SELECT id, nome FROM {table_name}").fetchall()
        return {row["nome"]: row["id"] for row in rows}

    def _rows_to_dicts(self, rows: list[sqlite3.Row]) -> list[dict]:
        return [dict(row) for row in rows]

    def list_professors(self, include_inactive: bool = True) -> list[dict]:
        sql = """
            SELECT p.*, e.nome AS espaco_principal_nome
            FROM professores p
            LEFT JOIN espacos e ON e.id = p.espaco_principal_id
        """
        params: list = []
        if not include_inactive:
            sql += " WHERE p.situacao = 'ativo'"
        sql += " ORDER BY p.nome_completo COLLATE NOCASE"
        with self.connect() as conn:
            return self._rows_to_dicts(conn.execute(sql, params).fetchall())

    def get_professor(self, professor_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT p.*, e.nome AS espaco_principal_nome
                FROM professores p
                LEFT JOIN espacos e ON e.id = p.espaco_principal_id
                WHERE p.id = ?
                """,
                (professor_id,),
            ).fetchone()
            return dict(row) if row else None

    def save_professor(self, data: dict, professor_id: int | None = None) -> None:
        now = current_timestamp()
        payload = (
            data["nome_completo"].strip(),
            data["nome_curto"].strip(),
            clean_optional(data.get("area_atuacao")),
            data.get("espaco_principal_id"),
            data["situacao"],
            data["vinculo"],
            clean_optional(data.get("telefone_institucional")),
            clean_optional(data.get("email_institucional")),
            clean_optional(data.get("observacoes")),
        )
        with self.connect() as conn:
            if professor_id is None:
                conn.execute(
                    """
                    INSERT INTO professores (
                        nome_completo, nome_curto, area_atuacao, espaco_principal_id,
                        situacao, vinculo, telefone_institucional, email_institucional,
                        observacoes, data_cadastro, data_atualizacao
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload + (now, now),
                )
            else:
                conn.execute(
                    """
                    UPDATE professores
                    SET nome_completo = ?, nome_curto = ?, area_atuacao = ?, espaco_principal_id = ?,
                        situacao = ?, vinculo = ?, telefone_institucional = ?, email_institucional = ?,
                        observacoes = ?, data_atualizacao = ?
                    WHERE id = ?
                    """,
                    payload + (now, professor_id),
                )

    def update_professor_status(self, professor_id: int, situacao: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE professores SET situacao = ?, data_atualizacao = ? WHERE id = ?",
                (situacao, current_timestamp(), professor_id),
            )

    def list_spaces(self, include_inactive: bool = True) -> list[dict]:
        sql = "SELECT * FROM espacos"
        if not include_inactive:
            sql += " WHERE situacao = 'ativo'"
        sql += " ORDER BY nome COLLATE NOCASE"
        with self.connect() as conn:
            return self._rows_to_dicts(conn.execute(sql).fetchall())

    def get_space(self, space_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM espacos WHERE id = ?", (space_id,)).fetchone()
            return dict(row) if row else None

    def save_space(self, data: dict, space_id: int | None = None) -> None:
        with self.connect() as conn:
            if space_id is None:
                conn.execute(
                    "INSERT INTO espacos (nome, descricao, situacao) VALUES (?, ?, ?)",
                    (data["nome"].strip(), clean_optional(data.get("descricao")), data["situacao"]),
                )
            else:
                conn.execute(
                    "UPDATE espacos SET nome = ?, descricao = ?, situacao = ? WHERE id = ?",
                    (data["nome"].strip(), clean_optional(data.get("descricao")), data["situacao"], space_id),
                )

    def update_space_status(self, space_id: int, situacao: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE espacos SET situacao = ? WHERE id = ?", (situacao, space_id))

    def list_occurrence_types(self, include_inactive: bool = True) -> list[dict]:
        sql = "SELECT * FROM tipos_ocorrencia"
        if not include_inactive:
            sql += " WHERE situacao = 'ativo'"
        sql += " ORDER BY nome COLLATE NOCASE"
        with self.connect() as conn:
            return self._rows_to_dicts(conn.execute(sql).fetchall())

    def get_occurrence_type(self, occurrence_type_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tipos_ocorrencia WHERE id = ?", (occurrence_type_id,)).fetchone()
            return dict(row) if row else None

    def save_occurrence_type(self, data: dict, occurrence_type_id: int | None = None) -> None:
        with self.connect() as conn:
            if occurrence_type_id is None:
                conn.execute(
                    """
                    INSERT INTO tipos_ocorrencia (nome, descricao, nivel_gravidade_padrao, situacao)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        data["nome"].strip(),
                        clean_optional(data.get("descricao")),
                        clean_optional(data.get("nivel_gravidade_padrao")),
                        data["situacao"],
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE tipos_ocorrencia
                    SET nome = ?, descricao = ?, nivel_gravidade_padrao = ?, situacao = ?
                    WHERE id = ?
                    """,
                    (
                        data["nome"].strip(),
                        clean_optional(data.get("descricao")),
                        clean_optional(data.get("nivel_gravidade_padrao")),
                        data["situacao"],
                        occurrence_type_id,
                    ),
                )

    def update_occurrence_type_status(self, occurrence_type_id: int, situacao: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE tipos_ocorrencia SET situacao = ? WHERE id = ?", (situacao, occurrence_type_id))

    def get_active_reference_data(self) -> dict:
        return {
            "professores": self.list_professors(include_inactive=False),
            "espacos": self.list_spaces(include_inactive=False),
            "tipos_ocorrencia": self.list_occurrence_types(include_inactive=False),
        }

    def _list_evidencias(self, conn: sqlite3.Connection, tipo_registro: str, registro_id: int) -> list[dict]:
        rows = conn.execute(
            """
            SELECT id, nome_arquivo, dados, data_hora_registro
            FROM evidencias_registros
            WHERE tipo_registro = ? AND registro_id = ?
            ORDER BY id
            """,
            (tipo_registro, registro_id),
        ).fetchall()
        return self._rows_to_dicts(rows)

    def _replace_evidencias(self, conn: sqlite3.Connection, tipo_registro: str, registro_id: int, evidencias: list[dict] | None) -> None:
        conn.execute(
            "DELETE FROM evidencias_registros WHERE tipo_registro = ? AND registro_id = ?",
            (tipo_registro, registro_id),
        )
        payload = []
        for item in evidencias or []:
            dados = item.get("dados") or b""
            nome_arquivo = (item.get("nome_arquivo") or "").strip() or "evidencia.png"
            if not dados:
                continue
            payload.append((tipo_registro, registro_id, nome_arquivo, sqlite3.Binary(dados), current_timestamp()))
        if payload:
            conn.executemany(
                """
                INSERT INTO evidencias_registros (
                    tipo_registro, registro_id, nome_arquivo, dados, data_hora_registro
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                payload,
            )

    def save_intercorrencia(self, data: dict, intercorrencia_id: int | None = None) -> int:
        now = current_timestamp()
        payload = (
            data["data"],
            data["hora"],
            data["tipo_ocorrencia_id"],
            data["espaco_id"],
            clean_optional(data.get("contexto_atuacao")),
            clean_optional(data.get("pessoas_relacionadas")),
            data.get("professor_relacionado_id"),
            data.get("todos_professores", "não"),
            data["descricao_objetiva"].strip(),
            clean_optional(data.get("providencias_adotadas")),
            clean_optional(data.get("encaminhado_para")),
            clean_optional(data.get("nivel_gravidade")),
            clean_optional(data.get("tags")),
            clean_optional(data.get("observacoes")),
        )
        with self.connect() as conn:
            if intercorrencia_id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO intercorrencias (
                        data, hora, tipo_ocorrencia_id, espaco_id, contexto_atuacao, pessoas_relacionadas,
                        professor_relacionado_id, todos_professores, descricao_objetiva, providencias_adotadas,
                        encaminhado_para, nivel_gravidade, tags, observacoes,
                        data_hora_registro, data_hora_atualizacao
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload + (now, now),
                )
                intercorrencia_id = int(cursor.lastrowid)
            else:
                conn.execute(
                    """
                    UPDATE intercorrencias
                    SET data = ?, hora = ?, tipo_ocorrencia_id = ?, espaco_id = ?, contexto_atuacao = ?, pessoas_relacionadas = ?,
                        professor_relacionado_id = ?, todos_professores = ?, descricao_objetiva = ?, providencias_adotadas = ?,
                        encaminhado_para = ?, nivel_gravidade = ?, tags = ?, observacoes = ?,
                        data_hora_atualizacao = ?
                    WHERE id = ?
                    """,
                    payload + (now, intercorrencia_id),
                )
            self._replace_evidencias(conn, "intercorrencia", intercorrencia_id, data.get("evidencias"))
        return int(intercorrencia_id)

    def get_intercorrencia(self, intercorrencia_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    i.*,
                    t.nome AS tipo_nome,
                    e.nome AS espaco_nome,
                    CASE
                        WHEN i.todos_professores = 'sim' THEN ?
                        ELSE p.nome_completo
                    END AS professor_nome
                FROM intercorrencias i
                INNER JOIN tipos_ocorrencia t ON t.id = i.tipo_ocorrencia_id
                INNER JOIN espacos e ON e.id = i.espaco_id
                LEFT JOIN professores p ON p.id = i.professor_relacionado_id
                WHERE i.id = ?
                """,
                (PROFESSOR_TODOS, intercorrencia_id),
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            result["evidencias"] = self._list_evidencias(conn, "intercorrencia", intercorrencia_id)
            return result

    def get_latest_intercorrencia(self) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, data, hora, contexto_atuacao
                FROM intercorrencias
                ORDER BY data DESC, hora DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
            return dict(row) if row else None

    def delete_intercorrencia(self, intercorrencia_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM evidencias_registros WHERE tipo_registro = ? AND registro_id = ?",
                ("intercorrencia", intercorrencia_id),
            )
            conn.execute("DELETE FROM intercorrencias WHERE id = ?", (intercorrencia_id,))

    def save_ausencia(self, data: dict, ausencia_id: int | None = None) -> None:
        now = current_timestamp()
        payload = (
            data["data"],
            data.get("ausencia_integral", "não"),
            clean_optional(data.get("hora_inicio")),
            clean_optional(data.get("hora_fim")),
            data["professor_id"],
            data["espaco_id"],
            clean_optional(data.get("contexto_atuacao")),
            clean_optional(data.get("turma_ou_grupo_afetado")),
            data["tipo_ausencia"],
            clean_optional(data.get("havia_comunicacao_previa")),
            clean_optional(data.get("houve_substituicao")),
            clean_optional(data.get("impacto_observado")),
            clean_optional(data.get("providencia_tomada")),
            clean_optional(data.get("observacoes")),
        )
        with self.connect() as conn:
            if ausencia_id is None:
                conn.execute(
                    """
                    INSERT INTO ausencias_professores (
                        data, ausencia_integral, hora_inicio, hora_fim, professor_id, espaco_id, contexto_atuacao,
                        turma_ou_grupo_afetado, tipo_ausencia, havia_comunicacao_previa,
                        houve_substituicao, impacto_observado, providencia_tomada,
                        observacoes, data_hora_registro, data_hora_atualizacao
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload + (now, now),
                )
            else:
                conn.execute(
                    """
                    UPDATE ausencias_professores
                    SET data = ?, ausencia_integral = ?, hora_inicio = ?, hora_fim = ?, professor_id = ?, espaco_id = ?,
                        contexto_atuacao = ?, turma_ou_grupo_afetado = ?, tipo_ausencia = ?, havia_comunicacao_previa = ?,
                        houve_substituicao = ?, impacto_observado = ?, providencia_tomada = ?,
                        observacoes = ?, data_hora_atualizacao = ?
                    WHERE id = ?
                    """,
                    payload + (now, ausencia_id),
                )

    def get_ausencia(self, ausencia_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*, p.nome_completo AS professor_nome, e.nome AS espaco_nome
                FROM ausencias_professores a
                INNER JOIN professores p ON p.id = a.professor_id
                INNER JOIN espacos e ON e.id = a.espaco_id
                WHERE a.id = ?
                """,
                (ausencia_id,),
            ).fetchone()
            return dict(row) if row else None

    def delete_ausencia(self, ausencia_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM ausencias_professores WHERE id = ?", (ausencia_id,))

    def _normalize_professor_ids(self, professor_ids: list[int] | tuple[int, ...] | None, fallback_professor_id: int | None = None) -> list[int]:
        ordered_ids: list[int] = []
        source_ids = list(professor_ids or [])
        if fallback_professor_id and fallback_professor_id not in source_ids:
            source_ids.insert(0, fallback_professor_id)
        for professor_id in source_ids:
            if professor_id and professor_id not in ordered_ids:
                ordered_ids.append(int(professor_id))
        return ordered_ids

    def _sync_rotina_docente_professores(self, conn: sqlite3.Connection, rotina_id: int, professor_ids: list[int]) -> None:
        conn.execute("DELETE FROM rotinas_docentes_professores WHERE rotina_docente_id = ?", (rotina_id,))
        conn.executemany(
            """
            INSERT INTO rotinas_docentes_professores (rotina_docente_id, professor_id, ordem)
            VALUES (?, ?, ?)
            """,
            [(rotina_id, professor_id, ordem) for ordem, professor_id in enumerate(professor_ids)],
        )

    def _get_rotina_docente_professores(self, conn: sqlite3.Connection, rotina_id: int) -> tuple[list[int], str]:
        rows = conn.execute(
            """
            SELECT rp.professor_id, p.nome_completo
            FROM rotinas_docentes_professores rp
            INNER JOIN professores p ON p.id = rp.professor_id
            WHERE rp.rotina_docente_id = ?
            ORDER BY rp.ordem, p.nome_completo
            """,
            (rotina_id,),
        ).fetchall()
        professor_ids = [int(row["professor_id"]) for row in rows]
        professor_nomes = ", ".join(row["nome_completo"] for row in rows)
        return professor_ids, professor_nomes

    def save_rotina_docente(self, data: dict, rotina_id: int | None = None) -> int:
        now = current_timestamp()
        professor_ids = self._normalize_professor_ids(data.get("professor_ids"), data.get("professor_id"))
        if not professor_ids:
            raise ValueError("Selecione ao menos um professor para a rotina docente.")
        professor_id_principal = professor_ids[0]
        payload = (
            data["data"],
            clean_optional(data.get("hora_inicio")),
            clean_optional(data.get("hora_fim")),
            data["categoria"],
            professor_id_principal,
            data.get("espaco_id"),
            clean_optional(data.get("contexto_atuacao")),
            clean_optional(data.get("turma_ou_publico")),
            data["titulo"].strip(),
            data["descricao_atividade"].strip(),
            clean_optional(data.get("objetivos")),
            clean_optional(data.get("recursos_utilizados")),
            clean_optional(data.get("encaminhamentos")),
            clean_optional(data.get("tags")),
            clean_optional(data.get("observacoes")),
        )
        with self.connect() as conn:
            if rotina_id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO rotinas_docentes (
                        data, hora_inicio, hora_fim, categoria, professor_id, espaco_id, contexto_atuacao,
                        turma_ou_publico, titulo, descricao_atividade, objetivos,
                        recursos_utilizados, encaminhamentos, tags, observacoes,
                        data_hora_registro, data_hora_atualizacao
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload + (now, now),
                )
                rotina_id = int(cursor.lastrowid)
            else:
                conn.execute(
                    """
                    UPDATE rotinas_docentes
                    SET data = ?, hora_inicio = ?, hora_fim = ?, categoria = ?, professor_id = ?, espaco_id = ?,
                        contexto_atuacao = ?, turma_ou_publico = ?, titulo = ?, descricao_atividade = ?, objetivos = ?,
                        recursos_utilizados = ?, encaminhamentos = ?, tags = ?, observacoes = ?,
                        data_hora_atualizacao = ?
                    WHERE id = ?
                    """,
                    payload + (now, rotina_id),
                )
            self._sync_rotina_docente_professores(conn, rotina_id, professor_ids)
            self._replace_evidencias(conn, "rotina_docente", rotina_id, data.get("evidencias"))
        return int(rotina_id)

    def get_rotina_docente(self, rotina_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT r.*, p.nome_completo AS professor_principal_nome, e.nome AS espaco_nome
                FROM rotinas_docentes r
                INNER JOIN professores p ON p.id = r.professor_id
                LEFT JOIN espacos e ON e.id = r.espaco_id
                WHERE r.id = ?
                """,
                (rotina_id,),
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            professor_ids, professor_nomes = self._get_rotina_docente_professores(conn, rotina_id)
            result["professor_ids"] = professor_ids
            result["professor_nome"] = professor_nomes or result.get("professor_principal_nome") or ""
            result["evidencias"] = self._list_evidencias(conn, "rotina_docente", rotina_id)
            return result

    def get_latest_rotina_docente(self) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, data, hora_inicio, hora_fim
                FROM rotinas_docentes
                ORDER BY data DESC, COALESCE(hora_fim, hora_inicio, '') DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
            return dict(row) if row else None

    def delete_rotina_docente(self, rotina_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM evidencias_registros WHERE tipo_registro = ? AND registro_id = ?",
                ("rotina_docente", rotina_id),
            )
            conn.execute("DELETE FROM rotinas_docentes WHERE id = ?", (rotina_id,))

    def search_rotinas_docentes(self, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        clauses = []
        params: list = []
        self._append_period_filters(filters, clauses, params)

        if filters.get("professor_id"):
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM rotinas_docentes_professores rp
                    WHERE rp.rotina_docente_id = base.id
                      AND rp.professor_id = ?
                )
                """
            )
            params.append(filters["professor_id"])
        if filters.get("espaco_id"):
            clauses.append("base.espaco_id = ?")
            params.append(filters["espaco_id"])
        if filters.get("contexto_atuacao"):
            clauses.append("COALESCE(base.contexto_atuacao, '') = ?")
            params.append(filters["contexto_atuacao"])
        if filters.get("categoria"):
            clauses.append("base.categoria = ?")
            params.append(filters["categoria"])
        if filters.get("keyword"):
            keyword = f"%{filters['keyword']}%"
            clauses.append(
                """
                (
                    base.titulo LIKE ?
                    OR base.descricao_atividade LIKE ?
                    OR COALESCE(base.objetivos, '') LIKE ?
                    OR COALESCE(base.recursos_utilizados, '') LIKE ?
                    OR COALESCE(base.encaminhamentos, '') LIKE ?
                    OR COALESCE(base.observacoes, '') LIKE ?
                    OR COALESCE(base.turma_ou_publico, '') LIKE ?
                )
                """
            )
            params.extend([keyword, keyword, keyword, keyword, keyword, keyword, keyword])
        if filters.get("tags"):
            clauses.append("COALESCE(base.tags, '') LIKE ?")
            params.append(f"%{filters['tags']}%")

        sql = """
            SELECT
                base.*, 
                COALESCE(
                    (
                        SELECT GROUP_CONCAT(nome_completo, ', ')
                        FROM (
                            SELECT p2.nome_completo AS nome_completo
                            FROM rotinas_docentes_professores rp2
                            INNER JOIN professores p2 ON p2.id = rp2.professor_id
                            WHERE rp2.rotina_docente_id = base.id
                            ORDER BY rp2.ordem, p2.nome_completo
                        )
                    ),
                    p.nome_completo
                ) AS professor_nome,
                e.nome AS espaco_nome
            FROM rotinas_docentes base
            INNER JOIN professores p ON p.id = base.professor_id
            LEFT JOIN espacos e ON e.id = base.espaco_id
        """
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY base.data, COALESCE(base.hora_inicio, ''), base.id"

        with self.connect() as conn:
            return self._rows_to_dicts(conn.execute(sql, params).fetchall())

    def _append_period_filters(self, filters: dict, clauses: list[str], params: list) -> None:
        if filters.get("specific_date"):
            clauses.append("base.data = ?")
            params.append(filters["specific_date"])
            return
        if filters.get("start_date"):
            clauses.append("base.data >= ?")
            params.append(filters["start_date"])
        if filters.get("end_date"):
            clauses.append("base.data <= ?")
            params.append(filters["end_date"])

    def search_intercorrencias(self, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        clauses = []
        params: list = []
        self._append_period_filters(filters, clauses, params)

        if filters.get("professor_id"):
            clauses.append("(base.professor_relacionado_id = ? OR base.todos_professores = 'sim')")
            params.append(filters["professor_id"])
        if filters.get("espaco_id"):
            clauses.append("(base.espaco_id = ? OR base.espaco_id = (SELECT id FROM espacos WHERE nome = ?))")
            params.extend([filters["espaco_id"], ESPACO_TODOS])
        if filters.get("contexto_atuacao"):
            clauses.append("COALESCE(base.contexto_atuacao, '') = ?")
            params.append(filters["contexto_atuacao"])
        if filters.get("tipo_ocorrencia_id"):
            clauses.append("base.tipo_ocorrencia_id = ?")
            params.append(filters["tipo_ocorrencia_id"])
        if filters.get("keyword"):
            keyword = f"%{filters['keyword']}%"
            clauses.append(
                """
                (
                    base.descricao_objetiva LIKE ?
                    OR COALESCE(base.providencias_adotadas, '') LIKE ?
                    OR COALESCE(base.encaminhado_para, '') LIKE ?
                    OR COALESCE(base.observacoes, '') LIKE ?
                    OR COALESCE(base.pessoas_relacionadas, '') LIKE ?
                )
                """
            )
            params.extend([keyword, keyword, keyword, keyword, keyword])
        if filters.get("tags"):
            clauses.append("COALESCE(base.tags, '') LIKE ?")
            params.append(f"%{filters['tags']}%")
        if filters.get("gravidade_minima"):
            min_rank = GRAVIDADE_ORDEM[filters["gravidade_minima"]]
            clauses.append(
                """
                CASE COALESCE(base.nivel_gravidade, '')
                    WHEN 'Baixo' THEN 1
                    WHEN 'Médio' THEN 2
                    WHEN 'Alto' THEN 3
                    WHEN 'Crítico' THEN 4
                    ELSE 0
                END >= ?
                """
            )
            params.append(min_rank)

        sql = """
            SELECT
                base.*,
                t.nome AS tipo_nome,
                e.nome AS espaco_nome,
                CASE
                    WHEN base.todos_professores = 'sim' THEN ?
                    ELSE p.nome_completo
                END AS professor_nome
            FROM intercorrencias base
            INNER JOIN tipos_ocorrencia t ON t.id = base.tipo_ocorrencia_id
            INNER JOIN espacos e ON e.id = base.espaco_id
            LEFT JOIN professores p ON p.id = base.professor_relacionado_id
        """
        params = [PROFESSOR_TODOS] + params
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY base.data, base.hora, base.id"

        with self.connect() as conn:
            return self._rows_to_dicts(conn.execute(sql, params).fetchall())

    def search_ausencias(self, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        clauses = []
        params: list = []
        self._append_period_filters(filters, clauses, params)

        if filters.get("professor_id"):
            clauses.append("base.professor_id = ?")
            params.append(filters["professor_id"])
        if filters.get("espaco_id"):
            clauses.append("base.espaco_id = ?")
            params.append(filters["espaco_id"])
        if filters.get("contexto_atuacao"):
            clauses.append("COALESCE(base.contexto_atuacao, '') = ?")
            params.append(filters["contexto_atuacao"])
        if filters.get("tipo_ausencia"):
            clauses.append("base.tipo_ausencia = ?")
            params.append(filters["tipo_ausencia"])
        if filters.get("keyword"):
            keyword = f"%{filters['keyword']}%"
            clauses.append(
                """
                (
                    COALESCE(base.impacto_observado, '') LIKE ?
                    OR COALESCE(base.providencia_tomada, '') LIKE ?
                    OR COALESCE(base.observacoes, '') LIKE ?
                    OR COALESCE(base.turma_ou_grupo_afetado, '') LIKE ?
                )
                """
            )
            params.extend([keyword, keyword, keyword, keyword])

        sql = """
            SELECT
                base.*,
                p.nome_completo AS professor_nome,
                e.nome AS espaco_nome
            FROM ausencias_professores base
            INNER JOIN professores p ON p.id = base.professor_id
            INNER JOIN espacos e ON e.id = base.espaco_id
        """
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY base.data, COALESCE(base.hora_inicio, ''), base.id"

        with self.connect() as conn:
            return self._rows_to_dicts(conn.execute(sql, params).fetchall())

    def get_statistics(self, start_date: str | None = None, end_date: str | None = None) -> dict:
        period_filters = []
        params: list[str] = []
        if start_date:
            period_filters.append("data >= ?")
            params.append(start_date)
        if end_date:
            period_filters.append("data <= ?")
            params.append(end_date)
        where_clause = f" WHERE {' AND '.join(period_filters)}" if period_filters else ""

        with self.connect() as conn:
            total_intercorrencias = conn.execute(
                f"SELECT COUNT(*) AS total FROM intercorrencias{where_clause}",
                params,
            ).fetchone()["total"]
            total_ausencias = conn.execute(
                f"SELECT COUNT(*) AS total FROM ausencias_professores{where_clause}",
                params,
            ).fetchone()["total"]
            total_rotinas = conn.execute(
                f"SELECT COUNT(*) AS total FROM rotinas_docentes{where_clause}",
                params,
            ).fetchone()["total"]

            por_tipo = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT t.nome, COUNT(*) AS quantidade
                    FROM intercorrencias i
                    INNER JOIN tipos_ocorrencia t ON t.id = i.tipo_ocorrencia_id
                    {where_clause.replace('data', 'i.data')}
                    GROUP BY t.nome
                    ORDER BY quantidade DESC, t.nome
                    """,
                    params,
                ).fetchall()
            )
            por_espaco = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT e.nome, COUNT(*) AS quantidade
                    FROM intercorrencias i
                    INNER JOIN espacos e ON e.id = i.espaco_id
                    {where_clause.replace('data', 'i.data')}
                    GROUP BY e.nome
                    ORDER BY quantidade DESC, e.nome
                    """,
                    params,
                ).fetchall()
            )
            ausencias_por_professor = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT p.nome_completo AS nome, COUNT(*) AS quantidade
                    FROM ausencias_professores a
                    INNER JOIN professores p ON p.id = a.professor_id
                    {where_clause.replace('data', 'a.data')}
                    GROUP BY p.nome_completo
                    ORDER BY quantidade DESC, p.nome_completo
                    """,
                    params,
                ).fetchall()
            )
            por_gravidade = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT COALESCE(nivel_gravidade, 'Não informado') AS nome, COUNT(*) AS quantidade
                    FROM intercorrencias
                    {where_clause}
                    GROUP BY COALESCE(nivel_gravidade, 'Não informado')
                    ORDER BY quantidade DESC, nome
                    """,
                    params,
                ).fetchall()
            )
            rotinas_por_categoria = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT categoria AS nome, COUNT(*) AS quantidade
                    FROM rotinas_docentes
                    {where_clause}
                    GROUP BY categoria
                    ORDER BY quantidade DESC, nome
                    """,
                    params,
                ).fetchall()
            )
            por_contexto = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT contexto_atuacao AS nome, COUNT(*) AS quantidade
                    FROM (
                        SELECT i.contexto_atuacao AS contexto_atuacao
                        FROM intercorrencias i
                        {where_clause.replace('data', 'i.data')}
                        UNION ALL
                        SELECT a.contexto_atuacao AS contexto_atuacao
                        FROM ausencias_professores a
                        {where_clause.replace('data', 'a.data')}
                        UNION ALL
                        SELECT r.contexto_atuacao AS contexto_atuacao
                        FROM rotinas_docentes r
                        {where_clause.replace('data', 'r.data')}
                    ) base
                    WHERE COALESCE(contexto_atuacao, '') <> ''
                    GROUP BY contexto_atuacao
                    ORDER BY quantidade DESC, nome
                    """,
                    params + params + params,
                ).fetchall()
            )

        return {
            "total_intercorrencias": total_intercorrencias,
            "total_ausencias": total_ausencias,
            "total_rotinas": total_rotinas,
            "por_tipo": por_tipo,
            "por_espaco": por_espaco,
            "ausencias_por_professor": ausencias_por_professor,
            "por_gravidade": por_gravidade,
            "por_contexto": por_contexto,
            "rotinas_por_categoria": rotinas_por_categoria,
        }

    def get_statistics_timeline(self, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
        period_filters = []
        params: list[str] = []
        if start_date:
            period_filters.append("data >= ?")
            params.append(start_date)
        if end_date:
            period_filters.append("data <= ?")
            params.append(end_date)
        where_clause = f" WHERE {' AND '.join(period_filters)}" if period_filters else ""

        with self.connect() as conn:
            inter_rows = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT data, COUNT(*) AS quantidade
                    FROM intercorrencias
                    {where_clause}
                    GROUP BY data
                    ORDER BY data
                    """,
                    params,
                ).fetchall()
            )
            aus_rows = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT data, COUNT(*) AS quantidade
                    FROM ausencias_professores
                    {where_clause}
                    GROUP BY data
                    ORDER BY data
                    """,
                    params,
                ).fetchall()
            )
            rot_rows = self._rows_to_dicts(
                conn.execute(
                    f"""
                    SELECT data, COUNT(*) AS quantidade
                    FROM rotinas_docentes
                    {where_clause}
                    GROUP BY data
                    ORDER BY data
                    """,
                    params,
                ).fetchall()
            )

        inter_map = {row["data"]: row["quantidade"] for row in inter_rows}
        aus_map = {row["data"]: row["quantidade"] for row in aus_rows}
        rot_map = {row["data"]: row["quantidade"] for row in rot_rows}
        all_dates = sorted(set(inter_map) | set(aus_map) | set(rot_map))

        if not all_dates and not (start_date and end_date):
            return []

        first_date = start_date or (all_dates[0] if all_dates else end_date)
        last_date = end_date or (all_dates[-1] if all_dates else start_date)
        if not first_date or not last_date:
            return []

        current = dt.datetime.strptime(first_date, "%Y-%m-%d").date()
        final = dt.datetime.strptime(last_date, "%Y-%m-%d").date()
        if current > final:
            current, final = final, current

        timeline: list[dict] = []
        while current <= final:
            date_key = current.strftime("%Y-%m-%d")
            intercorrencias = inter_map.get(date_key, 0)
            ausencias = aus_map.get(date_key, 0)
            rotinas = rot_map.get(date_key, 0)
            timeline.append(
                {
                    "data": date_key,
                    "intercorrencias": intercorrencias,
                    "ausencias": ausencias,
                    "rotinas": rotinas,
                    "total": intercorrencias + ausencias + rotinas,
                }
            )
            current += dt.timedelta(days=1)

        return timeline

    def get_dashboard_summary(self) -> dict:
        today = current_date_iso()
        with self.connect() as conn:
            return {
                "professores_ativos": conn.execute(
                    "SELECT COUNT(*) AS total FROM professores WHERE situacao = 'ativo'"
                ).fetchone()["total"],
                "espacos_ativos": conn.execute(
                    "SELECT COUNT(*) AS total FROM espacos WHERE situacao = 'ativo'"
                ).fetchone()["total"],
                "tipos_ativos": conn.execute(
                    "SELECT COUNT(*) AS total FROM tipos_ocorrencia WHERE situacao = 'ativo'"
                ).fetchone()["total"],
                "intercorrencias_hoje": conn.execute(
                    "SELECT COUNT(*) AS total FROM intercorrencias WHERE data = ?",
                    (today,),
                ).fetchone()["total"],
                "ausencias_hoje": conn.execute(
                    "SELECT COUNT(*) AS total FROM ausencias_professores WHERE data = ?",
                    (today,),
                ).fetchone()["total"],
                "rotinas_hoje": conn.execute(
                    "SELECT COUNT(*) AS total FROM rotinas_docentes WHERE data = ?",
                    (today,),
                ).fetchone()["total"],
            }

    def backup_database(self, destination: Path | None = None) -> Path:
        ensure_directories()
        if destination is None:
            destination = BACKUP_DIR / f"backup_gestao_registros_{current_timestamp().replace(':', '-').replace(' ', '_')}.db"
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, destination)
        return destination

    def restore_database(self, backup_path: Path) -> None:
        shutil.copy2(backup_path, self.db_path)

