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
        self.professor_map: dict[str, int | None] = {"": None, PROFESSOR_TODOS: None}
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

        ttk.Label(frame, text="Tipo de ocorr?ncia *").grid(row=2, column=0, sticky="w", pady=4)
        self.type_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.type_combo.grid(row=2, column=1, sticky="ew", pady=4)
        self.type_combo.bind("<<ComboboxSelected>>", self._apply_default_gravity)

        ttk.Label(frame, text="Espa?o *").grid(row=3, column=0, sticky="w", pady=4)
        self.space_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.space_combo.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Professor relacionado").grid(row=4, column=0, sticky="w", pady=4)
        self.professor_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.professor_combo.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Contexto de atua??o").grid(row=5, column=0, sticky="w", pady=4)
        self.context_combo = ttk.Combobox(frame, values=[""] + CONTEXTOS_ATUACAO, state="readonly", width=58)
        self.context_combo.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Pessoas relacionadas").grid(row=6, column=0, sticky="w", pady=4)
        self.pessoas_entry = ttk.Entry(frame, width=62)
        self.pessoas_entry.grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="N?vel de gravidade").grid(row=7, column=0, sticky="w", pady=4)
        self.gravidade_combo = ttk.Combobox(frame, values=[""] + NIVEIS_GRAVIDADE, state="readonly", width=58)
        self.gravidade_combo.grid(row=7, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Tags").grid(row=8, column=0, sticky="w", pady=4)
        self.tags_entry = ttk.Entry(frame, width=62)
        self.tags_entry.grid(row=8, column=1, sticky="ew", pady=4)

        self.description_text = self._add_text_field(frame, 9, "Descri??o objetiva *", 6)
        self.providencias_text = self._add_text_field(frame, 10, "Provid?ncias adotadas", 5)

        ttk.Label(frame, text="Encaminhado para").grid(row=11, column=0, sticky="w", pady=4)
        self.encaminhado_entry = ttk.Entry(frame, width=62)
        self.encaminhado_entry.grid(row=11, column=1, sticky="ew", pady=4)

        self.observacoes_text = self._add_text_field(frame, 12, "Observa??es", 4)
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
                "todos_professores": "sim" if selected_professor == PROFESSOR_TODOS else "n?o",
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
            show_error("Valida??o", str(exc), self)
            return

        if not data["data"] or not data["hora"] or not data["tipo_ocorrencia_id"] or not data["espaco_id"] or not data["descricao_objetiva"]:
            show_error(
                "Campos obrigat?rios",
                "Preencha data, hora, tipo de ocorr?ncia, espa?o e descri??o objetiva.",
                self,
            )
            return

        self.db.save_intercorrencia(data, self.record_id)
        if self.on_save:
            self.on_save()
        show_info("Registro salvo", "Intercorr?ncia salva com sucesso.", self)
        self.destroy()