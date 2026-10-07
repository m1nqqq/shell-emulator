"""Эмулятор оболочки ОС. Этап 1: REPL."""

import getpass
import socket
import sys


def make_prompt():
    """Возвращает приглашение вида username@hostname:~$ ."""
    username = getpass.getuser()
    hostname = socket.gethostname()
    return f"{username}@{hostname}:~$ "


def parse(command):
    """Делит строку на команду и список аргументов по пробелам."""
    parts = command.split()
    if not parts:
        return "", []
    return parts[0], parts[1:]


def execute(command, args):
    """Выполняет команду-заглушку ls, cd или exit."""
    if command == "ls":
        print(f"ls: args = {args}")
    elif command == "cd":
        print(f"cd: args = {args}")
    elif command == "exit":
        sys.exit(0)
    else:
        print(f"unknown command: {command}")


def repl():
    """Главный цикл: читает ввод, разбирает и выполняет команды."""
    while True:
        try:
            command = input(make_prompt())
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        name, args = parse(command)
        if not name:
            continue

        execute(name, args)


if __name__ == "__main__":
    repl()
