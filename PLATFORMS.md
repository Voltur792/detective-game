# Поддержка платформ

Linux и macOS — **экспериментальные**. Проверки Python и автоматические тесты не заменяют проверку графики, звука и работы внутри Astra на реальной ОС. Windows сохраняет прежние возможности.

Официальные хосты Astra сейчас доступны для Windows x64 и Linux x64. Код подготовлен также под macOS, но официального хоста Astra для Mac и ARM пока нет: установить и полноценно проверить плагин там внутри Astra нельзя. См. [платформы Astra](https://github.com/mihailinl/AstraPlugins/blob/master/docs/en/1-orientation/platforms.md).

Игровые правила и сохранения не требуют Windows API. На Linux используется `$XDG_DATA_HOME/detective-game` (по умолчанию `~/.local/share/detective-game`), на macOS — `~/Library/Application Support/detective-game`. Существующие сохранения в прежней папке продолжают использоваться. `ASTRA_DETECTIVE_DATA_DIR` имеет приоритет. На Windows путь `%APPDATA%/detective-game` сохранён.
