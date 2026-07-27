from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models import APP_NAME
from utils import center_window, show_error, show_info, validate_password_strength


class LoginWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db) -> None:
        super().__init__(parent)
        self.db = db
        self.authenticated_user: dict | None = None

        self.title("Acesso ao sistema")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        center_window(self, 460, 280)

        self._build()
        self.lift()
        self.focus_force()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )
        ttk.Label(
            frame,
            text="Informe usuário e senha para acessar os registros locais.",
            wraplength=400,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(frame, text="Usuário").grid(row=2, column=0, sticky="w", pady=4)
        self.username_entry = ttk.Entry(frame, width=34)
        self.username_entry.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Senha").grid(row=3, column=0, sticky="w", pady=4)
        self.password_entry = ttk.Entry(frame, width=34, show="*")
        self.password_entry.grid(row=3, column=1, sticky="ew", pady=4)
        self.password_entry.bind("<Return>", lambda _event: self.login())

        self.info_label = ttk.Label(frame, foreground="#7a5c00", wraplength=400, justify="left")
        self.info_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(button_frame, text="Entrar", command=self.login).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self._cancel).pack(side="left", padx=4)

        if not self.db.has_any_user():
            self.info_label.config(
                text=(
                    "Nenhum usuário foi cadastrado ainda. "
                    "Faça o primeiro acesso usando o botão abaixo para criar a conta administradora local."
                )
            )
            ttk.Button(button_frame, text="Criar primeiro usuário", command=self.open_first_user_setup).pack(
                side="left", padx=4
            )

        self.username_entry.focus_set()

    def login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            show_error("Campos obrigatórios", "Informe usuário e senha.", self)
            return
        user = self.db.authenticate_user(username, password)
        if not user:
            show_error("Acesso negado", "Usuário ou senha inválidos.", self)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
            return
        self.authenticated_user = user
        self.destroy()

    def open_first_user_setup(self) -> None:
        FirstUserSetupWindow(self, self.db, on_success=self._on_first_user_created)

    def _on_first_user_created(self, username: str) -> None:
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, tk.END)
        self.info_label.config(text="Primeiro usuário criado. Faça login para acessar o sistema.")
        show_info("Usuário criado", "Conta administradora local criada com sucesso.", self)
        self.username_entry.focus_set()

    def _cancel(self) -> None:
        self.authenticated_user = None
        self.destroy()


class FirstUserSetupWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, on_success=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_success = on_success
        self.title("Primeiro usuário")
        self.transient(parent)
        self.grab_set()
        center_window(self, 520, 340)
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Criar conta administradora local", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Label(
            frame,
            text=(
                "Esse usuário será exigido para abrir o sistema e ajuda a reduzir o risco de acesso "
                "indevido a dados sensíveis."
            ),
            wraplength=470,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(frame, text="Nome do responsável").grid(row=2, column=0, sticky="w", pady=4)
        self.full_name_entry = ttk.Entry(frame, width=36)
        self.full_name_entry.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Usuário").grid(row=3, column=0, sticky="w", pady=4)
        self.username_entry = ttk.Entry(frame, width=36)
        self.username_entry.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Senha").grid(row=4, column=0, sticky="w", pady=4)
        self.password_entry = ttk.Entry(frame, width=36, show="*")
        self.password_entry.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Confirmar senha").grid(row=5, column=0, sticky="w", pady=4)
        self.confirm_entry = ttk.Entry(frame, width=36, show="*")
        self.confirm_entry.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(
            frame,
            text="Recomendação: use no mínimo 8 caracteres e guarde a senha em local seguro.",
            wraplength=470,
            justify="left",
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(button_frame, text="Salvar usuário", command=self.save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def save(self) -> None:
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirmation = self.confirm_entry.get()

        if not full_name or not username or not password or not confirmation:
            show_error("Campos obrigatórios", "Preencha todos os campos.", self)
            return
        if password != confirmation:
            show_error("Senhas diferentes", "A confirmação da senha não confere.", self)
            return
        try:
            validate_password_strength(password)
            self.db.create_user(full_name, username, password)
        except ValueError as exc:
            show_error("Validação", str(exc), self)
            return

        if self.on_success:
            self.on_success(username)
        self.destroy()


class ChangePasswordWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db, user_id: int) -> None:
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.title("Alterar senha")
        self.transient(parent)
        self.grab_set()
        center_window(self, 500, 290)
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Senha atual").grid(row=0, column=0, sticky="w", pady=4)
        self.current_entry = ttk.Entry(frame, width=34, show="*")
        self.current_entry.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Nova senha").grid(row=1, column=0, sticky="w", pady=4)
        self.new_entry = ttk.Entry(frame, width=34, show="*")
        self.new_entry.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Confirmar nova senha").grid(row=2, column=0, sticky="w", pady=4)
        self.confirm_entry = ttk.Entry(frame, width=34, show="*")
        self.confirm_entry.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(
            frame,
            text="A nova senha precisa ter ao menos 8 caracteres.",
            wraplength=440,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(button_frame, text="Atualizar senha", command=self.save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def save(self) -> None:
        current_password = self.current_entry.get()
        new_password = self.new_entry.get()
        confirmation = self.confirm_entry.get()

        if not current_password or not new_password or not confirmation:
            show_error("Campos obrigatórios", "Preencha todos os campos.", self)
            return
        if new_password != confirmation:
            show_error("Senhas diferentes", "A confirmação da nova senha não confere.", self)
            return
        try:
            validate_password_strength(new_password)
            self.db.change_user_password(self.user_id, current_password, new_password)
        except ValueError as exc:
            show_error("Validação", str(exc), self)
            return

        show_info("Senha atualizada", "A senha foi alterada com sucesso.", self)
        self.destroy()
