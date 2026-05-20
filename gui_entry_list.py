"""左侧条目列表面板：显示 BibTeX 条目列表。"""

import tkinter as tk
from tkinter import ttk
from i18n import t


class EntryListPanel(ttk.Frame):
    """条目列表面板。"""

    def __init__(self, parent, fonts=None, on_select_callback=None):
        super().__init__(parent, padding=5)
        self.on_select_callback = on_select_callback
        self._fonts = fonts or {}
        self._entries = []  # 原始条目数据

        self._build_ui()

    def _build_ui(self):
        # 标题
        self._header_label = ttk.Label(
            self, text="Entries", font=self._fonts.get("header")
        )
        self._header_label.pack(anchor=tk.W, pady=(0, 5))

        # 列表框架
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            exportselection=False,
            font=self._fonts.get("mono"),
        )
        scrollbar.config(command=self.listbox.yview)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # 按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        self._add_btn = ttk.Button(btn_frame, text=t("menu.add_entry"), command=self._add_entry)
        self._add_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self._del_btn = ttk.Button(btn_frame, text=t("menu.delete_entry"), command=self._delete_entry)
        self._del_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

    def apply_font_scale(self, scale: float):
        """窗口缩放时更新字体。"""
        mono_font = self._fonts.get("mono")
        if mono_font:
            self.listbox.config(font=mono_font)

    def refresh_ui_text(self):
        """语言切换后刷新按钮文字。"""
        self._add_btn.config(text=t("menu.add_entry"))
        self._del_btn.config(text=t("menu.delete_entry"))

    def _on_select(self, event=None):
        sel = self.listbox.curselection()
        if sel and self.on_select_callback:
            index = sel[0]
            self.on_select_callback(index)

    def load_entries(self, entries: list[dict]):
        """加载条目列表。"""
        self._entries = entries
        self._refresh_list()

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, entry in enumerate(self._entries):
            etype = entry.get("ENTRYTYPE", "?")
            eid = entry.get("ID", "?")
            display = f"[{i+1}] @{etype}{{{eid},...}}"
            self.listbox.insert(tk.END, display)

    def _add_entry(self):
        """添加新条目。"""
        new_entry = {"ENTRYTYPE": "article", "ID": f"new_entry_{len(self._entries)+1}"}
        self._entries.append(new_entry)
        self._refresh_list()
        # 选中新条目
        last_idx = len(self._entries) - 1
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(last_idx)
        self.listbox.see(last_idx)
        if self.on_select_callback:
            self.on_select_callback(last_idx)

    def _delete_entry(self):
        sel = self.listbox.curselection()
        if sel:
            index = sel[0]
            del self._entries[index]
            self._refresh_list()
            # 选中前一个或第一个
            new_sel = min(index, len(self._entries) - 1)
            if new_sel >= 0:
                self.listbox.selection_set(new_sel)
                if self.on_select_callback:
                    self.on_select_callback(new_sel)
            elif self.on_select_callback:
                self.on_select_callback(-1)  # 表示无选中

    def get_entries(self) -> list[dict]:
        return self._entries

    def update_entry(self, index: int, entry: dict):
        """更新指定位置的条目数据并刷新列表。"""
        if 0 <= index < len(self._entries):
            self._entries[index] = entry
            self._refresh_list()
            self.listbox.selection_set(index)

    def select_index(self, index: int):
        if 0 <= index < len(self._entries):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.see(index)
