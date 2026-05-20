"""BibTeX Fixer — 程序入口。"""

import tkinter as tk
from gui_main import MainWindow


def main():
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
