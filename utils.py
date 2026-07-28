"""Utilitários compartilhados da interface e do projeto."""

from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import hmac
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
import unicodedata
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = None
    ImageGrab = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
EXPORT_DIR = BASE_DIR / "exports"
DOCS_DIR = BASE_DIR / "docs"
DB_PATH = DATA_DIR / "gestao_registros_ciebp.db"


def ensure_directories() -> None:
    for directory in (DATA_DIR, BACKUP_DIR, EXPORT_DIR, DOCS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def list_database_files() -> list[Path]:
    ensure_directories()
    return sorted(DATA_DIR.glob("*.db"))


def current_timestamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_date_iso() -> str:
    return dt.date.today().strftime("%Y-%m-%d")


def current_time_hm() -> str:
    return dt.datetime.now().strftime("%H:%M")


def normalize_date(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""

    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError("Use a data no formato DD/MM/AAAA ou AAAA-MM-DD.")


def format_date_display(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value


def normalize_time(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return dt.datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            continue
    raise ValueError("Use o horário no formato HH:MM.")


def clean_optional(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def text_or_none(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{salt.hex()}:{derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":", maxsplit=1)
    except ValueError:
        return False
    recalculated = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(recalculated, stored_hash)


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")


def center_window(window: tk.Misc, width: int, height: int, parent: tk.Misc | None = None) -> None:
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    max_width = max(screen_width - 80, 640)
    max_height = max(screen_height - 120, 480)
    final_width = min(width, max_width)
    final_height = min(height, max_height)
    if parent is not None:
        parent.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = max(parent.winfo_width(), final_width)
        parent_height = max(parent.winfo_height(), final_height)
        pos_x = parent_x + max((parent_width - final_width) // 2, 0)
        pos_y = parent_y + max((parent_height - final_height) // 2, 0)
    else:
        pos_x = max((screen_width - final_width) // 2, 0)
        pos_y = max((screen_height - final_height) // 2, 0)

    pos_x = min(max(pos_x, 20), max(screen_width - final_width - 20, 20))
    pos_y = min(max(pos_y, 40), max(screen_height - final_height - 60, 40))
    window.geometry(f"{final_width}x{final_height}+{pos_x}+{pos_y}")


def set_text(widget: tk.Text, content: str) -> None:
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", content)
    widget.config(state="disabled")


def get_text(widget: tk.Text) -> str:
    return widget.get("1.0", tk.END).strip()


def load_text_file(relative_path: str) -> str:
    file_path = BASE_DIR / relative_path
    if not file_path.exists():
        return "Arquivo de ajuda não encontrado."
    return file_path.read_text(encoding="utf-8")


def ask_yes_no(title: str, message: str, parent: tk.Misc | None = None) -> bool:
    return messagebox.askyesno(title, message, parent=parent)


def show_error(title: str, message: str, parent: tk.Misc | None = None) -> None:
    messagebox.showerror(title, message, parent=parent)


def show_info(title: str, message: str, parent: tk.Misc | None = None) -> None:
    messagebox.showinfo(title, message, parent=parent)


def show_warning(title: str, message: str, parent: tk.Misc | None = None) -> None:
    messagebox.showwarning(title, message, parent=parent)


def open_directory(path: Path, parent: tk.Misc | None = None) -> bool:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return True
    except Exception:
        show_warning(
            "Abertura manual",
            f"Não foi possível abrir a pasta automaticamente.\n\nAbra manualmente:\n{path}",
            parent,
        )
        return False


def install_combobox_typeahead(root: tk.Misc) -> None:
    if getattr(root, "_combobox_typeahead_installed", False):
        return

    def clear_buffer(widget: ttk.Combobox) -> None:
        after_id = getattr(widget, "_typeahead_after_id", None)
        if after_id:
            try:
                widget.after_cancel(after_id)
            except Exception:
                pass
            widget._typeahead_after_id = None
        widget._typeahead_buffer = ""

    def normalize_search_text(value: str) -> str:
        value = unicodedata.normalize("NFD", value or "")
        value = "".join(char for char in value if unicodedata.category(char) != "Mn")
        return value.casefold().strip()

    def schedule_clear(widget: ttk.Combobox) -> None:
        after_id = getattr(widget, "_typeahead_after_id", None)
        if after_id:
            try:
                widget.after_cancel(after_id)
            except Exception:
                pass
        widget._typeahead_after_id = widget.after(1200, lambda: clear_buffer(widget))

    def find_match(widget: ttk.Combobox, current_value: str, typed_char: str) -> str | None:
        raw_values = [str(value) for value in widget.cget("values")]
        values = [value for value in raw_values if value.strip()]
        if not values:
            return None

        buffer = getattr(widget, "_typeahead_buffer", "")
        if len(buffer) == 1 and buffer == typed_char:
            search_text = typed_char
            try:
                start_index = values.index(current_value) + 1
            except ValueError:
                start_index = 0
            candidates = values[start_index:] + values[:start_index]
        else:
            search_text = buffer + typed_char
            candidates = values

        normalized_candidates = [(value, normalize_search_text(value)) for value in candidates]
        match = next((value for value, normalized in normalized_candidates if normalized.startswith(search_text)), None)
        if match is None and len(search_text) > 1:
            match = next((value for value, normalized in normalized_candidates if normalized.startswith(typed_char)), None)
            search_text = typed_char if match else search_text

        widget._typeahead_buffer = search_text
        schedule_clear(widget)
        return match

    def handle_key_event(widget: ttk.Combobox, event) -> str | None:
        if str(widget.cget("state")).lower() != "readonly":
            return None

        if event.keysym in {"Tab", "Return", "Escape", "Up", "Down", "Left", "Right", "Home", "End", "Prior", "Next"}:
            if event.keysym == "Escape":
                clear_buffer(widget)
            return None

        if event.keysym == "BackSpace":
            buffer = getattr(widget, "_typeahead_buffer", "")
            widget._typeahead_buffer = buffer[:-1]
            schedule_clear(widget)
            return "break"

        if not event.char or not event.char.isprintable() or event.state & 0x4:
            return None

        typed_char = normalize_search_text(event.char)
        if not typed_char:
            return "break"

        match = find_match(widget, widget.get(), typed_char)
        if match:
            widget.set(match)
            widget.event_generate("<<ComboboxSelected>>")
        return "break"

    def get_combobox_from_popdown_listbox(listbox_widget: tk.Listbox) -> ttk.Combobox | None:
        widget_path = str(listbox_widget)
        suffixes = (".popdown.f.l", ".popdown.l")
        owner_path = ""
        for suffix in suffixes:
            if widget_path.endswith(suffix):
                owner_path = widget_path[: -len(suffix)]
                break
        if not owner_path:
            return None
        try:
            owner_widget = listbox_widget.nametowidget(owner_path)
        except Exception:
            return None
        return owner_widget if isinstance(owner_widget, ttk.Combobox) else None

    def handle_combobox_keypress(event) -> str | None:
        widget = event.widget
        if not isinstance(widget, ttk.Combobox):
            return None
        return handle_key_event(widget, event)

    def handle_popdown_listbox_keypress(event) -> str | None:
        widget = event.widget
        if not isinstance(widget, tk.Listbox):
            return None
        combobox = get_combobox_from_popdown_listbox(widget)
        if combobox is None:
            return None

        result = handle_key_event(combobox, event)
        if result != "break":
            return result

        try:
            values = list(widget.get(0, tk.END))
            current_value = combobox.get()
            index = values.index(current_value)
        except ValueError:
            return result

        widget.selection_clear(0, tk.END)
        widget.selection_set(index)
        widget.activate(index)
        widget.see(index)
        return result

    root.bind_class("TCombobox", "<KeyPress>", handle_combobox_keypress, add="+")
    root.bind_class("Listbox", "<KeyPress>", handle_popdown_listbox_keypress, add="+")
    root._combobox_typeahead_installed = True


class EvidenceInput(ttk.LabelFrame):
    IMAGE_FILE_TYPES = [
        ("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff"),
        ("PNG", "*.png"),
        ("JPEG", "*.jpg *.jpeg"),
        ("Bitmap", "*.bmp"),
        ("Todos os arquivos", "*.*"),
    ]

    def __init__(self, parent: tk.Misc, title: str = "Evidências (opcional)", height: int = 4) -> None:
        super().__init__(parent, text=title, padding=8)
        self.items: list[dict] = []
        self.height = height
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)

        list_frame = ttk.Frame(self)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, height=self.height, exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        action_frame = ttk.Frame(self)
        action_frame.grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Button(action_frame, text="Adicionar imagens", command=self.add_files).pack(side="left", padx=(0, 4))
        ttk.Button(action_frame, text="Colar print", command=self.paste_clipboard).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Remover selecionada", command=self.remove_selected).pack(side="left", padx=4)

        ttk.Label(
            self,
            text="Use este campo somente quando houver evidência útil para consulta futura ou relatório.",
            wraplength=680,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(6, 0))

    def _refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        for index, item in enumerate(self.items, start=1):
            size_kb = max(1, round(len(item.get("dados") or b"") / 1024))
            self.listbox.insert(tk.END, f"{index}. {item['nome_arquivo']} ({size_kb} KB)")

    def add_files(self) -> None:
        file_paths = filedialog.askopenfilenames(
            parent=self.winfo_toplevel(),
            title="Selecionar evidências em imagem",
            filetypes=self.IMAGE_FILE_TYPES,
        )
        if not file_paths:
            return

        added = 0
        for file_path in file_paths:
            path = Path(file_path)
            try:
                data = path.read_bytes()
            except OSError as exc:
                show_error("Falha ao carregar imagem", f"Não foi possível ler o arquivo:\n{path}\n\n{exc}", self.winfo_toplevel())
                continue
            self.items.append({"id": None, "nome_arquivo": path.name, "dados": data})
            added += 1

        self._refresh()
        if added:
            show_info("Evidências adicionadas", f"{added} imagem(ns) adicionada(s) ao registro.", self.winfo_toplevel())

    def paste_clipboard(self) -> None:
        if ImageGrab is None or Image is None:
            show_error(
                "Dependência ausente",
                "Para colar prints é necessário instalar a biblioteca Pillow.\n\nUse no terminal:\npip install Pillow",
                self.winfo_toplevel(),
            )
            return

        try:
            clipboard_data = ImageGrab.grabclipboard()
        except Exception as exc:
            show_error("Falha ao acessar a área de transferência", str(exc), self.winfo_toplevel())
            return

        if isinstance(clipboard_data, Image.Image):
            image = clipboard_data.convert("RGB") if clipboard_data.mode in ("RGBA", "P") else clipboard_data
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.items.append(
                {
                    "id": None,
                    "nome_arquivo": f"print_{timestamp}.png",
                    "dados": buffer.getvalue(),
                }
            )
            self._refresh()
            show_info("Print colado", "A imagem da área de transferência foi adicionada ao registro.", self.winfo_toplevel())
            return

        if isinstance(clipboard_data, list):
            valid_paths = [Path(item) for item in clipboard_data if Path(item).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"}]
            if valid_paths:
                added = 0
                for path in valid_paths:
                    try:
                        self.items.append({"id": None, "nome_arquivo": path.name, "dados": path.read_bytes()})
                    except OSError:
                        continue
                    added += 1
                self._refresh()
                if added:
                    show_info("Evidências adicionadas", f"{added} imagem(ns) adicionada(s) da área de transferência.", self.winfo_toplevel())
                    return

        show_warning(
            "Nenhuma imagem disponível",
            "A área de transferência não contém uma imagem pronta para ser anexada.",
            self.winfo_toplevel(),
        )

    def remove_selected(self) -> None:
        selection = list(self.listbox.curselection())
        if not selection:
            show_warning("Seleção obrigatória", "Selecione ao menos uma evidência para remover.", self.winfo_toplevel())
            return
        for index in reversed(selection):
            del self.items[index]
        self._refresh()

    def get_items(self) -> list[dict]:
        copied_items = []
        for item in self.items:
            copied_items.append(
                {
                    "id": item.get("id"),
                    "nome_arquivo": item["nome_arquivo"],
                    "dados": item.get("dados") or b"",
                }
            )
        return copied_items

    def set_items(self, items: list[dict] | None) -> None:
        self.items = []
        for item in items or []:
            self.items.append(
                {
                    "id": item.get("id"),
                    "nome_arquivo": item.get("nome_arquivo") or "evidencia.png",
                    "dados": item.get("dados") or b"",
                }
            )
        self._refresh()


class DateInput(ttk.Frame):
    def __init__(self, parent: tk.Misc, width: int = 14) -> None:
        super().__init__(parent)
        self._updating = False
        self._placeholder_visible = False
        self._placeholder = "DD/MM/AAAA"
        self._value = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self._value, width=width)
        self.entry.pack(side="left", fill="x", expand=True)
        self.button = ttk.Button(self, text="📅", width=3, command=self.open_calendar)
        self.button.pack(side="left", padx=(4, 0))
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        self._placeholder_visible = True
        self.entry.configure(foreground="#7a7a7a")
        self._value.set(self._placeholder)

    def _clear_placeholder(self) -> None:
        if not self._placeholder_visible:
            return
        self._placeholder_visible = False
        self.entry.configure(foreground="")
        self._value.set("")

    def _on_focus_in(self, _event=None) -> None:
        if self._placeholder_visible:
            self._clear_placeholder()

    def _apply_formatting(self) -> None:
        if self._updating:
            return
        if self._placeholder_visible:
            return
        digits = "".join(char for char in self._value.get() if char.isdigit())[:8]
        formatted = self._format_digits(digits)
        self._updating = True
        self._value.set(formatted)
        self._updating = False
        self.entry.icursor(tk.END)

    def _on_key_release(self, _event=None) -> None:
        if self._placeholder_visible:
            self._clear_placeholder()
        self._apply_formatting()

    def _on_focus_out(self, _event=None) -> None:
        if not "".join(char for char in self._value.get() if char.isdigit()):
            self._restore_placeholder_if_empty()
            return
        self._apply_formatting()

    def _restore_placeholder_if_empty(self) -> None:
        if "".join(char for char in self._value.get() if char.isdigit()):
            return
        self._show_placeholder()

    def _format_digits(self, digits: str) -> str:
        if len(digits) <= 2:
            return digits
        if len(digits) <= 4:
            return f"{digits[:2]}/{digits[2:]}"
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"

    def _initial_date(self) -> dt.date:
        current_value = self.get().strip()
        if not current_value:
            return dt.date.today()
        try:
            normalized = normalize_date(current_value)
            return dt.datetime.strptime(normalized, "%Y-%m-%d").date()
        except ValueError:
            return dt.date.today()

    def open_calendar(self) -> None:
        CalendarPopup(self, self._initial_date(), self.set_date)

    def set_date(self, value: dt.date) -> None:
        self._placeholder_visible = False
        self.entry.configure(foreground="")
        self._value.set(value.strftime("%d/%m/%Y"))

    def get(self) -> str:
        if self._placeholder_visible:
            return ""
        return self._value.get()

    def delete(self, first: int | str, last: int | str | None = None) -> None:
        self._clear_placeholder()
        self.entry.delete(first, last)
        self._restore_placeholder_if_empty()

    def insert(self, index: int | str, string: str) -> None:
        self._clear_placeholder()
        self.entry.insert(index, string)
        self._apply_formatting()

    def set(self, value: str) -> None:
        if not (value or "").strip():
            self._show_placeholder()
            return
        self._placeholder_visible = False
        self.entry.configure(foreground="")
        self._value.set(value)
        self._apply_formatting()

    def focus_set(self) -> None:  # type: ignore[override]
        self.entry.focus_set()

    def bind(self, sequence=None, func=None, add=None):  # type: ignore[override]
        return self.entry.bind(sequence, func, add)


class TimeInput(ttk.Frame):
    def __init__(self, parent: tk.Misc, width: int = 8) -> None:
        super().__init__(parent)
        self._updating = False
        self._placeholder_visible = False
        self._placeholder = "HH:MM"
        self._value = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self._value, width=width)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        self._placeholder_visible = True
        self.entry.configure(foreground="#7a7a7a")
        self._value.set(self._placeholder)

    def _clear_placeholder(self) -> None:
        if not self._placeholder_visible:
            return
        self._placeholder_visible = False
        self.entry.configure(foreground="")
        self._value.set("")

    def _restore_placeholder_if_empty(self) -> None:
        if "".join(char for char in self._value.get() if char.isdigit()):
            return
        self._show_placeholder()

    def _on_focus_in(self, _event=None) -> None:
        if self._placeholder_visible:
            self._clear_placeholder()

    def _apply_formatting(self) -> None:
        if self._updating:
            return
        if self._placeholder_visible:
            return
        digits = "".join(char for char in self._value.get() if char.isdigit())[:4]
        formatted = self._format_digits(digits)
        self._updating = True
        self._value.set(formatted)
        self._updating = False
        self.entry.icursor(tk.END)

    def _on_key_release(self, _event=None) -> None:
        if self._placeholder_visible:
            self._clear_placeholder()
        self._apply_formatting()

    def _on_focus_out(self, _event=None) -> None:
        if not "".join(char for char in self._value.get() if char.isdigit()):
            self._restore_placeholder_if_empty()
            return
        self._apply_formatting()

    def _format_digits(self, digits: str) -> str:
        if len(digits) <= 2:
            return digits
        return f"{digits[:2]}:{digits[2:]}"

    def get(self) -> str:
        if self._placeholder_visible:
            return ""
        return self._value.get()

    def delete(self, first: int | str, last: int | str | None = None) -> None:
        self._clear_placeholder()
        self.entry.delete(first, last)
        self._restore_placeholder_if_empty()

    def insert(self, index: int | str, string: str) -> None:
        self._clear_placeholder()
        self.entry.insert(index, string)
        self._apply_formatting()

    def set(self, value: str) -> None:
        if not (value or "").strip():
            self._show_placeholder()
            return
        self._placeholder_visible = False
        self.entry.configure(foreground="")
        self._value.set(value)
        self._apply_formatting()

    def focus_set(self) -> None:  # type: ignore[override]
        self.entry.focus_set()

    def bind(self, sequence=None, func=None, add=None):  # type: ignore[override]
        return self.entry.bind(sequence, func, add)


class CalendarPopup(tk.Toplevel):
    MONTH_NAMES = [
        "Janeiro",
        "Fevereiro",
        "Marco",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    WEEKDAY_NAMES = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]

    def __init__(self, parent: tk.Misc, initial_date: dt.date, on_select) -> None:
        super().__init__(parent)
        self.on_select = on_select
        self.year = initial_date.year
        self.month = initial_date.month
        self.today = dt.date.today()

        self.title("Selecionar data")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(False, False)

        self._build()
        self._position_near(parent)
        self._render_days()

    def _build(self) -> None:
        container = ttk.Frame(self, padding=8)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x")
        ttk.Button(header, text="<", width=3, command=self._previous_month).pack(side="left")
        self.title_label = ttk.Label(header, anchor="center", font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(header, text=">", width=3, command=self._next_month).pack(side="right")

        weekdays = ttk.Frame(container)
        weekdays.pack(fill="x", pady=(8, 4))
        for column, name in enumerate(self.WEEKDAY_NAMES):
            ttk.Label(weekdays, text=name, width=4, anchor="center").grid(row=0, column=column, padx=1, pady=1)

        self.days_frame = ttk.Frame(container)
        self.days_frame.pack(fill="both", expand=True)

    def _position_near(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        pos_x = parent.winfo_rootx()
        pos_y = parent.winfo_rooty() + parent.winfo_height() + 4
        self.geometry(f"+{pos_x}+{pos_y}")

    def _previous_month(self) -> None:
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self._render_days()

    def _next_month(self) -> None:
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self._render_days()

    def _render_days(self) -> None:
        for child in self.days_frame.winfo_children():
            child.destroy()

        self.title_label.config(text=f"{self.MONTH_NAMES[self.month - 1]} / {self.year}")
        month_matrix = calendar.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)
        for row_index, week in enumerate(month_matrix):
            for col_index, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text=" ", width=4).grid(row=row_index, column=col_index, padx=1, pady=1)
                    continue
                button_kwargs = {
                    "text": f"{day:02d}",
                    "width": 4,
                    "command": lambda d=day: self._select_day(d),
                    "relief": tk.RAISED,
                    "bd": 1,
                }
                if self.year == self.today.year and self.month == self.today.month and day == self.today.day:
                    button_kwargs.update(
                        {
                            "bg": "#f6d365",
                            "activebackground": "#f2c14e",
                            "highlightbackground": "#d49b00",
                            "font": ("Segoe UI", 9, "bold"),
                        }
                    )
                tk.Button(self.days_frame, **button_kwargs).grid(row=row_index, column=col_index, padx=1, pady=1)

    def _select_day(self, day: int) -> None:
        self.on_select(dt.date(self.year, self.month, day))
        self.destroy()
