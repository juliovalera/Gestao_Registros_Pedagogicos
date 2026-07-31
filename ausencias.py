"""Tela e formulário de ausências pedagógicas."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models import CONTEXTOS_ATUACAO, OPCOES_TRIPLAS, TIPOS_AUSENCIA
from utils import (
    confirm_end_time_after_start,
    DateInput,
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


class AusenciasWindow(tk.Toplevel):
    columns = ("id", "data", "inicio", "fim", "professor", "espaco", "tipo")

    def __init__(self, parent: tk.Misc, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.professor_map: dict[str, int | None] = {"": None}
        self.space_map: dict[str, int | None] = {"": None}

        self.title("Ausências de professores")
        self.resizable(True, True)
        center_window(self, 1220, 740, parent=parent)
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
        self.professor_combo = ttk.Combobox(filters, state="readonly", width=24)
        self.professor_combo.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Espaço").grid(row=1, column=2, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(filters, state="readonly", width=24)
        self.space_combo.grid(row=1, column=3, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Tipo de ausência").grid(row=1, column=4, padx=4, pady=4, sticky="w")
        self.tipo_combo = ttk.Combobox(filters, values=[""] + TIPOS_AUSENCIA, state="readonly", width=22)
        self.tipo_combo.grid(row=1, column=5, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Palavra-chave").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.keyword_entry = ttk.Entry(filters, width=34)
        self.keyword_entry.grid(row=2, column=1, columnspan=2, padx=4, pady=4, sticky="ew")

        ttk.Label(filters, text="Contexto").grid(row=2, column=3, padx=4, pady=4, sticky="w")
        self.context_combo = ttk.Combobox(filters, state="readonly", width=24, values=[""] + CONTEXTOS_ATUACAO)
        self.context_combo.grid(row=2, column=4, padx=4, pady=4, sticky="ew")

        filter_actions = ttk.Frame(filters)
        filter_actions.grid(row=2, column=5, sticky="e", padx=4, pady=4)
        ttk.Button(filter_actions, text="Pesquisar", command=self.search).pack(side="left", padx=4)
        ttk.Button(filter_actions, text="Limpar filtros", command=self.clear_filters).pack(side="left", padx=4)

        body = ttk.Frame(main_frame)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(body)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text="Nova ausência", command=self.new_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Editar", command=self.edit_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Excluir", command=self.delete_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar", command=self.search).pack(side="left", padx=4)

        table_frame = ttk.Frame(body)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        headings = {"id": "ID", "data": "Data", "inicio": "Início", "fim": "Fim", "professor": "Professor", "espaco": "Espaço", "tipo": "Tipo"}
        widths = {"id": 60, "data": 90, "inicio": 80, "fim": 80, "professor": 230, "espaco": 190, "tipo": 160}
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
        details_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        details_scroll.grid(row=0, column=1, sticky="ns")
        self.details_text.configure(yscrollcommand=details_scroll.set)
        self.details_text.config(state="disabled")

    def refresh_filters(self) -> None:
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
        self.context_combo["values"] = [""] + CONTEXTOS_ATUACAO

    def clear_filters(self) -> None:
        for entry in (self.data_entry, self.data_inicio_entry, self.data_fim_entry, self.keyword_entry):
            entry.delete(0, tk.END)
        for combo in (self.professor_combo, self.space_combo, self.tipo_combo, self.context_combo):
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
        if self.tipo_combo.get():
            filters["tipo_ausencia"] = self.tipo_combo.get()
        if self.context_combo.get():
            filters["contexto_atuacao"] = self.context_combo.get()
        if self.keyword_entry.get().strip():
            filters["keyword"] = self.keyword_entry.get().strip()
        return filters

    def search(self) -> None:
        records = self.db.search_ausencias(self._collect_filters())
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

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def show_details(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            set_text(self.details_text, "")
            return
        record = self.db.get_ausencia(record_id)
        if not record:
            set_text(self.details_text, "")
            return
        horario = "Ausência integral" if record.get("ausencia_integral") == "sim" else f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
        text = (
            f"Data: {format_date_display(record['data'])}\n"
            f"Horário: {horario}\n"
            f"Professor: {record['professor_nome']}\n"
            f"Espaço: {record['espaco_nome']}\n"
            f"Contexto de atuação: {record.get('contexto_atuacao') or '-'}\n"
            f"Turma ou grupo afetado: {record.get('turma_ou_grupo_afetado') or '-'}\n"
            f"Tipo de ausência: {record['tipo_ausencia']}\n"
            f"Comunicação prévia: {record.get('havia_comunicacao_previa') or '-'}\n"
            f"Substituição: {record.get('houve_substituicao') or '-'}\n\n"
            f"Impacto observado:\n{record.get('impacto_observado') or '-'}\n\n"
            f"Providência tomada:\n{record.get('providencia_tomada') or '-'}\n\n"
            f"Observações:\n{record.get('observacoes') or '-'}"
        )
        set_text(self.details_text, text)

    def new_record(self) -> None:
        AusenciaForm(self, self.db, on_save=self._after_change)

    def edit_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione uma ausência para editar.", self)
            return
        AusenciaForm(self, self.db, record_id=record_id, on_save=self._after_change)

    def delete_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione uma ausência para excluir.", self)
            return
        if not messagebox.askyesno("Confirmar exclusão", "Deseja realmente excluir a ausência selecionada?", parent=self):
            return
        self.db.delete_ausencia(record_id)
        self._after_change()
        show_info("Registro excluído", "Ausência excluída com sucesso.", self)

    def _after_change(self) -> None:
        self.refresh_filters()
        self.search()
        if self.on_change:
            self.on_change()


class AusenciaForm(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, record_id: int | None = None, on_save=None) -> None:
        super().__init__(parent)
        self.db = db
        self.record_id = record_id
        self.on_save = on_save
        self.professor_map: dict[str, int | None] = {"": None}
        self.space_map: dict[str, int | None] = {"": None}
        self.ausencia_integral_var = tk.BooleanVar(value=False)

        self.title("Cadastro de ausência")
        self.transient(parent)
        self.grab_set()
        center_window(self, 820, 700, parent=parent)

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

        def sync_scroll_region(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_frame_width(event) -> None:
            canvas.itemconfigure(frame_id, width=event.width)

        def on_mouse_wheel(event) -> None:
            delta = -1 * int(event.delta / 120) if event.delta else 0
            canvas.yview_scroll(delta, "units")

        frame.bind("<Configure>", sync_scroll_region)
        canvas.bind("<Configure>", sync_frame_width)
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)
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

        self.ausencia_integral_check = ttk.Checkbutton(
            frame,
            text="Ausência integral",
            variable=self.ausencia_integral_var,
            command=self._toggle_integral_absence,
        )
        self.ausencia_integral_check.grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Professor *").grid(row=4, column=0, sticky="w", pady=4)
        self.professor_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.professor_combo.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Espaço *").grid(row=5, column=0, sticky="w", pady=4)
        self.space_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.space_combo.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Contexto de atuação").grid(row=6, column=0, sticky="w", pady=4)
        self.context_combo = ttk.Combobox(frame, state="readonly", width=58, values=[""] + CONTEXTOS_ATUACAO)
        self.context_combo.grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Turma ou grupo afetado").grid(row=7, column=0, sticky="w", pady=4)
        self.turma_entry = ttk.Entry(frame, width=62)
        self.turma_entry.grid(row=7, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Tipo de ausência *").grid(row=8, column=0, sticky="w", pady=4)
        self.tipo_combo = ttk.Combobox(frame, values=TIPOS_AUSENCIA, state="readonly", width=58)
        self.tipo_combo.grid(row=8, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Havia comunicação prévia").grid(row=9, column=0, sticky="w", pady=4)
        self.comunicacao_combo = ttk.Combobox(frame, values=[""] + OPCOES_TRIPLAS, state="readonly", width=58)
        self.comunicacao_combo.grid(row=9, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Houve substituição").grid(row=10, column=0, sticky="w", pady=4)
        self.substituicao_combo = ttk.Combobox(frame, values=[""] + OPCOES_TRIPLAS, state="readonly", width=58)
        self.substituicao_combo.grid(row=10, column=1, sticky="ew", pady=4)

        self.impacto_text = self._add_text_field(frame, 11, "Impacto observado", 5)
        self.providencia_text = self._add_text_field(frame, 12, "Providência tomada", 5)
        self.observacoes_text = self._add_text_field(frame, 13, "Observações", 4)

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
        refs = self.db.get_active_reference_data()
        self.professor_map = {"": None}
        self.space_map = {"": None}
        for record in refs["professores"]:
            self.professor_map[record["nome_completo"]] = record["id"]
        for record in refs["espacos"]:
            self.space_map[record["nome"]] = record["id"]
        self.professor_combo["values"] = list(self.professor_map.keys())
        self.space_combo["values"] = list(self.space_map.keys())
        self.context_combo["values"] = [""] + CONTEXTOS_ATUACAO

    def _load_data(self) -> None:
        record = self.db.get_ausencia(self.record_id)
        if not record:
            return
        self.data_entry.insert(0, format_date_display(record["data"]))
        self.ausencia_integral_var.set(record.get("ausencia_integral") == "sim")
        self.hora_inicio_entry.insert(0, record.get("hora_inicio") or "")
        self.hora_fim_entry.insert(0, record.get("hora_fim") or "")
        self.professor_combo.set(record["professor_nome"])
        self.space_combo.set(record["espaco_nome"])
        self.context_combo.set(record.get("contexto_atuacao") or "")
        self.turma_entry.insert(0, record.get("turma_ou_grupo_afetado") or "")
        self.tipo_combo.set(record["tipo_ausencia"])
        self.comunicacao_combo.set(record.get("havia_comunicacao_previa") or "")
        self.substituicao_combo.set(record.get("houve_substituicao") or "")
        self.impacto_text.insert("1.0", record.get("impacto_observado") or "")
        self.providencia_text.insert("1.0", record.get("providencia_tomada") or "")
        self.observacoes_text.insert("1.0", record.get("observacoes") or "")
        self._toggle_integral_absence()

    def _toggle_integral_absence(self) -> None:
        is_integral = self.ausencia_integral_var.get()
        if is_integral:
            self.hora_inicio_entry.delete(0, tk.END)
            self.hora_fim_entry.delete(0, tk.END)
        state = "disabled" if is_integral else "normal"
        self.hora_inicio_entry.entry.configure(state=state)
        self.hora_fim_entry.entry.configure(state=state)

    def save(self) -> None:
        try:
            data = {
                "data": normalize_date(self.data_entry.get()),
                "ausencia_integral": "sim" if self.ausencia_integral_var.get() else "não",
                "hora_inicio": "" if self.ausencia_integral_var.get() else normalize_time(self.hora_inicio_entry.get()) if self.hora_inicio_entry.get().strip() else "",
                "hora_fim": "" if self.ausencia_integral_var.get() else normalize_time(self.hora_fim_entry.get()) if self.hora_fim_entry.get().strip() else "",
                "professor_id": self.professor_map.get(self.professor_combo.get()),
                "espaco_id": self.space_map.get(self.space_combo.get()),
                "contexto_atuacao": self.context_combo.get().strip(),
                "turma_ou_grupo_afetado": self.turma_entry.get().strip(),
                "tipo_ausencia": self.tipo_combo.get().strip(),
                "havia_comunicacao_previa": self.comunicacao_combo.get().strip(),
                "houve_substituicao": self.substituicao_combo.get().strip(),
                "impacto_observado": get_text(self.impacto_text),
                "providencia_tomada": get_text(self.providencia_text),
                "observacoes": get_text(self.observacoes_text),
            }
        except ValueError as exc:
            show_error("Validação", str(exc), self)
            return

        if not data["data"] or not data["professor_id"] or not data["espaco_id"] or not data["tipo_ausencia"]:
            show_error(
                "Campos obrigatórios",
                "Preencha data, professor, espaço e tipo de ausência.",
                self,
            )
            return
        if not data["impacto_observado"] and not data["observacoes"]:
            show_error(
                "Campos obrigatórios",
                "Preencha ao menos impacto observado ou observações.",
                self,
            )
            return

        if not self.ausencia_integral_var.get() and not confirm_end_time_after_start(
            data["hora_inicio"],
            data["hora_fim"],
            self,
        ):
            self.hora_fim_entry.focus_set()
            return

        self.db.save_ausencia(data, self.record_id)
        if self.on_save:
            self.on_save()
        show_info("Registro salvo", "Ausência salva com sucesso.", self)
        self.destroy()
