"""国际化模块：加载 YAML 语言文件，提供翻译函数。"""

import os
import yaml

_current_lang = "zh"
_translations = {}


def load_language(lang: str):
    """加载指定语言的 YAML 文件。"""
    global _current_lang, _translations
    _current_lang = lang
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lang_path = os.path.join(base_dir, "lang", f"{lang}.yml")
    with open(lang_path, "r", encoding="utf-8") as f:
        _translations = yaml.safe_load(f) or {}


def t(key: str, **kwargs) -> str:
    """通过点分隔的键路径获取翻译文本，支持格式化参数。

    例如: t('menu.file') -> '文件'
         t('dialog.file_loaded', count=10) -> '已加载 10 个条目'
    """
    keys = key.split(".")
    value = _translations
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)
    return value if isinstance(value, str) else key


def current_lang() -> str:
    return _current_lang


# 默认加载中文
load_language("zh")
