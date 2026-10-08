"""Команды эмулятора оболочки."""

import calendar
import datetime
import fnmatch
import posixpath

from vfs import HOME_MARK, ROOT, VFSError, normalize

CURRENT_DIR = "."
LS_OPTIONS = "al"
CAL_OPTIONS = "m"
TOUCH_OPTIONS = "c"
MIN_MONTH = 1
MAX_MONTH = 12
MIN_YEAR = 1
MAX_YEAR = 9999
CAL_MAX_ARGS = 2
FIND_OPTIONS = ("-name", "-type")
KIND_FILE = "f"
KIND_DIR = "d"
NO_SUCH_FILE = "No such file or directory"
QUOTES = "\"'"


class CommandError(Exception):
    """Ошибка выполнения команды, текст которой видит пользователь."""


def lookup(shell, path):
    """Возвращает узел VFS по пути относительно текущего каталога."""
    return shell.vfs.find_node(normalize(shell.cwd, path))


def split_options(args, allowed):
    """Отделяет короткие опции (-a, -la) от остальных аргументов."""
    flags = set()
    rest = []
    for arg in args:
        if arg.startswith("-") and len(arg) > 1:
            for char in arg[1:]:
                if char not in allowed:
                    raise CommandError(f"invalid option -- '{char}'")
                flags.add(char)
        else:
            rest.append(arg)
    return flags, rest


def format_entry(name, node, long_format):
    """Форматирует запись для ls: просто имя или строка для -l."""
    if not long_format:
        return name
    kind = "d" if node.is_dir else "-"
    return f"{kind} {node.size:>8} {name}"


def ls_block(path, node, flags, header):
    """Строки вывода ls для одного пути (файл или каталог)."""
    long_format = "l" in flags
    if not node.is_dir:
        return [format_entry(path, node, long_format)]
    names = sorted(node.children)
    if "a" not in flags:
        names = [name for name in names if not name.startswith(".")]
    if long_format:
        lines = [format_entry(n, node.children[n], True) for n in names]
    else:
        lines = ["  ".join(names)] if names else []
    return ([f"{path}:"] + lines) if header else lines


def cmd_ls(shell, args):
    """ls [-a] [-l] [ПУТЬ...] — содержимое каталогов и файлов."""
    flags, paths = split_options(args, LS_OPTIONS)
    found = []
    for path in paths or [CURRENT_DIR]:
        node = lookup(shell, path)
        if node is None:
            raise CommandError(f"cannot access '{path}': {NO_SUCH_FILE}")
        found.append((path, node))
    header = len(found) > 1
    lines = []
    for path, node in found:
        if lines:
            lines.append("")
        lines.extend(ls_block(path, node, flags, header))
    return lines


def cmd_cd(shell, args):
    """cd [ПУТЬ] — смена текущего каталога (без аргумента — в корень)."""
    if len(args) > 1:
        raise CommandError("too many arguments")
    target = args[0] if args else HOME_MARK
    node = lookup(shell, target)
    if node is None:
        raise CommandError(f"{target}: {NO_SUCH_FILE}")
    if not node.is_dir:
        raise CommandError(f"{target}: Not a directory")
    shell.cwd = normalize(shell.cwd, target)
    return []


def parse_number(text, label, low, high):
    """Преобразует текст в число из диапазона [low, high]."""
    try:
        value = int(text)
    except ValueError as error:
        raise CommandError(f"invalid {label} '{text}'") from error
    if not low <= value <= high:
        raise CommandError(f"{label} {value} not in range {low}..{high}")
    return value


def cal_lines(text):
    """Разбивает готовый текст календаря на строки без хвостовых пробелов."""
    return [line.rstrip() for line in text.splitlines()]


def cmd_cal(shell, args):
    """cal [-m] [[МЕСЯЦ] ГОД] — календарь; -m: неделя с понедельника."""
    flags, values = split_options(args, CAL_OPTIONS)
    if len(values) > CAL_MAX_ARGS:
        raise CommandError("too many arguments")
    first_day = calendar.MONDAY if "m" in flags else calendar.SUNDAY
    text_calendar = calendar.TextCalendar(first_day)
    today = datetime.date.today()
    if not values:
        return cal_lines(text_calendar.formatmonth(today.year, today.month))
    if len(values) == 1:
        year = parse_number(values[0], "year", MIN_YEAR, MAX_YEAR)
        return cal_lines(text_calendar.formatyear(year))
    month = parse_number(values[0], "month", MIN_MONTH, MAX_MONTH)
    year = parse_number(values[1], "year", MIN_YEAR, MAX_YEAR)
    return cal_lines(text_calendar.formatmonth(year, month))


