"""Вспомогательная загрузка модулей из каталога src для тестов."""

import importlib
import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")


def load(name):
    """Импортирует модуль из каталога src по имени."""
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    return importlib.import_module(name)
