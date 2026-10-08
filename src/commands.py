"""Команды эмулятора оболочки."""


class CommandError(Exception):
    """Ошибка выполнения команды, текст которой видит пользователь."""


def make_stub(name):
    """Создаёт команду-заглушку, выводящую своё имя и аргументы."""

    def stub(shell, args):
        """Возвращает строку с именем команды и её аргументами."""
        return [f"{name}: args = {args}"]

    return stub


def cmd_exit(shell, args):
    """Завершает работу эмулятора."""
    shell.running = False
    return []


COMMANDS = {
    "ls": make_stub("ls"),
    "cd": make_stub("cd"),
    "exit": cmd_exit,
}