def cmd_whoami(shell, args):
    """whoami — имя текущего пользователя."""
    if args:
        raise CommandError(f"extra operand '{args[0]}'")
    return [shell.username]


def strip_quotes(text):
    """Убирает парные кавычки вокруг шаблона: "*.txt" -> *.txt."""
    if len(text) > 1 and text[0] in QUOTES and text[-1] == text[0]:
        return text[1:-1]
    return text


def parse_find(args):
    """Разбирает аргументы find: пути, -name ШАБЛОН и -type f|d."""
    paths = []
    options = {}
    items = iter(args)
    for arg in items:
        if arg in FIND_OPTIONS:
            value = next(items, None)
            if value is None:
                raise CommandError(f"missing argument to '{arg}'")
            options[arg] = value
        elif arg.startswith("-"):
            raise CommandError(f"unknown predicate '{arg}'")
        else:
            paths.append(arg)
    kind = options.get("-type")
    if kind not in (None, KIND_FILE, KIND_DIR):
        raise CommandError(f"unknown argument to -type: {kind}")
    pattern = options.get("-name")
    if pattern is not None:
        pattern = strip_quotes(pattern)
    return paths or [CURRENT_DIR], pattern, kind


def join_shown(prefix, name):
    """Присоединяет имя к пути в том виде, в каком путь показан."""
    if prefix.endswith(ROOT):
        return prefix + name
    return prefix + ROOT + name


def walk(node, shown):
    """Обходит поддерево в глубину, отдавая пары (путь, узел)."""
    yield shown, node
    if node.is_dir:
        for name in sorted(node.children):
            child = node.children[name]
            yield from walk(child, join_shown(shown, name))


def matches(shown, node, pattern, kind):
    """Проверяет узел на соответствие условиям -type и -name."""
    if kind == KIND_FILE and node.is_dir:
        return False
    if kind == KIND_DIR and not node.is_dir:
        return False
    if pattern is None:
        return True
    name = posixpath.basename(shown.rstrip(ROOT)) or shown
    return fnmatch.fnmatchcase(name, pattern)


def cmd_find(shell, args):
    """find [ПУТЬ...] [-name ШАБЛОН] [-type f|d] — поиск в VFS."""
    paths, pattern, kind = parse_find(args)
    lines = []
    for path in paths:
        node = lookup(shell, path)
        if node is None:
            raise CommandError(f"'{path}': {NO_SUCH_FILE}")
        for shown, found in walk(node, path):
            if matches(shown, found, pattern, kind):
                lines.append(shown)
    return lines


def touch_one(shell, path, no_create):
    """Создаёт пустой файл в VFS, если его ещё нет (только в памяти)."""
    abs_path = normalize(shell.cwd, path)
    if no_create or shell.vfs.find_node(abs_path) is not None:
        return
    try:
        shell.vfs.create_file(abs_path)
    except VFSError as error:
        raise CommandError(f"cannot touch '{path}': {error}") from error


def cmd_touch(shell, args):
    """touch [-c] ФАЙЛ... — создаёт пустые файлы; -c: не создавать."""
    flags, paths = split_options(args, TOUCH_OPTIONS)
    if not paths:
        raise CommandError("missing file operand")
    for path in paths:
        touch_one(shell, path, "c" in flags)
    return []


def cmd_vfs_info(shell, args):
    """Служебная команда: сведения о загруженной VFS."""
    if args:
        raise CommandError(f"extra operand '{args[0]}'")
    dirs, files, size = shell.vfs.stats()
    source = shell.vfs.source or "<empty VFS>"
    return [
        f"source: {source}",
        f"directories: {dirs}",
        f"files: {files}",
        f"total size: {size} bytes",
    ]


def cmd_exit(shell, args):
    """Завершает работу эмулятора."""
    shell.running = False
    return []


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "cal": cmd_cal,
    "whoami": cmd_whoami,
    "find": cmd_find,
    "touch": cmd_touch,
    "vfs-info": cmd_vfs_info,
    "exit": cmd_exit,
}
