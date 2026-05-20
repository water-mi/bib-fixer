"""主窗口：菜单栏、左右面板组合、事件协调。"""

import os
import glob
import tempfile
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from i18n import t, load_language, current_lang
from bib_parser import load_bibtex, save_bibtex
from gui_entry_list import EntryListPanel
from gui_editor import EntryEditor
from gui_fetcher import FetcherPanel


class MainWindow:
    """BibTeX Fixer 主窗口。"""

    # 基准窗口尺寸（用于字号缩放计算）
    BASE_WIDTH = 1000
    BASE_HEIGHT = 650

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BibTeX Fixer")
        self.root.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}")
        self.root.minsize(600, 400)

        self._filepath = None
        self._modified = False
        self._current_index = -1
        self._current_scale = 1.0
        self._temp_files = []  # 记录运行期间创建的临时文件
        self._original_entry = None  # 加载条目时的原始副本，用于比较是否修改

        self._init_fonts()
        self._init_styles()
        self._build_menu()
        self._build_layout()
        self._update_title()

        # 绑定窗口缩放事件
        self.root.bind("<Configure>", self._on_resize)

    def _init_fonts(self):
        """创建可缩放的字体对象。"""
        self._fonts = {
            "header": tkfont.Font(family="", size=12, weight="bold"),
            "normal": tkfont.Font(family="", size=10),
            "mono":   tkfont.Font(family="Courier", size=10),
            "small":  tkfont.Font(family="", size=9),
        }
        # 存储基准字号
        self._font_base_sizes = {k: f.cget("size") for k, f in self._fonts.items()}

    def _init_styles(self):
        """初始化 ttk 样式。"""
        style = ttk.Style()
        style.configure("Status.TLabel", font=self._fonts["small"])
        style.configure("Editor.TLabel", font=self._fonts["normal"])
        style.configure("Editor.TButton", font=self._fonts["normal"])

    def _on_resize(self, event):
        """窗口大小变化时重新计算字号。"""
        # 只响应根窗口的 Configure 事件
        if event.widget != self.root:
            return
        new_w, new_h = event.width, event.height
        # 如果窗口被最小化，跳过
        if new_w < 50 or new_h < 50:
            return
        scale = min(new_w / self.BASE_WIDTH, new_h / self.BASE_HEIGHT)
        scale = max(0.7, min(scale, 2.0))  # 限制范围
        if abs(scale - self._current_scale) < 0.02:
            return  # 变化太小，跳过
        self._current_scale = scale
        self._apply_font_scale(scale)

    def _apply_font_scale(self, scale: float):
        """按比例缩放所有字体。"""
        # 更新字体对象
        for name, font in self._fonts.items():
            base = self._font_base_sizes[name]
            font.configure(size=int(base * scale))

        # 更新 ttk 样式
        style = ttk.Style()
        style.configure("Status.TLabel", font=self._fonts["small"])
        style.configure("Editor.TLabel", font=self._fonts["normal"])
        style.configure("Editor.TButton", font=self._fonts["normal"])

        # 通知面板刷新
        self.entry_list.apply_font_scale(scale)
        self.editor.apply_font_scale(scale)
        self.fetcher.apply_font_scale(scale)

    # ---------- 菜单 ----------

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=t("menu.open"), command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label=t("menu.save"), command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label=t("menu.save_as"), command=self._save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label=t("menu.exit"), command=self._on_exit, accelerator="Ctrl+Q")
        menubar.add_cascade(label=t("menu.file"), menu=file_menu)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label=t("menu.add_entry"), command=self._add_entry, accelerator="Ctrl+N")
        edit_menu.add_command(label=t("menu.delete_entry"), command=self._delete_entry, accelerator="Ctrl+D")
        menubar.add_cascade(label=t("menu.edit"), menu=edit_menu)

        # 语言菜单
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="中文", command=lambda: self._switch_lang("zh"))
        lang_menu.add_command(label="English", command=lambda: self._switch_lang("en"))
        menubar.add_cascade(label=t("menu.language"), menu=lang_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=t("menu.about"), command=self._show_about)
        menubar.add_cascade(label=t("menu.help"), menu=help_menu)

        self.root.config(menu=menubar)

        # 快捷键
        self.root.bind_all("<Control-o>", lambda e: self._open_file())
        self.root.bind_all("<Control-s>", lambda e: self._save_file())
        self.root.bind_all("<Control-Shift-S>", lambda e: self._save_as_file())
        self.root.bind_all("<Control-n>", lambda e: self._add_entry())
        self.root.bind_all("<Control-d>", lambda e: self._delete_entry())

    def _rebuild_menu(self):
        """语言切换后重建菜单。"""
        # 直接重建菜单栏
        self._build_menu()

    # ---------- 布局 ----------

    def _build_layout(self):
        # 主分栏（水平）
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：条目列表
        self.entry_list = EntryListPanel(
            main_paned, fonts=self._fonts, on_select_callback=self._on_entry_select
        )
        main_paned.add(self.entry_list, weight=1)

        # 右侧：上下分割（编辑器 + 获取面板）
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        main_paned.add(right_paned, weight=3)

        self.editor = EntryEditor(
            right_paned, fonts=self._fonts, on_change_callback=self._on_editor_change
        )
        right_paned.add(self.editor, weight=3)

        self.fetcher = FetcherPanel(
            right_paned, fonts=self._fonts,
            on_add_field=self.editor.add_field_from_fetcher,
        )
        right_paned.add(self.fetcher, weight=1)

        # 状态栏
        self.status_var = tk.StringVar(value=t("status.no_file"))
        self._status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN,
            anchor=tk.W, padding=(5, 2), style="Status.TLabel"
        )
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ---------- 文件操作 ----------

    def _open_file(self):
        if self._modified:
            if not self._confirm_save():
                return

        filepath = filedialog.askopenfilename(
            title=t("dialog.open_title"),
            filetypes=[
                (t("dialog.bib_filter"), "*.bib"),
                (t("dialog.all_files"), "*.*"),
            ],
        )
        if not filepath:
            return

        try:
            entries = load_bibtex(filepath)
        except Exception as e:
            messagebox.showerror(t("dialog.error_open"), f"{t('dialog.error_parse')}:\n{e}")
            return

        self._filepath = filepath
        self._modified = False
        self._current_index = -1

        self.entry_list.load_entries(entries)
        self.editor.load_entry(None)

        self.status_var.set(t("dialog.file_loaded", count=len(entries)))
        self._update_title()

    def _save_file(self):
        if not self._save_current_entry():
            return

        if not self._filepath:
            return self._save_as_file()

        try:
            save_bibtex(self._filepath, self.entry_list.get_entries())
        except Exception as e:
            messagebox.showerror(t("dialog.error_save"), str(e))
            return

        self._modified = False
        self.status_var.set(t("dialog.file_saved"))
        self._update_title()

    def _save_as_file(self):
        if not self._save_current_entry():
            return

        filepath = filedialog.asksaveasfilename(
            title=t("dialog.save_as_title"),
            filetypes=[
                (t("dialog.bib_filter"), "*.bib"),
                (t("dialog.all_files"), "*.*"),
            ],
            defaultextension=".bib",
        )
        if not filepath:
            return False

        try:
            save_bibtex(filepath, self.entry_list.get_entries())
        except Exception as e:
            messagebox.showerror(t("dialog.error_save"), str(e))
            return False

        self._filepath = filepath
        self._modified = False
        self.status_var.set(t("dialog.file_saved"))
        self._update_title()
        return True

    # ---------- 条目操作 ----------

    def _on_entry_select(self, index: int):
        """列表选中某条目时触发。如果当前条目有未保存修改，先询问。"""
        # 检查当前条目是否被修改
        if self._current_index >= 0 and self._has_entry_changed():
            answer = messagebox.askyesnocancel(
                t("dialog.confirm_save"),
                t("dialog.entry_modified")
            )
            if answer is None:  # 取消 — 留在当前条目
                self.entry_list.select_index(self._current_index)
                return
            if answer:  # 是 — 保存到内存再切换
                self._save_current_entry()
            # 否 — 直接丢弃修改，不保存
        else:
            # 没有修改，正常保存（写入可能存在的微小变动）
            self._save_current_entry()

        if index < 0:
            self.editor.load_entry(None)
            self._current_index = -1
            self._original_entry = None
            return

        entries = self.entry_list.get_entries()
        if 0 <= index < len(entries):
            self._current_index = index
            self.editor.load_entry(entries[index])
            self._original_entry = dict(entries[index])
            self.entry_list.select_index(index)

    def _has_entry_changed(self) -> bool:
        """比较当前编辑器状态与加载时的原始条目是否有变化。"""
        if self._original_entry is None:
            return False
        current = self.editor.get_entry_data()
        if current is None:
            return False
        # 比较字段
        orig_fields = {k: str(v) for k, v in self._original_entry.items()}
        curr_fields = {k: str(v) for k, v in current.items()}
        return orig_fields != curr_fields

    def _on_editor_change(self):
        """编辑器内容变化时触发。"""
        self._modified = True
        self._update_title()

    def _save_current_entry(self) -> bool:
        """将编辑器中的当前数据保存回条目列表。"""
        if self._current_index < 0:
            return True
        entry_data = self.editor.get_entry_data()
        if entry_data is None:
            return True
        self.entry_list.update_entry(self._current_index, entry_data)
        return True

    def _add_entry(self):
        self._save_current_entry()
        self.entry_list._add_entry()

    def _delete_entry(self):
        if self._current_index < 0:
            return
        ok = messagebox.askyesno(t("menu.delete_entry"), t("dialog.confirm_delete"))
        if not ok:
            return
        self.entry_list._delete_entry()
        self._modified = True
        self._update_title()

    # ---------- 语言切换 ----------

    def _switch_lang(self, lang: str):
        if lang == current_lang():
            return
        load_language(lang)
        self._rebuild_menu()
        self.entry_list.refresh_ui_text()
        self.editor.refresh_ui_text()
        self.fetcher.refresh_ui_text()
        self._update_title()
        self.status_var.set(t("status.ready"))

    # ---------- 辅助 ----------

    def _update_title(self):
        title = "BibTeX Fixer"
        if self._filepath:
            title += f" - {self._filepath}"
        if self._modified:
            title += " *"
        self.root.title(title)

    def _confirm_save(self) -> bool:
        """询问用户是否保存。返回 False 表示取消操作。"""
        answer = messagebox.askyesnocancel(
            t("dialog.confirm_save"), t("dialog.unsaved_changes")
        )
        if answer is None:  # 取消
            return False
        if answer:  # 是
            return self._save_file() or True
        return True  # 否，不保存继续

    def _show_about(self):
        messagebox.showinfo(t("about.title"), t("about.text"))

    def _on_exit(self):
        if self._modified:
            if not self._confirm_save():
                return
        self._cleanup_temp_files()
        self.root.destroy()

    def _cleanup_temp_files(self):
        """删除运行期间创建的所有临时文件。"""
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
        self._temp_files.clear()

        # 额外清理：删除程序工作目录下可能遗留的临时文件
        work_dir = os.path.dirname(os.path.abspath(__file__))
        for pattern in ["*.tmp", "*.temp", "*~"]:
            for f in glob.glob(os.path.join(work_dir, pattern)):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def register_temp_file(self, filepath: str):
        """注册一个临时文件，退出时自动删除。"""
        self._temp_files.append(filepath)
