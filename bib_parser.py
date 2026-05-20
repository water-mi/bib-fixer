"""BibTeX 文件读写模块，封装 bibtexparser。"""

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode


def load_bibtex(filepath: str) -> list[dict]:
    """从文件加载 BibTeX，返回条目列表。

    每个条目是一个 dict，包含：
    - ID: 引用键
    - ENTRYTYPE: 条目类型 (article, book, ...)
    - 其他字段: title, author, year, ...
    """
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with open(filepath, "r", encoding="utf-8") as f:
        db = bibtexparser.load(f, parser=parser)
    return db.entries


def save_bibtex(filepath: str, entries: list[dict]):
    """将条目列表保存为 BibTeX 文件。"""
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = entries
    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None  # 保持原有顺序
    with open(filepath, "w", encoding="utf-8") as f:
        bibtexparser.dump(db, f, writer=writer)
