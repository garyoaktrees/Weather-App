from __future__ import annotations


def build_stylesheet(mode: str = "modern") -> str:
    if mode == "classic":
        return """
        QMainWindow {
            background-color: #0b2a57;
        }

        QWidget {
            color: white;
            font-family: Segoe UI, Arial, sans-serif;
            font-size: 14px;
        }

        QLineEdit {
            background-color: #000000;
            color: lime;
            border: 2px solid cyan;
            border-radius: 4px;
            padding: 10px 12px;
            font-size: 18px;
            font-weight: 800;
            font-family: "Courier New";
        }

        QPushButton {
            background-color: yellow;
            color: black;
            border: 2px solid #0b2f75;
            border-radius: 4px;
            padding: 10px 14px;
            font-size: 15px;
            font-weight: 900;
            font-family: "Courier New";
        }

        QPushButton:hover {
            background-color: #ffe15f;
        }

        QLabel#SectionTitle {
            font-size: 16px;
            font-weight: 900;
            color: #ffd400;
        }

        QPlainTextEdit {
            background-color: black;
            border: 3px solid cyan;
            color: cyan;
            border-radius: 4px;
            font-family: "Courier New";
            padding: 6px;
        }

        QDialog {
            background-color: #0b2a57;
        }

        QComboBox, QSlider, QCheckBox {
            color: white;
        }
        """

    return """
    QMainWindow {
        background-color: #0b1f3a;
    }

    QWidget {
        color: white;
        font-family: Segoe UI, Arial, sans-serif;
        font-size: 14px;
    }

    QLineEdit {
        background-color: rgba(16, 43, 82, 0.92);
        border: 2px solid #3f6fb6;
        border-radius: 10px;
        padding: 10px 12px;
        color: white;
        selection-background-color: #ffd400;
        selection-color: black;
        font-size: 16px;
        font-weight: 700;
    }

    QPushButton {
        background-color: #ffd400;
        color: #0b1f3a;
        border: none;
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 800;
    }

    QPushButton:hover {
        background-color: #ffe14d;
    }

    QLabel#SectionTitle {
        font-size: 16px;
        font-weight: 900;
        color: #ffd400;
    }

    QPlainTextEdit {
        background-color: rgba(16, 43, 82, 0.90);
        border: 1px solid #35598f;
        border-radius: 12px;
        color: white;
        padding: 8px;
    }

    QDialog {
        background-color: #0b1f3a;
    }

    QComboBox, QSlider, QCheckBox {
        color: white;
    }
    """