from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from utils import BACKUP_DIR, center_window, show_error, show_info, show_warning


class BackupWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, db) -> None:
        super().__init__(parent)
        self.db = db
        self.title("Backup do banco local")
        center_window(self, 860, 480, parent=parent)
        self._build()
        self.refresh_list()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(
            frame,
            text=(
                "Crie cópias locais do banco SQLite para preservar o histórico. "
                "A restauração substitui o banco atual pelos dados do backup escolhido."
            ),
            wraplength=800,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        toolbar = ttk.Frame(frame)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="Criar backup automático", command=self.create_backup).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Salvar cópia em outro local", command=self.save_backup_as).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Restaurar backup", command=self.restore_backup).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Abrir pasta de backups", command=self.open_backup_folder).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar lista", command=self.refresh_list).pack(side="left", padx=4)

        list_frame = ttk.LabelFrame(frame, text="Backups disponíveis na pasta local")
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.listbox = tk.Listbox(list_frame)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scroll.set)

    def refresh_list(self) -> None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.listbox.delete(0, tk.END)
        for path in sorted(BACKUP_DIR.glob("*.db"), reverse=True):
            self.listbox.insert(tk.END, path.name)

    def open_backup_folder(self) -> None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(BACKUP_DIR))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(BACKUP_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(BACKUP_DIR)])
        except Exception:
            show_warning(
                "Abertura manual",
                f"Não foi possível abrir a pasta automaticamente.\n\nAbra manualmente:\n{BACKUP_DIR}",
                self,
            )

    def create_backup(self) -> None:
        destination = self.db.backup_database()
        self.refresh_list()
        show_info("Backup criado", f"Backup salvo em:\n{destination}", self)

    def save_backup_as(self) -> None:
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar backup como",
            defaultextension=".db",
            filetypes=[("Banco SQLite", "*.db"), ("Todos os arquivos", "*.*")],
            initialfile="backup_gestao_registros.db",
        )
        if not target:
            return
        destination = self.db.backup_database(Path(target))
        show_info("Backup criado", f"Cópia salva em:\n{destination}", self)

    def restore_backup(self) -> None:
        selected_name = self.listbox.get(tk.ACTIVE) if self.listbox.curselection() else ""
        initial = BACKUP_DIR / selected_name if selected_name else BACKUP_DIR
        backup_file = filedialog.askopenfilename(
            parent=self,
            title="Selecionar backup",
            initialdir=initial if isinstance(initial, str) else str(initial.parent if initial.is_file() else initial),
            filetypes=[("Banco SQLite", "*.db"), ("Todos os arquivos", "*.*")],
        )
        if not backup_file:
            return
        if not messagebox.askyesno(
            "Confirmar restauração",
            "A restauração substituirá o banco atual. Deseja continuar?",
            parent=self,
        ):
            return
        try:
            self.db.restore_database(Path(backup_file))
        except Exception as exc:
            show_error("Falha ao restaurar", str(exc), self)
            return
        show_info("Restauração concluída", "Backup restaurado com sucesso. Reabra módulos já abertos, se necessário.", self)
        self.refresh_list()
