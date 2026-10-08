"""Тесты ядра эмулятора: парсер, приглашение, команды и скрипты."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import context

shell = context.load("shell")


def make_shell():
    """Создаёт оболочку с фиксированными именем пользователя и хоста."""
    with mock.patch("getpass.getuser", return_value="bob"), \
            mock.patch("socket.gethostname", return_value="pc"):
        return shell.Shell()


def capture(func, *args):
    """Выполняет func и возвращает (результат, напечатанный текст)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = func(*args)
    return result, buffer.getvalue()


class ParseTest(unittest.TestCase):
    """Проверка разбора строки ввода."""

    def test_command_and_args(self):
        """Команда и аргументы делятся по пробелам."""
        self.assertEqual(shell.parse("ls -l /tmp"), ("ls", ["-l", "/tmp"]))

    def test_extra_spaces(self):
        """Лишние пробелы игнорируются."""
        self.assertEqual(shell.parse("  cd   a  b "), ("cd", ["a", "b"]))

    def test_empty(self):
        """Пустая строка даёт пустую команду."""
        self.assertEqual(shell.parse("   "), ("", []))

    def test_comment_only(self):
        """Строка-комментарий не содержит команды."""
        self.assertEqual(shell.parse("# just a comment"), ("", []))

    def test_trailing_comment(self):
        """Комментарий в конце строки отбрасывается."""
        self.assertEqual(shell.parse("cd docs # go"), ("cd", ["docs"]))


class PromptTest(unittest.TestCase):
    """Проверка приглашения к вводу."""

    def test_prompt_format(self):
        """Приглашение имеет вид username@hostname:~$ ."""
        self.assertEqual(make_shell().prompt(), "bob@pc:~$ ")

    def test_display_cwd(self):
        """Корень отображается как ~, остальное как ~/путь."""
        self.assertEqual(shell.display_cwd("/"), "~")
        self.assertEqual(shell.display_cwd("/a/b"), "~/a/b")


class ExecuteTest(unittest.TestCase):
    """Проверка выполнения команд."""

    def test_known_command(self):
        """Известная команда выполняется и выводит результат."""
        result, text = capture(make_shell().execute, "whoami")
        self.assertTrue(result)
        self.assertEqual(text, "bob\n")

    def test_command_error(self):
        """Ошибка команды выводится с её именем, результат — False."""
        result, text = capture(make_shell().execute, "cd nowhere")
        self.assertFalse(result)
        self.assertEqual(text, "cd: nowhere: No such file or directory\n")

    def test_prompt_follows_cwd(self):
        """После cd приглашение показывает текущий каталог."""
        instance = make_shell()
        instance.vfs.make_dirs(["a", "b"])
        capture(instance.execute, "cd a/b")
        self.assertEqual(instance.prompt(), "bob@pc:~/a/b$ ")

    def test_unknown_command(self):
        """Неизвестная команда сообщает об ошибке."""
        result, text = capture(make_shell().execute, "foo")
        self.assertFalse(result)
        self.assertEqual(text, "unknown command: foo\n")

    def test_empty_line(self):
        """Пустая строка ничего не делает."""
        result, text = capture(make_shell().execute, "")
        self.assertTrue(result)
        self.assertEqual(text, "")

    def test_vfs_info_empty(self):
        """vfs-info без VFS сообщает о пустой файловой системе."""
        _, text = capture(make_shell().execute, "vfs-info")
        self.assertIn("<empty VFS>", text)
        self.assertIn("files: 0", text)

    def test_vfs_info_rejects_arguments(self):
        """vfs-info не принимает аргументов."""
        result, text = capture(make_shell().execute, "vfs-info x")
        self.assertFalse(result)
        self.assertIn("extra operand 'x'", text)

    def test_exit(self):
        """Команда exit останавливает оболочку."""
        instance = make_shell()
        capture(instance.execute, "exit")
        self.assertFalse(instance.running)


class ScriptTest(unittest.TestCase):
    """Проверка выполнения стартового скрипта."""

    def run_text(self, text):
        """Выполняет скрипт с заданным текстом, возвращает вывод."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "start.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write(text)
            _, output = capture(make_shell().run_script, path)
        return output

    def test_input_and_output_shown(self):
        """На экране отображаются и ввод, и вывод."""
        output = self.run_text("whoami\n")
        self.assertEqual(output, "bob@pc:~$ whoami\nbob\n")

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки не выполняются."""
        output = self.run_text("# note\n\nwhoami # tail\n")
        self.assertEqual(
            output, "# note\nbob@pc:~$ whoami # tail\nbob\n")

    def test_error_reported_and_run_continues(self):
        """Ошибка сообщается, выполнение продолжается."""
        output = self.run_text("foo\nwhoami\n")
        self.assertIn("unknown command: foo", output)
        self.assertIn("script error: line 1: command failed", output)
        self.assertIn("\nbob\n", output)

    def test_stops_after_exit(self):
        """После exit остальные строки не выполняются."""
        output = self.run_text("exit\nwhoami\n")
        self.assertNotIn("whoami", output)

    def test_missing_file(self):
        """Отсутствующий файл скрипта вызывает OSError."""
        with self.assertRaises(OSError):
            make_shell().run_script("no_such_script.txt")


class ReplTest(unittest.TestCase):
    """Проверка интерактивного цикла."""

    def test_repl_runs_until_exit(self):
        """REPL выполняет команды и завершается по exit."""
        instance = make_shell()
        side = ["whoami", "exit", "whoami"]
        with mock.patch("builtins.input", side_effect=side):
            _, text = capture(instance.repl)
        self.assertEqual(text, "bob\n")

    def test_repl_eof(self):
        """Конец ввода завершает REPL."""
        with mock.patch("builtins.input", side_effect=EOFError):
            _, text = capture(make_shell().repl)
        self.assertEqual(text, "\n")

    def test_repl_interrupt(self):
        """Ctrl+C отменяет ввод строки, но не завершает REPL."""
        side = [KeyboardInterrupt, "exit"]
        with mock.patch("builtins.input", side_effect=side):
            _, text = capture(make_shell().repl)
        self.assertEqual(text, "\n")


if __name__ == "__main__":
    unittest.main()
