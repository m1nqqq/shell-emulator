"""Тесты VFS: загрузка из CSV, вложенность, base64, motd и ошибки."""

import os
import tempfile
import unittest

import context

vfs = context.load("vfs")

HEADER = "path,type,encoding,content\n"


def load_text(text, raw=None):
    """Записывает CSV во временный файл и загружает VFS."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "vfs.csv")
        with open(path, "wb") as file:
            file.write(raw if raw is not None else text.encode("utf-8"))
        return vfs.load_csv(path)


class LoadTest(unittest.TestCase):
    """Проверка успешной загрузки."""

    def test_header_only(self):
        """VFS из одного заголовка — пустая."""
        loaded = load_text(HEADER)
        self.assertEqual(loaded.stats(), (0, 0, 0))

    def test_nested_elements(self):
        """Вложенность задаётся путём, родители создаются сами."""
        loaded = load_text(HEADER + "/a/b/c/f.txt,file,text,hello\n")
        node = loaded.find_node("/a/b/c/f.txt")
        self.assertFalse(node.is_dir)
        self.assertEqual(node.data, b"hello")
        self.assertTrue(loaded.find_node("/a/b").is_dir)

    def test_directory_row(self):
        """Пустой каталог описывается строкой типа dir."""
        loaded = load_text(HEADER + "/empty,dir,,\n")
        self.assertTrue(loaded.find_node("/empty").is_dir)
        self.assertEqual(loaded.find_node("/empty").children, {})

    def test_base64_content(self):
        """Двоичные данные хранятся в base64."""
        loaded = load_text(HEADER + "/b.bin,file,base64,AAECAw==\n")
        self.assertEqual(loaded.find_node("/b.bin").data, b"\x00\x01\x02\x03")

    def test_multiline_text(self):
        """Текст с переводами строк хранится в кавычках."""
        loaded = load_text(HEADER + '/n.txt,file,text,"one\ntwo"\n')
        self.assertEqual(loaded.find_node("/n.txt").data, b"one\ntwo")

    def test_default_encoding_is_text(self):
        """Пустая колонка encoding означает text."""
        loaded = load_text(HEADER + "/a.txt,file,,hi\n")
        self.assertEqual(loaded.find_node("/a.txt").data, b"hi")

    def test_bom_and_crlf(self):
        """BOM и переводы строк Windows поддерживаются."""
        raw = b"\xef\xbb\xbf" + (HEADER + "/a.txt,file,text,x\n").replace(
            "\n", "\r\n").encode("utf-8")
        loaded = load_text("", raw)
        self.assertEqual(loaded.find_node("/a.txt").data, b"x")

    def test_stats_and_source(self):
        """stats считает каталоги, файлы и размер."""
        loaded = load_text(HEADER + "/d/a,file,text,xx\n/d/b,file,text,y\n")
        self.assertEqual(loaded.stats(), (1, 2, 3))
        self.assertTrue(loaded.source)

    def test_missing_node(self):
        """Несуществующий путь даёт None."""
        loaded = load_text(HEADER + "/a.txt,file,text,x\n")
        self.assertIsNone(loaded.find_node("/nope"))
        self.assertIsNone(loaded.find_node("/a.txt/inside"))


class InMemoryTest(unittest.TestCase):
    """Проверка того, что изменения VFS остаются только в памяти."""

    def test_create_file_does_not_touch_source(self):
        """create_file меняет дерево, но не исходный CSV."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "vfs.csv")
            with open(path, "w", encoding="utf-8", newline="") as file:
                file.write(HEADER + "/d,dir,,\n")
            with open(path, "rb") as file:
                before = file.read()
            loaded = vfs.load_csv(path)
            loaded.create_file("/d/new.txt")
            with open(path, "rb") as file:
                after = file.read()
        self.assertEqual(before, after)
        self.assertEqual(loaded.stats(), (1, 1, 0))

    def test_create_file_errors(self):
        """Нет родителя или родитель — файл."""
        loaded = load_text(HEADER + "/f,file,text,x\n")
        with self.assertRaises(vfs.VFSError):
            loaded.create_file("/nodir/a")
        with self.assertRaises(vfs.VFSError):
            loaded.create_file("/f/a")


class MotdTest(unittest.TestCase):
    """Проверка сообщения motd."""

    def test_motd_present(self):
        """Файл /motd в корне читается как текст."""
        loaded = load_text(HEADER + "/motd,file,text,Hello!\n")
        self.assertEqual(loaded.motd(), "Hello!")

    def test_motd_absent(self):
        """Без /motd сообщения нет."""
        self.assertIsNone(load_text(HEADER).motd())

    def test_motd_only_in_root(self):
        """motd в подкаталоге не считается."""
        loaded = load_text(HEADER + "/etc/motd,file,text,no\n")
        self.assertIsNone(loaded.motd())

    def test_motd_directory_ignored(self):
        """Каталог с именем motd не выводится."""
        self.assertIsNone(load_text(HEADER + "/motd,dir,,\n").motd())


class ErrorTest(unittest.TestCase):
    """Проверка ошибок загрузки."""

    def assert_error(self, text, fragment, raw=None):
        """Проверяет, что загрузка падает с VFSError и нужным текстом."""
        with self.assertRaises(vfs.VFSError) as caught:
            load_text(text, raw)
        self.assertIn(fragment, str(caught.exception))

    def test_file_not_found(self):
        """Отсутствующий файл."""
        with self.assertRaises(vfs.VFSError) as caught:
            vfs.load_csv("no_such_vfs.csv")
        self.assertIn("file not found", str(caught.exception))

    def test_directory_instead_of_file(self):
        """Каталог вместо файла."""
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(vfs.VFSError):
                vfs.load_csv(folder)

    def test_empty_file(self):
        """Пустой файл без заголовка."""
        self.assert_error("", "expected header")

    def test_wrong_header(self):
        """Неверный заголовок."""
        self.assert_error("name,kind\n", "expected header")

    def test_wrong_column_count(self):
        """Неверное число колонок."""
        self.assert_error(HEADER + "/a,file,text\n", "expected 4 columns")

    def test_unknown_type(self):
        """Неизвестный тип элемента."""
        self.assert_error(HEADER + "/a,link,,\n", "unknown type")

    def test_bad_base64(self):
        """Некорректные данные base64."""
        self.assert_error(HEADER + "/a,file,base64,@@@\n", "base64")

    def test_unknown_encoding(self):
        """Неизвестное имя кодировки."""
        self.assert_error(HEADER + "/a,file,rot13,x\n", "unknown encoding")

    def test_relative_path(self):
        """Путь должен быть абсолютным."""
        self.assert_error(HEADER + "a,file,text,x\n", "must be absolute")

    def test_duplicate(self):
        """Повторяющийся путь."""
        self.assert_error(
            HEADER + "/a,file,text,1\n/a,file,text,2\n", "duplicate")

    def test_file_used_as_directory(self):
        """Файл не может быть родителем."""
        self.assert_error(
            HEADER + "/a,file,text,1\n/a/b,file,text,2\n", "is a file")

    def test_root_as_file(self):
        """Корень не может быть файлом."""
        self.assert_error(HEADER + "/,file,text,x\n", "root")

    def test_not_utf8(self):
        """Файл не в кодировке UTF-8."""
        self.assert_error("", "not UTF-8", raw=b"\xff\xfe\x00\x01")

    def test_row_number_reported(self):
        """В сообщении указан номер строки с ошибкой."""
        self.assert_error(HEADER + "/a,file,text,1\n/b,bad,,\n", "row 3")


if __name__ == "__main__":
    unittest.main()
