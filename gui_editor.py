"""右侧编辑器面板：编辑选中条目的字段。"""

import tkinter as tk
from tkinter import ttk, messagebox
from i18n import t
from templates import ENTRY_TYPES, get_template_fields, align_to_template


class EntryEditor(ttk.Frame):
    """条目编辑器面板。"""

    def __init__(self, parent, fonts=None, on_change_callback=None):
        super().__init__(parent, padding=10)
        self.on_change_callback = on_change_callback
        self._fonts = fonts or {}
        self._current_entry = None
        self._field_rows = []  # [(name_var, value_var, name_entry, val_entry, row_frame), ...]
        self._suppress_change = False

        self._build_ui()

    def _build_ui(self):
        nf = self._fonts.get("normal")

        # --- 类型选择 ---
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, pady=(0, 5))
        self._type_label = ttk.Label(type_frame, text=t("entry.type") + ":", style="Editor.TLabel")
        self._type_label.pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            type_frame, textvariable=self.type_var, values=ENTRY_TYPES, state="readonly", width=18,
            font=nf,
        )
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)

        # --- 引用键 ---
        key_frame = ttk.Frame(self)
        key_frame.pack(fill=tk.X, pady=(0, 10))
        self._key_label = ttk.Label(key_frame, text=t("entry.key") + ":", style="Editor.TLabel")
        self._key_label.pack(side=tk.LEFT)
        self.key_var = tk.StringVar()
        self.key_var.trace_add("write", lambda *_: self._notify_change())
        self._key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=30, font=nf)
        self._key_entry.pack(side=tk.LEFT, padx=5)

        # --- 分隔线 ---
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # --- 字段区域标题 ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        self._fields_label = ttk.Label(
            header_frame, text=t("entry.fields"), font=self._fonts.get("header")
        )
        self._fields_label.pack(side=tk.LEFT)

        # --- 可滚动字段区域 ---
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.field_canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.field_canvas.yview)
        self.field_canvas.configure(yscrollcommand=scrollbar.set)

        self.field_container = ttk.Frame(self.field_canvas)
        self.field_container.bind("<Configure>", lambda e: self.field_canvas.configure(
            scrollregion=self.field_canvas.bbox("all")
        ))
        self.canvas_window = self.field_canvas.create_window((0, 0), window=self.field_container, anchor=tk.NW)

        self.field_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.field_canvas.bind("<Configure>", self._on_canvas_configure)
        self.field_canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.field_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        # --- 底部按钮 ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self._add_field_btn = ttk.Button(
            btn_frame, text=t("entry.add_field"), command=self._add_field, style="Editor.TButton"
        )
        self._add_field_btn.pack(side=tk.LEFT, padx=(0, 5))
        self._align_btn = ttk.Button(
            btn_frame, text=t("entry.align_template"), command=self._align_to_template, style="Editor.TButton"
        )
        self._align_btn.pack(side=tk.LEFT)

    def _on_canvas_configure(self, event):
        """让内部 frame 宽度跟随 canvas。"""
        self.field_canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self):
        if self._current_entry is not None:
            self.field_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.field_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.field_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _clear_fields(self):
        for _, _, _, _, row in self._field_rows:
            row.destroy()
        self._field_rows.clear()

    def _add_field(self, field_name="", value=""):
        """添加一个字段行。"""
        nf = self._fonts.get("normal")
        row = ttk.Frame(self.field_container)
        row.pack(fill=tk.X, pady=2)

        name_var = tk.StringVar(value=field_name)
        value_var = tk.StringVar(value=value)
        name_var.trace_add("write", lambda *_: self._notify_change())
        value_var.trace_add("write", lambda *_: self._notify_change())

        name_entry = ttk.Entry(row, textvariable=name_var, width=16, font=nf)
        name_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row, text="=", style="Editor.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        val_entry = ttk.Entry(row, textvariable=value_var, width=40, font=nf)
        val_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        del_btn = ttk.Button(row, text="✕", width=3,
                             command=lambda r=row, idx=len(self._field_rows): self._delete_field(r, idx))
        del_btn.pack(side=tk.RIGHT)

        self._field_rows.append((name_var, value_var, name_entry, val_entry, row))

    def _delete_field(self, row_frame, index):
        if 0 <= index < len(self._field_rows):
            row_frame.destroy()
            self._field_rows.pop(index)
            self._notify_change()

    def _align_to_template(self):
        if self._current_entry is None:
            return
        entry_type = self.type_var.get()
        if not entry_type:
            return
        ok = messagebox.askyesno(t("entry.align_template"), t("dialog.align_confirm"))
        if not ok:
            return

        current_fields = self.get_fields()
        aligned = align_to_template(entry_type, current_fields)
        self._suppress_change = True
        self._clear_fields()
        template_fields = get_template_fields(entry_type)
        for field in template_fields:
            self._add_field(field, aligned.get(field, ""))
        self._suppress_change = False
        self._notify_change()

    def _on_type_changed(self, event=None):
        self._notify_change()

    def _notify_change(self):
        if self._suppress_change:
            return
        if self.on_change_callback:
            self.on_change_callback()

    def load_entry(self, entry: dict | None):
        """加载一个条目到编辑器。"""
        self._suppress_change = True
        self._clear_fields()

        if entry is None:
            self._current_entry = None
            self.type_var.set("")
            self.key_var.set("")
        else:
            self._current_entry = entry
            entry_type = entry.get("ENTRYTYPE", "article")
            self.type_var.set(entry_type)
            self.key_var.set(entry.get("ID", ""))

            # 收集所有字段（排除 ID 和 ENTRYTYPE）
            for field, value in entry.items():
                if field not in ("ID", "ENTRYTYPE"):
                    self._add_field(field, str(value) if value else "")

        self._suppress_change = False

    def get_entry_data(self) -> dict | None:
        """获取当前编辑的条目数据。"""
        if self._current_entry is None and not self.key_var.get():
            return None

        entry = {
            "ENTRYTYPE": self.type_var.get(),
            "ID": self.key_var.get(),
        }
        for item in self._field_rows:
            name_var, value_var = item[0], item[1]
            fname = name_var.get().strip()
            if fname:
                entry[fname] = value_var.get()
        return entry

    def get_fields(self) -> dict:
        """获取当前所有字段（不含 ID/ENTRYTYPE）。"""
        fields = {}
        for item in self._field_rows:
            name_var, value_var = item[0], item[1]
            fname = name_var.get().strip()
            if fname:
                fields[fname] = value_var.get()
        return fields

    def has_entry(self) -> bool:
        return self._current_entry is not None

    def refresh_ui_text(self):
        """语言切换后刷新文本。"""
        self._type_label.config(text=t("entry.type") + ":")
        self._key_label.config(text=t("entry.key") + ":")
        self._fields_label.config(text=t("entry.fields"))
        self._add_field_btn.config(text=t("entry.add_field"))
        self._align_btn.config(text=t("entry.align_template"))

    def apply_font_scale(self, scale: float):
        """窗口缩放时更新字体。"""
        nf = self._fonts.get("normal")
        # 更新静态 Entry 控件
        if hasattr(self, '_key_entry'):
            self._key_entry.config(font=nf)
        # 更新 Combobox
        if hasattr(self, 'type_combo'):
            self.type_combo.config(font=nf)
        # 更新所有动态字段行中的 Entry
        for _, _, name_entry, val_entry, _ in self._field_rows:
            name_entry.config(font=nf)
            val_entry.config(font=nf)
