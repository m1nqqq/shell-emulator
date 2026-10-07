"""Тесты этапа 1: парсер, приглашение и команды."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main  # noqa: E402


class ParseTest(unittest.TestCase):
    """Проверка разбора строки ввода."""

    def test_command_and_args(self):
        """Команда и аргументы делятся по пробелам."""
        self.assertEqual(main.parse("ls -l /tmp"), ("ls", ["-l", "/tmp"]))

    def test_extra_spaces(self):
        """Лишние пробелы игнорируются."""
        self.assertEqual(main.parse("  cd   a  b "), ("cd", ["a", "b"]))

    def test_empty(self):
        """Пустая строка даёт пустую команду."""
        self.assertEqual(main.parse("   "), ("", []))


class PromptTest(unittest.TestCase):
    """Проверка приглашения к вводу."""

    def test_prompt_format(self):
        """Приглашение имеет вид username@hostname:~$ ."""
        with mock.patch("getpass.getuser", return_value="bob"), \
                mock.patch("socket.gethostname", return_value="pc"):
            self.assertEqual(main.make_prompt(), "bob@pc:~$ ")


class ExecuteTest(unittest.TestCase):
    """Проверка выполнения команд."""

    def test_ls_stub(self):
        """Заглушка ls выводит имя и аргументы."""
        with mock.patch("builtins.print") as fake_print:
            main.execute("ls", ["-l"])
        fake_print.assert_called_once_with("ls: args = ['-l']")

    def test_cd_stub(self):
        """Заглушка cd выводит имя и аргументы."""
        with mock.patch("builtins.print") as fake_print:
            main.execute("cd", ["docs"])
        fake_print.assert_called_once_with("cd: args = ['docs']")

    def test_unknown_command(self):
        """Неизвестная команда сообщает об ошибке."""
        with mock.patch("builtins.print") as fake_print:
            main.execute("foo", [])
        fake_print.assert_called_once_with("unknown command: foo")

    def test_exit(self):
        """Команда exit завершает работу."""
        with self.assertRaises(SystemExit):
            main.execute("exit", [])


if __name__ == "__main__":
    unittest.main()
