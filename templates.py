"""BibTeX 条目类型模板定义。

每个模板是一个字段名列表。
对齐模板时会：1) 保留模板中的字段及其值 2) 补全缺失字段为空 3) 删除模板外的多余字段。

内部标识（internal key）用于程序内部区分不同模板变体；
ENTRYTYPE 是 BibTeX 标准中的条目类型名，保存时会写入 @article{...} 等。
"""

# internal_key → 模板字段列表
TEMPLATES = {
    # ---- article 类型 ----
    "article": [
        # 期刊文章完整模板（journal）
        "title", "author", "journal", "volume", "number", "pages", "year"
    ],
    "article_arxiv": [
        # arXiv 预印本精简模板
        "title", "author", "journal", "year"
    ],

    # ---- book 类型 ----
    "book": [
        # 书籍模板
        "title", "author", "year", "publisher"
    ],

    # ---- inproceedings 类型 ----
    "inproceedings": [
        # 会议论文模板
        "title", "author", "booktitle", "pages", "address", "year"
    ],
}

# internal_key → BibTeX ENTRYTYPE（保存到文件时使用）
ENTRYTYPE_MAP = {
    "article":        "article",
    "article_arxiv":  "article",
    "book":           "book",
    "inproceedings":  "inproceedings",
}

# 下拉框选项顺序（internal_key 列表）
ENTRY_TYPES = ["article", "article_arxiv", "book", "inproceedings"]


def get_template_fields(internal_key: str) -> list:
    """返回指定 internal_key 的模板字段列表。"""
    return TEMPLATES.get(internal_key, [])


def get_entrytype(internal_key: str) -> str:
    """返回 internal_key 对应的 BibTeX ENTRYTYPE。"""
    return ENTRYTYPE_MAP.get(internal_key, internal_key)


def resolve_internal_key(entry: dict) -> str:
    """根据已有条目数据反推最匹配的 internal_key。
    
    用于从文件加载条目时，自动判断应该使用哪个模板变体。
    优先匹配字段数量最接近的模板。
    """
    entry_type = entry.get("ENTRYTYPE", "article")
    entry_fields = set(k for k in entry.keys() if k not in ("ID", "ENTRYTYPE"))

    candidates = [k for k in ENTRY_TYPES if ENTRYTYPE_MAP.get(k) == entry_type]
    if not candidates:
        return entry_type  # fallback

    best_key = candidates[0]
    best_diff = float("inf")
    for key in candidates:
        tmpl_fields = set(TEMPLATES.get(key, []))
        # 计算当前条目字段与模板字段的差异度
        extra = len(entry_fields - tmpl_fields)
        missing = len(tmpl_fields - entry_fields)
        diff = extra * 2 + missing  # 多余字段的权重更高
        if diff < best_diff:
            best_diff = diff
            best_key = key

    return best_key


def align_to_template(internal_key: str, fields: dict) -> dict:
    """将字段字典对齐到指定 internal_key 的模板。

    1. 保留模板中定义的字段及其值
    2. 删除模板中不存在的字段
    3. 为模板中存在但当前条目缺失的字段创建空值
    """
    template_fields = get_template_fields(internal_key)
    result = {}
    for field in template_fields:
        result[field] = fields.get(field, "")
    return result
