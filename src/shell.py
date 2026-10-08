"""Ядро эмулятора: разбор ввода, выполнение команд, скрипты и REPL."""

import getpass
import socket

import commands

COMMENT_MARK = "#"
HOME_DIR = "/"
DEFAULT_USER = "user"


def get_username():
    """Возвращает имя пользователя ОС или запасное значение."""
    try:
        return getpass.getuser()
    except (OSError, KeyError):
        return DEFAULT_USER


def parse(line):
    """Делит строку на команду и аргументы по пробелам.

    Всё, что начинается с токена, открывающего комментарий (#),
    отбрасывается.
    """
    tokens = []
    for token in line.split():
        if token.startswith(COMMENT_MARK):
            break
        tokens.append(token)
    if not tokens:
        return "", []
    return tokens[0], tokens[1:]


def display_cwd(cwd):
    """Возвращает текущий каталог в виде для приглашения (~ — корень)."""
    if cwd == HOME_DIR:
        return "~"
    return "~" + cwd


class Shell:
    """Состояние эмулятора и методы выполнения команд."""

    def __init__(self):
        """Создаёт оболочку с данными пользователя и хоста реальной ОС."""
        self.username = get_username()
        self.hostname = socket.gethostname()
        self.cwd = HOME_DIR
        self.running = True

    def prompt(self):
        """Возвращает приглашение вида username@hostname:~$ ."""
        place = display_cwd(self.cwd)
        return f"{self.username}@{self.hostname}:{place}$ "

    def execute(self, line):
        """Выполняет строку, печатает результат; False при ошибке."""
        name, args = parse(line)
        if not name:
            return True
        handler = commands.COMMANDS.get(name)
        if handler is None:
            print(f"unknown command: {name}")
            return False
        try:
            output = handler(self, args)
        except commands.CommandError as error:
            print(f"{name}: {error}")
            return False
        for text in output:
            print(text)
        return True

    def run_script_line(self, number, line):
        """Показывает строку скрипта как ввод и выполняет её."""
        text = line.strip()
        if not text:
            return
        if text.startswith(COMMENT_MARK):
            print(text)
            return
        print(f"{self.prompt()}{text}")
        if not self.execute(text):
            print(f"script error: line {number}: command failed")

    def run_script(self, path):
        """Выполняет стартовый скрипт, имитируя диалог с пользователем."""
        with open(path, encoding="utf-8-sig") as file:
            lines = file.read().splitlines()
        for number, line in enumerate(lines, start=1):
            if not self.running:
                break
            self.run_script_line(number, line)

    def repl(self):
        """Интерактивный цикл: читает ввод и выполняет команды."""
        while self.running:
            try:
                line = input(self.prompt())
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue
            self.execute(line)
