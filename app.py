import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
    QCheckBox,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QListWidgetItem,
    QLabel,
    QSplitter,
    QComboBox  # Добавляем QComboBox для выпадающего списка
)
from PyQt5.QtCore import Qt


class FileMergerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.settings = {}
        self.load_settings()
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()

        # Левая часть (папки, расширения)
        left_layout = QVBoxLayout()

        # Блок выбора папки
        folder_layout = QHBoxLayout()
        self.folder_path_input = QLineEdit(self)
        self.folder_path_input.setPlaceholderText("Выберите папку...")
        self.folder_path_input.setText(self.settings.get("folder_path", ""))
        folder_layout.addWidget(self.folder_path_input)

        self.browse_button = QPushButton("Обзор", self)
        self.browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_button)
        left_layout.addLayout(folder_layout)

        # Список папок
        self.folder_list_label = QLabel("Папки:")
        left_layout.addWidget(self.folder_list_label)
        self.folder_list_widget = QListWidget(self)
        self.folder_list_widget.setMinimumHeight(150)  # Увеличенная высота
        left_layout.addWidget(self.folder_list_widget)

        # Список расширений
        self.extensions_label = QLabel("Расширения файлов:")
        left_layout.addWidget(self.extensions_label)
        self.extensions_widget = QListWidget(self)
        self.extensions_widget.setMinimumHeight(150)  # Увеличенная высота
        left_layout.addWidget(self.extensions_widget)

        # Правая часть (выпадающий список, список файлов + текстовое поле)
        right_layout = QVBoxLayout()

        # Выпадающий список для выбора префикса перед относительным путем файла
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("Префикс:")
        prefix_layout.addWidget(prefix_label)
        self.prefix_combo = QComboBox(self)
        self.prefix_combo.addItems(["//", "#"])
        self.prefix_combo.setCurrentIndex(0)  # По умолчанию "//"
        prefix_layout.addWidget(self.prefix_combo)
        right_layout.addLayout(prefix_layout)

        # Список файлов
        self.file_list_label = QLabel("Файлы:")
        right_layout.addWidget(self.file_list_label)
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setMinimumHeight(300)
        right_layout.addWidget(self.file_list_widget)

        # Кнопка копирования файлов
        self.copy_button = QPushButton("Копировать", self)
        self.copy_button.clicked.connect(self.copy_files_content)
        right_layout.addWidget(self.copy_button)

        # Поле для вывода содержимого файлов
        self.output_text_edit = QTextEdit(self)
        self.output_text_edit.setReadOnly(True)
        right_layout.addWidget(self.output_text_edit)

        # Разделитель между списками
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        right_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        self.setWindowTitle("Слияние файлов")
        self.setGeometry(300, 300, 800, 500)
        self.setMinimumSize(600, 400)  # Теперь окно можно ресайзить по-жесткому

        # Если есть сохранённая папка, сканируем её
        if self.folder_path_input.text():
            self.scan_folder(self.folder_path_input.text())

    def browse_folder(self):
        """Выбор папки и её сканирование."""
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder_path:
            self.folder_path_input.setText(folder_path)
            self.settings["folder_path"] = folder_path
            self.save_settings()
            self.scan_folder(folder_path)

    def scan_folder(self, folder_path):
        """Сканирует папку, добавляет папки и расширения файлов."""
        self.folder_list_widget.clear()
        self.extensions_widget.clear()
        self.file_list_widget.clear()

        try:
            first_level_folders = [
                d for d in os.listdir(folder_path)
                if os.path.isdir(os.path.join(folder_path, d))
            ]
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка чтения папки:\n{folder_path}\n{str(e)}")
            return

        # Добавляем папки (по умолчанию не выбраны)
        for folder in first_level_folders:
            item = QListWidgetItem(folder)
            item.setCheckState(Qt.Unchecked)
            self.folder_list_widget.addItem(item)

        # Собираем расширения файлов
        extensions = set()
        for root, _, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext:
                    extensions.add(ext)

        # Добавляем расширения (по умолчанию не выбраны)
        for ext in sorted(extensions):
            item = QListWidgetItem(ext)
            item.setCheckState(Qt.Unchecked)
            self.extensions_widget.addItem(item)

        # Обновляем список файлов
        self.update_file_list()

        # Подключаем сигналы после заполнения списков
        self.folder_list_widget.itemChanged.connect(self.update_file_list)
        self.extensions_widget.itemChanged.connect(self.update_file_list)

    def update_file_list(self):
        """Обновляет список файлов на основе выбранных папок и расширений."""
        self.file_list_widget.clear()
        folder_path = self.folder_path_input.text()
        if not folder_path or not os.path.exists(folder_path):
            return

        selected_folders = [
            self.folder_list_widget.item(i).text()
            for i in range(self.folder_list_widget.count())
            if self.folder_list_widget.item(i).checkState() == Qt.Checked
        ]

        selected_extensions = [
            self.extensions_widget.item(i).text()
            for i in range(self.extensions_widget.count())
            if self.extensions_widget.item(i).checkState() == Qt.Checked
        ]

        for folder in selected_folders:
            full_path = os.path.join(folder_path, folder)
            self.add_files_from_folder(full_path, selected_extensions)

    def add_files_from_folder(self, folder_path, extensions):
        """Добавляет файлы из папки, если их расширение выбрано."""
        for root, _, files in os.walk(folder_path):
            for file in files:
                if os.path.splitext(file)[1] in extensions:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.folder_path_input.text())
                    list_item = QListWidgetItem()
                    checkbox = QCheckBox(relative_path)
                    checkbox.setChecked(True)  # Теперь файлы по умолчанию выбраны
                    checkbox.file_path = file_path
                    self.file_list_widget.addItem(list_item)
                    self.file_list_widget.setItemWidget(list_item, checkbox)

    def copy_files_content(self):
        """Копирует содержимое выбранных файлов в текстовое поле."""
        self.output_text_edit.clear()
        selected_prefix = self.prefix_combo.currentText()
        for i in range(self.file_list_widget.count()):
            list_item = self.file_list_widget.item(i)
            widget = self.file_list_widget.itemWidget(list_item)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                file_path = widget.file_path
                relative_path = widget.text()  # относительный путь уже здесь
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        header = f"{selected_prefix} {relative_path}"
                        # Если файл уже начинается с нужного префикса + пути, не дублируем
                        if content.lstrip().startswith(header):
                            self.output_text_edit.append(f"{content}\n")
                        else:
                            self.output_text_edit.append(f"{header}\n\n{content}\n")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Ошибка чтения файла:\n{file_path}\n{str(e)}")

    def load_settings(self):
        """Загружает настройки."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}

    def save_settings(self):
        """Сохраняет настройки."""
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileMergerApp()
    window.show()
    sys.exit(app.exec_())
