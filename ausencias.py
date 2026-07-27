from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models import CONTEXTOS_ATUACAO, OPCOES_TRIPLAS, TIPOS_AUSENCIA
from utils import (
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
        self.professor_map: dict[str, int] = {}
        self.space_map: dict[str, int] = {}

        self.title("Ausências de professores")
        center_window(self, 1220, 740)
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

        ttk.Label(frame, text="Hora in?cio").grid(row=1, column=0, sticky="w", pady=4)
        self.hora_inicio_entry = TimeInput(frame, width=18)
        self.hora_inicio_entry.grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Hora fim").grid(row=2, column=0, sticky="w", pady=4)
        self.hora_fim_entry = TimeInput(frame, width=18)
        self.hora_fim_entry.grid(row=2, column=1, sticky="w", pady=4)

        self.ausencia_integral_check = ttk.Checkbutton(
            frame,
            text="Aus?ncia integral",
            variable=self.ausencia_integral_var,
            command=self._toggle_integral_absence,
        )
        self.ausencia_integral_check.grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Professor *").grid(row=4, column=0, sticky="w", pady=4)
        self.professor_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.professor_combo.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Espa?o *").grid(row=5, column=0, sticky="w", pady=4)
        self.space_combo = ttk.Combobox(frame, state="readonly", width=58)
        self.space_combo.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Contexto de atua??o").grid(row=6, column=0, sticky="w", pady=4)
        self.context_combo = ttk.Combobox(frame, values=[""] + CONTEXTOS_ATUACAO, state="readonly", width=58)
        self.context_combo.grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Turma ou grupo afetado").grid(row=7, column=0, sticky="w", pady=4)
        self.turma_entry = ttk.Entry(frame, width=62)
        self.turma_entry.grid(row=7, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Tipo de aus?ncia *").grid(row=8, column=0, sticky="w", pady=4)
        self.tipo_combo = ttk.Combobox(frame, values=TIPOS_AUSENCIA, state="readonly", width=58)
        self.tipo_combo.grid(row=8, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Havia comunica??o pr?via").grid(row=9, column=0, sticky="w", pady=4)
        self.comunicacao_combo = ttk.Combobox(frame, values=[""] + OPCOES_TRIPLAS, state="readonly", width=58)
        self.comunicacao_combo.grid(row=9, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Houve substitui??o").grid(row=10, column=0, sticky="w", pady=4)
        self.substituicao_combo = ttk.Combobox(frame, values=[""] + OPCOES_TRIPLAS, state="readonly", width=58)
        self.substituicao_combo.grid(row=10, column=1, sticky="ew", pady=4)

        self.impacto_text = self._add_text_field(frame, 11, "Impacto observado", 5)
        self.providencia_text = self._add_text_field(frame, 12, "Provid?ncia tomada", 5)
        self.observacoes_text = self._add_text_field(frame, 13, "Observa??es", 4)

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
                "ausencia_integral": "sim" if self.ausencia_integral_var.get() else "n?o",
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
            show_error("Valida??o", str(exc), self)
            return

        if not data["data"] or not data["professor_id"] or not data["espaco_id"] or not data["tipo_ausencia"]:
            show_error(
                "Campos obrigat?rios",
                "Preencha data, professor, espa?o e tipo de aus?ncia.",
                self,
            )
            return
        if not data["impacto_observado"] and not data["observacoes"]:
            show_error(
                "Campos obrigat?rios",
                "Preencha ao menos impacto observado ou observa??es.",
                self,
            )
            return

        self.db.save_ausencia(data, self.record_id)
        if self.on_save:
            self.on_save()
        show_info("Registro salvo", "Aus?ncia salva com sucesso.", self)
        self.destroy()