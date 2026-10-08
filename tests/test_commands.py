"""Тесты команд этапа 4: ls, cd, cal, whoami и find."""

import contextlib
import datetime
import io
import unittest
from unittest import mock

import context

shell = context.load("shell")
vfs = context.load("vfs")

ROWS = [
    ["path", "type", "encoding", "content"],
    ["/readme.txt", "file", "text", "hello"],
    ["/.hidden", "file", "text", "x"],
    ["/docs/a.txt", "file", "text", "aaa"],
    ["/docs/b.md", "file", "text", "bb"],
    ["/docs/deep/c.txt", "file", "text", "c"],
    ["/empty", "dir", "", ""],
]


def make_shell():
    """Создаёт оболочку с тестовой VFS и пользователем bob."""
    with mock.patch("getpass.getuser", return_value="bob"), \
            mock.patch("socket.gethostname", return_value="pc"):
        return shell.Shell(vfs.build_vfs(ROWS, "test.csv"))


def run(instance, line):
    """Выполняет команду, возвращает (успех, список строк вывода)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = instance.execute(line)
    return result, buffer.getvalue().splitlines()


class NormalizeTest(unittest.TestCase):
    """Проверка преобразования путей."""

    def test_cases(self):
        """Абсолютные, относительные пути, ., .. и ~."""
        cases = [
            ("/", "a", "/a"),
            ("/a/b", "..", "/a"),
            ("/a/b", "../c", "/a/c"),
            ("/a", "/x/./y", "/x/y"),
            ("/a", "~", "/"),
            ("/a", "~/docs", "/docs"),
            ("/a", "../../..", "/"),
            ("/a", ".", "/a"),
            ("/", "//a//b/", "/a/b"),
        ]
        for cwd, path, expected in cases:
            self.assertEqual(vfs.normalize(cwd, path), expected, path)


class LsTest(unittest.TestCase):
    """Проверка ls."""

    def test_plain(self):
        """Скрытые файлы по умолчанию не показываются."""
        _, lines = run(make_shell(), "ls")
        self.assertEqual(lines, ["docs  empty  readme.txt"])

    def test_all(self):
        """Опция -a показывает скрытые файлы."""
        _, lines = run(make_shell(), "ls -a")
        self.assertEqual(lines, [".hidden  docs  empty  readme.txt"])

    def test_long(self):
        """Опция -l показывает тип и размер."""
        _, lines = run(make_shell(), "ls -l")
        self.assertEqual(lines, [
            "d        0 docs",
            "d        0 empty",
            "-        5 readme.txt",
        ])

    def test_combined_options(self):
        """Опции можно объединять: -la."""
        _, lines = run(make_shell(), "ls -la")
        self.assertEqual(len(lines), 4)

    def test_path_argument(self):
        """Путь к каталогу."""
        _, lines = run(make_shell(), "ls docs")
        self.assertEqual(lines, ["a.txt  b.md  deep"])

    def test_file_argument(self):
        """Путь к файлу выводит этот файл."""
        _, lines = run(make_shell(), "ls docs/a.txt")
        self.assertEqual(lines, ["docs/a.txt"])

    def test_multiple_paths(self):
        """Несколько путей выводятся с заголовками."""
        _, lines = run(make_shell(), "ls docs empty")
        self.assertEqual(lines, ["docs:", "a.txt  b.md  deep", "", "empty:"])

    def test_empty_directory(self):
        """Пустой каталог ничего не выводит."""
        result, lines = run(make_shell(), "ls empty")
        self.assertTrue(result)
        self.assertEqual(lines, [])

    def test_missing_path(self):
        """Несуществующий путь — ошибка."""
        result, lines = run(make_shell(), "ls nope")
        self.assertFalse(result)
        self.assertEqual(
            lines, ["ls: cannot access 'nope': No such file or directory"])

    def test_invalid_option(self):
        """Неизвестная опция — ошибка."""
        result, lines = run(make_shell(), "ls -z")
        self.assertFalse(result)
        self.assertEqual(lines, ["ls: invalid option -- 'z'"])


class CdTest(unittest.TestCase):
    """Проверка cd."""

    def test_relative_and_up(self):
        """Переход вниз и вверх по дереву."""
        instance = make_shell()
        run(instance, "cd docs/deep")
        self.assertEqual(instance.cwd, "/docs/deep")
        run(instance, "cd ..")
        self.assertEqual(instance.cwd, "/docs")

    def test_relative_ls_after_cd(self):
        """После cd относительные пути считаются от нового каталога."""
        instance = make_shell()
        run(instance, "cd docs")
        _, lines = run(instance, "ls deep")
        self.assertEqual(lines, ["c.txt"])

    def test_absolute(self):
        """Абсолютный путь."""
        instance = make_shell()
        run(instance, "cd /docs/deep")
        self.assertEqual(instance.cwd, "/docs/deep")

    def test_home_variants(self):
        """cd без аргумента, cd ~ и cd / ведут в корень."""
        for line in ("cd", "cd ~", "cd /"):
            instance = make_shell()
            run(instance, "cd docs")
            run(instance, line)
            self.assertEqual(instance.cwd, "/", line)

    def test_cannot_leave_root(self):
        """Выше корня подняться нельзя."""
        instance = make_shell()
        run(instance, "cd ../../..")
        self.assertEqual(instance.cwd, "/")

    def test_missing(self):
        """Несуществующий каталог."""
        result, lines = run(make_shell(), "cd nope")
        self.assertFalse(result)
        self.assertEqual(lines, ["cd: nope: No such file or directory"])

    def test_not_a_directory(self):
        """Файл вместо каталога."""
        instance = make_shell()
        result, lines = run(instance, "cd readme.txt")
        self.assertFalse(result)
        self.assertEqual(lines, ["cd: readme.txt: Not a directory"])
        self.assertEqual(instance.cwd, "/")

    def test_too_many_arguments(self):
        """Больше одного аргумента."""
        result, lines = run(make_shell(), "cd a b")
        self.assertFalse(result)
        self.assertEqual(lines, ["cd: too many arguments"])


class CalTest(unittest.TestCase):
    """Проверка cal."""

    def test_month_year(self):
        """Месяц и год: заголовок и первое число."""
        _, lines = run(make_shell(), "cal 2 2024")
        self.assertEqual(lines[0].strip(), "February 2024")
        self.assertEqual(lines[1], "Su Mo Tu We Th Fr Sa")
        self.assertEqual(lines[2], "             1  2  3")
        self.assertEqual(lines[-1], "25 26 27 28 29")

    def test_monday_first(self):
        """Опция -m начинает неделю с понедельника."""
        _, lines = run(make_shell(), "cal -m 2 2024")
        self.assertEqual(lines[1], "Mo Tu We Th Fr Sa Su")

    def test_year(self):
        """Один аргумент — год целиком."""
        _, lines = run(make_shell(), "cal 2024")
        self.assertEqual(lines[0].strip(), "2024")
        self.assertEqual(sum("Su Mo Tu" in line for line in lines), 4)

    def test_current_month(self):
        """Без аргументов — текущий месяц."""
        today = datetime.date.today()
        _, lines = run(make_shell(), "cal")
        self.assertIn(str(today.year), lines[0])

    def test_invalid_month(self):
        """Месяц вне диапазона."""
        result, lines = run(make_shell(), "cal 13 2024")
        self.assertFalse(result)
        self.assertIn("month 13 not in range 1..12", lines[0])

    def test_invalid_year(self):
        """Год вне диапазона и не число."""
        self.assertFalse(run(make_shell(), "cal 1 10000")[0])
        self.assertFalse(run(make_shell(), "cal 1 abc")[0])

    def test_too_many_arguments(self):
        """Больше двух значений."""
        result, lines = run(make_shell(), "cal 1 2 3")
        self.assertFalse(result)
        self.assertEqual(lines, ["cal: too many arguments"])


class WhoamiTest(unittest.TestCase):
    """Проверка whoami."""

    def test_name(self):
        """Выводит имя пользователя из приглашения."""
        _, lines = run(make_shell(), "whoami")
        self.assertEqual(lines, ["bob"])

    def test_extra_operand(self):
        """Лишний аргумент — ошибка."""
        result, lines = run(make_shell(), "whoami now")
        self.assertFalse(result)
        self.assertEqual(lines, ["whoami: extra operand 'now'"])


class TouchTest(unittest.TestCase):
    """Проверка touch."""

    def test_create_file(self):
        """Новый файл создаётся пустым."""
        instance = make_shell()
        result, lines = run(instance, "touch new.txt")
        self.assertTrue(result)
        self.assertEqual(lines, [])
        node = instance.vfs.find_node("/new.txt")
        self.assertFalse(node.is_dir)
        self.assertEqual(node.size, 0)

    def test_visible_to_other_commands(self):
        """Созданный файл виден в ls и find."""
        instance = make_shell()
        run(instance, "touch new.txt")
        self.assertIn("new.txt", run(instance, "ls")[1][0])
        self.assertIn("./new.txt", run(instance, "find")[1])

    def test_existing_file_unchanged(self):
        """touch существующего файла не меняет его содержимое."""
        instance = make_shell()
        run(instance, "touch readme.txt")
        self.assertEqual(instance.vfs.find_node("/readme.txt").data, b"hello")

    def test_existing_directory_ok(self):
        """touch существующего каталога — не ошибка."""
        result, _ = run(make_shell(), "touch docs")
        self.assertTrue(result)

    def test_multiple_files(self):
        """Несколько файлов за один вызов."""
        instance = make_shell()
        run(instance, "touch a b c")
        for name in ("a", "b", "c"):
            self.assertIsNotNone(instance.vfs.find_node("/" + name))

    def test_relative_and_absolute_paths(self):
        """Относительный (с ..), абсолютный пути и путь с ~."""
        instance = make_shell()
        run(instance, "cd docs/deep")
        run(instance, "touch ../x.txt /y.txt ~/z.txt")
        for path in ("/docs/x.txt", "/y.txt", "/z.txt"):
            self.assertIsNotNone(instance.vfs.find_node(path), path)

    def test_no_create_option(self):
        """Опция -c не создаёт отсутствующие файлы."""
        instance = make_shell()
        result, _ = run(instance, "touch -c ghost.txt")
        self.assertTrue(result)
        self.assertIsNone(instance.vfs.find_node("/ghost.txt"))

    def test_missing_operand(self):
        """Без аргументов — ошибка."""
        result, lines = run(make_shell(), "touch")
        self.assertFalse(result)
        self.assertEqual(lines, ["touch: missing file operand"])

    def test_invalid_option(self):
        """Неизвестная опция — ошибка."""
        result, lines = run(make_shell(), "touch -x f")
        self.assertFalse(result)
        self.assertEqual(lines, ["touch: invalid option -- 'x'"])

    def test_missing_parent(self):
        """Нет родительского каталога."""
        result, lines = run(make_shell(), "touch nodir/f.txt")
        self.assertFalse(result)
        self.assertEqual(lines, [
            "touch: cannot touch 'nodir/f.txt': No such file or directory"])

    def test_parent_is_file(self):
        """Родитель — файл, а не каталог."""
        result, lines = run(make_shell(), "touch readme.txt/f")
        self.assertFalse(result)
        self.assertEqual(lines, [
            "touch: cannot touch 'readme.txt/f': Not a directory"])

    def test_stops_at_first_error(self):
        """После первой ошибки остальные файлы не создаются."""
        instance = make_shell()
        run(instance, "touch ok1 nodir/bad ok2")
        self.assertIsNotNone(instance.vfs.find_node("/ok1"))
        self.assertIsNone(instance.vfs.find_node("/ok2"))


class FindTest(unittest.TestCase):
    """Проверка find."""

    def test_default(self):
        """Без аргументов обходит текущий каталог."""
        _, lines = run(make_shell(), "find")
        self.assertEqual(lines[0], ".")
        self.assertIn("./docs/deep/c.txt", lines)
        self.assertIn("./.hidden", lines)
        self.assertEqual(len(lines), 9)

    def test_path(self):
        """Путь задаёт начало поиска и префикс вывода."""
        _, lines = run(make_shell(), "find docs")
        self.assertEqual(lines, [
            "docs", "docs/a.txt", "docs/b.md", "docs/deep",
            "docs/deep/c.txt",
        ])

    def test_root(self):
        """Поиск от корня."""
        _, lines = run(make_shell(), "find / -type d")
        self.assertEqual(lines, ["/", "/docs", "/docs/deep", "/empty"])

    def test_name_pattern(self):
        """Шаблон -name, в том числе в кавычках."""
        _, plain = run(make_shell(), "find / -name *.txt")
        _, quoted = run(make_shell(), 'find / -name "*.txt"')
        expected = ["/docs/a.txt", "/docs/deep/c.txt", "/readme.txt"]
        self.assertEqual(plain, expected)
        self.assertEqual(quoted, expected)

    def test_type_file(self):
        """Условие -type f."""
        _, lines = run(make_shell(), "find docs -type f")
        self.assertEqual(
            lines, ["docs/a.txt", "docs/b.md", "docs/deep/c.txt"])

    def test_name_and_type(self):
        """Условия -name и -type вместе."""
        _, lines = run(make_shell(), "find . -name deep -type d")
        self.assertEqual(lines, ["./docs/deep"])

    def test_multiple_paths(self):
        """Несколько начальных путей."""
        _, lines = run(make_shell(), "find empty readme.txt")
        self.assertEqual(lines, ["empty", "readme.txt"])

    def test_errors(self):
        """Ошибки: нет пути, нет значения, неизвестные опции."""
        cases = [
            ("find nope", "find: 'nope': No such file or directory"),
            ("find -name", "find: missing argument to '-name'"),
            ("find -foo", "find: unknown predicate '-foo'"),
            ("find -type x", "find: unknown argument to -type: x"),
        ]
        for line, message in cases:
            result, lines = run(make_shell(), line)
            self.assertFalse(result, line)
            self.assertEqual(lines, [message], line)


if __name__ == "__main__":
    unittest.main()
