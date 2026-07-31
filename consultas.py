"""Consultas combinadas e análise estatística."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from models import CONTEXTOS_ATUACAO, NIVEIS_GRAVIDADE, ROTINA_DOCENTE_CATEGORIAS, TIPOS_AUSENCIA
from utils import DateInput, EXPORT_DIR, center_window, current_timestamp, format_date_display, normalize_date, set_text, show_info

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None
    MATPLOTLIB_AVAILABLE = False


class ConsultasWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db) -> None:
        super().__init__(parent)
        self.db = db
        self.title("Consultas e análise")
        center_window(self, 1260, 780)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        notebook.add(IntercorrenciasConsultaTab(notebook, db), text="Intercorrências")
        notebook.add(AusenciasConsultaTab(notebook, db), text="Ausências")
        notebook.add(RotinasDocentesConsultaTab(notebook, db), text="Rotinas docentes")
        notebook.add(EstatisticasTab(notebook, db), text="Resumo estatístico")


class BaseConsultaTab(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, db) -> None:
        super().__init__(parent)
        self.db = db

    def build_two_pane(self, columns: tuple[str, ...], headings: dict[str, str], widths: dict[str, int]) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(body)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.show_details())

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll.set)

        details_frame = ttk.LabelFrame(body, text="Detalhes")
        details_frame.grid(row=0, column=1, sticky="nsew")
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)

        self.details_text = tk.Text(details_frame, wrap="word")
        self.details_text.grid(row=0, column=0, sticky="nsew")
        details_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        details_scroll.grid(row=0, column=1, sticky="ns")
        self.details_text.configure(yscrollcommand=details_scroll.set)
        self.details_text.config(state="disabled")


class IntercorrenciasConsultaTab(BaseConsultaTab):
    columns = ("id", "data", "hora", "tipo", "espaco", "professor", "gravidade")

    def __init__(self, parent: ttk.Notebook, db) -> None:
        super().__init__(parent, db)
        self.professor_map = {"": None}
        self.space_map = {"": None}
        self.type_map = {"": None}
        self._build()
        self.load_references()
        self.search()

    def _build(self) -> None:
        filters = ttk.LabelFrame(self, text="Filtros combinados")
        filters.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ttk.Label(filters, text="Data específica").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.specific_entry = DateInput(filters, width=14)
        self.specific_entry.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Data inicial").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.start_entry = DateInput(filters, width=14)
        self.start_entry.grid(row=0, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Data final").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        self.end_entry = DateInput(filters, width=14)
        self.end_entry.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Professor").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.professor_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.professor_combo.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Espaço").grid(row=1, column=2, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.space_combo.grid(row=1, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Tipo").grid(row=1, column=4, padx=4, pady=4, sticky="w")
        self.type_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.type_combo.grid(row=1, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Palavra-chave").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.keyword_entry = ttk.Entry(filters, width=30)
        self.keyword_entry.grid(row=2, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Tags").grid(row=2, column=2, padx=4, pady=4, sticky="w")
        self.tags_entry = ttk.Entry(filters, width=22)
        self.tags_entry.grid(row=2, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Gravidade mínima").grid(row=2, column=4, padx=4, pady=4, sticky="w")
        self.gravidade_combo = ttk.Combobox(filters, values=[""] + NIVEIS_GRAVIDADE, state="readonly", width=28)
        self.gravidade_combo.grid(row=2, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Contexto").grid(row=3, column=0, padx=4, pady=4, sticky="w")
        self.context_combo = ttk.Combobox(filters, values=[""] + CONTEXTOS_ATUACAO, state="readonly", width=28)
        self.context_combo.grid(row=3, column=1, padx=4, pady=4)

        ttk.Button(filters, text="Pesquisar", command=self.search).grid(row=3, column=4, padx=4, pady=4)
        ttk.Button(filters, text="Limpar", command=self.clear).grid(row=3, column=5, padx=4, pady=4)

        self.build_two_pane(
            self.columns,
            {
                "id": "ID",
                "data": "Data",
                "hora": "Hora",
                "tipo": "Tipo",
                "espaco": "Espaço",
                "professor": "Professor",
                "gravidade": "Gravidade",
            },
            {"id": 60, "data": 90, "hora": 80, "tipo": 220, "espaco": 170, "professor": 180, "gravidade": 100},
        )

    def load_references(self) -> None:
        refs = self.db.get_active_reference_data()
        self.professor_map = {"": None}
        self.space_map = {"": None}
        self.type_map = {"": None}

        professor_values = [""]
        for record in refs["professores"]:
            professor_values.append(record["nome_completo"])
            self.professor_map[record["nome_completo"]] = record["id"]
        self.professor_combo["values"] = professor_values

        space_values = [""]
        for record in refs["espacos"]:
            space_values.append(record["nome"])
            self.space_map[record["nome"]] = record["id"]
        self.space_combo["values"] = space_values

        type_values = [""]
        for record in refs["tipos_ocorrencia"]:
            type_values.append(record["nome"])
            self.type_map[record["nome"]] = record["id"]
        self.type_combo["values"] = type_values

    def _filters(self) -> dict:
        filters = {}
        if self.specific_entry.get().strip():
            filters["specific_date"] = normalize_date(self.specific_entry.get())
        if self.start_entry.get().strip():
            filters["start_date"] = normalize_date(self.start_entry.get())
        if self.end_entry.get().strip():
            filters["end_date"] = normalize_date(self.end_entry.get())
        if self.professor_combo.get():
            filters["professor_id"] = self.professor_map.get(self.professor_combo.get())
        if self.space_combo.get():
            filters["espaco_id"] = self.space_map.get(self.space_combo.get())
        if self.type_combo.get():
            filters["tipo_ocorrencia_id"] = self.type_map.get(self.type_combo.get())
        if self.context_combo.get():
            filters["contexto_atuacao"] = self.context_combo.get()
        if self.keyword_entry.get().strip():
            filters["keyword"] = self.keyword_entry.get().strip()
        if self.tags_entry.get().strip():
            filters["tags"] = self.tags_entry.get().strip()
        if self.gravidade_combo.get():
            filters["gravidade_minima"] = self.gravidade_combo.get()
        return filters

    def search(self) -> None:
        records = self.db.search_intercorrencias(self._filters())
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in records:
            self.tree.insert(
                "",
                "end",
                iid=str(record["id"]),
                values=(
                    record["id"],
                    format_date_display(record["data"]),
                    record["hora"],
                    record["tipo_nome"],
                    record["espaco_nome"],
                    record.get("professor_nome") or "",
                    record.get("nivel_gravidade") or "",
                ),
            )
        set_text(self.details_text, "")

    def show_details(self) -> None:
        selected = self.tree.selection()
        if not selected:
            set_text(self.details_text, "")
            return
        record = self.db.get_intercorrencia(int(selected[0]))
        if not record:
            set_text(self.details_text, "")
            return
        set_text(
            self.details_text,
            (
                f"Data: {format_date_display(record['data'])}\n"
                f"Hora: {record['hora']}\n"
                f"Tipo: {record['tipo_nome']}\n"
                f"Espaço: {record['espaco_nome']}\n"
                f"Contexto de atuação: {record.get('contexto_atuacao') or '-'}\n"
                f"Professor: {record.get('professor_nome') or '-'}\n"
                f"Descrição:\n{record['descricao_objetiva']}\n\n"
                f"Providências:\n{record.get('providencias_adotadas') or '-'}\n\n"
                f"Encaminhamento:\n{record.get('encaminhado_para') or '-'}\n\n"
                f"Observações:\n{record.get('observacoes') or '-'}"
            ),
        )

    def clear(self) -> None:
        for entry in (self.specific_entry, self.start_entry, self.end_entry, self.keyword_entry, self.tags_entry):
            entry.delete(0, tk.END)
        for combo in (self.professor_combo, self.space_combo, self.type_combo, self.gravidade_combo, self.context_combo):
            combo.set("")
        self.search()


class AusenciasConsultaTab(BaseConsultaTab):
    columns = ("id", "data", "inicio", "fim", "professor", "espaco", "tipo")

    def __init__(self, parent: ttk.Notebook, db) -> None:
        super().__init__(parent, db)
        self.professor_map = {"": None}
        self.space_map = {"": None}
        self._build()
        self.load_references()
        self.search()

    def _build(self) -> None:
        filters = ttk.LabelFrame(self, text="Filtros combinados")
        filters.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ttk.Label(filters, text="Data específica").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.specific_entry = DateInput(filters, width=14)
        self.specific_entry.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Data inicial").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.start_entry = DateInput(filters, width=14)
        self.start_entry.grid(row=0, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Data final").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        self.end_entry = DateInput(filters, width=14)
        self.end_entry.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Professor").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.professor_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.professor_combo.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Espaço").grid(row=1, column=2, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.space_combo.grid(row=1, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Tipo de ausência").grid(row=1, column=4, padx=4, pady=4, sticky="w")
        self.type_combo = ttk.Combobox(filters, values=[""] + TIPOS_AUSENCIA, state="readonly", width=28)
        self.type_combo.grid(row=1, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Palavra-chave").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.keyword_entry = ttk.Entry(filters, width=40)
        self.keyword_entry.grid(row=2, column=1, columnspan=3, padx=4, pady=4)
        ttk.Label(filters, text="Contexto").grid(row=2, column=4, padx=4, pady=4, sticky="w")
        self.context_combo = ttk.Combobox(filters, values=[""] + CONTEXTOS_ATUACAO, state="readonly", width=28)
        self.context_combo.grid(row=2, column=5, padx=4, pady=4)

        ttk.Button(filters, text="Pesquisar", command=self.search).grid(row=3, column=4, padx=4, pady=4)
        ttk.Button(filters, text="Limpar", command=self.clear).grid(row=3, column=5, padx=4, pady=4)

        self.build_two_pane(
            self.columns,
            {"id": "ID", "data": "Data", "inicio": "Início", "fim": "Fim", "professor": "Professor", "espaco": "Espaço", "tipo": "Tipo"},
            {"id": 60, "data": 90, "inicio": 80, "fim": 80, "professor": 220, "espaco": 180, "tipo": 160},
        )

    def load_references(self) -> None:
        refs = self.db.get_active_reference_data()
        self.professor_map = {"": None}
        self.space_map = {"": None}

        values = [""]
        for record in refs["professores"]:
            values.append(record["nome_completo"])
            self.professor_map[record["nome_completo"]] = record["id"]
        self.professor_combo["values"] = values

        space_values = [""]
        for record in refs["espacos"]:
            space_values.append(record["nome"])
            self.space_map[record["nome"]] = record["id"]
        self.space_combo["values"] = space_values

    def _filters(self) -> dict:
        filters = {}
        if self.specific_entry.get().strip():
            filters["specific_date"] = normalize_date(self.specific_entry.get())
        if self.start_entry.get().strip():
            filters["start_date"] = normalize_date(self.start_entry.get())
        if self.end_entry.get().strip():
            filters["end_date"] = normalize_date(self.end_entry.get())
        if self.professor_combo.get():
            filters["professor_id"] = self.professor_map.get(self.professor_combo.get())
        if self.space_combo.get():
            filters["espaco_id"] = self.space_map.get(self.space_combo.get())
        if self.type_combo.get():
            filters["tipo_ausencia"] = self.type_combo.get()
        if self.context_combo.get():
            filters["contexto_atuacao"] = self.context_combo.get()
        if self.keyword_entry.get().strip():
            filters["keyword"] = self.keyword_entry.get().strip()
        return filters

    def search(self) -> None:
        records = self.db.search_ausencias(self._filters())
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in records:
            inicio = "Integral" if record.get("ausencia_integral") == "sim" else record.get("hora_inicio") or ""
            fim = "" if record.get("ausencia_integral") == "sim" else record.get("hora_fim") or ""
            self.tree.insert(
                "",
                "end",
                iid=str(record["id"]),
                values=(
                    record["id"],
                    format_date_display(record["data"]),
                    inicio,
                    fim,
                    record["professor_nome"],
                    record["espaco_nome"],
                    record["tipo_ausencia"],
                ),
            )
        set_text(self.details_text, "")

    def show_details(self) -> None:
        selected = self.tree.selection()
        if not selected:
            set_text(self.details_text, "")
            return
        record = self.db.get_ausencia(int(selected[0]))
        if not record:
            set_text(self.details_text, "")
            return
        horario = "Ausência integral" if record.get("ausencia_integral") == "sim" else f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
        set_text(
            self.details_text,
            (
                f"Data: {format_date_display(record['data'])}\n"
                f"Horário: {horario}\n"
                f"Professores: {record['professor_nome']}\n"
                f"Espaço: {record['espaco_nome']}\n"
                f"Contexto de atuação: {record.get('contexto_atuacao') or '-'}\n"
                f"Tipo: {record['tipo_ausencia']}\n"
                f"Comunicação prévia: {record.get('havia_comunicacao_previa') or '-'}\n"
                f"Substituição: {record.get('houve_substituicao') or '-'}\n\n"
                f"Impacto observado:\n{record.get('impacto_observado') or '-'}\n\n"
                f"Providência tomada:\n{record.get('providencia_tomada') or '-'}\n\n"
                f"Observações:\n{record.get('observacoes') or '-'}"
            ),
        )

    def clear(self) -> None:
        for entry in (self.specific_entry, self.start_entry, self.end_entry, self.keyword_entry):
            entry.delete(0, tk.END)
        for combo in (self.professor_combo, self.space_combo, self.type_combo, self.context_combo):
            combo.set("")
        self.search()


class RotinasDocentesConsultaTab(BaseConsultaTab):
    columns = ("id", "data", "inicio", "fim", "categoria", "professor", "espaco")

    def __init__(self, parent: ttk.Notebook, db) -> None:
        super().__init__(parent, db)
        self.professor_map = {"": None}
        self.space_map = {"": None}
        self._build()
        self.load_references()
        self.search()

    def _build(self) -> None:
        filters = ttk.LabelFrame(self, text="Filtros combinados")
        filters.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ttk.Label(filters, text="Data específica").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.specific_entry = DateInput(filters, width=14)
        self.specific_entry.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Data inicial").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.start_entry = DateInput(filters, width=14)
        self.start_entry.grid(row=0, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Data final").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        self.end_entry = DateInput(filters, width=14)
        self.end_entry.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Professor").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.professor_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.professor_combo.grid(row=1, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Espaço").grid(row=1, column=2, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.space_combo.grid(row=1, column=3, padx=4, pady=4)
        ttk.Label(filters, text="Categoria").grid(row=1, column=4, padx=4, pady=4, sticky="w")
        self.category_combo = ttk.Combobox(filters, values=[""] + ROTINA_DOCENTE_CATEGORIAS, state="readonly", width=28)
        self.category_combo.grid(row=1, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Palavra-chave").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.keyword_entry = ttk.Entry(filters, width=40)
        self.keyword_entry.grid(row=2, column=1, columnspan=3, padx=4, pady=4)
        ttk.Label(filters, text="Tags").grid(row=2, column=4, padx=4, pady=4, sticky="w")
        self.tags_entry = ttk.Entry(filters, width=28)
        self.tags_entry.grid(row=2, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Contexto").grid(row=3, column=0, padx=4, pady=4, sticky="w")
        self.context_combo = ttk.Combobox(filters, values=[""] + CONTEXTOS_ATUACAO, state="readonly", width=28)
        self.context_combo.grid(row=3, column=1, padx=4, pady=4)

        ttk.Button(filters, text="Pesquisar", command=self.search).grid(row=3, column=4, padx=4, pady=4)
        ttk.Button(filters, text="Limpar", command=self.clear).grid(row=3, column=5, padx=4, pady=4)

        self.build_two_pane(
            self.columns,
            {
                "id": "ID",
                "data": "Data",
                "inicio": "Início",
                "fim": "Fim",
                "categoria": "Categoria",
                "professor": "Professor",
                "espaco": "Espaço",
            },
            {"id": 60, "data": 90, "inicio": 80, "fim": 80, "categoria": 220, "professor": 200, "espaco": 180},
        )

    def load_references(self) -> None:
        refs = self.db.get_active_reference_data()
        self.professor_map = {"": None}
        self.space_map = {"": None}

        professor_values = [""]
        for record in refs["professores"]:
            professor_values.append(record["nome_completo"])
            self.professor_map[record["nome_completo"]] = record["id"]
        self.professor_combo["values"] = professor_values

        space_values = [""]
        for record in refs["espacos"]:
            space_values.append(record["nome"])
            self.space_map[record["nome"]] = record["id"]
        self.space_combo["values"] = space_values

    def _filters(self) -> dict:
        filters = {}
        if self.specific_entry.get().strip():
            filters["specific_date"] = normalize_date(self.specific_entry.get())
        if self.start_entry.get().strip():
            filters["start_date"] = normalize_date(self.start_entry.get())
        if self.end_entry.get().strip():
            filters["end_date"] = normalize_date(self.end_entry.get())
        if self.professor_combo.get():
            filters["professor_id"] = self.professor_map.get(self.professor_combo.get())
        if self.space_combo.get():
            filters["espaco_id"] = self.space_map.get(self.space_combo.get())
        if self.category_combo.get():
            filters["categoria"] = self.category_combo.get()
        if self.context_combo.get():
            filters["contexto_atuacao"] = self.context_combo.get()
        if self.keyword_entry.get().strip():
            filters["keyword"] = self.keyword_entry.get().strip()
        if self.tags_entry.get().strip():
            filters["tags"] = self.tags_entry.get().strip()
        return filters

    def search(self) -> None:
        records = self.db.search_rotinas_docentes(self._filters())
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in records:
            self.tree.insert(
                "",
                "end",
                iid=str(record["id"]),
                values=(
                    record["id"],
                    format_date_display(record["data"]),
                    record.get("hora_inicio") or "",
                    record.get("hora_fim") or "",
                    record["categoria"],
                    record["professor_nome"],
                    record.get("espaco_nome") or "",
                ),
            )
        set_text(self.details_text, "")

    def show_details(self) -> None:
        selected = self.tree.selection()
        if not selected:
            set_text(self.details_text, "")
            return
        record = self.db.get_rotina_docente(int(selected[0]))
        if not record:
            set_text(self.details_text, "")
            return
        set_text(
            self.details_text,
            (
                f"Data: {format_date_display(record['data'])}\n"
                f"Horário: {record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}\n"
                f"Professores: {record['professor_nome']}\n"
                f"Categoria: {record['categoria']}\n"
                f"Contexto de atuação: {record.get('contexto_atuacao') or '-'}\n"
                f"Espaço: {record.get('espaco_nome') or '-'}\n"
                f"Turma ou público: {record.get('turma_ou_publico') or '-'}\n"
                f"Título: {record['titulo']}\n"
                f"Tags: {record.get('tags') or '-'}\n\n"
                f"Descrição da atividade:\n{record['descricao_atividade']}\n\n"
                f"Objetivos:\n{record.get('objetivos') or '-'}\n\n"
                f"Recursos utilizados:\n{record.get('recursos_utilizados') or '-'}\n\n"
                f"Encaminhamentos:\n{record.get('encaminhamentos') or '-'}\n\n"
                f"Observações:\n{record.get('observacoes') or '-'}"
            ),
        )

    def clear(self) -> None:
        for entry in (self.specific_entry, self.start_entry, self.end_entry, self.keyword_entry, self.tags_entry):
            entry.delete(0, tk.END)
        for combo in (self.professor_combo, self.space_combo, self.category_combo, self.context_combo):
            combo.set("")
        self.search()


class EstatisticasTab(ttk.Frame):
    CHART_OPTIONS = [
        ("Evolução diária dos registros", "timeline", "line"),
        ("Intercorrências por tipo", "por_tipo", "#2f6fad"),
        ("Intercorrências por espaço", "por_espaco", "#1f7a6b"),
        ("Ausências por professor", "ausencias_por_professor", "#b26b00"),
        ("Rotinas por categoria", "rotinas_por_categoria", "#7a3eb1"),
        ("Registros por gravidade", "por_gravidade", "#b13e57"),
        ("Registros por contexto", "por_contexto", "#4c8c2b"),
    ]

    def __init__(self, parent: ttk.Notebook, db) -> None:
        super().__init__(parent)
        self.db = db
        self.current_stats: dict = {}
        self.current_timeline: list[dict] = []
        self.current_figure = None
        self.chart_option_map = {label: (key, style) for label, key, style in self.CHART_OPTIONS}
        self._build()
        self.refresh()

    def _build(self) -> None:
        filters = ttk.LabelFrame(self, text="Período")
        filters.pack(fill="x", padx=10, pady=10)

        ttk.Label(filters, text="Data inicial").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.start_entry = DateInput(filters, width=14)
        self.start_entry.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(filters, text="Data final").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.end_entry = DateInput(filters, width=14)
        self.end_entry.grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(filters, text="Atualizar resumo e gráficos", command=self.refresh).grid(row=0, column=4, padx=4, pady=4)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        summary_frame = ttk.LabelFrame(body, text="Resumo estatístico")
        summary_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        self.text = tk.Text(summary_frame, wrap="word")
        self.text.grid(row=0, column=0, sticky="nsew")
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.text.yview)
        summary_scroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=summary_scroll.set)
        self.text.config(state="disabled")

        chart_frame = ttk.LabelFrame(body, text="Gráficos")
        chart_frame.grid(row=0, column=1, sticky="nsew")
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(1, weight=1)

        chart_controls = ttk.Frame(chart_frame)
        chart_controls.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        chart_controls.columnconfigure(1, weight=1)

        ttk.Label(chart_controls, text="Visualização").grid(row=0, column=0, padx=(0, 6), pady=4, sticky="w")
        self.chart_combo = ttk.Combobox(
            chart_controls,
            values=[label for label, _key, _style in self.CHART_OPTIONS],
            state="readonly",
            width=30,
        )
        self.chart_combo.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.chart_combo.set(self.CHART_OPTIONS[0][0])
        self.chart_combo.bind("<<ComboboxSelected>>", lambda _event: self.render_chart())

        self.export_chart_button = ttk.Button(chart_controls, text="Exportar gráfico PNG", command=self.export_chart_png)
        self.export_chart_button.grid(row=0, column=2, padx=(8, 0), pady=4, sticky="e")

        ttk.Label(chart_controls, text="Os gráficos usam os mesmos filtros do resumo estatístico.").grid(
            row=1, column=0, columnspan=3, padx=4, pady=(0, 2), sticky="w"
        )

        self.chart_host = ttk.Frame(chart_frame)
        self.chart_host.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.chart_host.columnconfigure(0, weight=1)
        self.chart_host.rowconfigure(0, weight=1)

    def refresh(self) -> None:
        start = normalize_date(self.start_entry.get()) if self.start_entry.get().strip() else None
        end = normalize_date(self.end_entry.get()) if self.end_entry.get().strip() else None
        stats = self.db.get_statistics(start, end)
        timeline = self.db.get_statistics_timeline(start, end)
        self.current_stats = stats
        self.current_timeline = timeline

        def render_items(items: list[dict], name_key: str = "nome") -> str:
            if not items:
                return "Nenhum registro encontrado."
            return "\n".join(f"- {item[name_key]}: {item['quantidade']}" for item in items)

        text = (
            f"Quantidade de intercorrências no período: {stats['total_intercorrencias']}\n"
            f"Quantidade de ausências no período: {stats['total_ausencias']}\n"
            f"Quantidade de rotinas docentes no período: {stats['total_rotinas']}\n\n"
            "Quantidade por tipo de ocorrência:\n"
            f"{render_items(stats['por_tipo'])}\n\n"
            "Quantidade por espaço:\n"
            f"{render_items(stats['por_espaco'])}\n\n"
            "Quantidade de ausências por professor:\n"
            f"{render_items(stats['ausencias_por_professor'])}\n\n"
            "Quantidade por categoria de rotina docente:\n"
            f"{render_items(stats['rotinas_por_categoria'])}\n\n"
            "Quantidade de registros por nível de gravidade:\n"
            f"{render_items(stats['por_gravidade'])}\n\n"
            "Quantidade de registros por contexto de atuação:\n"
            f"{render_items(stats['por_contexto'])}"
        )
        set_text(self.text, text)
        self.render_chart()

    def render_chart(self) -> None:
        for child in self.chart_host.winfo_children():
            child.destroy()

        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(
                self.chart_host,
                text="Instale a biblioteca matplotlib para visualizar os gráficos.\n\nUse: pip install matplotlib",
                justify="center",
            ).grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
            self.current_figure = None
            self.export_chart_button.config(state="disabled")
            return

        chart_label = self.chart_combo.get() or self.CHART_OPTIONS[0][0]
        key, style = self.chart_option_map[chart_label]
        if style == "line":
            self.current_figure = self._build_timeline_chart(chart_label, self.current_timeline)
        else:
            items = self.current_stats.get(key, [])
            self.current_figure = self._build_bar_chart(chart_label, items, style)

        if self.current_figure is None:
            ttk.Label(
                self.chart_host,
                text="Nenhum dado encontrado para o gráfico selecionado.",
                justify="center",
            ).grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
            self.export_chart_button.config(state="disabled")
            return

        canvas = FigureCanvasTkAgg(self.current_figure, master=self.chart_host)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.export_chart_button.config(state="normal")

    def _build_bar_chart(self, title: str, items: list[dict], color: str):
        if not items or Figure is None:
            return None

        labels = [item["nome"] for item in items][::-1]
        values = [item["quantidade"] for item in items][::-1]
        display_labels = [label if len(label) <= 40 else f"{label[:37]}..." for label in labels]
        figure_height = max(4.2, min(7.6, 1.4 + len(display_labels) * 0.5))

        figure = Figure(figsize=(7.8, figure_height), dpi=100)
        axis = figure.add_subplot(111)
        axis.barh(display_labels, values, color=color)
        axis.set_title(title, fontsize=12)
        axis.set_xlabel("Quantidade")
        axis.grid(axis="x", alpha=0.25)
        axis.set_axisbelow(True)

        max_value = max(values) if values else 0
        text_offset = max(0.15, max_value * 0.01)
        for index, value in enumerate(values):
            axis.text(value + text_offset, index, str(value), va="center", fontsize=9)

        figure.subplots_adjust(left=0.34, right=0.96, top=0.9, bottom=0.12)
        return figure

    def _build_timeline_chart(self, title: str, timeline: list[dict]):
        if not timeline or Figure is None:
            return None

        labels = [format_date_display(item["data"]) for item in timeline]
        intercorrencias = [item["intercorrencias"] for item in timeline]
        ausencias = [item["ausencias"] for item in timeline]
        rotinas = [item["rotinas"] for item in timeline]
        total = [item["total"] for item in timeline]

        step = max(1, len(labels) // 8)
        tick_positions = list(range(0, len(labels), step))
        if tick_positions[-1] != len(labels) - 1:
            tick_positions.append(len(labels) - 1)

        figure = Figure(figsize=(7.8, 4.8), dpi=100)
        axis = figure.add_subplot(111)
        axis.plot(intercorrencias, label="Intercorrências", color="#2f6fad", marker="o", linewidth=1.8, markersize=4)
        axis.plot(ausencias, label="Ausências", color="#b26b00", marker="o", linewidth=1.8, markersize=4)
        axis.plot(rotinas, label="Rotinas", color="#1f7a6b", marker="o", linewidth=1.8, markersize=4)
        axis.plot(total, label="Total", color="#444444", linestyle="--", linewidth=1.6)
        axis.set_title(title, fontsize=12)
        axis.set_ylabel("Quantidade")
        axis.set_xlabel("Data")
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)
        axis.set_xticks(tick_positions)
        axis.set_xticklabels([labels[index] for index in tick_positions], rotation=35, ha="right")
        axis.legend(loc="upper left", fontsize=8)
        figure.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.24)
        return figure

    def export_chart_png(self) -> None:
        if self.current_figure is None:
            return

        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        chart_label = self.chart_combo.get() or "grafico"
        safe_name = (
            chart_label.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )
        timestamp = current_timestamp().replace(":", "-").replace(" ", "_")
        target = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Exportar gráfico em PNG",
            defaultextension=".png",
            initialdir=str(EXPORT_DIR),
            initialfile=f"{safe_name}_{timestamp}.png",
            filetypes=[("PNG", "*.png"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return

        self.current_figure.savefig(target, dpi=180, bbox_inches="tight")
        show_info("Exportação concluída", f"Gráfico salvo em:\n{target}", self.winfo_toplevel())
