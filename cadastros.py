"""Cadastros básicos de referências do sistema."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models import NIVEIS_GRAVIDADE, PROFESSOR_SITUACOES, PROFESSOR_VINCULOS, SITUACOES_ATIVO_INATIVO
from utils import center_window, get_text, show_error, show_info


class CadastrosWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.title("Cadastros básicos")
        self.resizable(True, True)
        self.grab_set()
        center_window(self, 1180, 700, parent=parent)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.professores_tab = CadastroProfessoresTab(self.notebook, db, on_change=self._notify_change)
        self.espacos_tab = CadastroEspacosTab(self.notebook, db, on_change=self._notify_change)
        self.tipos_tab = CadastroTiposTab(self.notebook, db, on_change=self._notify_change)

        self.notebook.add(self.professores_tab, text="Professores")
        self.notebook.add(self.espacos_tab, text="Espaços")
        self.notebook.add(self.tipos_tab, text="Tipos de ocorrência")

    def _notify_change(self) -> None:
        if self.on_change:
            self.on_change()


class CadastroProfessoresTab(ttk.Frame):
    columns = ("id", "nome_completo", "nome_curto", "area_atuacao", "espaco", "situacao", "vinculo")

    def __init__(self, parent: ttk.Notebook, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Button(toolbar, text="Novo professor", command=self.new_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Editar", command=self.edit_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Ativar", command=lambda: self.change_status("ativo")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Inativar", command=lambda: self.change_status("inativo")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar lista", command=self.refresh).pack(side="left", padx=4)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings", height=18)
        headings = {
            "id": "ID",
            "nome_completo": "Nome completo",
            "nome_curto": "Nome curto",
            "area_atuacao": "Área",
            "espaco": "Espaço principal",
            "situacao": "Situação",
            "vinculo": "Vínculo",
        }
        widths = {"id": 60, "nome_completo": 280, "nome_curto": 170, "area_atuacao": 140, "espaco": 180, "situacao": 110, "vinculo": 150}
        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for professor in self.db.list_professors(include_inactive=True):
            self.tree.insert(
                "",
                "end",
                iid=str(professor["id"]),
                values=(
                    professor["id"],
                    professor["nome_completo"],
                    professor["nome_curto"],
                    professor.get("area_atuacao") or "",
                    professor.get("espaco_principal_nome") or "",
                    professor["situacao"],
                    professor["vinculo"],
                ),
            )

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def new_record(self) -> None:
        ProfessorForm(self, self.db, on_save=self._after_change)

    def edit_record(self) -> None:
        professor_id = self.selected_id()
        if not professor_id:
            show_error("Seleção obrigatória", "Selecione um professor para editar.", self)
            return
        ProfessorForm(self, self.db, professor_id=professor_id, on_save=self._after_change)

    def change_status(self, situacao: str) -> None:
        professor_id = self.selected_id()
        if not professor_id:
            show_error("Seleção obrigatória", "Selecione um professor para alterar a situação.", self)
            return
        self.db.update_professor_status(professor_id, situacao)
        self._after_change()
        show_info("Situação atualizada", f"Professor atualizado para '{situacao}'.", self)

    def _after_change(self) -> None:
        self.refresh()
        if self.on_change:
            self.on_change()


class CadastroEspacosTab(ttk.Frame):
    columns = ("id", "nome", "descricao", "situacao")

    def __init__(self, parent: ttk.Notebook, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        ttk.Button(toolbar, text="Novo espaço", command=self.new_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Editar", command=self.edit_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Ativar", command=lambda: self.change_status("ativo")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Inativar", command=lambda: self.change_status("inativo")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar lista", command=self.refresh).pack(side="left", padx=4)

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(frame, columns=self.columns, show="headings", height=18)
        widths = {"id": 60, "nome": 240, "descricao": 620, "situacao": 100}
        headings = {"id": "ID", "nome": "Nome", "descricao": "Descrição", "situacao": "Situação"}
        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in self.db.list_spaces(include_inactive=True):
            self.tree.insert(
                "",
                "end",
                iid=str(record["id"]),
                values=(record["id"], record["nome"], record.get("descricao") or "", record["situacao"]),
            )

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def new_record(self) -> None:
        EntityForm(self, self.db, entity_name="espaço", on_save=self._after_change)

    def edit_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione um espaço para editar.", self)
            return
        EntityForm(self, self.db, entity_name="espaço", record_id=record_id, on_save=self._after_change)

    def change_status(self, situacao: str) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione um espaço para alterar a situação.", self)
            return
        self.db.update_space_status(record_id, situacao)
        self._after_change()
        show_info("Situação atualizada", f"Espaço atualizado para '{situacao}'.", self)

    def _after_change(self) -> None:
        self.refresh()
        if self.on_change:
            self.on_change()


class CadastroTiposTab(ttk.Frame):
    columns = ("id", "nome", "descricao", "gravidade", "situacao")

    def __init__(self, parent: ttk.Notebook, db, on_change=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        ttk.Button(toolbar, text="Novo tipo", command=self.new_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Editar", command=self.edit_record).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Ativar", command=lambda: self.change_status("ativo")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Inativar", command=lambda: self.change_status("inativo")).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar lista", command=self.refresh).pack(side="left", padx=4)

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(frame, columns=self.columns, show="headings", height=18)
        widths = {"id": 60, "nome": 220, "descricao": 520, "gravidade": 120, "situacao": 100}
        headings = {
            "id": "ID",
            "nome": "Nome",
            "descricao": "Descrição",
            "gravidade": "Gravidade padrão",
            "situacao": "Situação",
        }
        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in self.db.list_occurrence_types(include_inactive=True):
            self.tree.insert(
                "",
                "end",
                iid=str(record["id"]),
                values=(
                    record["id"],
                    record["nome"],
                    record.get("descricao") or "",
                    record.get("nivel_gravidade_padrao") or "",
                    record["situacao"],
                ),
            )

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def new_record(self) -> None:
        EntityForm(self, self.db, entity_name="tipo", on_save=self._after_change)

    def edit_record(self) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione um tipo para editar.", self)
            return
        EntityForm(self, self.db, entity_name="tipo", record_id=record_id, on_save=self._after_change)

    def change_status(self, situacao: str) -> None:
        record_id = self.selected_id()
        if not record_id:
            show_error("Seleção obrigatória", "Selecione um tipo para alterar a situação.", self)
            return
        self.db.update_occurrence_type_status(record_id, situacao)
        self._after_change()
        show_info("Situação atualizada", f"Tipo atualizado para '{situacao}'.", self)

    def _after_change(self) -> None:
        self.refresh()
        if self.on_change:
            self.on_change()


class ProfessorForm(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, professor_id: int | None = None, on_save=None) -> None:
        super().__init__(parent)
        self.db = db
        self.professor_id = professor_id
        self.on_save = on_save
        self.space_map: dict[str, int | None] = {"": None}

        self.title("Cadastro de professor")
        self.transient(parent)
        self.grab_set()
        center_window(self, 680, 560)

        self._build()
        self._load_spaces()
        if professor_id:
            self._load_data()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        self.entries = {}
        labels = [
            ("nome_completo", "Nome completo *"),
            ("nome_curto", "Nome curto *"),
            ("area_atuacao", "Área de atuação"),
            ("telefone_institucional", "Telefone institucional"),
            ("email_institucional", "E-mail institucional"),
        ]
        for row_index, (key, label) in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=row_index, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame, width=58)
            entry.grid(row=row_index, column=1, sticky="ew", pady=4)
            self.entries[key] = entry

        ttk.Label(frame, text="Espaço principal").grid(row=5, column=0, sticky="w", pady=4)
        self.space_combo = ttk.Combobox(frame, state="readonly", width=55)
        self.space_combo.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Situação *").grid(row=6, column=0, sticky="w", pady=4)
        self.situacao_combo = ttk.Combobox(frame, values=PROFESSOR_SITUACOES, state="readonly", width=55)
        self.situacao_combo.grid(row=6, column=1, sticky="ew", pady=4)
        self.situacao_combo.set("ativo")

        ttk.Label(frame, text="Vínculo *").grid(row=7, column=0, sticky="w", pady=4)
        self.vinculo_combo = ttk.Combobox(frame, values=PROFESSOR_VINCULOS, state="readonly", width=55)
        self.vinculo_combo.grid(row=7, column=1, sticky="ew", pady=4)
        self.vinculo_combo.set(PROFESSOR_VINCULOS[0])

        ttk.Label(frame, text="Observações").grid(row=8, column=0, sticky="nw", pady=4)
        self.observacoes_text = tk.Text(frame, width=48, height=8)
        self.observacoes_text.grid(row=8, column=1, sticky="ew", pady=4)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=9, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Salvar", command=self.save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        frame.columnconfigure(1, weight=1)

    def _load_spaces(self) -> None:
        values = [""]
        for space in self.db.list_spaces(include_inactive=False):
            values.append(space["nome"])
            self.space_map[space["nome"]] = space["id"]
        self.space_combo["values"] = values
        self.space_combo.set("")

    def _load_data(self) -> None:
        record = self.db.get_professor(self.professor_id)
        if not record:
            return
        for key, entry in self.entries.items():
            entry.insert(0, record.get(key) or "")
        self.space_combo.set(record.get("espaco_principal_nome") or "")
        self.situacao_combo.set(record["situacao"])
        self.vinculo_combo.set(record["vinculo"])
        self.observacoes_text.insert("1.0", record.get("observacoes") or "")

    def save(self) -> None:
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        data["espaco_principal_id"] = self.space_map.get(self.space_combo.get())
        data["situacao"] = self.situacao_combo.get().strip()
        data["vinculo"] = self.vinculo_combo.get().strip()
        data["observacoes"] = get_text(self.observacoes_text)

        if not data["nome_completo"] or not data["nome_curto"] or not data["situacao"] or not data["vinculo"]:
            show_error("Campos obrigatórios", "Preencha nome completo, nome curto, situação e vínculo.", self)
            return

        self.db.save_professor(data, self.professor_id)
        if self.on_save:
            self.on_save()
        show_info("Cadastro salvo", "Professor salvo com sucesso.", self)
        self.destroy()


class EntityForm(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, entity_name: str, record_id: int | None = None, on_save=None) -> None:
        super().__init__(parent)
        self.db = db
        self.entity_name = entity_name
        self.record_id = record_id
        self.on_save = on_save

        self.title(f"Cadastro de {entity_name}")
        self.transient(parent)
        self.grab_set()
        center_window(self, 640, 420)

        self._build()
        if record_id:
            self._load_data()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nome *").grid(row=0, column=0, sticky="w", pady=4)
        self.nome_entry = ttk.Entry(frame, width=60)
        self.nome_entry.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Descrição").grid(row=1, column=0, sticky="nw", pady=4)
        self.descricao_text = tk.Text(frame, width=48, height=8)
        self.descricao_text.grid(row=1, column=1, sticky="ew", pady=4)

        current_row = 2
        self.gravidade_combo = None
        if self.entity_name == "tipo":
            ttk.Label(frame, text="Gravidade padrão").grid(row=current_row, column=0, sticky="w", pady=4)
            self.gravidade_combo = ttk.Combobox(frame, values=[""] + NIVEIS_GRAVIDADE, state="readonly", width=57)
            self.gravidade_combo.grid(row=current_row, column=1, sticky="ew", pady=4)
            self.gravidade_combo.set("")
            current_row += 1

        ttk.Label(frame, text="Situação *").grid(row=current_row, column=0, sticky="w", pady=4)
        self.situacao_combo = ttk.Combobox(frame, values=SITUACOES_ATIVO_INATIVO, state="readonly", width=57)
        self.situacao_combo.grid(row=current_row, column=1, sticky="ew", pady=4)
        self.situacao_combo.set("ativo")

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=current_row + 1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Salvar", command=self.save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)
        frame.columnconfigure(1, weight=1)

    def _load_data(self) -> None:
        record = self.db.get_space(self.record_id) if self.entity_name == "espaço" else self.db.get_occurrence_type(self.record_id)
        if not record:
            return
        self.nome_entry.insert(0, record["nome"])
        self.descricao_text.delete("1.0", tk.END)
        self.descricao_text.insert("1.0", record.get("descricao") or "")
        self.situacao_combo.set(record["situacao"])
        if self.gravidade_combo is not None:
            self.gravidade_combo.set(record.get("nivel_gravidade_padrao") or "")

    def save(self) -> None:
        data = {
            "nome": self.nome_entry.get().strip(),
            "descricao": get_text(self.descricao_text),
            "situacao": self.situacao_combo.get().strip(),
            "nivel_gravidade_padrao": self.gravidade_combo.get().strip() if self.gravidade_combo else None,
        }
        if not data["nome"] or not data["situacao"]:
            show_error("Campos obrigatórios", "Preencha ao menos nome e situação.", self)
            return

        if self.entity_name == "espaço":
            self.db.save_space(data, self.record_id)
        else:
            self.db.save_occurrence_type(data, self.record_id)

        if self.on_save:
            self.on_save()
        show_info("Cadastro salvo", f"{self.entity_name.capitalize()} salvo com sucesso.", self)
        self.destroy()
