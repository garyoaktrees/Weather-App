from PySide6.QtWidgets import QLabel


class TickerWidget(QLabel):
    def __init__(self) -> None:
        super().__init__("Ticker placeholder")