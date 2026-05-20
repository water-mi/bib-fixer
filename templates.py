"""BibTeX 条目类型模板定义。

每个模板是一个字段名列表，对齐模板时会保留这些字段、补全缺失字段、删除多余字段。
"""

TEMPLATES = {
    "article": ["title", "author", "journal", "volume", "number", "pages", "year"],
    "book": ["title", "author", "year", "publisher"],
    "inproceedings": ["title", "author", "booktitle", "pages", "address", "year"],
}

# 所有支持的条目类型列表
ENTRY_TYPES = list(TEMPLATES.keys())


def get_template_fields(entry_type: str) -> list:
    """返回指定类型的模板字段列表。"""
    return TEMPLATES.get(entry_type, [])


def align_to_template(entry_type: str, fields: dict) -> dict:
    """将字段字典对齐到指定类型的模板。

    1. 删除不在模板中的字段
    2. 为模板中存在但当前缺失的字段创建空值
    """
    template_fields = get_template_fields(entry_type)
    result = {}
    for field in template_fields:
        result[field] = fields.get(field, "")
    return result
