"""Janela inicial do Programa Multiplica."""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from models import (
    MODO_MULTIPLICA_LABELS,
    MODO_MULTIPLICA_PADRAO,
    MULTIPLICA_DIAS_SEMANA,
    MULTIPLICA_ENCONTRO_PAPEIS,
    MULTIPLICA_ENCONTRO_SITUACOES,
    MULTIPLICA_TABS,
    MULTIPLICA_TEXTOS_AUTOMATICOS,
    MULTIPLICA_TURMA_SITUACOES,
)
from utils import (
    DateInput,
    EvidenceInput,
    EXPORT_DIR,
    TimeInput,
    center_window,
    current_timestamp,
    format_date_display,
    normalize_date,
    normalize_time,
    set_text,
    show_error,
    show_info,
)


class MultiplicaWindow(tk.Toplevel):
    """Apresenta um painel inicial para multiplicador, cursista ou uso geral."""

    def __init__(
        self,
        parent: tk.Misc,
        db,
        user: dict | None,
        *,
        on_open_rotinas=None,
        on_open_relatorios=None,
        on_open_config=None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.user = user or {}
        self.on_open_rotinas = on_open_rotinas
        self.on_open_relatorios = on_open_relatorios
        self.on_open_config = on_open_config

        self.mode_value = self.user.get("modo_multiplica") or MODO_MULTIPLICA_PADRAO
        self.mode_label = MODO_MULTIPLICA_LABELS.get(self.mode_value, MODO_MULTIPLICA_LABELS[MODO_MULTIPLICA_PADRAO])
        self.linked_professor = self._load_linked_professor()

        self.current_turma_id: int | None = None
        self.current_encontro_id: int | None = None
        self.current_cursista_id: int | None = None

        self.codigo_var = tk.StringVar()
        self.dia_var = tk.StringVar()
        self.componente_var = tk.StringVar()
        self.situacao_var = tk.StringVar(value="ativa")

        self.encontro_turma_var = tk.StringVar()
        self.encontro_pauta_var = tk.StringVar()
        self.encontro_participantes_var = tk.StringVar()
        self.encontro_papel_var = tk.StringVar(value=self._default_encontro_papel())
        self.encontro_situacao_var = tk.StringVar(value="realizado")
        self.encontro_texto_auto_var = tk.StringVar(value=MULTIPLICA_TEXTOS_AUTOMATICOS[0])
        self.encontro_duracao_var = tk.StringVar()

        self.cursista_turma_var = tk.StringVar()
        self.cursista_nome_var = tk.StringVar()
        self.cursista_unidade_var = tk.StringVar()
        self.cursista_email_var = tk.StringVar()
        self.cursista_telefone_var = tk.StringVar()
        self.cursista_situacao_var = tk.StringVar(value="ativo")

        self.relatorio_turma_var = tk.StringVar(value="Todas as turmas")
        self.relatorio_papel_var = tk.StringVar(value="Todos")
        self.relatorio_situacao_var = tk.StringVar(value="Todas")
        self.current_report_rows: list[dict] = []
        self.current_report_text = ""

        self.turma_map: dict[str, int] = {}
        self.turma_details_map: dict[str, dict] = {}

        self.title("Programa Multiplica")
        self.minsize(1080, 780)
        center_window(self, 1320, 920, parent=parent)

        self._build()

    def _load_linked_professor(self) -> dict | None:
        professor_id = self.user.get("professor_id")
        if not professor_id:
            return None
        return self.db.get_professor(int(professor_id))

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.LabelFrame(root, text="Programa Multiplica", padding=10)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        ttk.Label(
            header,
            text=f"Modo atual: {self.mode_label}",
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text=(
                f"Professor vinculado: {self.linked_professor.get('nome_completo') if self.linked_professor else '-'}"
            ),
            justify="right",
        ).grid(row=0, column=1, sticky="e", padx=(16, 0))

        ttk.Label(
            header,
            text=f"Usuario: {self.user.get('nome_completo') or self.user.get('nome_usuario') or '-'}",
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        notebook = ttk.Notebook(root)
        notebook.grid(row=1, column=0, sticky="nsew")

        tab_names = MULTIPLICA_TABS.get(self.mode_value) or ["Painel"]
        for tab_name in tab_names:
            frame = ttk.Frame(notebook, padding=16)
            frame.columnconfigure(0, weight=1)
            notebook.add(frame, text=tab_name)
            if tab_name == "Painel":
                self._build_dashboard_tab(frame)
            elif self.mode_value == "multiplicador" and tab_name == "Turmas":
                self._build_turmas_tab(frame)
            elif self.mode_value == "multiplicador" and tab_name == "Encontros":
                self._build_encontros_tab(frame)
            elif self.mode_value == "multiplicador" and tab_name == "Cursistas":
                self._build_cursistas_tab(frame)
            elif tab_name.lower().startswith("relat"):
                self._build_relatorios_tab(frame)
            else:
                self._build_placeholder_tab(frame, tab_name)

    def _default_encontro_papel(self) -> str:
        if self.mode_value == "cursista":
            return "cursista"
        return "multiplicador"

    def _build_dashboard_tab(self, frame: ttk.Frame) -> None:
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Visao inicial", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        content = ttk.LabelFrame(frame, text="Resumo do modo selecionado", padding=14)
        content.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        content.columnconfigure(0, weight=1)

        ttk.Label(
            content,
            text=self._build_summary_text(),
            justify="left",
            wraplength=1040,
        ).grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(content)
        actions.grid(row=1, column=0, sticky="w", pady=(16, 0))
        ttk.Button(actions, text="Abrir rotina docente", command=self._open_rotinas).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Abrir relatorios", command=self._open_relatorios).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Configurar modo", command=self._open_config).pack(side="left")

    def _build_turmas_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(frame, text="Cadastro de turma", padding=12)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        form.columnconfigure(5, weight=0)

        ttk.Label(form, text="Codigo da turma").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.codigo_var, width=24).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Dia da semana").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=4)
        self.dia_combo = ttk.Combobox(form, textvariable=self.dia_var, state="readonly", width=10, values=MULTIPLICA_DIAS_SEMANA)
        self.dia_combo.grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Horario").grid(row=0, column=4, sticky="w", padx=(18, 8), pady=4)
        self.horario_entry = TimeInput(form, width=12)
        self.horario_entry.grid(row=0, column=5, sticky="w", pady=4)

        ttk.Label(form, text="Tema / componente").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.componente_var, width=36).grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(form, text="Situacao").grid(row=1, column=4, sticky="w", padx=(18, 8), pady=4)
        self.situacao_combo = ttk.Combobox(
            form,
            textvariable=self.situacao_var,
            state="readonly",
            width=12,
            values=MULTIPLICA_TURMA_SITUACOES,
        )
        self.situacao_combo.grid(row=1, column=5, sticky="w", pady=4)

        actions = ttk.Frame(form)
        actions.grid(row=2, column=0, columnspan=6, sticky="w", pady=(10, 0))
        ttk.Button(actions, text="Salvar turma", command=self._save_turma).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Nova turma", command=self._clear_turma_form).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Carregar selecionada", command=self._load_selected_turma).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Alterar situacao", command=self._toggle_selected_turma_status).pack(side="left")

        list_frame = ttk.LabelFrame(frame, text="Turmas cadastradas", padding=8)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("codigo", "dia", "horario", "componente", "situacao")
        self.turmas_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        headings = {
            "codigo": "Codigo",
            "dia": "Dia",
            "horario": "Horario",
            "componente": "Componente",
            "situacao": "Situacao",
        }
        widths = {
            "codigo": 140,
            "dia": 90,
            "horario": 120,
            "componente": 320,
            "situacao": 120,
        }
        for key in columns:
            self.turmas_tree.heading(key, text=headings[key])
            self.turmas_tree.column(key, width=widths[key], anchor="w")
        self.turmas_tree.grid(row=0, column=0, sticky="nsew")
        self.turmas_tree.bind("<Double-1>", lambda _event: self._load_selected_turma())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.turmas_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.turmas_tree.configure(yscrollcommand=scrollbar.set)

        if not self.linked_professor:
            ttk.Label(
                frame,
                text=(
                    "Vincule um professor ao usuario em Seguranca > Modo do Programa Multiplica "
                    "para poder cadastrar turmas."
                ),
                foreground="#8B1E1E",
                justify="left",
            ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        self._clear_turma_form()
        self._refresh_turmas()
        self._refresh_turma_options()

    def _build_encontros_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(frame, highlightthickness=0, borderwidth=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        canvas_scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas_scroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=canvas_scroll.set)

        scroll_body = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=scroll_body, anchor="nw")

        def _refresh_scrollregion(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_canvas_width(event) -> None:
            canvas.itemconfigure(canvas_window, width=event.width)

        scroll_body.bind("<Configure>", _refresh_scrollregion)
        canvas.bind("<Configure>", _sync_canvas_width)

        top = ttk.Frame(scroll_body)
        top.grid(row=0, column=0, sticky="nsew")
        top.columnconfigure(0, weight=1, minsize=560)
        top.columnconfigure(1, weight=1, minsize=420)
        top.rowconfigure(0, weight=1, minsize=680)

        left = ttk.Frame(top)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=0)
        left.rowconfigure(1, weight=1, minsize=320)

        form = ttk.LabelFrame(left, text="Registro de encontro", padding=12)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1, minsize=210)
        form.columnconfigure(3, weight=1, minsize=145)

        ttk.Label(form, text="Turma").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self.encontro_turma_combo = ttk.Combobox(form, textvariable=self.encontro_turma_var, state="readonly", width=30)
        self.encontro_turma_combo.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)
        self.encontro_turma_combo.bind("<<ComboboxSelected>>", lambda _event: self._sync_encontro_calendar_highlights())

        ttk.Label(form, text="Data").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.encontro_data_entry = DateInput(form, width=12)
        self.encontro_data_entry.grid(row=1, column=1, sticky="w", pady=4, padx=(0, 12))

        ttk.Label(form, text="Nº/pauta").grid(row=1, column=2, sticky="w", pady=4, padx=(12, 8))
        ttk.Entry(form, textvariable=self.encontro_pauta_var, width=10).grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Inicio").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        self.encontro_inicio_entry = TimeInput(form, width=10)
        self.encontro_inicio_entry.grid(row=2, column=1, sticky="w", pady=4)
        self.encontro_inicio_entry.bind("<FocusOut>", lambda _event: self._update_encontro_duration_from_times(), add="+")

        ttk.Label(form, text="Termino").grid(row=2, column=2, sticky="w", pady=4, padx=(18, 8))
        self.encontro_termino_entry = TimeInput(form, width=10)
        self.encontro_termino_entry.grid(row=2, column=3, sticky="w", pady=4)
        self.encontro_termino_entry.bind("<FocusOut>", lambda _event: self._update_encontro_duration_from_times(), add="+")

        ttk.Label(form, text="Participantes").grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Entry(form, textvariable=self.encontro_participantes_var, width=10).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Duracao").grid(row=3, column=2, sticky="w", pady=4, padx=(18, 8))
        ttk.Entry(form, textvariable=self.encontro_duracao_var, width=10).grid(row=3, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Papel no encontro").grid(row=4, column=0, sticky="w", pady=4, padx=(0, 8))
        self.encontro_papel_combo = ttk.Combobox(
            form,
            textvariable=self.encontro_papel_var,
            state="readonly",
            width=16,
            values=MULTIPLICA_ENCONTRO_PAPEIS,
        )
        self.encontro_papel_combo.grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Situacao").grid(row=4, column=2, sticky="w", pady=4, padx=(18, 8))
        self.encontro_situacao_combo = ttk.Combobox(
            form,
            textvariable=self.encontro_situacao_var,
            state="readonly",
            width=16,
            values=MULTIPLICA_ENCONTRO_SITUACOES,
        )
        self.encontro_situacao_combo.grid(row=4, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Texto automatico").grid(row=5, column=0, sticky="w", pady=4, padx=(0, 8))
        self.encontro_texto_combo = ttk.Combobox(
            form,
            textvariable=self.encontro_texto_auto_var,
            state="readonly",
            width=24,
            values=MULTIPLICA_TEXTOS_AUTOMATICOS,
        )
        self.encontro_texto_combo.grid(row=5, column=1, columnspan=2, sticky="ew", pady=4, padx=(0, 8))

        ttk.Button(form, text="Aplicar", command=self._apply_auto_text).grid(row=5, column=3, sticky="w", pady=4)

        encounter_actions = ttk.Frame(form)
        encounter_actions.grid(row=6, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Button(encounter_actions, text="Salvar encontro", command=self._save_encontro).pack(side="left", padx=(0, 8))
        ttk.Button(encounter_actions, text="Inserir encontro", command=self._clear_encontro_form).pack(side="left", padx=(0, 8))
        ttk.Button(encounter_actions, text="Atualizar mes", command=self._refresh_encontros).pack(side="left", padx=(0, 8))
        ttk.Button(encounter_actions, text="Carregar selecionado", command=self._load_selected_encontro).pack(side="left")

        lower_left = ttk.Frame(left)
        lower_left.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        lower_left.columnconfigure(0, weight=1)
        lower_left.rowconfigure(0, weight=1, minsize=145)
        lower_left.rowconfigure(1, weight=1, minsize=145)

        observacao_frame = ttk.LabelFrame(lower_left, text="Observacao", padding=6)
        observacao_frame.grid(row=0, column=0, sticky="nsew")
        observacao_frame.columnconfigure(0, weight=1)
        observacao_frame.rowconfigure(0, weight=1)

        self.encontro_observacao = tk.Text(observacao_frame, height=5, wrap="word")
        self.encontro_observacao.grid(row=0, column=0, sticky="nsew")
        obs_scroll = ttk.Scrollbar(observacao_frame, orient="vertical", command=self.encontro_observacao.yview)
        obs_scroll.grid(row=0, column=1, sticky="ns")
        self.encontro_observacao.configure(yscrollcommand=obs_scroll.set)

        self.encontro_evidencias = EvidenceInput(
            lower_left,
            title="Evidencias do encontro",
            height=4,
        )
        self.encontro_evidencias.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        right = ttk.Frame(top)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        month_frame = ttk.LabelFrame(right, text="Encontros do mes", padding=8)
        month_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        month_frame.columnconfigure(0, weight=1)
        month_frame.rowconfigure(0, weight=1)

        columns = ("data", "pauta", "turma", "papel", "situacao", "participantes", "imagens")
        self.encontros_tree = ttk.Treeview(month_frame, columns=columns, show="headings", height=3)
        headings = {
            "data": "Data",
            "pauta": "Pauta",
            "turma": "Turma",
            "papel": "Papel",
            "situacao": "Situacao",
            "participantes": "Participantes",
            "imagens": "Imagens",
        }
        widths = {
            "data": 90,
            "pauta": 65,
            "turma": 85,
            "papel": 95,
            "situacao": 120,
            "participantes": 95,
            "imagens": 80,
        }
        for key in columns:
            self.encontros_tree.heading(key, text=headings[key])
            self.encontros_tree.column(key, width=widths[key], anchor="w")
        self.encontros_tree.grid(row=0, column=0, sticky="nsew")
        self.encontros_tree.bind("<<TreeviewSelect>>", lambda _event: self._update_encontro_preview())
        self.encontros_tree.bind("<Double-1>", lambda _event: self._load_selected_encontro())

        month_scroll = ttk.Scrollbar(month_frame, orient="vertical", command=self.encontros_tree.yview)
        month_scroll.grid(row=0, column=1, sticky="ns")
        self.encontros_tree.configure(yscrollcommand=month_scroll.set)

        preview_frame = ttk.LabelFrame(right, text="Pre-visualizacao do encontro", padding=8)
        preview_frame.grid(row=1, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.encontro_preview = tk.Text(preview_frame, wrap="word", height=6)
        self.encontro_preview.grid(row=0, column=0, sticky="nsew")
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.encontro_preview.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.encontro_preview.configure(yscrollcommand=preview_scroll.set)
        set_text(self.encontro_preview, "Selecione um encontro para visualizar os detalhes.")

        self._clear_encontro_form()
        self._refresh_turma_options()
        self._refresh_encontros()

    def _build_placeholder_tab(self, frame: ttk.Frame, tab_name: str) -> None:
        ttk.Label(frame, text=tab_name, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            text=self._build_tab_guidance(tab_name),
            wraplength=1040,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

    def _build_summary_text(self) -> str:
        if self.mode_value == "multiplicador":
            return (
                "Este modo esta preparado para apoiar o professor multiplicador na organizacao do percurso "
                "formativo, no acompanhamento de encontros e na consolidacao de registros para devolutivas.\n\n"
                "Nesta etapa, as abas Turmas e Encontros ja permitem cadastrar a estrutura base do acompanhamento."
            )
        if self.mode_value == "cursista":
            return (
                "Este modo esta preparado para apoiar o professor cursista no registro das formacoes recebidas, "
                "nas aplicacoes em aula e nas evidencias do percurso formativo.\n\n"
                "Nesta primeira etapa segura, o sistema ja diferencia o perfil de uso, vincula o professor "
                "responsavel e mantem os atalhos para os registros pedagogicos ja existentes."
            )
        return (
            "O sistema esta em uso geral. Os modulos pedagogicos continuam disponiveis normalmente.\n\n"
            "Se desejar habilitar o acompanhamento especifico do Programa Multiplica, utilize o botao "
            "\"Configurar modo\" e selecione Professor multiplicador ou Professor cursista."
        )

    def _build_tab_guidance(self, tab_name: str) -> str:
        if self.mode_value == "multiplicador":
            hints = {
                "Cursistas": "Espaco reservado para evoluir com acompanhamento individual dos professores cursistas.",
                "Relatórios": "Espaco reservado para evoluir com relatorios especificos do percurso do professor multiplicador.",
            }
            return hints.get(tab_name, "Espaco reservado para evolucao do modulo.")
        if self.mode_value == "cursista":
            hints = {
                "Formações": "Espaco reservado para evoluir com o registro das formacoes recebidas no Programa Multiplica.",
                "Aplicações em aula": "Espaco reservado para evoluir com as aplicacoes praticas feitas pelo professor cursista.",
                "Reflexões": "Espaco reservado para evoluir com registros reflexivos sobre os estudos, encontros e resultados.",
                "Relatórios": "Espaco reservado para evoluir com relatorios especificos do percurso do professor cursista.",
            }
            return hints.get(tab_name, "Espaco reservado para evolucao do modulo.")
        return (
            "Este painel permanece neutro enquanto o sistema estiver em uso geral. "
            "Ao ativar um perfil do Programa Multiplica, cada aba passa a refletir a rotina do modo escolhido."
        )

    def _refresh_turmas(self) -> None:
        if not hasattr(self, "turmas_tree"):
            return
        for item_id in self.turmas_tree.get_children():
            self.turmas_tree.delete(item_id)
        if not self.linked_professor:
            return

        turmas = self.db.list_multiplica_turmas(int(self.linked_professor["id"]), include_inactive=True)
        for turma in turmas:
            self.turmas_tree.insert(
                "",
                tk.END,
                iid=str(turma["id"]),
                values=(
                    turma["codigo_turma"],
                    turma["dia_semana"],
                    turma["horario"],
                    turma["componente"],
                    turma["situacao"],
                ),
            )

    def _refresh_turma_options(self) -> None:
        self.turma_map = {}
        self.turma_details_map = {}
        values: list[str] = []
        if self.linked_professor:
            turmas = self.db.list_multiplica_turmas(int(self.linked_professor["id"]), include_inactive=True)
            for turma in turmas:
                suffix = "" if turma.get("situacao") == "ativa" else f" [{turma.get('situacao')}]"
                label = f"{turma['codigo_turma']} - {turma['componente']}{suffix}"
                self.turma_map[label] = int(turma["id"])
                self.turma_details_map[label] = turma
                values.append(label)
        if hasattr(self, "encontro_turma_combo"):
            self.encontro_turma_combo["values"] = values
            self._sync_encontro_calendar_highlights(apply_defaults=False)
        if hasattr(self, "cursista_turma_combo"):
            self.cursista_turma_combo["values"] = values
        if hasattr(self, "relatorio_turma_combo"):
            self.relatorio_turma_combo["values"] = ["Todas as turmas", *values]

    def _build_cursistas_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(frame, text="Cadastro de cursista", padding=12)
        form.grid(row=0, column=0, columnspan=2, sticky="ew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Turma").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.cursista_turma_combo = ttk.Combobox(
            form,
            textvariable=self.cursista_turma_var,
            state="readonly",
            width=30,
        )
        self.cursista_turma_combo.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Nome completo").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=4)
        ttk.Entry(form, textvariable=self.cursista_nome_var, width=38).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(form, text="Unidade escolar").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.cursista_unidade_var, width=30).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="E-mail").grid(row=1, column=2, sticky="w", padx=(18, 8), pady=4)
        ttk.Entry(form, textvariable=self.cursista_email_var, width=38).grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(form, text="Telefone").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.cursista_telefone_var, width=18).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Situacao").grid(row=2, column=2, sticky="w", padx=(18, 8), pady=4)
        ttk.Combobox(
            form,
            textvariable=self.cursista_situacao_var,
            values=("ativo", "inativo"),
            state="readonly",
            width=14,
        ).grid(row=2, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Observacoes").grid(row=3, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.cursista_observacoes = tk.Text(form, height=3, wrap="word")
        self.cursista_observacoes.grid(row=3, column=1, columnspan=3, sticky="ew", pady=4)

        actions = ttk.Frame(form)
        actions.grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Button(actions, text="Salvar cursista", command=self._save_cursista).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Novo cursista", command=self._clear_cursista_form).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Carregar selecionado", command=self._load_selected_cursista).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Alterar situacao", command=self._toggle_selected_cursista_status).pack(side="left")

        list_frame = ttk.LabelFrame(frame, text="Cursistas cadastrados", padding=8)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0), padx=(0, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        columns = ("nome", "turma", "unidade", "situacao")
        self.cursistas_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        headings = {"nome": "Nome", "turma": "Turma", "unidade": "Unidade escolar", "situacao": "Situacao"}
        widths = {"nome": 240, "turma": 100, "unidade": 200, "situacao": 90}
        for key in columns:
            self.cursistas_tree.heading(key, text=headings[key])
            self.cursistas_tree.column(key, width=widths[key], anchor="w")
        self.cursistas_tree.grid(row=0, column=0, sticky="nsew")
        self.cursistas_tree.bind("<<TreeviewSelect>>", lambda _event: self._update_cursista_preview())
        self.cursistas_tree.bind("<Double-1>", lambda _event: self._load_selected_cursista())
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.cursistas_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.cursistas_tree.configure(yscrollcommand=scrollbar.set)

        preview_frame = ttk.LabelFrame(frame, text="Detalhes do cursista", padding=8)
        preview_frame.grid(row=1, column=1, sticky="nsew", pady=(12, 0), padx=(8, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.cursista_preview = tk.Text(preview_frame, wrap="word", height=14)
        self.cursista_preview.grid(row=0, column=0, sticky="nsew")
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.cursista_preview.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.cursista_preview.configure(yscrollcommand=preview_scroll.set)

        self._clear_cursista_form()
        self._refresh_turma_options()
        self._refresh_cursistas()

    def _selected_cursista_id(self) -> int | None:
        if not hasattr(self, "cursistas_tree"):
            return None
        selected = self.cursistas_tree.selection()
        return int(selected[0]) if selected else None

    def _clear_cursista_form(self) -> None:
        self.current_cursista_id = None
        self.cursista_turma_var.set("")
        self.cursista_nome_var.set("")
        self.cursista_unidade_var.set("")
        self.cursista_email_var.set("")
        self.cursista_telefone_var.set("")
        self.cursista_situacao_var.set("ativo")
        if hasattr(self, "cursista_observacoes"):
            self.cursista_observacoes.delete("1.0", tk.END)

    def _refresh_cursistas(self) -> None:
        if not hasattr(self, "cursistas_tree"):
            return
        for item_id in self.cursistas_tree.get_children():
            self.cursistas_tree.delete(item_id)
        if not self.linked_professor:
            return
        for cursista in self.db.list_multiplica_cursistas(int(self.linked_professor["id"])):
            self.cursistas_tree.insert(
                "",
                tk.END,
                iid=str(cursista["id"]),
                values=(
                    cursista.get("nome_completo") or "",
                    cursista.get("codigo_turma") or "",
                    cursista.get("unidade_escolar") or "",
                    cursista.get("situacao") or "",
                ),
            )
        self._update_cursista_preview()

    def _save_cursista(self) -> None:
        if not self.linked_professor:
            show_error("Professor vinculado obrigatorio", "Vincule um professor antes de cadastrar cursistas.", self)
            return
        turma_id = self.turma_map.get(self.cursista_turma_var.get().strip())
        if not turma_id:
            show_error("Turma obrigatoria", "Selecione a turma do cursista.", self)
            return
        payload = {
            "professor_id": int(self.linked_professor["id"]),
            "turma_id": turma_id,
            "nome_completo": self.cursista_nome_var.get().strip(),
            "unidade_escolar": self.cursista_unidade_var.get().strip(),
            "email": self.cursista_email_var.get().strip(),
            "telefone": self.cursista_telefone_var.get().strip(),
            "situacao": self.cursista_situacao_var.get().strip(),
            "observacoes": self.cursista_observacoes.get("1.0", tk.END).strip(),
        }
        try:
            cursista_id = self.db.save_multiplica_cursista(payload, self.current_cursista_id)
        except ValueError as exc:
            show_error("Nao foi possivel salvar", str(exc), self)
            return
        self.current_cursista_id = cursista_id
        self._refresh_cursistas()
        self.cursistas_tree.selection_set(str(cursista_id))
        self.cursistas_tree.focus(str(cursista_id))
        self.cursistas_tree.see(str(cursista_id))
        self._update_cursista_preview()
        show_info("Cursista salvo", "Os dados do cursista foram salvos com sucesso.", self)

    def _load_selected_cursista(self) -> None:
        cursista_id = self._selected_cursista_id()
        if not cursista_id:
            show_error("Selecao necessaria", "Selecione um cursista na lista para carregar.", self)
            return
        cursista = self.db.get_multiplica_cursista(cursista_id)
        if not cursista:
            show_error("Cursista nao encontrado", "Nao foi possivel carregar o cursista selecionado.", self)
            return
        self.current_cursista_id = cursista_id
        self.cursista_nome_var.set(cursista.get("nome_completo") or "")
        self.cursista_unidade_var.set(cursista.get("unidade_escolar") or "")
        self.cursista_email_var.set(cursista.get("email") or "")
        self.cursista_telefone_var.set(cursista.get("telefone") or "")
        self.cursista_situacao_var.set(cursista.get("situacao") or "ativo")
        self.cursista_observacoes.delete("1.0", tk.END)
        self.cursista_observacoes.insert("1.0", cursista.get("observacoes") or "")
        for label, turma_id in self.turma_map.items():
            if turma_id == int(cursista["turma_id"]):
                self.cursista_turma_var.set(label)
                break
        self._update_cursista_preview()

    def _toggle_selected_cursista_status(self) -> None:
        cursista_id = self._selected_cursista_id()
        if not cursista_id:
            show_error("Selecao necessaria", "Selecione um cursista para alterar a situacao.", self)
            return
        cursista = self.db.get_multiplica_cursista(cursista_id)
        if not cursista:
            show_error("Cursista nao encontrado", "Nao foi possivel localizar o cursista selecionado.", self)
            return
        nova_situacao = "inativo" if cursista.get("situacao") == "ativo" else "ativo"
        try:
            self.db.update_multiplica_cursista_status(cursista_id, nova_situacao)
        except ValueError as exc:
            show_error("Nao foi possivel alterar", str(exc), self)
            return
        self._refresh_cursistas()
        self.cursistas_tree.selection_set(str(cursista_id))
        self.cursistas_tree.focus(str(cursista_id))
        self._load_selected_cursista()
        show_info("Situacao atualizada", f"O cursista agora esta {nova_situacao}.", self)

    def _update_cursista_preview(self) -> None:
        if not hasattr(self, "cursista_preview"):
            return
        cursista_id = self._selected_cursista_id()
        if not cursista_id:
            set_text(self.cursista_preview, "Selecione um cursista para visualizar os detalhes.")
            return
        cursista = self.db.get_multiplica_cursista(cursista_id)
        if not cursista:
            set_text(self.cursista_preview, "Nao foi possivel carregar os detalhes do cursista.")
            return
        set_text(
            self.cursista_preview,
            (
                f"Nome: {cursista.get('nome_completo') or '-'}\n"
                f"Turma: {cursista.get('codigo_turma') or '-'} - {cursista.get('turma_componente') or '-'}\n"
                f"Situacao: {cursista.get('situacao') or '-'}\n"
                f"Unidade escolar: {cursista.get('unidade_escolar') or '-'}\n"
                f"E-mail: {cursista.get('email') or '-'}\n"
                f"Telefone: {cursista.get('telefone') or '-'}\n\n"
                f"Observacoes:\n{cursista.get('observacoes') or '-'}"
            ),
        )

    def _build_relatorios_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.rowconfigure(3, weight=1)

        filters = ttk.LabelFrame(frame, text="Filtros do relatorio", padding=10)
        filters.grid(row=0, column=0, sticky="ew")
        filters.columnconfigure(5, weight=1)
        ttk.Label(filters, text="De").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.relatorio_data_inicial = DateInput(filters, width=12)
        self.relatorio_data_inicial.grid(row=0, column=1, sticky="w", pady=4)
        self.relatorio_data_inicial.set(dt.date.today().replace(month=1, day=1).strftime("%d/%m/%Y"))
        ttk.Label(filters, text="Ate").grid(row=0, column=2, sticky="w", padx=(14, 6), pady=4)
        self.relatorio_data_final = DateInput(filters, width=12)
        self.relatorio_data_final.grid(row=0, column=3, sticky="w", pady=4)
        self.relatorio_data_final.set(dt.date.today().strftime("%d/%m/%Y"))
        ttk.Label(filters, text="Turma").grid(row=0, column=4, sticky="w", padx=(14, 6), pady=4)
        self.relatorio_turma_combo = ttk.Combobox(filters, textvariable=self.relatorio_turma_var, state="readonly", width=28)
        self.relatorio_turma_combo.grid(row=0, column=5, sticky="ew", pady=4)
        ttk.Label(filters, text="Papel").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Combobox(filters, textvariable=self.relatorio_papel_var, state="readonly", width=14, values=("Todos", *MULTIPLICA_ENCONTRO_PAPEIS)).grid(row=1, column=1, sticky="w", pady=4)
        ttk.Label(filters, text="Situacao").grid(row=1, column=2, sticky="w", padx=(14, 6), pady=4)
        ttk.Combobox(filters, textvariable=self.relatorio_situacao_var, state="readonly", width=16, values=("Todas", *MULTIPLICA_ENCONTRO_SITUACOES)).grid(row=1, column=3, sticky="w", pady=4)
        actions = ttk.Frame(filters)
        actions.grid(row=1, column=5, sticky="e", pady=4)
        ttk.Button(actions, text="Gerar relatorio", command=self._generate_multiplica_report).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Exportar TXT", command=self._export_multiplica_txt).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Exportar CSV", command=self._export_multiplica_csv).pack(side="left")

        self.relatorio_resumo_var = tk.StringVar(value="Defina os filtros e gere o relatorio.")
        ttk.Label(frame, textvariable=self.relatorio_resumo_var, justify="left").grid(row=1, column=0, sticky="w", pady=(10, 6))

        list_frame = ttk.LabelFrame(frame, text="Encontros encontrados", padding=8)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        columns = ("data", "turma", "pauta", "papel", "situacao", "participantes", "evidencias")
        self.relatorio_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=7)
        headings = {"data": "Data", "turma": "Turma", "pauta": "Pauta", "papel": "Papel", "situacao": "Situacao", "participantes": "Participantes", "evidencias": "Evidencias"}
        widths = {"data": 95, "turma": 120, "pauta": 70, "papel": 110, "situacao": 120, "participantes": 105, "evidencias": 90}
        for key in columns:
            self.relatorio_tree.heading(key, text=headings[key])
            self.relatorio_tree.column(key, width=widths[key], anchor="w")
        self.relatorio_tree.grid(row=0, column=0, sticky="nsew")
        self.relatorio_tree.bind("<<TreeviewSelect>>", lambda _event: self._update_relatorio_preview())
        report_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.relatorio_tree.yview)
        report_scroll.grid(row=0, column=1, sticky="ns")
        self.relatorio_tree.configure(yscrollcommand=report_scroll.set)

        preview_frame = ttk.LabelFrame(frame, text="Pre-visualizacao do relatorio", padding=8)
        preview_frame.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.relatorio_preview = tk.Text(preview_frame, wrap="word", height=12)
        self.relatorio_preview.grid(row=0, column=0, sticky="nsew")
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.relatorio_preview.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.relatorio_preview.configure(yscrollcommand=preview_scroll.set)
        set_text(self.relatorio_preview, "O relatorio consolidado aparecera aqui.")
        self._refresh_turma_options()

    def _report_filters(self) -> dict | None:
        try:
            data_inicial = normalize_date(self.relatorio_data_inicial.get())
            data_final = normalize_date(self.relatorio_data_final.get())
        except ValueError as exc:
            show_error("Periodo invalido", str(exc), self)
            return None
        if data_inicial > data_final:
            show_error("Periodo invalido", "A data inicial nao pode ser posterior a data final.", self)
            return None
        turma_label = self.relatorio_turma_var.get().strip()
        return {
            "data_inicial": data_inicial,
            "data_final": data_final,
            "turma_id": self.turma_map.get(turma_label) if turma_label != "Todas as turmas" else None,
            "papel": self.relatorio_papel_var.get() if self.relatorio_papel_var.get() != "Todos" else None,
            "situacao": self.relatorio_situacao_var.get() if self.relatorio_situacao_var.get() != "Todas" else None,
        }

    def _generate_multiplica_report(self) -> None:
        if not self.linked_professor:
            show_error("Professor vinculado obrigatorio", "Vincule um professor antes de gerar relatorios.", self)
            return
        filters = self._report_filters()
        if filters is None:
            return
        self.current_report_rows = self.db.list_multiplica_encontros(int(self.linked_professor["id"]), filters)
        for item_id in self.relatorio_tree.get_children():
            self.relatorio_tree.delete(item_id)
        for encontro in self.current_report_rows:
            self.relatorio_tree.insert(
                "", tk.END, iid=str(encontro["id"]), values=(
                    format_date_display(encontro["data"]), encontro.get("codigo_turma") or "",
                    encontro.get("pauta_numero") or "", encontro.get("papel_no_encontro") or "",
                    encontro.get("situacao") or "", encontro.get("participantes") or 0,
                    encontro.get("imagens") or 0,
                )
            )
        cursistas = self.db.list_multiplica_cursistas(
            int(self.linked_professor["id"]), filters.get("turma_id"), include_inactive=False
        )
        total = len(self.current_report_rows)
        realizados = sum(1 for item in self.current_report_rows if item.get("situacao") == "realizado")
        formacoes_recebidas = sum(1 for item in self.current_report_rows if item.get("papel_no_encontro") == "cursista")
        participantes = sum(int(item.get("participantes") or 0) for item in self.current_report_rows)
        evidencias = sum(int(item.get("imagens") or 0) for item in self.current_report_rows)
        self.relatorio_resumo_var.set(
            f"{total} encontro(s), {realizados} realizado(s), {formacoes_recebidas} como cursista, "
            f"{len(cursistas)} cursista(s) ativo(s), {participantes} participacao(oes) e {evidencias} evidencia(s)."
        )
        turma_texto = self.relatorio_turma_var.get() or "Todas as turmas"
        linhas = [
            "RELATORIO - PROGRAMA MULTIPLICA",
            f"Professor vinculado: {self.linked_professor.get('nome_completo') or '-'}",
            f"Periodo: {format_date_display(filters['data_inicial'])} a {format_date_display(filters['data_final'])}",
            f"Turma: {turma_texto}",
            f"Papel: {self.relatorio_papel_var.get()} | Situacao: {self.relatorio_situacao_var.get()}",
            "",
            "RESUMO",
            f"- Encontros: {total}",
            f"- Encontros realizados: {realizados}",
            f"- Formacoes recebidas como cursista: {formacoes_recebidas}",
            f"- Cursistas ativos acompanhados: {len(cursistas)}",
            f"- Participacoes registradas: {participantes}",
            f"- Evidencias anexadas: {evidencias}",
            "",
            "ENCONTROS",
        ]
        if self.current_report_rows:
            for encontro in reversed(self.current_report_rows):
                linhas.extend([
                    (
                        f"{format_date_display(encontro['data'])} | Turma {encontro.get('codigo_turma') or '-'} | "
                        f"Pauta {encontro.get('pauta_numero') or '-'} | {encontro.get('papel_no_encontro') or '-'} | "
                        f"{encontro.get('situacao') or '-'}"
                    ),
                    f"  Horario: {encontro.get('hora_inicio') or '-'} - {encontro.get('hora_termino') or '-'} | Duracao: {encontro.get('duracao') or '-'}",
                    f"  Participantes: {encontro.get('participantes') or 0} | Evidencias: {encontro.get('imagens') or 0}",
                ])
                if encontro.get("observacao"):
                    linhas.append(f"  Observacao: {encontro['observacao']}")
        else:
            linhas.append("Nenhum encontro encontrado para os filtros informados.")
        linhas.extend(["", "CURSISTAS ATIVOS"])
        if cursistas:
            linhas.extend(f"- {item['nome_completo']} ({item.get('codigo_turma') or '-'})" for item in cursistas)
        else:
            linhas.append("Nenhum cursista ativo encontrado.")
        self.current_report_text = "\n".join(linhas)
        set_text(self.relatorio_preview, self.current_report_text)

    def _update_relatorio_preview(self) -> None:
        if not hasattr(self, "relatorio_tree"):
            return
        selected = self.relatorio_tree.selection()
        if not selected:
            return
        encontro = self.db.get_multiplica_encontro(int(selected[0]))
        if not encontro:
            return
        set_text(
            self.relatorio_preview,
            (
                f"Data: {format_date_display(encontro['data'])}\n"
                f"Turma: {encontro.get('codigo_turma') or '-'} - {encontro.get('turma_componente') or '-'}\n"
                f"Pauta: {encontro.get('pauta_numero') or '-'}\n"
                f"Papel: {encontro.get('papel_no_encontro') or '-'}\n"
                f"Situacao: {encontro.get('situacao') or '-'}\n"
                f"Horario: {encontro.get('hora_inicio') or '-'} - {encontro.get('hora_termino') or '-'}\n"
                f"Duracao: {encontro.get('duracao') or '-'}\n"
                f"Participantes: {encontro.get('participantes') or 0}\n\n"
                f"Observacao:\n{encontro.get('observacao') or '-'}"
            ),
        )

    def _export_multiplica_txt(self) -> None:
        if not self.current_report_text:
            show_error("Sem relatorio", "Gere o relatorio antes de exportar.", self)
            return
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        target = filedialog.asksaveasfilename(
            parent=self, title="Exportar relatorio em TXT", defaultextension=".txt",
            initialdir=str(EXPORT_DIR), initialfile=f"relatorio_multiplica_{current_timestamp().replace(':', '-').replace(' ', '_')}.txt",
            filetypes=[("Texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return
        Path(target).write_text(self.current_report_text, encoding="utf-8")
        show_info("Exportacao concluida", f"Relatorio salvo em:\n{target}", self)

    def _export_multiplica_csv(self) -> None:
        if not self.current_report_rows:
            show_error("Sem dados", "Gere um relatorio com encontros antes de exportar.", self)
            return
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        target = filedialog.asksaveasfilename(
            parent=self, title="Exportar relatorio em CSV", defaultextension=".csv",
            initialdir=str(EXPORT_DIR), initialfile=f"relatorio_multiplica_{current_timestamp().replace(':', '-').replace(' ', '_')}.csv",
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not target:
            return
        fields = ["data", "codigo_turma", "turma_componente", "pauta_numero", "papel_no_encontro", "situacao", "hora_inicio", "hora_termino", "duracao", "participantes", "imagens", "observacao"]
        with Path(target).open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.current_report_rows)
        show_info("Exportacao concluida", f"Relatorio salvo em:\n{target}", self)

    def _weekday_index_from_sigla(self, sigla: str) -> int | None:
        mapping = {
            "SEG": 0,
            "TER": 1,
            "QUA": 2,
            "QUI": 3,
            "SEX": 4,
            "SAB": 5,
            "DOM": 6,
        }
        return mapping.get((sigla or "").strip().upper())

    def _sync_encontro_calendar_highlights(self, apply_defaults: bool = True) -> None:
        if not hasattr(self, "encontro_data_entry"):
            return
        turma = self.turma_details_map.get(self.encontro_turma_var.get().strip())
        weekday_index = self._weekday_index_from_sigla((turma or {}).get("dia_semana") or "")
        if weekday_index is None:
            self.encontro_data_entry.set_calendar_weekday_highlights([])
        else:
            self.encontro_data_entry.set_calendar_weekday_highlights([weekday_index])
        if apply_defaults:
            self._apply_turma_schedule_defaults(turma)

    def _apply_turma_schedule_defaults(self, turma: dict | None) -> None:
        if not turma:
            return
        horario_base = (turma.get("horario") or "").strip()
        if not horario_base:
            return
        try:
            horario_normalizado = normalize_time(horario_base)
        except ValueError:
            return

        self.encontro_inicio_entry.set(horario_normalizado)
        try:
            inicio_dt = dt.datetime.strptime(horario_normalizado, "%H:%M")
        except ValueError:
            return
        termino_dt = inicio_dt + dt.timedelta(minutes=90)
        self.encontro_termino_entry.set(termino_dt.strftime("%H:%M"))
        self.encontro_duracao_var.set("01:30")

    def _update_encontro_duration_from_times(self) -> None:
        hora_inicio = self.encontro_inicio_entry.get().strip()
        hora_termino = self.encontro_termino_entry.get().strip()
        if not hora_inicio or not hora_termino:
            self.encontro_duracao_var.set("")
            return
        try:
            hora_inicio = normalize_time(hora_inicio)
            hora_termino = normalize_time(hora_termino)
        except ValueError:
            self.encontro_duracao_var.set("")
            return
        self.encontro_duracao_var.set(self._calculate_duration(hora_inicio, hora_termino))

    def _clear_turma_form(self) -> None:
        self.current_turma_id = None
        self.codigo_var.set("")
        self.dia_var.set("")
        self.horario_entry.set("")
        self.componente_var.set("")
        self.situacao_var.set("ativa")

    def _selected_turma_id(self) -> int | None:
        if not hasattr(self, "turmas_tree"):
            return None
        selected = self.turmas_tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def _load_selected_turma(self) -> None:
        turma_id = self._selected_turma_id()
        if not turma_id:
            show_error("Selecao necessaria", "Selecione uma turma na lista para carregar.", self)
            return
        turma = self.db.get_multiplica_turma(turma_id)
        if not turma:
            show_error("Turma nao encontrada", "Nao foi possivel carregar a turma selecionada.", self)
            return

        self.current_turma_id = turma["id"]
        self.codigo_var.set(turma.get("codigo_turma") or "")
        self.dia_var.set(turma.get("dia_semana") or "")
        self.horario_entry.set(turma.get("horario") or "")
        self.componente_var.set(turma.get("componente") or "")
        self.situacao_var.set(turma.get("situacao") or "ativa")

    def _save_turma(self) -> None:
        if not self.linked_professor:
            show_error(
                "Professor vinculado obrigatorio",
                "Vincule um professor ao usuario antes de cadastrar turmas do Programa Multiplica.",
                self,
            )
            return

        try:
            payload = {
                "professor_id": int(self.linked_professor["id"]),
                "codigo_turma": self.codigo_var.get().strip(),
                "dia_semana": self.dia_var.get().strip(),
                "horario": normalize_time(self.horario_entry.get()),
                "componente": self.componente_var.get().strip(),
                "situacao": self.situacao_var.get().strip() or "ativa",
            }
        except ValueError as exc:
            show_error("Horario invalido", str(exc), self)
            return

        try:
            turma_id = self.db.save_multiplica_turma(payload, self.current_turma_id)
        except ValueError as exc:
            show_error("Nao foi possivel salvar", str(exc), self)
            return

        self.current_turma_id = turma_id
        self._refresh_turmas()
        self._refresh_turma_options()
        if hasattr(self, "turmas_tree"):
            self.turmas_tree.selection_set(str(turma_id))
            self.turmas_tree.focus(str(turma_id))
            self.turmas_tree.see(str(turma_id))
        show_info("Turma salva", "Os dados da turma foram salvos com sucesso.", self)

    def _toggle_selected_turma_status(self) -> None:
        turma_id = self._selected_turma_id()
        if not turma_id:
            show_error("Selecao necessaria", "Selecione uma turma na lista para alterar a situacao.", self)
            return
        turma = self.db.get_multiplica_turma(turma_id)
        if not turma:
            show_error("Turma nao encontrada", "Nao foi possivel localizar a turma selecionada.", self)
            return

        nova_situacao = "inativa" if turma.get("situacao") == "ativa" else "ativa"
        try:
            self.db.update_multiplica_turma_status(turma_id, nova_situacao)
        except ValueError as exc:
            show_error("Nao foi possivel alterar", str(exc), self)
            return

        self._refresh_turmas()
        self._refresh_turma_options()
        if hasattr(self, "turmas_tree"):
            self.turmas_tree.selection_set(str(turma_id))
            self.turmas_tree.focus(str(turma_id))
            self.turmas_tree.see(str(turma_id))
        self._load_selected_turma()
        show_info("Situacao atualizada", f"A turma agora esta {nova_situacao}.", self)

    def _clear_encontro_form(self) -> None:
        self.current_encontro_id = None
        if hasattr(self, "encontro_data_entry"):
            self.encontro_turma_var.set("")
            self.encontro_data_entry.set(dt.date.today().strftime("%d/%m/%Y"))
            self.encontro_pauta_var.set("")
            self.encontro_inicio_entry.set("")
            self.encontro_termino_entry.set("")
            self.encontro_participantes_var.set("")
            self.encontro_duracao_var.set("")
            self.encontro_papel_var.set(self._default_encontro_papel())
            self.encontro_situacao_var.set("realizado")
            self.encontro_texto_auto_var.set(MULTIPLICA_TEXTOS_AUTOMATICOS[0])
            self.encontro_observacao.delete("1.0", tk.END)
            self.encontro_evidencias.set_items([])
            self._sync_encontro_calendar_highlights(apply_defaults=False)

    def _selected_encontro_id(self) -> int | None:
        if not hasattr(self, "encontros_tree"):
            return None
        selected = self.encontros_tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def _month_scope(self) -> tuple[int, int]:
        if hasattr(self, "encontro_data_entry"):
            raw = self.encontro_data_entry.get().strip()
            if raw:
                try:
                    normalized = normalize_date(raw)
                    date_value = dt.datetime.strptime(normalized, "%Y-%m-%d").date()
                    return date_value.year, date_value.month
                except ValueError:
                    pass
        today = dt.date.today()
        return today.year, today.month

    def _refresh_encontros(self) -> None:
        if not hasattr(self, "encontros_tree"):
            return
        for item_id in self.encontros_tree.get_children():
            self.encontros_tree.delete(item_id)
        if not self.linked_professor:
            return

        ano, mes = self._month_scope()
        encontros = self.db.list_multiplica_encontros_mes(int(self.linked_professor["id"]), ano, mes)
        for encontro in encontros:
            data_display = format_date_display(encontro["data"])
            if len(data_display) >= 5:
                data_display = data_display[:5]
            self.encontros_tree.insert(
                "",
                tk.END,
                iid=str(encontro["id"]),
                values=(
                    data_display,
                    encontro.get("pauta_numero") or "",
                    encontro.get("codigo_turma") or "",
                    encontro.get("papel_no_encontro") or self._default_encontro_papel(),
                    encontro.get("situacao") or "",
                    encontro.get("participantes") or 0,
                    encontro.get("imagens") or 0,
                ),
            )
        self._update_encontro_preview()

    def _calculate_duration(self, hora_inicio: str, hora_termino: str) -> str:
        if not hora_inicio or not hora_termino:
            return ""
        try:
            inicio = dt.datetime.strptime(hora_inicio, "%H:%M")
            termino = dt.datetime.strptime(hora_termino, "%H:%M")
        except ValueError:
            return ""
        if termino < inicio:
            return ""
        delta = termino - inicio
        total_minutes = int(delta.total_seconds() // 60)
        horas = total_minutes // 60
        minutos = total_minutes % 60
        return f"{horas:02d}:{minutos:02d}"

    def _apply_auto_text(self) -> None:
        text = self.encontro_texto_auto_var.get().strip()
        if not text:
            return
        current = self.encontro_observacao.get("1.0", tk.END).strip()
        if current:
            self.encontro_observacao.insert(tk.END, f"\n\n{text}")
        else:
            self.encontro_observacao.insert("1.0", text)

    def _save_encontro(self) -> None:
        if not self.linked_professor:
            show_error(
                "Professor vinculado obrigatorio",
                "Vincule um professor ao usuario antes de cadastrar encontros do Programa Multiplica.",
                self,
            )
            return

        turma_id = self.turma_map.get(self.encontro_turma_var.get().strip())
        if not turma_id:
            show_error("Turma obrigatoria", "Selecione uma turma para registrar o encontro.", self)
            return

        try:
            data_iso = normalize_date(self.encontro_data_entry.get())
            hora_inicio = normalize_time(self.encontro_inicio_entry.get()) if self.encontro_inicio_entry.get().strip() else ""
            hora_termino = normalize_time(self.encontro_termino_entry.get()) if self.encontro_termino_entry.get().strip() else ""
        except ValueError as exc:
            show_error("Dados invalidos", str(exc), self)
            return

        participantes_raw = self.encontro_participantes_var.get().strip()
        if participantes_raw and not participantes_raw.isdigit():
            show_error("Participantes invalidos", "Informe apenas numeros inteiros no campo Participantes.", self)
            return

        duracao = self.encontro_duracao_var.get().strip()
        if not duracao:
            duracao = self._calculate_duration(hora_inicio, hora_termino)

        payload = {
            "professor_id": int(self.linked_professor["id"]),
            "turma_id": turma_id,
            "data": data_iso,
            "pauta_numero": self.encontro_pauta_var.get().strip(),
            "hora_inicio": hora_inicio,
            "hora_termino": hora_termino,
            "duracao": duracao,
            "participantes": int(participantes_raw or 0),
            "papel_no_encontro": self.encontro_papel_var.get().strip() or self._default_encontro_papel(),
            "situacao": self.encontro_situacao_var.get().strip() or "realizado",
            "texto_automatico": self.encontro_texto_auto_var.get().strip(),
            "observacao": self.encontro_observacao.get("1.0", tk.END).strip(),
            "evidencias": self.encontro_evidencias.get_items(),
        }

        try:
            encontro_id = self.db.save_multiplica_encontro(payload, self.current_encontro_id)
        except ValueError as exc:
            show_error("Nao foi possivel salvar", str(exc), self)
            return

        self.current_encontro_id = encontro_id
        self._refresh_encontros()
        if hasattr(self, "encontros_tree"):
            self.encontros_tree.selection_set(str(encontro_id))
            self.encontros_tree.focus(str(encontro_id))
            self.encontros_tree.see(str(encontro_id))
        self._update_encontro_preview()
        show_info("Encontro salvo", "Os dados do encontro foram salvos com sucesso.", self)

    def _load_selected_encontro(self) -> None:
        encontro_id = self._selected_encontro_id()
        if not encontro_id:
            show_error("Selecao necessaria", "Selecione um encontro na lista para carregar.", self)
            return
        encontro = self.db.get_multiplica_encontro(encontro_id)
        if not encontro:
            show_error("Encontro nao encontrado", "Nao foi possivel carregar o encontro selecionado.", self)
            return

        self.current_encontro_id = encontro["id"]
        self.encontro_data_entry.set(format_date_display(encontro["data"]))
        self.encontro_pauta_var.set(str(encontro.get("pauta_numero") or ""))
        self.encontro_inicio_entry.set(encontro.get("hora_inicio") or "")
        self.encontro_termino_entry.set(encontro.get("hora_termino") or "")
        self.encontro_participantes_var.set(str(encontro.get("participantes") or ""))
        self.encontro_duracao_var.set(encontro.get("duracao") or "")
        self.encontro_papel_var.set(encontro.get("papel_no_encontro") or self._default_encontro_papel())
        self.encontro_situacao_var.set(encontro.get("situacao") or "realizado")
        self.encontro_texto_auto_var.set(encontro.get("texto_automatico") or MULTIPLICA_TEXTOS_AUTOMATICOS[0])
        self.encontro_observacao.delete("1.0", tk.END)
        self.encontro_observacao.insert("1.0", encontro.get("observacao") or "")
        self.encontro_evidencias.set_items(encontro.get("evidencias") or [])

        turma_label = ""
        for label, turma_id in self.turma_map.items():
            if turma_id == int(encontro["turma_id"]):
                turma_label = label
                break
        self.encontro_turma_var.set(turma_label)
        self._sync_encontro_calendar_highlights(apply_defaults=False)
        self._update_encontro_preview()

    def _update_encontro_preview(self) -> None:
        if not hasattr(self, "encontro_preview"):
            return
        encontro_id = self._selected_encontro_id()
        if not encontro_id:
            set_text(self.encontro_preview, "Selecione um encontro para visualizar os detalhes.")
            return

        encontro = self.db.get_multiplica_encontro(encontro_id)
        if not encontro:
            set_text(self.encontro_preview, "Nao foi possivel carregar os detalhes do encontro.")
            return

        evidence_names = [item.get("nome_arquivo") or "imagem" for item in encontro.get("evidencias") or []]
        evidence_text = "\n".join(f"- {name}" for name in evidence_names) if evidence_names else "- nenhuma evidencia anexada"
        content = (
            f"Data: {format_date_display(encontro['data'])}\n"
            f"Turma: {encontro.get('codigo_turma') or '-'}\n"
            f"Pauta: {encontro.get('pauta_numero') or '-'}\n"
            f"Inicio: {encontro.get('hora_inicio') or '-'}\n"
            f"Termino: {encontro.get('hora_termino') or '-'}\n"
            f"Duracao: {encontro.get('duracao') or '-'}\n"
            f"Participantes: {encontro.get('participantes') or 0}\n"
            f"Papel no encontro: {encontro.get('papel_no_encontro') or self._default_encontro_papel()}\n"
            f"Situacao: {encontro.get('situacao') or '-'}\n"
            f"Texto automatico: {encontro.get('texto_automatico') or '-'}\n\n"
            f"Observacao:\n{encontro.get('observacao') or '-'}\n\n"
            f"Evidencias:\n{evidence_text}"
        )
        set_text(self.encontro_preview, content)

    def _open_rotinas(self) -> None:
        if callable(self.on_open_rotinas):
            self.on_open_rotinas()

    def _open_relatorios(self) -> None:
        if callable(self.on_open_relatorios):
            self.on_open_relatorios()

    def _open_config(self) -> None:
        if callable(self.on_open_config):
            self.on_open_config()
