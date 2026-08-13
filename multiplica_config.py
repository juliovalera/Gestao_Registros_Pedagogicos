"""Janela de configuração do modo de uso do Programa Multiplica."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models import MODOS_MULTIPLICA, MODO_MULTIPLICA_LABELS, MODO_MULTIPLICA_PADRAO
from utils import center_window, install_combobox_typeahead, show_error, show_info


class MultiplicaModeWindow(tk.Toplevel):
    """Permite vincular um professor ao usuário e definir o modo do sistema."""

    def __init__(self, parent: tk.Misc, db, user_id: int, on_save=None) -> None:
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.on_save = on_save
        self.professor_map: dict[str, int | None] = {"": None}
        self.mode_label_to_value = {label: value for value, label in MODOS_MULTIPLICA}

        self.title("Modo de uso do sistema")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        center_window(self, 640, 370, parent=parent)

        self._build()
        self._load_data()
        install_combobox_typeahead(self)

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Modo de uso do sistema",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            frame,
            text=(
                "Escolha como o sistema deve se comportar neste computador. "
                "O modo selecionado libera os recursos do Programa Multiplica sem alterar os registros já existentes."
            ),
            wraplength=580,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 14))

        ttk.Label(frame, text="Professor vinculado").grid(row=2, column=0, sticky="w", pady=6, padx=(0, 12))
        self.professor_combo = ttk.Combobox(frame, state="readonly", width=42)
        self.professor_combo.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Modo no Programa Multiplica").grid(
            row=3,
            column=0,
            sticky="w",
            pady=6,
            padx=(0, 12),
        )
        self.mode_combo = ttk.Combobox(
            frame,
            state="readonly",
            width=42,
            values=[label for _value, label in MODOS_MULTIPLICA],
        )
        self.mode_combo.grid(row=3, column=1, sticky="ew", pady=6)
        self.mode_combo.bind("<<ComboboxSelected>>", self._update_hint)

        hint_frame = ttk.LabelFrame(frame, text="Orientação", padding=10)
        hint_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        hint_frame.columnconfigure(0, weight=1)
        self.hint_label = ttk.Label(hint_frame, text="", wraplength=560, justify="left")
        self.hint_label.grid(row=0, column=0, sticky="w")

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(18, 0))
        ttk.Button(buttons, text="Salvar configuração", command=self.save).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left")

    def _load_data(self) -> None:
        values = [""]
        for professor in self.db.list_professors(include_inactive=True):
            situacao = str(professor.get("situacao") or "ativo")
            suffix = "" if situacao == "ativo" else f" [{situacao}]"
            label = f"{professor['nome_completo']}{suffix}"
            self.professor_map[label] = professor["id"]
            values.append(label)
        self.professor_combo["values"] = values

        settings = self.db.get_user_multiplica_settings(self.user_id)
        professor_id = settings.get("professor_id")
        modo = settings.get("modo_multiplica") or MODO_MULTIPLICA_PADRAO

        selected_professor = ""
        if professor_id:
            for label, mapped_id in self.professor_map.items():
                if mapped_id == professor_id:
                    selected_professor = label
                    break
        self.professor_combo.set(selected_professor)
        self.mode_combo.set(MODO_MULTIPLICA_LABELS.get(modo, MODO_MULTIPLICA_LABELS[MODO_MULTIPLICA_PADRAO]))
        self._update_hint()

    def _update_hint(self, _event=None) -> None:
        mode_value = self.mode_label_to_value.get(self.mode_combo.get(), MODO_MULTIPLICA_PADRAO)
        if mode_value == "multiplicador":
            text = (
                "Professor multiplicador: prepara o sistema para o acompanhamento de turmas, encontros, "
                "cursistas e relatórios específicos do Programa Multiplica."
            )
        elif mode_value == "cursista":
            text = (
                "Professor cursista: prepara o sistema para o registro de formações recebidas, "
                "aplicações em aula, reflexões e evidências do percurso formativo."
            )
        else:
            text = (
                "Uso geral: mantém o sistema no fluxo pedagógico já existente, sem habilitar os recursos "
                "específicos do Programa Multiplica."
            )
        self.hint_label.config(text=text)

    def save(self) -> None:
        mode_value = self.mode_label_to_value.get(self.mode_combo.get(), MODO_MULTIPLICA_PADRAO)
        professor_id = self.professor_map.get(self.professor_combo.get().strip())

        if mode_value != MODO_MULTIPLICA_PADRAO and not professor_id:
            show_error(
                "Professor vinculado obrigatório",
                "Selecione o professor vinculado ao usuário antes de ativar o modo de Professor multiplicador ou Professor cursista.",
                self,
            )
            return

        try:
            updated_user = self.db.update_user_multiplica_settings(self.user_id, mode_value, professor_id)
        except ValueError as exc:
            show_error("Não foi possível salvar", str(exc), self)
            return

        if callable(self.on_save):
            self.on_save(updated_user)
        show_info("Configuração salva", "O modo de uso do sistema foi atualizado com sucesso.", self)
        self.destroy()
