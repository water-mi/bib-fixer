"""会议名快捷填充弹窗。

从 conferences.json 读取预设，支持 {ord}（序数词）和 {num}（数字）占位符。
选中会议后，如果模板含占位符则弹出输入框让用户填写年份/届数。
"""

import json
import os
import tkinter as tk
from tkinter import ttk
from i18n import t


def _conferences_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "conferences.json")


def ordinal(n: int) -> str:
    """将整数转换为序数词字符串，如 1→1st, 2→2nd, 21→21st。"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def load_conferences() -> dict:
    """读取 conferences.json，返回 {short_name: template_string}。"""
    path = _conferences_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


class ConferencePickerDialog(tk.Toplevel):
    """会议选择弹窗，支持 {ord}/{num} 占位符输入。"""

    def __init__(self, parent, on_select_callback, fonts=None):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self._fonts = fonts or {}
        self._conferences = load_conferences()
        self._selected_template = ""

        self.title(t("conference.title"))
        self.geometry("480x480")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_list()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 480) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        nf = self._fonts.get("normal")
        sf = self._fonts.get("small")
        mono = self._fonts.get("mono")

        # 搜索框
        search_frame = ttk.Frame(self, padding=5)
        search_frame.pack(fill=tk.X)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        ttk.Entry(search_frame, textvariable=self._search_var, font=nf).pack(fill=tk.X)

        # 列表
        list_frame = ttk.Frame(self, padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        self._listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, font=mono, exportselection=False, height=8
        )
        scrollbar.config(command=self._listbox.yview)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Double-Button-1>", lambda e: self._on_confirm())

        # 占位符输入区
        param_frame = ttk.LabelFrame(self, text="Parameters", padding=8)
        param_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        # {ord} 输入
        ord_frame = ttk.Frame(param_frame)
        ord_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ord_frame, text="{ord} (届数/序数):", font=nf).pack(side=tk.LEFT)
        self._ord_var = tk.StringVar()
        self._ord_entry = ttk.Entry(ord_frame, textvariable=self._ord_var, width=8, font=nf)
        self._ord_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(ord_frame, text="→ 21st, 22nd...", font=sf, foreground="gray").pack(side=tk.LEFT)

        # {num} 输入
        num_frame = ttk.Frame(param_frame)
        num_frame.pack(fill=tk.X, pady=2)
        ttk.Label(num_frame, text="{num} (数字):", font=nf).pack(side=tk.LEFT)
        self._num_var = tk.StringVar()
        self._num_entry = ttk.Entry(num_frame, textvariable=self._num_var, width=8, font=nf)
        self._num_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(num_frame, text="→ 38", font=sf, foreground="gray").pack(side=tk.LEFT)

        # 预览
        preview_frame = ttk.Frame(self, padding=5)
        preview_frame.pack(fill=tk.X)
        ttk.Label(preview_frame, text="Preview:", font=sf).pack(anchor=tk.W)
        self._preview_var = tk.StringVar(value="(select a conference)")
        self._preview_label = ttk.Label(
            preview_frame, textvariable=self._preview_var,
            font=mono, wraplength=450, justify=tk.LEFT
        )
        self._preview_label.pack(fill=tk.X, pady=3)

        # 占位符输入变化时更新预览
        self._ord_var.trace_add("write", lambda *_: self._update_preview())
        self._num_var.trace_add("write", lambda *_: self._update_preview())

        # 底部按钮
        btn_frame = ttk.Frame(self, padding=5)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text=t("conference.refresh"), command=self._load_list).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="OK", command=self._on_confirm).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _load_list(self):
        """加载会议列表。"""
        self._conferences = load_conferences()
        self._all_keys = list(self._conferences.keys())
        self._filter_list()

    def _filter_list(self):
        query = self._search_var.get().lower()
        self._listbox.delete(0, tk.END)
        for key in self._all_keys:
            tmpl = self._conferences.get(key, "")
            if query in key.lower() or query in tmpl.lower():
                self._listbox.insert(tk.END, f"{key}  →  {tmpl}")

    def _on_select(self, event=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        visible = self._get_visible_keys()
        if idx < len(visible):
            key = visible[idx]
            self._selected_template = self._conferences.get(key, "")
            # 检测占位符
            has_ord = "{ord}" in self._selected_template
            has_num = "{num}" in self._selected_template
            self._ord_entry.config(state=tk.NORMAL if has_ord else tk.DISABLED)
            self._num_entry.config(state=tk.NORMAL if has_num else tk.DISABLED)
            if not has_ord:
                self._ord_var.set("")
            if not has_num:
                self._num_var.set("")
        self._update_preview()

    def _get_visible_keys(self) -> list:
        """返回当前过滤后可见的 key 列表。"""
        query = self._search_var.get().lower()
        return [k for k in self._all_keys
                if query in k.lower() or query in self._conferences.get(k, "").lower()]

    def _update_preview(self):
        if not self._selected_template:
            self._preview_var.set("(select a conference)")
            return
        result = self._selected_template
        # 替换 {ord}
        if "{ord}" in result:
            try:
                n = int(self._ord_var.get())
                result = result.replace("{ord}", ordinal(n))
            except (ValueError, TypeError):
                result = result.replace("{ord}", "{ord?}")
        # 替换 {num}
        if "{num}" in result:
            val = self._num_var.get().strip()
            result = result.replace("{num}", val if val else "{num?}")
        self._preview_var.set(result)

    def _on_confirm(self):
        """确认选择，渲染模板并回调。"""
        if not self._selected_template:
            return
        # 检查是否还有未填充的占位符
        unresolved = self._selected_template
        try:
            if "{ord}" in unresolved:
                unresolved = unresolved.replace("{ord}", ordinal(int(self._ord_var.get())))
        except (ValueError, TypeError):
            pass
        if "{num}" in unresolved:
            val = self._num_var.get().strip()
            unresolved = unresolved.replace("{num}", val if val else "")
        if self.on_select_callback:
            self.on_select_callback(unresolved)
        self.destroy()
