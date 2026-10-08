"""Точка входа эмулятора оболочки ОС."""

import argparse
import sys

from shell import Shell

NOT_SET = "<not set>"
EXIT_OK = 0
EXIT_FAILURE = 1


def build_parser():
    """Создаёт разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Эмулятор языка оболочки UNIX-подобной ОС.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--vfs", metavar="PATH",
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script", metavar="PATH",
        help="путь к стартовому скрипту",
    )
    return parser


def print_debug(args):
    """Выводит все заданные параметры в формате ключ-значение."""
    print("[debug] startup parameters:")
    for key, value in vars(args).items():
        shown = NOT_SET if value is None else value
        print(f"[debug]   {key} = {shown}")


def run_startup_script(shell, path):
    """Выполняет стартовый скрипт; сообщает, если его не удалось прочесть."""
    try:
        shell.run_script(path)
    except (OSError, UnicodeDecodeError) as error:
        reason = getattr(error, "strerror", None) or "invalid UTF-8 text"
        print(f"error: cannot read startup script '{path}': {reason}",
              file=sys.stderr)
        return False
    return True


def main(argv=None):
    """Запускает эмулятор и возвращает код завершения процесса."""
    args = build_parser().parse_args(argv)
    print_debug(args)
    shell = Shell()
    if args.script and not run_startup_script(shell, args.script):
        return EXIT_FAILURE
    if shell.running:
        shell.repl()
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
