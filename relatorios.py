from __future__ import annotations

import csv
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, ttk

from utils import (
    DateInput,
    EXPORT_DIR,
    center_window,
    current_date_iso,
    current_timestamp,
    format_date_display,
    normalize_date,
    set_text,
    show_error,
    show_info,
    show_warning,
)


def has_reportlab() -> bool:
    try:
        from reportlab.lib.pagesizes import A4  # noqa: F401
        from reportlab.pdfgen import canvas  # noqa: F401
        return True
    except ImportError:
        return False


class RelatoriosWindow(tk.Toplevel):
    PERIOD_EVIDENCE_OPTIONS = {
        "Ocultar totalmente": "none",
        "Mostrar apenas a quantidade": "count",
        "Incluir evidências no relatório": "embed",
    }
    ATA_BREAK_OPTIONS = {
        "Quebrar por data": "date",
        "Quebrar por hora": "time",
    }
    DEFAULT_CSV_FIELDS = [
        "categoria",
        "data",
        "hora",
        "tipo",
        "espaco",
        "professor",
        "descricao",
        "providencias",
        "encaminhamento",
        "observacoes",
    ]

    def __init__(self, parent: tk.Misc, db, initial_mode: str = "dia") -> None:
        super().__init__(parent)
        self.db = db
        self.initial_mode = initial_mode
        self.professor_map = {"": None}
        self.space_map = {"": None}
        self.current_dataset: list[dict] = []
        self.current_csv_fields = list(self.DEFAULT_CSV_FIELDS)
        self.current_dataset_name = ""
        self.current_preview = ""
        self.current_report_context: dict = {}
        self.pdf_available = has_reportlab()

        self.title("Relatórios e exportações")
        center_window(self, 1320, 820, parent=parent)
        self._build()
        self._load_references()
        self._apply_mode(initial_mode)

    def _build(self) -> None:
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        controls = ttk.LabelFrame(main_frame, text="Configuração do relatório")
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)
        controls.columnconfigure(5, weight=1)

        ttk.Label(controls, text="Data do relatório").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.day_entry = DateInput(controls, width=14)
        self.day_entry.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(controls, text="Data inicial").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.start_entry = DateInput(controls, width=14)
        self.start_entry.grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(controls, text="Data final").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        self.end_entry = DateInput(controls, width=14)
        self.end_entry.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(controls, text="Professor").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.professor_combo = ttk.Combobox(controls, state="readonly", width=28)
        self.professor_combo.grid(row=1, column=1, columnspan=2, padx=4, pady=4, sticky="ew")

        ttk.Label(controls, text="Espaço").grid(row=1, column=3, padx=4, pady=4, sticky="w")
        self.space_combo = ttk.Combobox(controls, state="readonly", width=28)
        self.space_combo.grid(row=1, column=4, columnspan=2, padx=4, pady=4, sticky="ew")

        ttk.Label(controls, text="Evidências no relatório").grid(row=2, column=0, padx=4, pady=4, sticky="w")
        self.period_evidence_combo = ttk.Combobox(
            controls,
            state="readonly",
            values=list(self.PERIOD_EVIDENCE_OPTIONS.keys()),
            width=28,
        )
        self.period_evidence_combo.grid(row=2, column=1, columnspan=2, padx=4, pady=4, sticky="ew")
        self.period_evidence_combo.set("Ocultar totalmente")

        ttk.Label(controls, text="Formato da ata").grid(row=2, column=3, padx=4, pady=4, sticky="w")
        self.ata_break_combo = ttk.Combobox(
            controls,
            state="readonly",
            values=list(self.ATA_BREAK_OPTIONS.keys()),
            width=28,
        )
        self.ata_break_combo.grid(row=2, column=4, columnspan=2, padx=4, pady=4, sticky="ew")
        self.ata_break_combo.set("Quebrar por data")

        report_actions = ttk.Frame(controls)
        report_actions.grid(row=3, column=0, columnspan=6, sticky="w", padx=4, pady=4)
        ttk.Button(report_actions, text="Relatório do dia", command=self.generate_day_report).pack(side="left", padx=4)
        ttk.Button(report_actions, text="Relatório por período", command=self.generate_period_report).pack(side="left", padx=4)
        ttk.Button(report_actions, text="Relatório por professor", command=self.generate_professor_report).pack(side="left", padx=4)
        ttk.Button(report_actions, text="Relatório por espaço", command=self.generate_space_report).pack(side="left", padx=4)
        ttk.Button(report_actions, text="Relatório em ata", command=self.generate_minutes_report).pack(side="left", padx=4)
        ttk.Button(report_actions, text="Ata por período", command=self.generate_period_minutes_report).pack(side="left", padx=4)

        export_actions = ttk.Frame(controls)
        export_actions.grid(row=4, column=0, columnspan=6, sticky="w", padx=4, pady=(0, 4))
        ttk.Button(export_actions, text="Exportar TXT", command=self.export_txt).pack(side="left", padx=4)
        ttk.Button(export_actions, text="Exportar CSV", command=self.export_csv).pack(side="left", padx=4)

        self.pdf_button = ttk.Button(export_actions, text="Exportar PDF", command=self.export_pdf)
        self.pdf_button.pack(side="left", padx=4)

        self.evidence_pdf_button = ttk.Button(export_actions, text="Evidências PDF", command=self.export_evidence_pdf)
        self.evidence_pdf_button.pack(side="left", padx=4)

        ttk.Button(export_actions, text="Abrir pasta exportada", command=self.open_export_folder).pack(side="left", padx=4)

        ttk.Label(
            controls,
            text="Dica: Professor e Espaço em branco = todos. Exceções: relatório por professor exige professor e relatório por espaço exige espaço.",
        ).grid(row=5, column=0, columnspan=6, sticky="w", padx=4, pady=(2, 0))

        if not self.pdf_available:
            self.pdf_button.config(text="Exportar PDF (instale reportlab)", state="disabled")
            self.evidence_pdf_button.config(text="Evidências PDF (instale reportlab)", state="disabled")
            ttk.Label(
                controls,
                text="PDF indisponível neste Python. Instale com: pip install reportlab",
                foreground="#8a5a00",
            ).grid(row=6, column=0, columnspan=6, sticky="w", padx=4, pady=(4, 0))

        preview_frame = ttk.LabelFrame(main_frame, text="Pré-visualização")
        preview_frame.grid(row=1, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.preview_text = tk.Text(preview_frame, wrap="word")
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        self.preview_text.config(state="disabled")

    def _load_references(self) -> None:
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

        self.day_entry.insert(0, format_date_display(current_date_iso()))

    def _apply_mode(self, mode: str) -> None:
        if mode == "dia":
            self.generate_day_report()
        elif mode == "periodo":
            self.generate_period_report()
        elif mode == "professor":
            self.generate_professor_report()
        elif mode == "espaco":
            self.generate_space_report()
        elif mode == "exportar":
            self.generate_day_report()

    def _normalized_period(self) -> tuple[str | None, str | None]:
        start = normalize_date(self.start_entry.get()) if self.start_entry.get().strip() else None
        end = normalize_date(self.end_entry.get()) if self.end_entry.get().strip() else None
        return start, end

    def _selected_period_evidence_mode(self) -> str:
        return self.PERIOD_EVIDENCE_OPTIONS.get(self.period_evidence_combo.get(), "count")

    def _selected_ata_break_mode(self) -> str:
        return self.ATA_BREAK_OPTIONS.get(self.ata_break_combo.get(), "date")

    def _has_meaningful_value(self, value: object) -> bool:
        if value is None:
            return False
        text = str(value).strip()
        return bool(text) and text != "-"

    def _append_minutes_part(self, parts: list[str], label: str, value: object) -> None:
        if self._has_meaningful_value(value):
            parts.append(f"{label}: {value}")

    def _format_time_range(self, start: str | None, end: str | None, fallback: str = "Sem horário informado") -> str:
        if start and end:
            return f"{start} até {end}"
        if start:
            return f"a partir de {start}"
        if end:
            return f"até {end}"
        return fallback

    def _build_clean_intercorrencia_minutes_text(self, record: dict, evidence_mode: str) -> str:
        full_record = self._get_intercorrencia_with_evidences(record)
        evidencias = full_record.get("evidencias") or []
        parts = [
            f"registra-se intercorrência classificada como {record['tipo_nome']}, no espaço {record['espaco_nome']}",
            f"descrição objetiva: {record['descricao_objetiva']}",
        ]
        if self._has_meaningful_value(record.get("professor_nome")):
            parts.append(f"com professor relacionado {record['professor_nome']}")
        self._append_minutes_part(parts, "pessoas relacionadas", record.get("pessoas_relacionadas"))
        self._append_minutes_part(parts, "providências adotadas", record.get("providencias_adotadas"))
        self._append_minutes_part(parts, "encaminhamento realizado", record.get("encaminhado_para"))
        self._append_minutes_part(parts, "observações complementares", record.get("observacoes"))
        if evidence_mode == "count" and evidencias:
            parts.append(f"evidências anexadas: {len(evidencias)}")
        elif evidence_mode == "embed" and evidencias:
            nomes = ", ".join(
                item.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                for index, item in enumerate(evidencias)
            )
            parts.append(f"evidências anexadas: {len(evidencias)}")
            parts.append(f"arquivos de evidência: {nomes}")
        return "; ".join(parts) + "."

    def _build_clean_ausencia_minutes_text(self, record: dict) -> str:
        parts = [
            f"registra-se ausência do professor {record['professor_nome']}",
            f"no espaço {record['espaco_nome']}",
            f"tipo de ausência: {record['tipo_ausencia']}",
        ]
        if record.get("ausencia_integral") == "sim":
            parts.append("horário informado: ausência integral")
        elif record.get("hora_inicio") or record.get("hora_fim"):
            parts.append(
                f"horário informado: {self._format_time_range(record.get('hora_inicio'), record.get('hora_fim'))}"
            )
        self._append_minutes_part(parts, "comunicação prévia", record.get("havia_comunicacao_previa"))
        self._append_minutes_part(parts, "houve substituição", record.get("houve_substituicao"))
        self._append_minutes_part(parts, "impacto observado", record.get("impacto_observado"))
        self._append_minutes_part(parts, "providência adotada", record.get("providencia_tomada"))
        self._append_minutes_part(parts, "observações complementares", record.get("observacoes"))
        return "; ".join(parts) + "."

    def _build_clean_rotina_minutes_text(self, record: dict, evidence_mode: str) -> str:
        full_record = self._get_rotina_with_evidences(record)
        evidencias = full_record.get("evidencias") or []
        parts = [
            f"registra-se rotina docente na categoria {record['categoria']}",
            f"professores envolvidos: {record['professor_nome']}",
            f"título da atividade: {record['titulo']}",
            f"descrição da atividade: {record['descricao_atividade']}",
        ]
        self._append_minutes_part(parts, "espaço", record.get("espaco_nome"))
        self._append_minutes_part(parts, "turma ou público", record.get("turma_ou_publico"))
        self._append_minutes_part(parts, "objetivos", record.get("objetivos"))
        self._append_minutes_part(parts, "recursos utilizados", record.get("recursos_utilizados"))
        self._append_minutes_part(parts, "encaminhamentos", record.get("encaminhamentos"))
        self._append_minutes_part(parts, "observações complementares", record.get("observacoes"))
        if evidence_mode == "count" and evidencias:
            parts.append(f"evidências anexadas: {len(evidencias)}")
        elif evidence_mode == "embed" and evidencias:
            nomes = ", ".join(
                item.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                for index, item in enumerate(evidencias)
            )
            parts.append(f"evidências anexadas: {len(evidencias)}")
            parts.append(f"arquivos de evidência: {nomes}")
        return "; ".join(parts) + "."

    def _set_output(
        self,
        title: str,
        preview: str,
        dataset: list[dict],
        dataset_name: str,
        csv_fields: list[str] | None = None,
        context: dict | None = None,
    ) -> None:
        self.current_preview = f"{title}\n\n{preview}" if preview else title
        self.current_dataset = dataset
        self.current_csv_fields = csv_fields or list(self.DEFAULT_CSV_FIELDS)
        self.current_dataset_name = dataset_name
        self.current_report_context = context or {}
        set_text(self.preview_text, self.current_preview)

    def _collect_report_filters(self) -> tuple[dict, str | None, bool]:
        filters: dict = {}
        specific_date = normalize_date(self.day_entry.get()) if self.day_entry.get().strip() else None
        start, end = self._normalized_period()
        has_period = bool(start or end)
        if has_period:
            if start:
                filters["start_date"] = start
            if end:
                filters["end_date"] = end
            specific_date = None
        elif specific_date:
            filters["specific_date"] = specific_date

        professor_id = self.professor_map.get(self.professor_combo.get())
        if professor_id:
            filters["professor_id"] = professor_id

        space_id = self.space_map.get(self.space_combo.get())
        if space_id:
            filters["espaco_id"] = space_id

        return filters, specific_date, has_period

    def _get_intercorrencia_with_evidences(self, record: dict) -> dict:
        if "evidencias" in record:
            return record
        return self.db.get_intercorrencia(record["id"]) or record

    def _get_rotina_with_evidences(self, record: dict) -> dict:
        if "evidencias" in record:
            return record
        return self.db.get_rotina_docente(record["id"]) or record

    def _render_intercorrencias(self, records: list[dict], evidence_mode: str = "count") -> str:
        if not records:
            return "Nenhuma intercorrência encontrada."
        lines = []
        for record in records:
            full_record = self._get_intercorrencia_with_evidences(record)
            evidencias = full_record.get("evidencias") or []
            lines.append(
                f"Data: {format_date_display(record['data'])} | Hora: {record['hora']} | Tipo: {record['tipo_nome']} | "
                f"Espaço: {record['espaco_nome']} | Professor: {record.get('professor_nome') or '-'}"
            )
            lines.append(f"Descrição objetiva: {record['descricao_objetiva']}")
            lines.append(f"Providências adotadas: {record.get('providencias_adotadas') or '-'}")
            lines.append(f"Encaminhamento: {record.get('encaminhado_para') or '-'}")
            lines.append(f"Observações: {record.get('observacoes') or '-'}")
            if evidence_mode == "count":
                lines.append(f"Evidências anexadas: {len(evidencias)}")
            elif evidence_mode == "embed":
                lines.append(f"Evidências anexadas: {len(evidencias)}")
                nomes = ", ".join(
                    item.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                    for index, item in enumerate(evidencias)
                )
                lines.append(f"Arquivos de evidência: {nomes or '-'}")
            lines.append("")
        return "\n".join(lines).strip()

    def _render_ausencias(self, records: list[dict]) -> str:
        if not records:
            return "Nenhuma ausência encontrada."
        lines = []
        for record in records:
            horario = (
                "Ausência integral"
                if record.get("ausencia_integral") == "sim"
                else f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
            )
            lines.append(
                f"Data: {format_date_display(record['data'])} | Horário: {horario} | Professor: {record['professor_nome']} | "
                f"Espaço: {record['espaco_nome']} | Tipo: {record['tipo_ausencia']}"
            )
            lines.append(f"Comunicação prévia: {record.get('havia_comunicacao_previa') or '-'}")
            lines.append(f"Substituição: {record.get('houve_substituicao') or '-'}")
            lines.append(f"Impacto observado: {record.get('impacto_observado') or '-'}")
            lines.append(f"Providência tomada: {record.get('providencia_tomada') or '-'}")
            lines.append(f"Observações: {record.get('observacoes') or '-'}")
            lines.append("")
        return "\n".join(lines).strip()

    def _render_rotinas(self, records: list[dict], evidence_mode: str = "count") -> str:
        if not records:
            return "Nenhuma rotina docente encontrada."
        lines = []
        for record in records:
            full_record = self._get_rotina_with_evidences(record)
            evidencias = full_record.get("evidencias") or []
            horario = ""
            if record.get("hora_inicio") or record.get("hora_fim"):
                horario = f" | Horário: {record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
            lines.append(
                f"Data: {format_date_display(record['data'])}{horario} | Categoria: {record['categoria']} | "
                f"Professores: {record['professor_nome']} | Espaço: {record.get('espaco_nome') or '-'}"
            )
            lines.append(f"Título: {record['titulo']}")
            lines.append(f"Turma ou público: {record.get('turma_ou_publico') or '-'}")
            lines.append(f"Descrição da atividade: {record['descricao_atividade']}")
            lines.append(f"Objetivos: {record.get('objetivos') or '-'}")
            lines.append(f"Recursos utilizados: {record.get('recursos_utilizados') or '-'}")
            lines.append(f"Encaminhamentos: {record.get('encaminhamentos') or '-'}")
            lines.append(f"Observações: {record.get('observacoes') or '-'}")
            if evidence_mode == "count":
                lines.append(f"Evidências anexadas: {len(evidencias)}")
            elif evidence_mode == "embed":
                lines.append(f"Evidências anexadas: {len(evidencias)}")
                nomes = ", ".join(
                    item.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                    for index, item in enumerate(evidencias)
                )
                lines.append(f"Arquivos de evidência: {nomes or '-'}")
            lines.append("")
        return "\n".join(lines).strip()

    def generate_day_report(self) -> None:
        report_date = normalize_date(self.day_entry.get()) if self.day_entry.get().strip() else current_date_iso()
        evidence_mode = self._selected_period_evidence_mode()
        filters = {"specific_date": report_date}
        inter = self.db.search_intercorrencias(filters)
        aus = self.db.search_ausencias(filters)
        rotinas = self.db.search_rotinas_docentes(filters)

        if evidence_mode == "embed":
            inter_context = [self._get_intercorrencia_with_evidences(record) for record in inter]
            rotinas_context = [self._get_rotina_with_evidences(record) for record in rotinas]
        else:
            inter_context = inter
            rotinas_context = rotinas

        title = f"Relatório do dia - {format_date_display(report_date)}"
        preview = (
            "Intercorrências\n"
            f"{self._render_intercorrencias(inter_context, evidence_mode=evidence_mode)}\n\n"
            "Ausências de professores\n"
            f"{self._render_ausencias(aus)}\n\n"
            "Rotinas docentes\n"
            f"{self._render_rotinas(rotinas_context, evidence_mode=evidence_mode)}"
        )
        dataset, csv_fields = self._combine_for_export(inter_context, aus, rotinas_context, evidence_mode=evidence_mode)
        self._set_output(
            title,
            preview,
            dataset,
            "relatorio_dia",
            csv_fields=csv_fields,
            context={
                "mode": "dia",
                "evidence_mode": evidence_mode,
                "inter": inter_context,
                "aus": aus,
                "rotinas": rotinas_context,
                "title": title,
            },
        )

    def generate_period_report(self) -> None:
        start, end = self._normalized_period()
        evidence_mode = self._selected_period_evidence_mode()
        filters = {"start_date": start, "end_date": end}
        inter = self.db.search_intercorrencias(filters)
        aus = self.db.search_ausencias(filters)
        rotinas = self.db.search_rotinas_docentes(filters)

        if evidence_mode == "embed":
            inter_context = [self._get_intercorrencia_with_evidences(record) for record in inter]
            rotinas_context = [self._get_rotina_with_evidences(record) for record in rotinas]
        else:
            inter_context = inter
            rotinas_context = rotinas

        title = f"Relatório por período - {format_date_display(start or '') or 'início aberto'} a {format_date_display(end or '') or 'fim aberto'}"
        preview = (
            f"Total de intercorrências: {len(inter)}\n"
            f"Total de ausências: {len(aus)}\n"
            f"Total de rotinas docentes: {len(rotinas)}\n\n"
            "Intercorrências\n"
            f"{self._render_intercorrencias(inter_context, evidence_mode=evidence_mode)}\n\n"
            "Ausências de professores\n"
            f"{self._render_ausencias(aus)}\n\n"
            "Rotinas docentes\n"
            f"{self._render_rotinas(rotinas_context, evidence_mode=evidence_mode)}"
        )
        dataset, csv_fields = self._combine_for_export(inter_context, aus, rotinas_context, evidence_mode=evidence_mode)
        self._set_output(
            title,
            preview,
            dataset,
            "relatorio_periodo",
            csv_fields=csv_fields,
            context={
                "mode": "periodo",
                "evidence_mode": evidence_mode,
                "inter": inter_context,
                "aus": aus,
                "rotinas": rotinas_context,
                "title": title,
                "start": start,
                "end": end,
            },
        )

    def generate_professor_report(self) -> None:
        professor_name = self.professor_combo.get()
        professor_id = self.professor_map.get(professor_name)
        if not professor_id:
            show_error("Filtro obrigatório", "Selecione um professor para gerar o relatório.", self)
            return
        start, end = self._normalized_period()
        evidence_mode = self._selected_period_evidence_mode()
        filters = {"professor_id": professor_id, "start_date": start, "end_date": end}
        inter = self.db.search_intercorrencias(filters)
        aus = self.db.search_ausencias(filters)
        rotinas = self.db.search_rotinas_docentes(filters)

        if evidence_mode == "embed":
            inter_context = [self._get_intercorrencia_with_evidences(record) for record in inter]
            rotinas_context = [self._get_rotina_with_evidences(record) for record in rotinas]
        else:
            inter_context = inter
            rotinas_context = rotinas

        title = f"Histórico do professor - {professor_name}"
        preview = (
            f"Período: {format_date_display(start or '') or 'início aberto'} a {format_date_display(end or '') or 'fim aberto'}\n\n"
            "Intercorrências\n"
            f"{self._render_intercorrencias(inter_context, evidence_mode=evidence_mode)}\n\n"
            "Ausências de professores\n"
            f"{self._render_ausencias(aus)}\n\n"
            "Rotinas docentes\n"
            f"{self._render_rotinas(rotinas_context, evidence_mode=evidence_mode)}"
        )
        dataset, csv_fields = self._combine_for_export(inter_context, aus, rotinas_context, evidence_mode=evidence_mode)
        self._set_output(
            title,
            preview,
            dataset,
            "relatorio_professor",
            csv_fields=csv_fields,
            context={
                "mode": "professor",
                "evidence_mode": evidence_mode,
                "inter": inter_context,
                "aus": aus,
                "rotinas": rotinas_context,
                "title": title,
            },
        )

    def generate_space_report(self) -> None:
        space_name = self.space_combo.get()
        space_id = self.space_map.get(space_name)
        if not space_id:
            show_error("Filtro obrigatório", "Selecione um espaço para gerar o relatório.", self)
            return
        start, end = self._normalized_period()
        evidence_mode = self._selected_period_evidence_mode()
        filters = {"espaco_id": space_id, "start_date": start, "end_date": end}
        inter = self.db.search_intercorrencias(filters)
        aus = self.db.search_ausencias(filters)
        rotinas = self.db.search_rotinas_docentes(filters)

        if evidence_mode == "embed":
            inter_context = [self._get_intercorrencia_with_evidences(record) for record in inter]
            rotinas_context = [self._get_rotina_with_evidences(record) for record in rotinas]
        else:
            inter_context = inter
            rotinas_context = rotinas

        title = f"Histórico do espaço - {space_name}"
        preview = (
            f"Período: {format_date_display(start or '') or 'início aberto'} a {format_date_display(end or '') or 'fim aberto'}\n\n"
            "Intercorrências\n"
            f"{self._render_intercorrencias(inter_context, evidence_mode=evidence_mode)}\n\n"
            "Ausências de professores\n"
            f"{self._render_ausencias(aus)}\n\n"
            "Rotinas docentes\n"
            f"{self._render_rotinas(rotinas_context, evidence_mode=evidence_mode)}"
        )
        dataset, csv_fields = self._combine_for_export(inter_context, aus, rotinas_context, evidence_mode=evidence_mode)
        self._set_output(
            title,
            preview,
            dataset,
            "relatorio_espaco",
            csv_fields=csv_fields,
            context={
                "mode": "espaco",
                "evidence_mode": evidence_mode,
                "inter": inter_context,
                "aus": aus,
                "rotinas": rotinas_context,
                "title": title,
            },
        )

    def _intercorrencia_minutes_text(self, record: dict, evidence_mode: str) -> str:
        full_record = self._get_intercorrencia_with_evidences(record)
        evidencias = full_record.get("evidencias") or []
        parts = [
            f"registra-se intercorrência classificada como {record['tipo_nome']}, no espaço {record['espaco_nome']}",
            f"com professor relacionado {record.get('professor_nome') or '-'}",
            f"pessoas relacionadas: {record.get('pessoas_relacionadas') or '-'}",
            f"descrição objetiva: {record['descricao_objetiva']}",
            f"providências adotadas: {record.get('providencias_adotadas') or '-'}",
            f"encaminhamento realizado: {record.get('encaminhado_para') or '-'}",
            f"observações complementares: {record.get('observacoes') or '-'}",
        ]
        if evidence_mode == "count":
            parts.append(f"evidências anexadas: {len(evidencias)}")
        elif evidence_mode == "embed":
            nomes = ", ".join(
                item.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                for index, item in enumerate(evidencias)
            )
            parts.append(f"evidências anexadas: {len(evidencias)}")
            parts.append(f"arquivos de evidência: {nomes or '-'}")
        return "; ".join(parts) + "."

    def _ausencia_minutes_text(self, record: dict) -> str:
        horario = (
            "ausência integral"
            if record.get("ausencia_integral") == "sim"
            else f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
        )
        parts = [
            f"registra-se ausência do professor {record['professor_nome']}",
            f"no espaço {record['espaco_nome']}",
            f"tipo de ausência: {record['tipo_ausencia']}",
            f"horário informado: {horario}",
            f"comunicação prévia: {record.get('havia_comunicacao_previa') or '-'}",
            f"houve substituição: {record.get('houve_substituicao') or '-'}",
            f"impacto observado: {record.get('impacto_observado') or '-'}",
            f"providência adotada: {record.get('providencia_tomada') or '-'}",
            f"observações complementares: {record.get('observacoes') or '-'}",
        ]
        return "; ".join(parts) + "."

    def _rotina_minutes_text(self, record: dict, evidence_mode: str) -> str:
        full_record = self._get_rotina_with_evidences(record)
        evidencias = full_record.get("evidencias") or []
        parts = [
            f"registra-se rotina docente na categoria {record['categoria']}",
            f"professores envolvidos: {record['professor_nome']}",
            f"espaço: {record.get('espaco_nome') or '-'}",
            f"título da atividade: {record['titulo']}",
            f"turma ou público: {record.get('turma_ou_publico') or '-'}",
            f"descrição da atividade: {record['descricao_atividade']}",
            f"objetivos: {record.get('objetivos') or '-'}",
            f"recursos utilizados: {record.get('recursos_utilizados') or '-'}",
            f"encaminhamentos: {record.get('encaminhamentos') or '-'}",
            f"observações complementares: {record.get('observacoes') or '-'}",
        ]
        if evidence_mode == "count":
            parts.append(f"evidências anexadas: {len(evidencias)}")
        elif evidence_mode == "embed":
            nomes = ", ".join(
                item.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                for index, item in enumerate(evidencias)
            )
            parts.append(f"evidências anexadas: {len(evidencias)}")
            parts.append(f"arquivos de evidência: {nomes or '-'}")
        return "; ".join(parts) + "."

    def _build_minutes_events(
        self,
        inter: list[dict],
        aus: list[dict],
        rotinas: list[dict],
        evidence_mode: str,
    ) -> list[dict]:
        events: list[dict] = []
        for record in inter:
            events.append(
                {
                    "date": record["data"],
                    "date_display": format_date_display(record["data"]),
                    "time_sort": record.get("hora") or "99:99",
                    "time_display": record.get("hora") or "Sem horário",
                    "text": self._build_clean_intercorrencia_minutes_text(record, evidence_mode),
                }
            )
        for record in aus:
            time_sort = record.get("hora_inicio") or record.get("hora_fim") or "99:99"
            time_display = (
                "Ausência integral"
                if record.get("ausencia_integral") == "sim"
                else f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
            )
            events.append(
                {
                    "date": record["data"],
                    "date_display": format_date_display(record["data"]),
                    "time_sort": time_sort,
                    "time_display": time_display,
                    "text": self._build_clean_ausencia_minutes_text(record),
                }
            )
        for record in rotinas:
            time_sort = record.get("hora_inicio") or record.get("hora_fim") or "99:99"
            time_display = (
                f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
                if record.get("hora_inicio") or record.get("hora_fim")
                else "Sem horário"
            )
            events.append(
                {
                    "date": record["data"],
                    "date_display": format_date_display(record["data"]),
                    "time_sort": time_sort,
                    "time_display": time_display,
                    "text": self._build_clean_rotina_minutes_text(record, evidence_mode),
                }
            )
        events.sort(key=lambda item: (item["date"], item["time_sort"], item["text"]))
        return events

    def _build_minutes_preview(self, events: list[dict], break_mode: str) -> str:
        if not events:
            return "Nenhum registro encontrado para gerar a ata."

        if break_mode == "time":
            lines = []
            for event in events:
                lines.append(f"Na data de {event['date_display']}, no horário de {event['time_display']}, {event['text']}")
                lines.append("")
            return "\n".join(lines).strip()

        lines = []
        current_date = None
        for event in events:
            if event["date"] != current_date:
                if lines:
                    lines.append("")
                current_date = event["date"]
                lines.append(f"Data: {event['date_display']}")
            lines.append(f"No horário de {event['time_display']}, {event['text']}")
        return "\n".join(lines).strip()

    def _generate_minutes_report(self, force_period: bool = False) -> None:
        evidence_mode = self._selected_period_evidence_mode()
        break_mode = self._selected_ata_break_mode()
        start, end = self._normalized_period()
        if force_period and not (start or end):
            show_error("Filtro obrigatório", "Informe a data inicial e/ou a data final para gerar a ata por período.", self)
            return

        if force_period:
            filters = {}
            if start:
                filters["start_date"] = start
            if end:
                filters["end_date"] = end
            professor_id = self.professor_map.get(self.professor_combo.get())
            if professor_id:
                filters["professor_id"] = professor_id
            space_id = self.space_map.get(self.space_combo.get())
            if space_id:
                filters["espaco_id"] = space_id
            specific_date = None
            has_period = True
        else:
            filters, specific_date, has_period = self._collect_report_filters()

        inter = self.db.search_intercorrencias(filters)
        aus = self.db.search_ausencias(filters)
        rotinas = self.db.search_rotinas_docentes(filters)

        if evidence_mode == "embed":
            inter_context = [self._get_intercorrencia_with_evidences(record) for record in inter]
            rotinas_context = [self._get_rotina_with_evidences(record) for record in rotinas]
        else:
            inter_context = inter
            rotinas_context = rotinas

        title_parts = []
        if has_period:
            title_parts.append(f"{format_date_display(start or '') or 'início aberto'} a {format_date_display(end or '') or 'fim aberto'}")
        elif specific_date:
            title_parts.append(format_date_display(specific_date))
        if self.professor_combo.get():
            title_parts.append(f"Professor: {self.professor_combo.get()}")
        if self.space_combo.get():
            title_parts.append(f"Espaço: {self.space_combo.get()}")

        title = "Ata de registros"
        if title_parts:
            title += " - " + " | ".join(title_parts)

        events = self._build_minutes_events(inter_context, aus, rotinas_context, evidence_mode)
        organization_text = "organizada por data" if break_mode == "date" else "organizada por horário"
        if has_period:
            scope_text = f"no período de {format_date_display(start or '') or 'início aberto'} a {format_date_display(end or '') or 'fim aberto'}"
        elif specific_date:
            scope_text = f"na data de {format_date_display(specific_date)}"
        else:
            scope_text = "no recorte informado"
        intro = (
            f"Fica registrada a presente ata, {organization_text}, referente aos fatos observados {scope_text}.\n"
        )
        totals = (
            f"Total de intercorrências: {len(inter)}\n"
            f"Total de ausências: {len(aus)}\n"
            f"Total de rotinas docentes: {len(rotinas)}\n\n"
        )
        preview = intro + totals + self._build_minutes_preview(events, break_mode)
        dataset, csv_fields = self._combine_for_export(inter_context, aus, rotinas_context, evidence_mode=evidence_mode)
        self._set_output(
            title,
            preview,
            dataset,
            "ata_registros",
            csv_fields=csv_fields,
            context={
                "mode": "ata",
                "layout": "ata",
                "evidence_mode": evidence_mode,
                "break_mode": break_mode,
                "inter": inter_context,
                "aus": aus,
                "rotinas": rotinas_context,
                "title": title,
            },
        )

    def generate_minutes_report(self) -> None:
        self._generate_minutes_report(force_period=False)

    def generate_period_minutes_report(self) -> None:
        self._generate_minutes_report(force_period=True)

    def _build_evidence_export_fields(self, evidence_mode: str) -> list[str]:
        fields = list(self.DEFAULT_CSV_FIELDS)
        if evidence_mode in {"count", "embed"}:
            fields.append("evidence_count")
        if evidence_mode == "embed":
            fields.append("evidence_files")
        return fields

    def _combine_for_export(
        self,
        inter: list[dict],
        aus: list[dict],
        rotinas: list[dict],
        evidence_mode: str = "count",
    ) -> tuple[list[dict], list[str]]:
        dataset: list[dict] = []
        csv_fields = self._build_evidence_export_fields(evidence_mode)

        for record in inter:
            full_record = self._get_intercorrencia_with_evidences(record)
            evidencias = full_record.get("evidencias") or []
            item = {
                "categoria": "intercorrencia",
                "data": format_date_display(record["data"]),
                "hora": record["hora"],
                "tipo": record["tipo_nome"],
                "espaco": record["espaco_nome"],
                "professor": record.get("professor_nome") or "",
                "descricao": record["descricao_objetiva"],
                "providencias": record.get("providencias_adotadas") or "",
                "encaminhamento": record.get("encaminhado_para") or "",
                "observacoes": record.get("observacoes") or "",
            }
            if evidence_mode in {"count", "embed"}:
                item["evidence_count"] = len(evidencias)
            if evidence_mode == "embed":
                item["evidence_files"] = ", ".join(
                    evidence.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                    for index, evidence in enumerate(evidencias)
                )
            dataset.append(item)

        for record in aus:
            item = {
                "categoria": "ausencia",
                "data": format_date_display(record["data"]),
                "hora": "Ausência integral"
                if record.get("ausencia_integral") == "sim"
                else f"{record.get('hora_inicio') or ''} - {record.get('hora_fim') or ''}".strip(" -"),
                "tipo": record["tipo_ausencia"],
                "espaco": record["espaco_nome"],
                "professor": record["professor_nome"],
                "descricao": record.get("impacto_observado") or "",
                "providencias": record.get("providencia_tomada") or "",
                "encaminhamento": record.get("havia_comunicacao_previa") or "",
                "observacoes": record.get("observacoes") or "",
            }
            if evidence_mode in {"count", "embed"}:
                item["evidence_count"] = ""
            if evidence_mode == "embed":
                item["evidence_files"] = ""
            dataset.append(item)

        for record in rotinas:
            full_record = self._get_rotina_with_evidences(record)
            evidencias = full_record.get("evidencias") or []
            item = {
                "categoria": "rotina_docente",
                "data": format_date_display(record["data"]),
                "hora": f"{record.get('hora_inicio') or ''} - {record.get('hora_fim') or ''}".strip(" -"),
                "tipo": record["categoria"],
                "espaco": record.get("espaco_nome") or "",
                "professor": record["professor_nome"],
                "descricao": f"{record['titulo']} | {record['descricao_atividade']}",
                "providencias": record.get("encaminhamentos") or "",
                "encaminhamento": record.get("objetivos") or "",
                "observacoes": record.get("observacoes") or "",
            }
            if evidence_mode in {"count", "embed"}:
                item["evidence_count"] = len(evidencias)
            if evidence_mode == "embed":
                item["evidence_files"] = ", ".join(
                    evidence.get("nome_arquivo") or f"evidencia_{index + 1}.png"
                    for index, evidence in enumerate(evidencias)
                )
            dataset.append(item)

        dataset.sort(key=lambda item: (item["data"], item["hora"], item["categoria"]))
        return dataset, csv_fields

    def _default_export_path(self, suffix: str, base_name: str | None = None) -> Path:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        name = base_name or self.current_dataset_name or "relatorio"
        timestamp = current_timestamp().replace(":", "-").replace(" ", "_")
        return EXPORT_DIR / f"{name}_{timestamp}.{suffix}"

    def open_export_folder(self) -> None:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(EXPORT_DIR))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(EXPORT_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(EXPORT_DIR)])
        except Exception:
            show_warning(
                "Abertura manual",
                f"Não foi possível abrir a pasta automaticamente.\n\nAbra manualmente:\n{EXPORT_DIR}",
                self,
            )

    def _wrap_line(self, text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
        from reportlab.pdfbase.pdfmetrics import stringWidth

        if not text:
            return [""]
        wrapped_lines: list[str] = []
        for paragraph in text.splitlines() or [""]:
            if not paragraph.strip():
                wrapped_lines.append("")
                continue
            current = ""
            for word in paragraph.split():
                candidate = word if not current else f"{current} {word}"
                if stringWidth(candidate, font_name, font_size) <= max_width:
                    current = candidate
                else:
                    if current:
                        wrapped_lines.append(current)
                    current = word
                    while stringWidth(current, font_name, font_size) > max_width and len(current) > 1:
                        split_index = len(current) - 1
                        while split_index > 1 and stringWidth(current[:split_index], font_name, font_size) > max_width:
                            split_index -= 1
                        wrapped_lines.append(current[:split_index])
                        current = current[split_index:]
            if current:
                wrapped_lines.append(current)
        return wrapped_lines or [""]

    def export_txt(self) -> None:
        if not self.current_preview:
            show_error("Sem relatório", "Gere um relatório antes de exportar.", self)
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar TXT",
            defaultextension=".txt",
            initialfile=self._default_export_path("txt").name,
            initialdir=str(EXPORT_DIR),
            filetypes=[("Texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return
        Path(target).write_text(self.current_preview, encoding="utf-8")
        show_info("Exportação concluída", f"Arquivo TXT salvo em:\n{target}", self)

    def export_csv(self) -> None:
        if not self.current_dataset:
            show_error("Sem dados", "Gere um relatório antes de exportar.", self)
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar CSV",
            defaultextension=".csv",
            initialfile=self._default_export_path("csv").name,
            initialdir=str(EXPORT_DIR),
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return
        with Path(target).open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.current_csv_fields)
            writer.writeheader()
            writer.writerows(self.current_dataset)
        show_info("Exportação concluída", f"Arquivo CSV salvo em:\n{target}", self)

    def export_pdf(self) -> None:
        if not self.current_preview:
            show_error("Sem relatório", "Gere um relatório antes de exportar.", self)
            return
        if not self.pdf_available:
            show_error(
                "Dependência ausente",
                "A exportação em PDF exige a biblioteca reportlab.\n\nUse no terminal:\npip install reportlab",
                self,
            )
            return

        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar PDF",
            defaultextension=".pdf",
            initialfile=self._default_export_path("pdf").name,
            initialdir=str(EXPORT_DIR),
            filetypes=[("PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return

        if self.current_report_context.get("evidence_mode") == "embed" and self.current_report_context.get("layout") != "ata":
            self._export_period_pdf_with_evidences(Path(target))
            return

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        pdf = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        left_margin = 40
        right_margin = 40
        top_margin = 40
        bottom_margin = 40
        line_height = 14
        font_name = "Helvetica"
        font_size = 10
        usable_width = width - left_margin - right_margin
        y = height - top_margin
        pdf.setFont(font_name, font_size)

        for original_line in self.current_preview.splitlines():
            for line in self._wrap_line(original_line, usable_width, font_name, font_size):
                if y < bottom_margin:
                    pdf.showPage()
                    pdf.setFont(font_name, font_size)
                    y = height - top_margin
                pdf.drawString(left_margin, y, line)
                y -= line_height

        pdf.save()
        show_info("Exportação concluída", f"Arquivo PDF salvo em:\n{target}", self)

    def _export_period_pdf_with_evidences(self, target: Path) -> None:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        context = self.current_report_context
        inter = context.get("inter", [])
        aus = context.get("aus", [])
        rotinas = context.get("rotinas", [])
        title = context.get("title", "Relatório por período")

        pdf = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        left_margin = 36
        right_margin = 36
        top_margin = 42
        bottom_margin = 36
        line_height = 14
        section_gap = 12
        image_gap = 10
        max_image_height = 260
        usable_width = width - left_margin - right_margin
        y = height - top_margin

        def new_page() -> None:
            nonlocal y
            pdf.showPage()
            y = height - top_margin

        def ensure_space(required_height: float) -> None:
            nonlocal y
            if y - required_height < bottom_margin:
                new_page()

        def draw_wrapped_text(text: str, font_name: str, font_size: int, extra_gap: int = 0) -> None:
            nonlocal y
            pdf.setFont(font_name, font_size)
            for line in self._wrap_line(text, usable_width, font_name, font_size):
                ensure_space(line_height)
                pdf.drawString(left_margin, y, line)
                y -= line_height
            y -= extra_gap

        draw_wrapped_text(title, "Helvetica-Bold", 14, extra_gap=4)
        draw_wrapped_text(
            f"Gerado em {current_timestamp()} | Total de intercorrências: {len(inter)} | Total de ausências: {len(aus)} | Total de rotinas docentes: {len(rotinas)}",
            "Helvetica",
            10,
            extra_gap=section_gap,
        )

        if inter:
            draw_wrapped_text("Intercorrências", "Helvetica-Bold", 12, extra_gap=4)
            for record in inter:
                full_record = self._get_intercorrencia_with_evidences(record)
                linhas = [
                    f"Data: {format_date_display(record['data'])} | Hora: {record['hora']} | Tipo: {record['tipo_nome']}",
                    f"Espaço: {record['espaco_nome']} | Professor: {record.get('professor_nome') or '-'}",
                    f"Descrição objetiva: {record['descricao_objetiva']}",
                    f"Providências adotadas: {record.get('providencias_adotadas') or '-'}",
                    f"Encaminhamento: {record.get('encaminhado_para') or '-'}",
                    f"Observações: {record.get('observacoes') or '-'}",
                ]
                for linha in linhas:
                    draw_wrapped_text(linha, "Helvetica", 10)
                evidencias = full_record.get("evidencias") or []
                draw_wrapped_text(f"Evidências anexadas: {len(evidencias)}", "Helvetica", 10)
                for index, evidencia in enumerate(evidencias, start=1):
                    nome = evidencia.get("nome_arquivo") or f"evidencia_{index}.png"
                    draw_wrapped_text(f"Evidência {index}: {nome}", "Helvetica-Bold", 10, extra_gap=4)
                    try:
                        image = ImageReader(BytesIO(evidencia.get("dados") or b""))
                        image_width, image_height = image.getSize()
                        scale = min(usable_width / image_width, max_image_height / image_height, 1.0)
                        draw_width = image_width * scale
                        draw_height = image_height * scale
                        ensure_space(draw_height + image_gap)
                        pdf.drawImage(
                            image,
                            left_margin,
                            y - draw_height,
                            width=draw_width,
                            height=draw_height,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                        y -= draw_height + image_gap
                    except Exception:
                        draw_wrapped_text("Não foi possível renderizar esta evidência no PDF.", "Helvetica", 10, extra_gap=4)
                y -= section_gap

        if aus:
            draw_wrapped_text("Ausências de professores", "Helvetica-Bold", 12, extra_gap=4)
            for record in aus:
                horario = (
                    "Ausência integral"
                    if record.get("ausencia_integral") == "sim"
                    else f"{record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
                )
                linhas = [
                    f"Data: {format_date_display(record['data'])} | Horário: {horario} | Professor: {record['professor_nome']}",
                    f"Espaço: {record['espaco_nome']} | Tipo: {record['tipo_ausencia']}",
                    f"Comunicação prévia: {record.get('havia_comunicacao_previa') or '-'}",
                    f"Substituição: {record.get('houve_substituicao') or '-'}",
                    f"Impacto observado: {record.get('impacto_observado') or '-'}",
                    f"Providência tomada: {record.get('providencia_tomada') or '-'}",
                    f"Observações: {record.get('observacoes') or '-'}",
                ]
                for linha in linhas:
                    draw_wrapped_text(linha, "Helvetica", 10)
                y -= section_gap

        if rotinas:
            draw_wrapped_text("Rotinas docentes", "Helvetica-Bold", 12, extra_gap=4)
            for record in rotinas:
                full_record = self._get_rotina_with_evidences(record)
                horario = ""
                if record.get("hora_inicio") or record.get("hora_fim"):
                    horario = f" | Horário: {record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
                linhas = [
                    f"Data: {format_date_display(record['data'])}{horario} | Categoria: {record['categoria']}",
                    f"Professores: {record['professor_nome']} | Espaço: {record.get('espaco_nome') or '-'}",
                    f"Título: {record['titulo']}",
                    f"Turma ou público: {record.get('turma_ou_publico') or '-'}",
                    f"Descrição da atividade: {record['descricao_atividade']}",
                    f"Objetivos: {record.get('objetivos') or '-'}",
                    f"Recursos utilizados: {record.get('recursos_utilizados') or '-'}",
                    f"Encaminhamentos: {record.get('encaminhamentos') or '-'}",
                    f"Observações: {record.get('observacoes') or '-'}",
                ]
                for linha in linhas:
                    draw_wrapped_text(linha, "Helvetica", 10)
                evidencias = full_record.get("evidencias") or []
                draw_wrapped_text(f"Evidências anexadas: {len(evidencias)}", "Helvetica", 10)
                for index, evidencia in enumerate(evidencias, start=1):
                    nome = evidencia.get("nome_arquivo") or f"evidencia_{index}.png"
                    draw_wrapped_text(f"Evidência {index}: {nome}", "Helvetica-Bold", 10, extra_gap=4)
                    try:
                        image = ImageReader(BytesIO(evidencia.get("dados") or b""))
                        image_width, image_height = image.getSize()
                        scale = min(usable_width / image_width, max_image_height / image_height, 1.0)
                        draw_width = image_width * scale
                        draw_height = image_height * scale
                        ensure_space(draw_height + image_gap)
                        pdf.drawImage(
                            image,
                            left_margin,
                            y - draw_height,
                            width=draw_width,
                            height=draw_height,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                        y -= draw_height + image_gap
                    except Exception:
                        draw_wrapped_text("Não foi possível renderizar esta evidência no PDF.", "Helvetica", 10, extra_gap=4)
                y -= section_gap

        pdf.save()
        show_info("Exportação concluída", f"Arquivo PDF salvo em:\n{target}", self)

    def _collect_evidence_filters(self) -> dict:
        filters: dict[str, str | int | None] = {}
        start, end = self._normalized_period()
        if start or end:
            filters["start_date"] = start
            filters["end_date"] = end
        elif self.day_entry.get().strip():
            filters["specific_date"] = normalize_date(self.day_entry.get())

        if self.professor_combo.get():
            filters["professor_id"] = self.professor_map.get(self.professor_combo.get())
        if self.space_combo.get():
            filters["espaco_id"] = self.space_map.get(self.space_combo.get())
        return filters

    def _load_records_with_evidences(self, filters: dict) -> tuple[list[dict], list[dict]]:
        intercorrencias: list[dict] = []
        for record in self.db.search_intercorrencias(filters):
            completo = self.db.get_intercorrencia(record["id"])
            if completo and completo.get("evidencias"):
                intercorrencias.append(completo)

        rotinas: list[dict] = []
        for record in self.db.search_rotinas_docentes(filters):
            completo = self.db.get_rotina_docente(record["id"])
            if completo and completo.get("evidencias"):
                rotinas.append(completo)

        return intercorrencias, rotinas

    def export_evidence_pdf(self) -> None:
        if not self.pdf_available:
            show_error(
                "Dependência ausente",
                "A exportação em PDF exige a biblioteca reportlab.\n\nUse no terminal:\npip install reportlab",
                self,
            )
            return

        filters = self._collect_evidence_filters()
        intercorrencias, rotinas = self._load_records_with_evidences(filters)
        if not intercorrencias and not rotinas:
            show_error(
                "Sem evidências",
                "Nenhuma intercorrência ou rotina docente com evidências foi encontrada com os filtros atuais.",
                self,
            )
            return

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        target = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar relatório de evidências em PDF",
            defaultextension=".pdf",
            initialfile=self._default_export_path("pdf", "relatorio_evidencias").name,
            initialdir=str(EXPORT_DIR),
            filetypes=[("PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return

        pdf = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        left_margin = 36
        right_margin = 36
        top_margin = 42
        bottom_margin = 36
        line_height = 14
        section_gap = 12
        image_gap = 10
        max_image_height = 260
        usable_width = width - left_margin - right_margin
        y = height - top_margin

        def new_page() -> None:
            nonlocal y
            pdf.showPage()
            y = height - top_margin

        def ensure_space(required_height: float) -> None:
            nonlocal y
            if y - required_height < bottom_margin:
                new_page()

        def draw_wrapped_text(text: str, font_name: str, font_size: int, extra_gap: int = 0) -> None:
            nonlocal y
            pdf.setFont(font_name, font_size)
            for line in self._wrap_line(text, usable_width, font_name, font_size):
                ensure_space(line_height)
                pdf.drawString(left_margin, y, line)
                y -= line_height
            y -= extra_gap

        draw_wrapped_text("Relatório de evidências", "Helvetica-Bold", 14, extra_gap=4)
        draw_wrapped_text(
            f"Gerado em {current_timestamp()} | Intercorrências com evidências: {len(intercorrencias)} | Rotinas com evidências: {len(rotinas)}",
            "Helvetica",
            10,
            extra_gap=section_gap,
        )

        if intercorrencias:
            draw_wrapped_text("Intercorrências", "Helvetica-Bold", 12, extra_gap=4)
            for record in intercorrencias:
                linhas = [
                    f"Data: {format_date_display(record['data'])} | Hora: {record['hora']} | Tipo: {record['tipo_nome']}",
                    f"Espaço: {record['espaco_nome']} | Professor relacionado: {record.get('professor_nome') or '-'}",
                    f"Descrição objetiva: {record['descricao_objetiva']}",
                    f"Providências adotadas: {record.get('providencias_adotadas') or '-'}",
                    f"Encaminhamento: {record.get('encaminhado_para') or '-'}",
                    f"Observações: {record.get('observacoes') or '-'}",
                ]
                for linha in linhas:
                    draw_wrapped_text(linha, "Helvetica", 10)
                evidencias = record.get("evidencias") or []
                for index, evidencia in enumerate(evidencias, start=1):
                    nome = evidencia.get("nome_arquivo") or f"evidencia_{index}.png"
                    draw_wrapped_text(f"Evidência {index}: {nome}", "Helvetica-Bold", 10, extra_gap=4)
                    try:
                        image = ImageReader(BytesIO(evidencia.get("dados") or b""))
                        image_width, image_height = image.getSize()
                        scale = min(usable_width / image_width, max_image_height / image_height, 1.0)
                        draw_width = image_width * scale
                        draw_height = image_height * scale
                        ensure_space(draw_height + image_gap)
                        pdf.drawImage(
                            image,
                            left_margin,
                            y - draw_height,
                            width=draw_width,
                            height=draw_height,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                        y -= draw_height + image_gap
                    except Exception:
                        draw_wrapped_text("Não foi possível renderizar esta evidência no PDF.", "Helvetica", 10, extra_gap=4)
                y -= section_gap

        if rotinas:
            draw_wrapped_text("Rotinas docentes", "Helvetica-Bold", 12, extra_gap=4)
            for record in rotinas:
                horario = ""
                if record.get("hora_inicio") or record.get("hora_fim"):
                    horario = f" | Horário: {record.get('hora_inicio') or '-'} até {record.get('hora_fim') or '-'}"
                linhas = [
                    f"Data: {format_date_display(record['data'])}{horario} | Categoria: {record['categoria']}",
                    f"Professores: {record['professor_nome']} | Espaço: {record.get('espaco_nome') or '-'}",
                    f"Título: {record['titulo']}",
                    f"Turma ou público: {record.get('turma_ou_publico') or '-'}",
                    f"Descrição da atividade: {record['descricao_atividade']}",
                    f"Objetivos: {record.get('objetivos') or '-'}",
                    f"Recursos utilizados: {record.get('recursos_utilizados') or '-'}",
                    f"Encaminhamentos: {record.get('encaminhamentos') or '-'}",
                    f"Observações: {record.get('observacoes') or '-'}",
                ]
                for linha in linhas:
                    draw_wrapped_text(linha, "Helvetica", 10)
                evidencias = record.get("evidencias") or []
                for index, evidencia in enumerate(evidencias, start=1):
                    nome = evidencia.get("nome_arquivo") or f"evidencia_{index}.png"
                    draw_wrapped_text(f"Evidência {index}: {nome}", "Helvetica-Bold", 10, extra_gap=4)
                    try:
                        image = ImageReader(BytesIO(evidencia.get("dados") or b""))
                        image_width, image_height = image.getSize()
                        scale = min(usable_width / image_width, max_image_height / image_height, 1.0)
                        draw_width = image_width * scale
                        draw_height = image_height * scale
                        ensure_space(draw_height + image_gap)
                        pdf.drawImage(
                            image,
                            left_margin,
                            y - draw_height,
                            width=draw_width,
                            height=draw_height,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                        y -= draw_height + image_gap
                    except Exception:
                        draw_wrapped_text("Não foi possível renderizar esta evidência no PDF.", "Helvetica", 10, extra_gap=4)
                y -= section_gap

        pdf.save()
        show_info("Exportação concluída", f"Relatório de evidências salvo em:\n{target}", self)
