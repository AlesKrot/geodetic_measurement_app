from __future__ import annotations

# import sys
# import os
# import traceback

# # 1. Адразу ствараем файл і пішам, што пачалі
# with open("crash_log.txt", "w", encoding="utf-8") as f:
#     f.write("Пачатак загрузкі модуляў...\n")

# try:
#     # 2. Спрабуем імпартаваць асноўныя рэчы па адной
#     with open("crash_log.txt", "a", encoding="utf-8") as f:
#         f.write("Імпарт PySide6...\n")
#     from PySide6.QtWidgets import QApplication
    
#     with open("crash_log.txt", "a", encoding="utf-8") as f:
#         f.write("Імпарт main_window...\n")
#     # УВАГА: Правер, каб імя файла супадала (MainWindow ці main_window)
#     from main_window import MainWindow 
    
#     with open("crash_log.txt", "a", encoding="utf-8") as f:
#         f.write("Усе імпарты паспяховыя!\n")

# except Exception as e:
#     with open("crash_log.txt", "a", encoding="utf-8") as f:
#         f.write(f"\nКРЫТЫЧНАЯ ПАМЫЛКА ПРЫ ЗАГРУЗЦЫ:\n{str(e)}\n")
#         f.write(traceback.format_exc())
#     sys.exit(1)

# # Гэтая функцыя будзе лавіць памылкі ўжо ПАДЧАС працы праграмы
# def log_exception(exc_type, exc_value, exc_traceback):
#     with open("crash_log.txt", "a", encoding="utf-8") as f:
#         traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

# sys.excepthook = log_exception

# # Далей твой звычайны код запуску ( if __name__ == "__main__": ... )

import sys

from PySide6.QtWidgets import QApplication

from geodetic_app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
