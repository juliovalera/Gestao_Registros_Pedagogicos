from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models import ROTINA_DOCENTE_CATEGORIAS
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


class RotinasDocentesWindow(tk.Toplevel):
    columns = ("id", "data", "inicio", "fim", "categoria", "professor", "espaco")

    def __init__(self, parent: tk.Misc, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.professor_map: dict[str, int | None] = {"": None}
        self.space_map: dict[str, int | None] = {"": None}

        self.title("Rotinas docentes")
        self.resizable(True, True)
        center_window(self, 1280, 780, parent=parent)
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
        self.professor_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.professor_combo.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Espaço").grid(row=1, column=2, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(filters, state="readonly", width=28)
        self.space_combo.grid(row=1, column=3, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Categoria").grid(row=1, column=4, padx=4, pady=4, sticky="w")
        self.category_combo = ttk.Combobox(filters, values=[""] + ROTINA_DOCENTE_CATEGORIAS, state="readonly", width=30)
        self.category_combo.grid(row=1, column=5, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Palavra-chave").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.keyword_entry = ttk.Entry(filters, width=32)
        self.keyword_entry.grid(row=2, column=1, columnspan=3, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Tags").grid(row=2, column=4, padx=4, pady=4, sticky="w")
        self.tags_entry = ttk.Entry(filters, width=22)
        self.tags_entry.grid(row=2, column=5, padx=4, pady=4, sticky="ew")

        filter_actions = ttk.Frame(filters)
        filter_actions.grid(row=3, column=0, columnspan=6, sticky="e", padx=4, pady=(0, 4))
        ttk.Button(filter_actions, text="Pesquisar", command=self.search).pack(side="left", padx=4)
        ttk.Button(filter_actions, text="Limpar filtros", command=self.clear_filters).pack(side="left", padx=4)

        body = ttk.Frame(main_frame)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(body)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text="Nova rotina docente", command=self.new_record).pack(side="left", padx=4)
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
            "inicio": "Início",
            "fim": "Fim",
            "categoria": "Categoria",
            "professor": "Professores",
            "espaco": "Espaço",
        }
        widths = {"id": 60, "data": 90, "inicio": 80, "fim": 80, "categoria": 220, "professor": 240, "espaco": 180}
        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.show_details())

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)

        details_frame = ttk.LabelFrame(body, text="Detalhes do registro")
        details_frame.grid(row=1, column=1, sticky="nsew")
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        self.details_text = tk.Text(details_frame, wrap="word")
        self.details_text.grid(row=0, column=0, sticky="nsew")
        self.details_text.config(state="disabled")

    def refresh_filters(self) -> None:
        refs = self.db.get_active_reference_data()
        professor_values = [""]
        self.professor_map = {"": None}
        for record in refs["professores"]:
            professor_values.append(record["nome_completo"])
            self.professor_map[record["nome_completo"]] = record["id"]
        self.professor_combo["values"] = professor_values

        space_values = [""]
        self.space_map = {"": None}
        for record in refs["espacos"]:
            space_values.append(record["nome"])
            self.space_map[record["nome"]] = record["id"]
        self.space_combo["values"] = space_values

    def clear_filters(self) -> None:
        for widget in (self.data_entry, self.data_inicio_entry, self.data_fim_entry, self.keyword_entry, self.tags_entry):
            widget.delete(0, tk.END)
        for combo in (self.professor_combo, self.space_combo, self.category_combo):
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
        if self.category_combo.get():
            filters["categoria"] = self.category_combo.get()
        if self.keyword_entry.get().strip():
            filters["keyword"] = self.keyword_entry.get().strip()
        if self.tags_entry.get().strip():
            filters["tags"] = self.tags_entry.get().strip()
        return filters

    def search(self) -> None:
        records = self.db.search_rotinas_docentes(self._collect_filters())
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

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def show_details(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            set_text(self.details_text, "")
            return
        record = self.db.get_rotina_docente(record_id)
        if not record:
            set_text(self.details_text, "")
            return
        set_text(
            self.details_text,
            (
                f"Data: {format_date_display(record['data'])}\n"
                f"Horário: {record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}\n"
                f"Categoria: {record['categoria']}\n"
                f"Professores: {record['professor_nome']}\n"
                f"Espaço: {record.get('espaco_nome') or '-'}\n"
                f"Turma ou público: {record.get('turma_ou_publico') or '-'}\n"
                f"Título: {record['titulo']}\n"
                f"Tags: {record.get('tags') or '-'}\n"
                f"Evidências anexadas: {len(record.get('evidencias') or [])}\n\n"
                f"Descrição da atividade:\n{record['descricao_atividade']}\n\n"
                f"Objetivos:\n{record.get('objetivos') or '-'}\n\n"
                f"Recursos utilizados:\n{record.get('recursos_utilizados') or '-'}\n\n"
                f"Encaminhamentos:\n{record.get('encaminhamentos') or '-'}\n\n"
                f"Observações:\n{record.get('observacoes') or '-'}"
            ),
        )

    def new_record(self) -> None:
        RotinaDocenteForm(self, self.db, on_save=self._after_change)

    def edit_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione uma rotina para editar.", self)
            return
        RotinaDocenteForm(self, self.db, record_id=record_id, on_save=self._after_change)

    def delete_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione uma rotina para excluir.", self)
            return
        if not messagebox.askyesno("Confirmar exclusão", "Deseja realmente excluir a rotina docente selecionada?", parent=self):
            return
        self.db.delete_rotina_docente(record_id)
        self._after_change()
        show_info("Registro excluído", "Rotina docente excluída com sucesso.", self)

    def _after_change(self) -> None:
        self.refresh_filters()
        self.search()
        if self.on_change:
            self.on_change()


class RotinaDocenteForm(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, record_id: int | None = None, on_save=None) -> None:
        super().__init__(parent)
        self.db = db
        self.record_id = record_id
        self.on_save = on_save
        self.professor_options: list[tuple[int, str]] = []
        self.space_map: dict[str, int | None] = {"": None}

        self.title("Cadastro de rotina docente")
        self.resizable(True, True)
        self.grab_set()
        center_window(self, 920, 820, parent=parent)

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

        ttk.Label(frame, text="Hora início").grid(row=1, column=0, sticky="w", pady=4)
        self.hora_inicio_entry = TimeInput(frame, width=18)
        self.hora_inicio_entry.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Hora fim").grid(row=2, column=0, sticky="w", pady=4)
        self.hora_fim_entry = TimeInput(frame, width=18)
        self.hora_fim_entry.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Professor(es) *").grid(row=3, column=0, sticky="nw", pady=4)
        professores_frame = ttk.Frame(frame)
        professores_frame.grid(row=3, column=1, sticky="ew", pady=4)
        professores_frame.columnconfigure(0, weight=1)
        self.professor_listbox = tk.Listbox(professores_frame, selectmode="multiple", exportselection=False, height=6)
        self.professor_listbox.grid(row=0, column=0, sticky="ew")
        professor_scroll = ttk.Scrollbar(professores_frame, orient="vertical", command=self.professor_listbox.yview)
        professor_scroll.grid(row=0, column=1, sticky="ns")
        self.professor_listbox.configure(yscrollcommand=professor_scroll.set)
        ttk.Label(professores_frame, text="Clique para marcar um ou mais professores.").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        professor_actions = ttk.Frame(professores_frame)
        professor_actions.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Button(professor_actions, text="Selecionar todos", command=self._select_all_professors).pack(side="left", padx=(0, 4))
        ttk.Button(professor_actions, text="Limpar seleção", command=self._clear_professor_selection).pack(side="left")

        ttk.Label(frame, text="Categoria *").grid(row=4, column=0, sticky="w", pady=4)
        self.category_combo = ttk.Combobox(frame, values=ROTINA_DOCENTE_CATEGORIAS, state="readonly", width=58)
        self.category_combo.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Espaço").grid(row=5, column=0, sticky="w", pady=4)
        self.space_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.space_combo.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Turma ou público").grid(row=6, column=0, sticky="w", pady=4)
        self.publico_entry = ttk.Entry(frame, width=62)
        self.publico_entry.grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Título *").grid(row=7, column=0, sticky="w", pady=4)
        self.titulo_entry = ttk.Entry(frame, width=62)
        self.titulo_entry.grid(row=7, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Tags").grid(row=8, column=0, sticky="w", pady=4)
        self.tags_entry = ttk.Entry(frame, width=62)
        self.tags_entry.grid(row=8, column=1, sticky="ew", pady=4)

        self.descricao_text = self._add_text_field(frame, 9, "Descrição da atividade *", 6)
        self.objetivos_text = self._add_text_field(frame, 10, "Objetivos", 4)
        self.recursos_text = self._add_text_field(frame, 11, "Recursos utilizados", 4)
        self.encaminhamentos_text = self._add_text_field(frame, 12, "Encaminhamentos", 4)
        self.observacoes_text = self._add_text_field(frame, 13, "Observações", 4)
        self.evidence_input = EvidenceInput(frame, height=4)
        self.evidence_input.grid(row=14, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=15, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Salvar", command=self.save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _add_text_field(self, frame: ttk.Frame, row: int, label: str, height: int) -> tk.Text:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="nw", pady=4)
        widget = tk.Text(frame, width=50, height=height)
        widget.grid(row=row, column=1, sticky="ew", pady=4)
        return widget

    def _load_references(self) -> None:
        refs = self.db.get_active_reference_data()
        for record in refs["professores"]:
            self.professor_options.append((record["id"], record["nome_completo"]))
            self.professor_listbox.insert(tk.END, record["nome_completo"])
        for record in refs["espacos"]:
            self.space_map[record["nome"]] = record["id"]
        self.space_combo["values"] = list(self.space_map.keys())

    def _load_data(self) -> None:
        record = self.db.get_rotina_docente(self.record_id)
        if not record:
            return
        self.data_entry.insert(0, format_date_display(record["data"]))
        self.hora_inicio_entry.insert(0, record.get("hora_inicio") or "")
        self.hora_fim_entry.insert(0, record.get("hora_fim") or "")
        self._set_selected_professor_ids(record.get("professor_ids") or [])
        self.category_combo.set(record["categoria"])
        self.space_combo.set(record.get("espaco_nome") or "")
        self.publico_entry.insert(0, record.get("turma_ou_publico") or "")
        self.titulo_entry.insert(0, record["titulo"])
        self.tags_entry.insert(0, record.get("tags") or "")
        self.descricao_text.insert("1.0", record["descricao_atividade"])
        self.objetivos_text.insert("1.0", record.get("objetivos") or "")
        self.recursos_text.insert("1.0", record.get("recursos_utilizados") or "")
        self.encaminhamentos_text.insert("1.0", record.get("encaminhamentos") or "")
        self.observacoes_text.insert("1.0", record.get("observacoes") or "")
        self.evidence_input.set_items(record.get("evidencias"))

    def _selected_professor_ids(self) -> list[int]:
        return [self.professor_options[index][0] for index in self.professor_listbox.curselection()]

    def _set_selected_professor_ids(self, professor_ids: list[int]) -> None:
        selected = set(professor_ids)
        self.professor_listbox.selection_clear(0, tk.END)
        for index, (professor_id, _nome) in enumerate(self.professor_options):
            if professor_id in selected:
                self.professor_listbox.selection_set(index)

    def _select_all_professors(self) -> None:
        self.professor_listbox.selection_set(0, tk.END)

    def _clear_professor_selection(self) -> None:
        self.professor_listbox.selection_clear(0, tk.END)

    def save(self) -> None:
        try:
            data = {
                "data": normalize_date(self.data_entry.get()),
                "hora_inicio": normalize_time(self.hora_inicio_entry.get()) if self.hora_inicio_entry.get().strip() else "",
                "hora_fim": normalize_time(self.hora_fim_entry.get()) if self.hora_fim_entry.get().strip() else "",
                "professor_ids": self._selected_professor_ids(),
                "categoria": self.category_combo.get().strip(),
                "espaco_id": self.space_map.get(self.space_combo.get()),
                "turma_ou_publico": self.publico_entry.get().strip(),
                "titulo": self.titulo_entry.get().strip(),
                "descricao_atividade": get_text(self.descricao_text),
                "objetivos": get_text(self.objetivos_text),
                "recursos_utilizados": get_text(self.recursos_text),
                "encaminhamentos": get_text(self.encaminhamentos_text),
                "tags": self.tags_entry.get().strip(),
                "observacoes": get_text(self.observacoes_text),
                "evidencias": self.evidence_input.get_items(),
            }
        except ValueError as exc:
            show_error("Validação", str(exc), self)
            return

        if not data["data"] or not data["professor_ids"] or not data["categoria"] or not data["titulo"] or not data["descricao_atividade"]:
            show_error(
                "Campos obrigatórios",
                "Preencha data, ao menos um professor, categoria, título e descrição da atividade.",
                self,
            )
            return

        self.db.save_rotina_docente(data, self.record_id)
        if self.on_save:
            self.on_save()
        show_info("Registro salvo", "Rotina docente salva com sucesso.", self)
        self.destroy()
