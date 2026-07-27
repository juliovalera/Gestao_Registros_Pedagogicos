"""Aplicação principal da Gestão de Registros Pedagógicos."""

from __future__ import annotations

import sys
import traceback
import tkinter as tk
from tkinter import ttk

from auth import ChangePasswordWindow, LoginWindow
from ausencias import AusenciasWindow
from backup import BackupWindow
from cadastros import CadastrosWindow
from consultas import ConsultasWindow
from database import DatabaseManager
from intercorrencias import IntercorrenciasWindow
from models import APP_CREDITS, APP_NAME, APP_TITLE, APP_VERSION
from relatorios import RelatoriosWindow
from rotinas import RotinasDocentesWindow
from utils import DATA_DIR, center_window, ensure_directories, list_database_files, load_text_file, open_directory, set_text, show_error


class MainApplication(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        ensure_directories()
        self.db = DatabaseManager()
        self.db.initialize_database()
        self.current_user: dict | None = None
        self._multiple_db_warning_open = False

        self.title(APP_TITLE)
        center_window(self, 1080, 720)
        self.minsize(980, 650)
        self._build_style()
        self._build_menu()
        self._build_layout()
        self.refresh_dashboard()
        self.bind("<FocusIn>", self._handle_focus_refresh)
        self.after(60000, self._schedule_dashboard_refresh)
        self.after(150, self._warn_if_multiple_databases)
        self.after(50, self.require_login)

    def report_callback_exception(self, exc, val, tb) -> None:  # type: ignore[override]
        details = "".join(traceback.format_exception(exc, val, tb))
        show_error(
            "Erro inesperado",
            f"O sistema tratou um erro sem encerrar a aplicação.\n\n{val}\n\nDetalhes técnicos:\n{details}",
            self,
        )

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    def _warn_if_multiple_databases(self) -> None:
        database_files = list_database_files()
        if len(database_files) <= 1 or self._multiple_db_warning_open:
            return

        self._multiple_db_warning_open = True
        file_names = "\n".join(f"- {path.name}" for path in database_files)
        dialog = tk.Toplevel(self)
        dialog.title("Atenção aos bancos de dados")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        center_window(dialog, 620, 360, parent=self)

        def close_dialog() -> None:
            self._multiple_db_warning_open = False
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text=(
                "Foram encontrados vários arquivos de banco na pasta 'data'.\n\n"
                "O sistema usa apenas o banco principal do sistema, mas a existência de outros arquivos "
                "pode indicar conflito de sincronização ou cópia duplicada."
            ),
            wraplength=570,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        files_box = ttk.LabelFrame(frame, text="Arquivos encontrados", padding=8)
        files_box.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        ttk.Label(files_box, text=file_names, justify="left").pack(anchor="w")

        ttk.Label(
            frame,
            text=(
                "Recomendação:\n"
                "- mantenha apenas o banco principal na pasta 'data';\n"
                "- revise bancos extras manualmente antes de mover para 'backups'."
            ),
            justify="left",
            wraplength=570,
        ).grid(row=2, column=0, sticky="w")

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Abrir pasta data", command=lambda: open_directory(DATA_DIR, dialog)).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Fechar", command=close_dialog).pack(side="left")

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)
        ajuda_menu = tk.Menu(menu_bar, tearoff=0)
        ajuda_menu.add_command(label="Manual do usuário", command=self.show_manual)
        ajuda_menu.add_command(label="README / Documentação", command=self.show_readme)
        ajuda_menu.add_separator()
        ajuda_menu.add_command(label="Sobre", command=self.show_about)
        seguranca_menu = tk.Menu(menu_bar, tearoff=0)
        seguranca_menu.add_command(label="Alterar senha", command=self.change_password)
        seguranca_menu.add_command(label="Trocar usuário", command=self.logout)
        menu_bar.add_cascade(label="Segurança", menu=seguranca_menu)
        menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)
        self.config(menu=menu_bar)

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self, padding=14)
        root_frame.pack(fill="both", expand=True)

        header = ttk.Frame(root_frame)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(anchor="w")
        self.user_label = ttk.Label(header, text="Usuário não autenticado")
        self.user_label.pack(anchor="w", pady=(8, 0))

        content = ttk.Frame(root_frame)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=0)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        nav = ttk.LabelFrame(content, text="Módulos", style="Card.TLabelframe")
        nav.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        nav.columnconfigure(0, weight=1)
        nav.rowconfigure(0, weight=1)

        nav_canvas = tk.Canvas(nav, width=320, highlightthickness=0, borderwidth=0)
        nav_canvas.grid(row=0, column=0, sticky="ns")
        nav_scrollbar = ttk.Scrollbar(nav, orient="vertical", command=nav_canvas.yview)
        nav_scrollbar.grid(row=0, column=1, sticky="ns")
        nav_canvas.configure(yscrollcommand=nav_scrollbar.set)

        nav_inner = ttk.Frame(nav_canvas)
        nav_window = nav_canvas.create_window((0, 0), window=nav_inner, anchor="nw")

        def update_nav_scroll(_event=None) -> None:
            nav_canvas.configure(scrollregion=nav_canvas.bbox("all"))

        def resize_nav_inner(_event) -> None:
            nav_canvas.itemconfigure(nav_window, width=_event.width)

        nav_inner.bind("<Configure>", update_nav_scroll)
        nav_canvas.bind("<Configure>", resize_nav_inner)

        buttons = [
            ("1. Cadastros básicos", self.open_cadastros),
            ("2. Nova intercorrência", self.open_intercorrencias),
            ("3. Registrar ausência de professor", self.open_ausencias),
            ("4. Rotina docente", self.open_rotinas),
            ("5. Consultar registros", self.open_consultas),
            ("6. Relatório do dia", lambda: self.open_relatorios("dia")),
            ("7. Relatório por período", lambda: self.open_relatorios("periodo")),
            ("8. Relatório por professor", lambda: self.open_relatorios("professor")),
            ("9. Relatório por espaço", lambda: self.open_relatorios("espaco")),
            ("10. Exportar dados", lambda: self.open_relatorios("exportar")),
            ("11. Backup", self.open_backup),
            ("12. Sair", self.destroy),
            ("Ajuda rápida", self.show_manual),
        ]
        for index, (text, command) in enumerate(buttons):
            pady = (4, 4) if index < 10 else (8, 4)
            ttk.Button(nav_inner, text=text, command=command, width=34).pack(fill="x", pady=pady)

        right_panel = ttk.Frame(content)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        summary_frame = ttk.LabelFrame(right_panel, text="Resumo inicial", style="Card.TLabelframe")
        summary_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.summary_labels = {}
        summary_items = [
            ("professores_ativos", "Professores ativos"),
            ("espacos_ativos", "Espaços ativos"),
            ("tipos_ativos", "Tipos de ocorrência ativos"),
            ("intercorrencias_hoje", "Intercorrências hoje"),
            ("ausencias_hoje", "Ausências hoje"),
            ("rotinas_hoje", "Rotinas docentes hoje"),
        ]
        for index, (key, label) in enumerate(summary_items):
            ttk.Label(summary_frame, text=f"{label}:").grid(row=index, column=0, sticky="w", padx=4, pady=3)
            value_label = ttk.Label(summary_frame, text="0")
            value_label.grid(row=index, column=1, sticky="w", padx=4, pady=3)
            self.summary_labels[key] = value_label

        help_frame = ttk.LabelFrame(right_panel, text="Orientação de uso", style="Card.TLabelframe")
        help_frame.grid(row=1, column=0, sticky="nsew")
        help_frame.rowconfigure(0, weight=1)
        help_frame.columnconfigure(0, weight=1)
        self.help_text = tk.Text(help_frame, wrap="word")
        self.help_text.grid(row=0, column=0, sticky="nsew")
        self.help_text.insert(
            "1.0",
            "Use registros objetivos, profissionais e cronológicos.\n\n"
            "Evite julgamentos pessoais, dados sensíveis desnecessários e identificação completa de estudantes. "
            "Prefira iniciais, turma ou identificação genérica quando necessário.\n\n"
            "Fluxo sugerido:\n"
            "1. Revise os cadastros básicos.\n"
            "2. Registre intercorrências, ausências e rotinas docentes.\n"
            "3. Consulte e filtre os históricos.\n"
            "4. Gere relatórios para acompanhamento e coordenação.\n"
            "5. Faça backups regularmente.",
        )
        self.help_text.config(state="disabled")

    def refresh_dashboard(self) -> None:
        summary = self.db.get_dashboard_summary()
        for key, widget in self.summary_labels.items():
            widget.config(text=str(summary.get(key, 0)))
        if self.current_user:
            nome = self.current_user.get("nome_completo") or self.current_user.get("nome_usuario") or ""
            usuario = self.current_user.get("nome_usuario") or ""
            self.user_label.config(text=f"Acesso autenticado: {nome} ({usuario})")
        else:
            self.user_label.config(text="Usuário não autenticado")

    def _handle_focus_refresh(self, _event=None) -> None:
        self.refresh_dashboard()

    def _schedule_dashboard_refresh(self) -> None:
        if self.winfo_exists():
            self.refresh_dashboard()
            self.after(60000, self._schedule_dashboard_refresh)

    def require_login(self) -> None:
        login = LoginWindow(self, self.db)
        self.wait_window(login)
        if not login.authenticated_user:
            self.destroy()
            return
        self.current_user = login.authenticated_user
        self.refresh_dashboard()
        self.lift()
        self.focus_force()

    def change_password(self) -> None:
        if not self.current_user:
            show_error("Acesso necessário", "Faça login para alterar a senha.", self)
            return
        ChangePasswordWindow(self, self.db, self.current_user["id"])

    def logout(self) -> None:
        for child in list(self.winfo_children()):
            if isinstance(child, tk.Toplevel):
                child.destroy()
        self.current_user = None
        self.require_login()

    def open_cadastros(self) -> None:
        CadastrosWindow(self, self.db, on_change=self.refresh_dashboard)

    def open_intercorrencias(self) -> None:
        IntercorrenciasWindow(self, self.db, on_change=self.refresh_dashboard)

    def open_ausencias(self) -> None:
        AusenciasWindow(self, self.db, on_change=self.refresh_dashboard)

    def open_rotinas(self) -> None:
        RotinasDocentesWindow(self, self.db, on_change=self.refresh_dashboard)

    def open_consultas(self) -> None:
        ConsultasWindow(self, self.db)

    def open_relatorios(self, mode: str = "dia") -> None:
        RelatoriosWindow(self, self.db, initial_mode=mode)

    def open_backup(self) -> None:
        BackupWindow(self, self.db)

    def _show_document_text(self, title: str, path: str) -> None:
        window = tk.Toplevel(self)
        window.title(title)
        center_window(window, 900, 640)
        frame = ttk.Frame(window, padding=10)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="word")
        text.pack(fill="both", expand=True)
        set_text(text, load_text_file(path))

    def show_manual(self) -> None:
        self._show_document_text("Manual do usuário", "docs/manual_usuario.md")

    def show_readme(self) -> None:
        self._show_document_text("README", "README.md")

    def show_about(self) -> None:
        window = tk.Toplevel(self)
        window.title("Sobre")
        center_window(window, 520, 280)
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text=f"Versão {APP_VERSION}").pack(anchor="w", pady=(6, 0))
        ttk.Label(frame, text=APP_CREDITS, justify="left").pack(anchor="w", pady=10)
        ttk.Label(
            frame,
            text=(
                "Sistema local em Python 3, SQLite e Tkinter para registro, consulta, análise, "
                "relatórios e backup de intercorrências diárias no contexto pedagógico escolar."
            ),
            wraplength=460,
            justify="left",
        ).pack(anchor="w")


def _wait_before_exit(message: str) -> None:
    print(message)
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nPressione Enter para fechar...")
    except EOFError:
        pass


if __name__ == "__main__":
    try:
        app = MainApplication()
        app.mainloop()
    except tk.TclError as exc:
        _wait_before_exit(
            "Falha ao iniciar a interface Tkinter.\n"
            "Verifique se o Python foi instalado com suporte a Tcl/Tk.\n\n"
            f"Detalhes: {exc}"
        )
    except Exception as exc:
        _wait_before_exit(
            "O sistema encontrou um erro ao iniciar.\n\n"
            f"Detalhes: {exc}"
        )
