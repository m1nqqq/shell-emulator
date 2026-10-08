"""Тесты точки входа: параметры командной строки и запуск скрипта."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import context

main = context.load("main")


def run_main(argv):
    """Запускает main, возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with mock.patch("builtins.input", side_effect=EOFError):
            code = main.main(argv)
    return code, out.getvalue(), err.getvalue()


def write_script(folder, text):
    """Создаёт файл стартового скрипта и возвращает его путь."""
    path = os.path.join(folder, "start.txt")
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    return path


class ArgsTest(unittest.TestCase):
    """Проверка параметров командной строки."""

    def test_defaults(self):
        """Без параметров значения не заданы."""
        args = main.build_parser().parse_args([])
        self.assertIsNone(args.vfs)
        self.assertIsNone(args.script)

    def test_both_params(self):
        """Параметры --vfs и --script читаются."""
        args = main.build_parser().parse_args(
            ["--vfs", "a.csv", "--script", "s.txt"])
        self.assertEqual((args.vfs, args.script), ("a.csv", "s.txt"))

    def test_unknown_param(self):
        """Неизвестный параметр вызывает ошибку разбора."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main.build_parser().parse_args(["--bogus"])


class DebugTest(unittest.TestCase):
    """Проверка отладочного вывода параметров."""

    def test_debug_output(self):
        """Все параметры выводятся в формате ключ-значение."""
        _, out, _ = run_main(["--vfs", "a.csv"])
        self.assertIn("[debug]   vfs = a.csv", out)
        self.assertIn("[debug]   script = <not set>", out)


def write_vfs(folder, text):
    """Создаёт CSV-файл VFS и возвращает его путь."""
    path = os.path.join(folder, "vfs.csv")
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(text)
    return path


class VfsTest(unittest.TestCase):
    """Проверка подключения VFS."""

    header = "path,type,encoding,content\n"

    def test_motd_shown_at_start(self):
        """Сообщение motd выводится при старте."""
        with tempfile.TemporaryDirectory() as folder:
            path = write_vfs(folder, self.header + "/motd,file,text,Hi!\n")
            code, out, _ = run_main(["--vfs", path])
        self.assertEqual(code, 0)
        self.assertIn("Hi!", out)

    def test_no_motd(self):
        """Без motd ничего лишнего не выводится."""
        with tempfile.TemporaryDirectory() as folder:
            path = write_vfs(folder, self.header)
            _, out, _ = run_main(["--vfs", path])
        self.assertNotIn("Hi!", out)

    def test_vfs_file_not_found(self):
        """Отсутствующий файл VFS: сообщение и код 1."""
        code, _, err = run_main(["--vfs", "no_such_vfs.csv"])
        self.assertEqual(code, 1)
        self.assertIn("cannot load VFS: file not found", err)

    def test_vfs_invalid_format(self):
        """Неверный формат VFS: сообщение и код 1."""
        with tempfile.TemporaryDirectory() as folder:
            path = write_vfs(folder, "wrong\n")
            code, _, err = run_main(["--vfs", path])
        self.assertEqual(code, 1)
        self.assertIn("invalid format", err)

    def test_vfs_info_in_script(self):
        """Служебная команда vfs-info видит загруженную VFS."""
        with tempfile.TemporaryDirectory() as folder:
            vfs_path = write_vfs(
                folder, self.header + "/d/a.txt,file,text,abc\n")
            script = write_script(folder, "vfs-info\nexit\n")
            _, out, _ = run_main(["--vfs", vfs_path, "--script", script])
        self.assertIn("directories: 1", out)
        self.assertIn("files: 1", out)
        self.assertIn("total size: 3 bytes", out)


class MainTest(unittest.TestCase):
    """Проверка запуска эмулятора."""

    def test_script_executed(self):
        """Стартовый скрипт выполняется и завершает работу."""
        with tempfile.TemporaryDirectory() as folder:
            path = write_script(folder, "cal 2 2024\nexit\n")
            code, out, _ = run_main(["--script", path])
        self.assertEqual(code, 0)
        self.assertIn("February 2024", out)

    def test_missing_script(self):
        """Отсутствующий скрипт даёт сообщение об ошибке и код 1."""
        code, _, err = run_main(["--script", "no_such_script.txt"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read startup script", err)

    def test_bad_encoding_script(self):
        """Скрипт в неверной кодировке сообщает об ошибке."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad.txt")
            with open(path, "wb") as file:
                file.write(b"\xff\xfe\x00")
            code, _, err = run_main(["--script", path])
        self.assertEqual(code, 1)
        self.assertIn("invalid UTF-8", err)

    def test_interactive_after_script_without_exit(self):
        """Если скрипт не завершился командой exit, начинается REPL."""
        with tempfile.TemporaryDirectory() as folder:
            path = write_script(folder, "cal 2024\n")
            code, out, _ = run_main(["--script", path])
        self.assertEqual(code, 0)
        self.assertTrue(out.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
