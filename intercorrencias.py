"""Tela e formulário de intercorrências pedagógicas."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models import CONTEXTOS_ATUACAO, ESPACO_TODOS, NIVEIS_GRAVIDADE, PROFESSOR_TODOS
from utils import (
    DateInput,
    EvidenceInput,
    TimeInput,
    center_window,
    format_date_display,
    get_text,
    normalize_date,
    normalize_time,
    set_text,
    show_error,
    show_info,
)


class IntercorrenciasWindow(tk.Toplevel):
    columns = ("id", "data", "hora", "tipo", "espaco", "professor", "gravidade")

    def __init__(self, parent: tk.Misc, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.professor_map: dict[str, int | None] = {"": None}
        self.space_map: dict[str, int | None] = {"": None}
        self.type_map: dict[str, int | None] = {"": None}
        self.type_defaults: dict[str, str] = {}

        self.title("Intercorrências")
        self.resizable(True, True)
        center_window(self, 1240, 760, parent=parent)
        self._build()
        self.refresh_filters()
        self.search()

    def _build(self) -> None:
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        filters = ttk.LabelFrame(main_frame, text="Busca rápida")
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filters.columnconfigure(1, weight=1)
        filters.columnconfigure(3, weight=1)
        filters.columnconfigure(5, weight=1)

        ttk.Label(filters, text="Data específica").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.data_entry = DateInput(filters, width=14)
        self.data_entry.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(filters, text="Data inicial").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.data_inicio_entry = DateInput(filters, width=14)
        self.data_inicio_entry.grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(filters, text="Data final").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        self.data_fim_entry = DateInput(filters, width=14)
        self.data_fim_entry.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(filters, text="Professor").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.professor_combo = ttk.Combobox(filters, state="readonly", width=26)
        self.professor_combo.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Espaço").grid(row=1, column=2, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(filters, state="readonly", width=24)
        self.space_combo.grid(row=1, column=3, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Tipo").grid(row=1, column=4, padx=4, pady=4, sticky="w")
        self.type_combo = ttk.Combobox(filters, state="readonly", width=24)
        self.type_combo.grid(row=1, column=5, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Palavra-chave").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.keyword_entry = ttk.Entry(filters, width=32)
        self.keyword_entry.grid(row=2, column=1, columnspan=2, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Tags").grid(row=2, column=3, padx=4, pady=4, sticky="w")
        self.tags_entry = ttk.Entry(filters, width=18)
        self.tags_entry.grid(row=2, column=4, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Contexto").grid(row=2, column=5, padx=4, pady=4, sticky="w")
        self.context_combo = ttk.Combobox(filters, state="readonly", width=24, values=[""] + CONTEXTOS_ATUACAO)
        self.context_combo.grid(row=2, column=6, padx=4, pady=4, sticky="ew")
        filters.columnconfigure(6, weight=1)

        filter_actions = ttk.Frame(filters)
        filter_actions.grid(row=3, column=0, columnspan=7, sticky="e", padx=4, pady=(0, 4))
        ttk.Button(filter_actions, text="Pesquisar", command=self.search).pack(side="left", padx=4)
        ttk.Button(filter_actions, text="Limpar filtros", command=self.clear_filters).pack(side="left", padx=4)

        body = ttk.Frame(main_frame)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(body)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text="Nova intercorrência", command=self.new_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Editar", command=self.edit_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Excluir", command=self.delete_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar", command=self.search).pack(side="left", padx=4)

        table_frame = ttk.Frame(body)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        headings = {
            "id": "ID",
            "data": "Data",
            "hora": "Hora",
            "tipo": "Tipo",
            "espaco": "Espaço",
            "professor": "Professor",
            "gravidade": "Gravidade",
        }
        widths = {"id": 60, "data": 90, "hora": 80, "tipo": 220, "espaco": 170, "professor": 180, "gravidade": 100}
        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.show_details())

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll.set)

        details_frame = ttk.LabelFrame(body, text="Detalhes do registro")
        details_frame.grid(row=1, column=1, sticky="nsew")
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        self.details_text = tk.Text(details_frame, wrap="word")
        self.details_text.grid(row=0, column=0, sticky="nsew")
        self.details_text.config(state="disabled")

    def refresh_filters(self) -> None:
        references = self.db.get_active_reference_data()
        self.professor_map = {"": None}
        self.space_map = {"": None}
        self.type_map = {"": None}
        self.type_defaults = {}

        professor_values = [""]
        for record in references["professores"]:
            professor_values.append(record["nome_completo"])
            self.professor_map[record["nome_completo"]] = record["id"]
        self.professor_combo["values"] = professor_values

        space_values = [""]
        for record in references["espacos"]:
            space_values.append(record["nome"])
            self.space_map[record["nome"]] = record["id"]
        self.space_combo["values"] = space_values

        type_values = [""]
        for record in references["tipos_ocorrencia"]:
            type_values.append(record["nome"])
            self.type_map[record["nome"]] = record["id"]
            self.type_defaults[record["nome"]] = record.get("nivel_gravidade_padrao") or ""
        self.type_combo["values"] = type_values
        self.context_combo["values"] = [""] + CONTEXTOS_ATUACAO

    def clear_filters(self) -> None:
        for widget in (self.data_entry, self.data_inicio_entry, self.data_fim_entry, self.keyword_entry, self.tags_entry):
            widget.delete(0, tk.END)
        for combo in (self.professor_combo, self.space_combo, self.type_combo, self.context_combo):
            combo.set("")
        self.search()

    def _collect_filters(self) -> dict:
        filters = {}
        if self.data_entry.get().strip():
            filters["specific_date"] = normalize_date(self.data_entry.get())
        if self.data_inicio_entry.get().strip():
            filters["start_date"] = normalize_date(self.data_inicio_entry.get())
        if self.data_fim_entry.get().strip():
            filters["end_date"] = normalize_date(self.data_fim_entry.get())
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
        return filters

    def search(self) -> None:
        records = self.db.search_intercorrencias(self._collect_filters())
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

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def show_details(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            set_text(self.details_text, "")
            return
        record = self.db.get_intercorrencia(record_id)
        if not record:
            set_text(self.details_text, "")
            return

        evidencias = record.get("evidencias") or []
        text = (
            f"Data: {format_date_display(record['data'])}\n"
            f"Hora: {record['hora']}\n"
            f"Tipo: {record['tipo_nome']}\n"
            f"Espaço: {record['espaco_nome']}\n"
            f"Contexto de atuação: {record.get('contexto_atuacao') or '-'}\n"
            f"Professor relacionado: {record.get('professor_nome') or '-'}\n"
            f"Pessoas relacionadas: {record.get('pessoas_relacionadas') or '-'}\n"
            f"Gravidade: {record.get('nivel_gravidade') or '-'}\n"
            f"Tags: {record.get('tags') or '-'}\n"
            f"Evidências anexadas: {len(evidencias)}\n\n"
            f"Descrição objetiva:\n{record['descricao_objetiva']}\n\n"
            f"Providências adotadas:\n{record.get('providencias_adotadas') or '-'}\n\n"
            f"Encaminhado para:\n{record.get('encaminhado_para') or '-'}\n\n"
            f"Observações:\n{record.get('observacoes') or '-'}"
        )
        set_text(self.details_text, text)

    def new_record(self) -> None:
        IntercorrenciaForm(self, self.db, on_save=self._after_change)

    def edit_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione uma intercorrência para editar.", self)
            return
        IntercorrenciaForm(self, self.db, record_id=record_id, on_save=self._after_change)

    def delete_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione uma intercorrência para excluir.", self)
            return
        if not messagebox.askyesno("Confirmar exclusão", "Deseja realmente excluir a intercorrência selecionada?", parent=self):
            return
        self.db.delete_intercorrencia(record_id)
        self._after_change()
        show_info("Registro excluído", "Intercorrência excluída com sucesso.", self)

    def _after_change(self) -> None:
        self.refresh_filters()
        self.search()
        if self.on_change:
            self.on_change()


class IntercorrenciaForm(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, record_id: int | None = None, on_save=None) -> None:
        super().__init__(parent)
        self.db = db
        self.record_id = record_id
        self.on_save = on_save

        self.professor_map: dict[str, int | None] = {"": None, PROFESSOR_TODOS: None}
        self.space_map: dict[str, int | None] = {"": None}
        self.type_map: dict[str, int | None] = {"": None}
        self.type_defaults: dict[str, str] = {}

        self.title("Cadastro de intercorrência")
        self.transient(parent)
        self.grab_set()
        center_window(self, 780, 820, parent=parent)

        self._build()
        self._load_references()
        if record_id:
            self._load_data()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self, padding=8)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        frame = ttk.Frame(canvas, padding=12)
        frame.columnconfigure(1, weight=1)
        frame_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        frame.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(frame_id, width=event.width))
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * int(event.delta / 120), "units"))
        self.bind("<Destroy>", lambda _event: canvas.unbind_all("<MouseWheel>"))

        ttk.Label(frame, text="Data *").grid(row=0, column=0, sticky="w", pady=4)
        self.data_entry = DateInput(frame, width=18)
        self.data_entry.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Hora *").grid(row=1, column=0, sticky="w", pady=4)
        self.hora_entry = TimeInput(frame, width=18)
        self.hora_entry.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Tipo de ocorrência *").grid(row=2, column=0, sticky="w", pady=4)
        self.type_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.type_combo.grid(row=2, column=1, sticky="ew", pady=4)
        self.type_combo.bind("<<ComboboxSelected>>", self._apply_default_gravity)

        ttk.Label(frame, text="Espaço *").grid(row=3, column=0, sticky="w", pady=4)
        self.space_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.space_combo.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Professor relacionado").grid(row=4, column=0, sticky="w", pady=4)
        self.professor_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.professor_combo.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Contexto de atuação").grid(row=5, column=0, sticky="w", pady=4)
        self.context_combo = ttk.Combobox(frame, state="readonly", width=58, values=[""] + CONTEXTOS_ATUACAO)
        self.context_combo.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Pessoas relacionadas").grid(row=6, column=0, sticky="w", pady=4)
        self.pessoas_entry = ttk.Entry(frame, width=62)
        self.pessoas_entry.grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Nível de gravidade").grid(row=7, column=0, sticky="w", pady=4)
        self.gravidade_combo = ttk.Combobox(frame, values=[""] + NIVEIS_GRAVIDADE, state="readonly", width=58)
        self.gravidade_combo.grid(row=7, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Tags").grid(row=8, column=0, sticky="w", pady=4)
        self.tags_entry = ttk.Entry(frame, width=62)
        self.tags_entry.grid(row=8, column=1, sticky="ew", pady=4)

        self.description_text = self._add_text_field(frame, 9, "Descrição objetiva *", 6)
        self.providencias_text = self._add_text_field(frame, 10, "Providências adotadas", 5)

        ttk.Label(frame, text="Encaminhado para").grid(row=11, column=0, sticky="w", pady=4)
        self.encaminhado_entry = ttk.Entry(frame, width=62)
        self.encaminhado_entry.grid(row=11, column=1, sticky="ew", pady=4)

        self.observacoes_text = self._add_text_field(frame, 12, "Observações", 4)
        self.evidence_input = EvidenceInput(frame, height=4)
        self.evidence_input.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=14, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Salvar", command=self.save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _add_text_field(self, frame: ttk.Frame, row: int, label: str, height: int) -> tk.Text:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="nw", pady=4)
        text_widget = tk.Text(frame, width=50, height=height)
        text_widget.grid(row=row, column=1, sticky="ew", pady=4)
        return text_widget

    def _load_references(self) -> None:
        references = self.db.get_active_reference_data()
        self.professor_map = {"": None, PROFESSOR_TODOS: None}
        self.space_map = {"": None}
        self.type_map = {"": None}
        self.type_defaults = {}

        professor_values = ["", PROFESSOR_TODOS]
        for record in references["professores"]:
            self.professor_map[record["nome_completo"]] = record["id"]
            professor_values.append(record["nome_completo"])

        space_values = [""]
        for record in references["espacos"]:
            self.space_map[record["nome"]] = record["id"]
            space_values.append(record["nome"])

        type_values = [""]
        for record in references["tipos_ocorrencia"]:
            self.type_map[record["nome"]] = record["id"]
            self.type_defaults[record["nome"]] = record.get("nivel_gravidade_padrao") or ""
            type_values.append(record["nome"])

        self.professor_combo["values"] = professor_values
        self.space_combo["values"] = space_values
        self.type_combo["values"] = type_values
        self.context_combo["values"] = [""] + CONTEXTOS_ATUACAO

    def _apply_default_gravity(self, _event=None) -> None:
        selected = self.type_combo.get()
        if selected and not self.gravidade_combo.get():
            self.gravidade_combo.set(self.type_defaults.get(selected, ""))

    def _load_data(self) -> None:
        record = self.db.get_intercorrencia(self.record_id)
        if not record:
            return
        self.data_entry.insert(0, format_date_display(record["data"]))
        self.hora_entry.insert(0, record["hora"])
        self.type_combo.set(record["tipo_nome"])
        self.space_combo.set(record["espaco_nome"])
        if record.get("todos_professores") == "sim":
            self.professor_combo.set(PROFESSOR_TODOS)
        else:
            self.professor_combo.set(record.get("professor_nome") or "")
        self.context_combo.set(record.get("contexto_atuacao") or "")
        self.pessoas_entry.insert(0, record.get("pessoas_relacionadas") or "")
        self.gravidade_combo.set(record.get("nivel_gravidade") or "")
        self.tags_entry.insert(0, record.get("tags") or "")
        self.description_text.insert("1.0", record["descricao_objetiva"])
        self.providencias_text.insert("1.0", record.get("providencias_adotadas") or "")
        self.encaminhado_entry.insert(0, record.get("encaminhado_para") or "")
        self.observacoes_text.insert("1.0", record.get("observacoes") or "")
        self.evidence_input.set_items(record.get("evidencias"))

    def save(self) -> None:
        try:
            selected_professor = self.professor_combo.get()
            data = {
                "data": normalize_date(self.data_entry.get()),
                "hora": normalize_time(self.hora_entry.get()),
                "tipo_ocorrencia_id": self.type_map.get(self.type_combo.get()),
                "espaco_id": self.space_map.get(self.space_combo.get()),
                "professor_relacionado_id": None if selected_professor == PROFESSOR_TODOS else self.professor_map.get(selected_professor),
                "todos_professores": "sim" if selected_professor == PROFESSOR_TODOS else "não",
                "contexto_atuacao": self.context_combo.get().strip(),
                "pessoas_relacionadas": self.pessoas_entry.get().strip(),
                "descricao_objetiva": get_text(self.description_text),
                "providencias_adotadas": get_text(self.providencias_text),
                "encaminhado_para": self.encaminhado_entry.get().strip(),
                "nivel_gravidade": self.gravidade_combo.get().strip(),
                "tags": self.tags_entry.get().strip(),
                "observacoes": get_text(self.observacoes_text),
                "evidencias": self.evidence_input.get_items(),
            }
        except ValueError as exc:
            show_error("Validação", str(exc), self)
            return

        if not data["data"] or not data["hora"] or not data["tipo_ocorrencia_id"] or not data["espaco_id"] or not data["descricao_objetiva"]:
            show_error(
                "Campos obrigatórios",
                "Preencha data, hora, tipo de ocorrência, espaço e descrição objetiva.",
                self,
            )
            return

        self.db.save_intercorrencia(data, self.record_id)
        if self.on_save:
            self.on_save()
        show_info("Registro salvo", "Intercorrência salva com sucesso.", self)
        self.destroy()
