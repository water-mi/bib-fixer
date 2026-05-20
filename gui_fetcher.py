"""DOI / arXiv 获取面板：输入标识符，通过 doi2bib3 获取 BibTeX 并展示。

展示区使用 Notebook 切换两个视图：
  - Raw Text：原始 BibTeX 文本（获取失败时展示错误信息）
  - Parsed Fields：解析后的字段列表（获取成功时自动切换到此视图）
"""

import tkinter as tk
from tkinter import ttk
from i18n import t


class FetcherPanel(ttk.LabelFrame):
    """DOI/arXiv 获取面板。"""

    def __init__(self, parent, fonts=None, on_add_field=None):
        super().__init__(parent, text=t("fetcher.title"), padding=8)
        self._fonts = fonts or {}
        self._on_add_field = on_add_field  # callback(field_name, value)
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

        # --- 结果展示区 (Notebook 双标签) ---
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Raw Text
        raw_frame = ttk.Frame(self._notebook, padding=2)
        self._notebook.add(raw_frame, text=t("fetcher.tab_raw"))

        self._raw_text = tk.Text(
            raw_frame, wrap=tk.NONE, font=self._fonts.get("mono"),
            state=tk.DISABLED, height=6,
        )
        scroll_ry = ttk.Scrollbar(raw_frame, orient=tk.VERTICAL, command=self._raw_text.yview)
        scroll_rx = ttk.Scrollbar(raw_frame, orient=tk.HORIZONTAL, command=self._raw_text.xview)
        self._raw_text.configure(yscrollcommand=scroll_ry.set, xscrollcommand=scroll_rx.set)
        self._raw_text.grid(row=0, column=0, sticky="nsew")
        scroll_ry.grid(row=0, column=1, sticky="ns")
        scroll_rx.grid(row=1, column=0, sticky="ew")
        raw_frame.rowconfigure(0, weight=1)
        raw_frame.columnconfigure(0, weight=1)

        # Tab 2: Parsed Fields (使用 Treeview 显示字段表)
        parsed_frame = ttk.Frame(self._notebook, padding=2)
        self._notebook.add(parsed_frame, text=t("fetcher.tab_parsed"))

        # Treeview: 列为 Field | Value | Action
        self._parsed_tree = ttk.Treeview(
            parsed_frame, columns=("field", "value", "action"), show="headings", height=6,
        )
        self._parsed_tree.heading("field", text="Field")
        self._parsed_tree.heading("value", text="Value")
        self._parsed_tree.heading("action", text="➕")
        self._parsed_tree.column("field", width=100, minwidth=80)
        self._parsed_tree.column("value", width=300, minwidth=150)
        self._parsed_tree.column("action", width=40, minwidth=30, anchor=tk.CENTER)

        scroll_py = ttk.Scrollbar(parsed_frame, orient=tk.VERTICAL, command=self._parsed_tree.yview)
        self._parsed_tree.configure(yscrollcommand=scroll_py.set)
        self._parsed_tree.grid(row=0, column=0, sticky="nsew")
        scroll_py.grid(row=0, column=1, sticky="ns")
        parsed_frame.rowconfigure(0, weight=1)
        parsed_frame.columnconfigure(0, weight=1)

        # 点击 action 列触发添加，双击 value 列可编辑
        self._parsed_tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self._parsed_tree.bind("<Double-1>", self._on_tree_double_click)

        # 复制提示
        self._copy_hint = ttk.Label(
            self, text=t("fetcher.copy_hint"), font=sf, foreground="gray"
        )
        self._copy_hint.pack(anchor=tk.W, pady=(3, 0))

        # 绑定回车键
        self._input_entry.bind("<Return>", lambda e: self._do_fetch())

    def _do_fetch(self):
        """执行获取操作。成功则自动解析并切换到 Parsed Fields 标签。"""
        identifier = self._input_var.get().strip()
        if not identifier:
            return

        self._fetch_btn.config(state=tk.DISABLED)
        self._fetch_btn.config(text=t("fetcher.fetching"))
        self._set_raw_text("")
        self._clear_parsed()
        self._notebook.select(0)  # 先切到 raw tab
        self.update_idletasks()

        try:
            from doi2bib3 import fetch_bibtex
            bib = fetch_bibtex(identifier)
            self._set_raw_text(bib)
            self._try_parse_and_show(bib)
        except Exception as e:
            self._set_raw_text(f"{t('fetcher.error')}: {e}")
            # 解析失败时保持在 raw text 视图
        finally:
            self._fetch_btn.config(state=tk.NORMAL)
            self._fetch_btn.config(text=t("fetcher.fetch"))

    def _try_parse_and_show(self, bibtex_str: str):
        """尝试解析 BibTeX 字符串并展示字段。成功则切换到 Parsed Fields 标签。"""
        try:
            import bibtexparser
            from bibtexparser.bparser import BibTexParser
            from bibtexparser.customization import convert_to_unicode

            parser = BibTexParser(common_strings=True)
            parser.customization = convert_to_unicode
            db = bibtexparser.loads(bibtex_str, parser=parser)
            entries = db.entries

            if not entries:
                self._set_raw_text(
                    self._raw_text.get("1.0", tk.END).strip() +
                    f"\n\n{t('fetcher.parse_error')}: no entries found"
                )
                return

            self._clear_parsed()
            for entry in entries:
                etype = entry.get("ENTRYTYPE", "?")
                eid = entry.get("ID", "?")
                # 类型和引用键作为独立行展示
                self._parsed_tree.insert("", tk.END, values=("@type", etype, ""), tags=("meta",))
                self._parsed_tree.insert("", tk.END, values=("@key", eid, ""), tags=("meta",))
                # 分隔行
                sep_id = self._parsed_tree.insert("", tk.END, values=("───", "───", ""), tags=("sep",))
                for field, value in entry.items():
                    if field in ("ID", "ENTRYTYPE"):
                        continue
                    self._parsed_tree.insert("", tk.END, values=(field, str(value) if value else "", "➕"))
                # 条目间分隔
                self._parsed_tree.insert("", tk.END, values=("", "", ""), tags=("sep",))

            # 设置元信息行样式
            self._parsed_tree.tag_configure("meta", foreground="gray")
            self._parsed_tree.tag_configure("sep", foreground="lightgray")

            # 解析成功 → 自动切换到 Parsed Fields
            self._notebook.select(1)
        except Exception as e:
            self._set_raw_text(
                self._raw_text.get("1.0", tk.END).strip() +
                f"\n\n{t('fetcher.parse_error')}: {e}"
            )
            # 停留在 raw text 视图

    def _set_raw_text(self, text: str):
        """设置 Raw Text 标签内容（只读）。"""
        self._raw_text.config(state=tk.NORMAL)
        self._raw_text.delete("1.0", tk.END)
        self._raw_text.insert("1.0", text)
        self._raw_text.config(state=tk.DISABLED)

    def _on_tree_click(self, event):
        """处理单击：点击 action 列时添加字段到编辑器。"""
        region = self._parsed_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self._parsed_tree.identify_column(event.x)
        if column != "#3":  # action 列
            return
        item = self._parsed_tree.identify_row(event.y)
        if not item:
            return
        values = self._parsed_tree.item(item, "values")
        if not values or len(values) < 2:
            return
        field_name = values[0]
        field_value = values[1]
        if not field_name or field_name.startswith("@") or field_name == "───":
            return
        if self._on_add_field:
            self._on_add_field(field_name, field_value)

    def _on_tree_double_click(self, event):
        """处理双击：在 value 列上启动就地编辑。"""
        region = self._parsed_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self._parsed_tree.identify_column(event.x)
        if column != "#2":  # value 列
            return
        item = self._parsed_tree.identify_row(event.y)
        if not item:
            return
        values = self._parsed_tree.item(item, "values")
        if not values or len(values) < 2:
            return
        if values[0].startswith("@") or values[0] == "───":
            return  # 元信息行不可编辑

        # 获取单元格位置
        bbox = self._parsed_tree.bbox(item, column)
        if not bbox:
            return
        x, y, w, h = bbox

        # 创建覆盖编辑框
        edit_var = tk.StringVar(value=values[1])
        edit_entry = ttk.Entry(self._parsed_tree, textvariable=edit_var, font=self._fonts.get("normal"))
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.focus_set()
        edit_entry.select_range(0, tk.END)

        def save_edit():
            new_val = edit_var.get()
            all_vals = list(self._parsed_tree.item(item, "values"))
            if len(all_vals) >= 2:
                all_vals[1] = new_val
                self._parsed_tree.item(item, values=tuple(all_vals))
            edit_entry.destroy()

        edit_entry.bind("<Return>", lambda e: save_edit())
        edit_entry.bind("<FocusOut>", lambda e: save_edit())
        edit_entry.bind("<Escape>", lambda e: edit_entry.destroy())

    def _clear_parsed(self):
        """清空 Parsed Fields 树。"""
        for item in self._parsed_tree.get_children():
            self._parsed_tree.delete(item)

    def refresh_ui_text(self):
        """语言切换后刷新文本。"""
        self.config(text=t("fetcher.title"))
        self._hint_label.config(text=t("fetcher.input_hint"))
        self._fetch_btn.config(text=t("fetcher.fetch"))
        self._copy_hint.config(text=t("fetcher.copy_hint"))
        # 更新 notebook 标签页名称
        self._notebook.tab(0, text=t("fetcher.tab_raw"))
        self._notebook.tab(1, text=t("fetcher.tab_parsed"))
        # 更新 treeview 列标题
        self._parsed_tree.heading("field", text="Field")
        self._parsed_tree.heading("value", text="Value")

    def apply_font_scale(self, scale: float):
        """窗口缩放时更新字体。"""
        nf = self._fonts.get("normal")
        mono = self._fonts.get("mono")
        sf = self._fonts.get("small")
        self._input_entry.config(font=nf)
        self._raw_text.config(font=mono)
        self._hint_label.config(font=sf)
        self._copy_hint.config(font=sf)
