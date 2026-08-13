"""Ferramentas de backup e restauração local."""

from __future__ import annotations

import os
from datetime import datetime
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
        ttk.Button(toolbar, text="Excluir backup", command=self.delete_selected_backup).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Abrir pasta de backups", command=self.open_backup_folder).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Atualizar lista", command=self.refresh_list).pack(side="left", padx=4)

        list_frame = ttk.LabelFrame(frame, text="Backups disponíveis na pasta local")
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.backups_tree = ttk.Treeview(
            list_frame,
            columns=("arquivo", "tamanho", "modificado_em"),
            show="headings",
            selectmode="browse",
        )
        self.backups_tree.heading("arquivo", text="Arquivo")
        self.backups_tree.heading("tamanho", text="Tamanho")
        self.backups_tree.heading("modificado_em", text="Modificado em")
        self.backups_tree.column("arquivo", width=470, anchor="w")
        self.backups_tree.column("tamanho", width=140, anchor="center")
        self.backups_tree.column("modificado_em", width=180, anchor="center")
        self.backups_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.backups_tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.backups_tree.configure(yscrollcommand=scroll.set)

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.2f} MB"

    @staticmethod
    def _format_modified_time(path: Path) -> str:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M")

    def refresh_list(self) -> None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        for item_id in self.backups_tree.get_children():
            self.backups_tree.delete(item_id)
        for path in sorted(
            BACKUP_DIR.glob("*.db"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        ):
            self.backups_tree.insert(
                "",
                tk.END,
                values=(
                    path.name,
                    self._format_file_size(path.stat().st_size),
                    self._format_modified_time(path),
                ),
            )

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

    def _get_selected_backup_path(self) -> Path | None:
        selected = self.backups_tree.selection()
        if not selected:
            show_warning("Seleção necessária", "Selecione um backup na lista.", self)
            return None
        values = self.backups_tree.item(selected[0], "values")
        if not values:
            show_warning("Seleção inválida", "Não foi possível identificar o backup selecionado.", self)
            return None
        backup_path = BACKUP_DIR / str(values[0])
        if not backup_path.exists():
            show_warning("Arquivo não encontrado", "O arquivo selecionado não foi localizado na pasta de backups.", self)
            self.refresh_list()
            return None
        return backup_path

    def restore_backup(self) -> None:
        selected_name = ""
        selected_path = self._get_selected_backup_path()
        if selected_path is not None:
            selected_name = selected_path.name
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

    def delete_selected_backup(self) -> None:
        backup_path = self._get_selected_backup_path()
        if backup_path is None:
            return
        ordered_backups = sorted(
            BACKUP_DIR.glob("*.db"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        is_latest_backup = bool(ordered_backups) and ordered_backups[0] == backup_path

        confirmation_title = "Confirmar exclusão"
        confirmation_message = f"Deseja excluir este backup?\n\n{backup_path.name}"
        if is_latest_backup:
            confirmation_title = "Excluir backup mais recente"
            confirmation_message = (
                "O arquivo selecionado é o backup mais recente.\n"
                "Se continuar, você perderá a cópia local mais atual do sistema.\n\n"
                f"Backup selecionado:\n{backup_path.name}\n\n"
                "Deseja realmente excluir mesmo assim?"
            )

        if not messagebox.askyesno(
            confirmation_title,
            confirmation_message,
            parent=self,
        ):
            return
        try:
            backup_path.unlink()
        except Exception as exc:
            show_error("Falha ao excluir", str(exc), self)
            return
        self.refresh_list()
        show_info("Backup excluído", "O backup selecionado foi removido da pasta local.", self)
