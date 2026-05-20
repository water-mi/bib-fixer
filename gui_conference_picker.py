"""会议名快捷填充：弹窗选择预设会议，自动填入 booktitle 字段。"""

import json
import os
import tkinter as tk
from tkinter import ttk
from i18n import t


# booktitle_presets.json 的路径
def _presets_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "booktitle_presets.json")


# 默认预设内容
_DEFAULT_PRESETS = {
    "NeurIPS": "Advances in Neural Information Processing Systems",
}


def load_presets() -> dict:
    """从 JSON 文件加载会议预设，文件不存在时自动创建默认文件。"""
    path = _presets_path()
    if not os.path.exists(path):
        _save_presets(_DEFAULT_PRESETS)
        return dict(_DEFAULT_PRESETS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_presets(data: dict):
    """保存预设到 JSON 文件。"""
    path = _presets_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ConferencePickerDialog(tk.Toplevel):
    """会议选择弹窗。"""

    def __init__(self, parent, on_select_callback, fonts=None):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self._fonts = fonts or {}

        self.title(t("conference.title"))
        self.geometry("420x420")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_list()

        # 居中于父窗口
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        nf = self._fonts.get("normal")
        mono = self._fonts.get("mono")

        # 搜索框
        search_frame = ttk.Frame(self, padding=5)
        search_frame.pack(fill=tk.X)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        search_entry = ttk.Entry(search_frame, textvariable=self._search_var, font=nf)
        search_entry.pack(fill=tk.X)
        search_entry.focus_set()

        # 列表
        list_frame = ttk.Frame(self, padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, font=mono, exportselection=False
        )
        scrollbar.config(command=self._listbox.yview)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox.bind("<Double-Button-1>", lambda e: self._on_confirm())
        self._listbox.bind("<Return>", lambda e: self._on_confirm())

        # 底部按钮
        btn_frame = ttk.Frame(self, padding=5)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text=t("conference.refresh"), command=self._load_list).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text=t("entry.align_template"), command=self._on_confirm).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _load_list(self):
        """加载预设列表。"""
        self._all_items = []  # [(short_name, full_booktitle), ...]
        try:
            presets = load_presets()
            if not presets:
                self._all_items = [(t("conference.no_presets"), "")]
            else:
                for short_name, full_name in presets.items():
                    self._all_items.append((short_name, full_name))
        except Exception:
            self._all_items = [(t("conference.load_error"), "")]
        self._filter_list()

    def _filter_list(self):
        """根据搜索框过滤列表。"""
        query = self._search_var.get().lower()
        self._listbox.delete(0, tk.END)
        for short, full in self._all_items:
            if query in short.lower() or query in full.lower():
                display = f"{short}  →  {full}"
                self._listbox.insert(tk.END, display)

    def _on_confirm(self):
        """确认选择，回调并关闭。"""
        sel = self._listbox.curselection()
        if sel:
            idx = sel[0]
            # 从当前显示列表中反查
            visible_items = []
            for short, full in self._all_items:
                if self._search_var.get().lower() in short.lower() or \
                   self._search_var.get().lower() in full.lower():
                    visible_items.append((short, full))
            if idx < len(visible_items):
                _, full_name = visible_items[idx]
                if full_name and self.on_select_callback:
                    self.on_select_callback(full_name)
        self.destroy()
