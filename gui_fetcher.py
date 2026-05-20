"""DOI / arXiv 获取面板：输入标识符，通过 doi2bib3 获取 BibTeX 并展示。"""

import tkinter as tk
from tkinter import ttk
from i18n import t


class FetcherPanel(ttk.LabelFrame):
    """DOI/arXiv 获取面板。"""

    def __init__(self, parent, fonts=None):
        super().__init__(parent, text=t("fetcher.title"), padding=8)
        self._fonts = fonts or {}
        self._build_ui()

    def _build_ui(self):
        nf = self._fonts.get("normal")
        sf = self._fonts.get("small")

        # --- 输入行 ---
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, pady=(0, 5))

        self._input_var = tk.StringVar()
        self._input_entry = ttk.Entry(input_frame, textvariable=self._input_var, font=nf)
        self._input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self._fetch_btn = ttk.Button(
            input_frame, text=t("fetcher.fetch"), command=self._do_fetch
        )
        self._fetch_btn.pack(side=tk.RIGHT)

        # 输入提示
        self._hint_label = ttk.Label(
            self, text=t("fetcher.input_hint"), font=sf, foreground="gray"
        )
        self._hint_label.pack(anchor=tk.W, pady=(0, 5))

        # --- 结果展示区 ---
        result_frame = ttk.Frame(self)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self._result_text = tk.Text(
            result_frame, wrap=tk.NONE, font=self._fonts.get("mono"),
            state=tk.DISABLED, height=8,
        )
        scroll_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self._result_text.yview)
        scroll_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self._result_text.xview)
        self._result_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self._result_text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        # 复制提示
        self._copy_hint = ttk.Label(
            self, text=t("fetcher.copy_hint"), font=sf, foreground="gray"
        )
        self._copy_hint.pack(anchor=tk.W, pady=(3, 0))

        # 绑定回车键
        self._input_entry.bind("<Return>", lambda e: self._do_fetch())

    def _do_fetch(self):
        """执行获取操作。"""
        identifier = self._input_var.get().strip()
        if not identifier:
            return

        self._fetch_btn.config(state=tk.DISABLED)
        self._fetch_btn.config(text=t("fetcher.fetching"))
        self._set_result("")
        self.update_idletasks()

        try:
            from doi2bib3 import fetch_bibtex
            bib = fetch_bibtex(identifier)
            self._set_result(bib)
        except Exception as e:
            self._set_result(f"{t('fetcher.error')}: {e}")
        finally:
            self._fetch_btn.config(state=tk.NORMAL)
            self._fetch_btn.config(text=t("fetcher.fetch"))

    def _set_result(self, text: str):
        """设置结果文本框内容（只读）。"""
        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)
        self._result_text.insert("1.0", text)
        self._result_text.config(state=tk.DISABLED)

    def refresh_ui_text(self):
        """语言切换后刷新文本。"""
        self.config(text=t("fetcher.title"))
        self._hint_label.config(text=t("fetcher.input_hint"))
        self._fetch_btn.config(text=t("fetcher.fetch"))
        self._copy_hint.config(text=t("fetcher.copy_hint"))

    def apply_font_scale(self, scale: float):
        """窗口缩放时更新字体。"""
        nf = self._fonts.get("normal")
        mono = self._fonts.get("mono")
        sf = self._fonts.get("small")
        self._input_entry.config(font=nf)
        self._result_text.config(font=mono)
        self._hint_label.config(font=sf)
        self._copy_hint.config(font=sf)
