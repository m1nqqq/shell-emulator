"""Команды эмулятора оболочки."""


class CommandError(Exception):
    """Ошибка выполнения команды, текст которой видит пользователь."""


def make_stub(name):
    """Создаёт команду-заглушку, выводящую своё имя и аргументы."""

    def stub(shell, args):
        """Возвращает строку с именем команды и её аргументами."""
        return [f"{name}: args = {args}"]

    return stub


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
    "ls": make_stub("ls"),
    "cd": make_stub("cd"),
    "vfs-info": cmd_vfs_info,
    "exit": cmd_exit,
}
