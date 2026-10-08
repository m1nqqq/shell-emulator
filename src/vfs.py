"""Виртуальная файловая система (VFS), целиком хранящаяся в памяти.

Формат источника — CSV-файл с заголовком ``path,type,encoding,content``:

* ``path``     — абсолютный путь элемента (вложенность задаётся путём);
* ``type``     — ``dir`` (каталог) или ``file`` (файл);
* ``encoding`` — для файлов ``text`` (содержимое как есть, по умолчанию)
  или ``base64`` (двоичные данные); для каталогов пусто;
* ``content``  — содержимое файла; для каталогов пусто.

Недостающие родительские каталоги создаются автоматически.
"""

import base64
import binascii
import csv
import posixpath

ROOT = "/"
HOME_MARK = "~"
COLUMNS = ["path", "type", "encoding", "content"]
TYPE_DIR = "dir"
TYPE_FILE = "file"
ENCODING_TEXT = "text"
ENCODING_BASE64 = "base64"
MOTD_PATH = "/motd"
FILE_ENCODING = "utf-8-sig"
CSV_FIELD_LIMIT = 2 ** 31 - 1


class VFSError(Exception):
    """Ошибка загрузки VFS или обращения к ней."""


class Node:
    """Узел VFS: каталог (есть children) или файл (есть data)."""

    def __init__(self, name, is_dir, data=b""):
        """Создаёт узел с именем name; для файла хранит байты data."""
        self.name = name
        self.is_dir = is_dir
        self.data = data
        self.children = {}

    @property
    def size(self):
        """Размер содержимого файла в байтах (у каталога — 0)."""
        return len(self.data)


def split_path(path):
    """Делит абсолютный путь на непустые компоненты."""
    return [part for part in path.split(ROOT) if part]


def normalize(cwd, path):
    """Превращает путь (абсолютный, относительный или с ~) в абсолютный.

    Символ ~ обозначает домашний каталог, то есть корень VFS.
    Компоненты . и .. раскрываются; выше корня подняться нельзя.
    """
    if path == HOME_MARK or path.startswith(HOME_MARK + ROOT):
        path = ROOT + path[len(HOME_MARK):]
    if not path.startswith(ROOT):
        path = posixpath.join(cwd, path)
    return ROOT + posixpath.normpath(path).lstrip(ROOT)


def decode_content(encoding, content):
    """Превращает содержимое из CSV в байты согласно колонке encoding."""
    if encoding in ("", ENCODING_TEXT):
        return content.encode("utf-8")
    if encoding == ENCODING_BASE64:
        try:
            return base64.b64decode(content, validate=True)
        except binascii.Error as error:
            raise VFSError("invalid base64 data") from error
    raise VFSError(f"unknown encoding '{encoding}'")


class VFS:
    """Дерево каталогов и файлов в оперативной памяти."""

    def __init__(self, source=None):
        """Создаёт пустую VFS (только корень); source — путь к CSV."""
        self.source = source
        self.root = Node("", True)

    def find_node(self, abs_path):
        """Возвращает узел по абсолютному пути или None."""
        node = self.root
        for part in split_path(abs_path):
            if not node.is_dir or part not in node.children:
                return None
            node = node.children[part]
        return node

    def make_dirs(self, parts):
        """Создаёт цепочку каталогов и возвращает последний из них."""
        node = self.root
        for part in parts:
            child = node.children.get(part)
            if child is None:
                child = Node(part, True)
                node.children[part] = child
            elif not child.is_dir:
                raise VFSError(f"'{part}' is a file, not a directory")
            node = child
        return node

    def add_file(self, parts, data):
        """Добавляет файл по компонентам пути; дубликаты запрещены."""
        if not parts:
            raise VFSError("the root cannot be a file")
        parent = self.make_dirs(parts[:-1])
        name = parts[-1]
        if name in parent.children:
            raise VFSError(f"duplicate path '{ROOT + ROOT.join(parts)}'")
        parent.children[name] = Node(name, False, data)

    def create_file(self, abs_path):
        """Создаёт пустой файл в памяти по абсолютному пути.

        Родительский каталог должен существовать. Исходный CSV не меняется.
        """
        parent = self.find_node(posixpath.dirname(abs_path))
        if parent is None:
            raise VFSError("No such file or directory")
        if not parent.is_dir:
            raise VFSError("Not a directory")
        name = posixpath.basename(abs_path)
        parent.children[name] = Node(name, False)

    def add_row(self, row):
        """Добавляет в VFS элемент, описанный строкой CSV."""
        if len(row) != len(COLUMNS):
            raise VFSError(f"expected {len(COLUMNS)} columns, got {len(row)}")
        path, kind, encoding, content = row
        if not path.startswith(ROOT):
            raise VFSError(f"path '{path}' must be absolute")
        parts = split_path(posixpath.normpath(path))
        if kind == TYPE_DIR:
            self.make_dirs(parts)
        elif kind == TYPE_FILE:
            self.add_file(parts, decode_content(encoding, content))
        else:
            raise VFSError(f"unknown type '{kind}'")

    def stats(self):
        """Возвращает (каталогов без корня, файлов, общий размер файлов)."""
        dirs = files = size = 0
        stack = list(self.root.children.values())
        while stack:
            node = stack.pop()
            if node.is_dir:
                dirs += 1
                stack.extend(node.children.values())
            else:
                files += 1
                size += node.size
        return dirs, files, size

    def motd(self):
        """Возвращает текст файла /motd из корня VFS или None."""
        node = self.find_node(MOTD_PATH)
        if node is None or node.is_dir:
            return None
        return node.data.decode("utf-8", errors="replace")


def build_vfs(rows, source):
    """Строит VFS из строк CSV (первая строка — заголовок)."""
    if not rows or rows[0] != COLUMNS:
        header = ",".join(COLUMNS)
        raise VFSError(f"invalid format: expected header '{header}'")
    vfs = VFS(source)
    for number, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        try:
            vfs.add_row(row)
        except VFSError as error:
            raise VFSError(f"invalid format, row {number}: {error}") from error
    return vfs


def load_csv(path):
    """Загружает VFS из CSV-файла целиком в память.

    Исходный файл только читается и никогда не изменяется.
    """
    csv.field_size_limit(CSV_FIELD_LIMIT)
    try:
        with open(path, newline="", encoding=FILE_ENCODING) as file:
            rows = list(csv.reader(file))
    except FileNotFoundError as error:
        raise VFSError(f"file not found: {path}") from error
    except OSError as error:
        raise VFSError(f"cannot read '{path}': {error.strerror}") from error
    except UnicodeDecodeError as error:
        raise VFSError("invalid format: not UTF-8 text") from error
    except csv.Error as error:
        raise VFSError(f"invalid format: {error}") from error
    return build_vfs(rows, path)
