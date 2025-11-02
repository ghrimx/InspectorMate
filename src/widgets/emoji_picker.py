# emoji_grid.py
from qtpy import QtWidgets, QtCore, QtGui


DEFAULT_EMOJIS = [
    "❗","‼️","❌","⁉️","❓",
    "✔️","✅","❎","🔻","🚩",
    "⚠️","🚧","💡","🚀","📢",
    "⛔","❤️","💥","👁️‍🗨️","⭐",
    "🟩","🟧","🟦","🟥","🟨",
    "🟢","🟠","🔵","🔴","🟡",
    "→","←","↔","📌","👉",
]


class EmojiGridWidget(QtWidgets.QWidget):
    emojiSelected = QtCore.pyqtSignal(str)  # Emits the emoji (string) when selected

    def __init__(self, emojis=None, rows=7, cols=5, emoji_size=24, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Emoji Picker")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.rows = rows
        self.cols = cols
        self.emoji_size = emoji_size
        self.emojis = (emojis or DEFAULT_EMOJIS)[: rows * cols]

        while len(self.emojis) < rows * cols:
            self.emojis.append(" ")

        self._buttons = []
        self._selected_btn = None

        self._build_ui()

    def _build_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        emoji_layout = QtWidgets.QGridLayout()
        emoji_layout.setContentsMargins(0, 0, 0, 0)
        vbox.addLayout(emoji_layout)

        index = 0
        for r in range(self.rows):
            for c in range(self.cols):
                emoji = self.emojis[index]
                btn = QtWidgets.QPushButton(emoji)
                btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
                btn.setAutoExclusive(True)  # only one selected at a time
                btn.setMinimumSize(self.emoji_size + 8, self.emoji_size + 8)
                btn.setMaximumSize(self.emoji_size + 8, self.emoji_size + 8)
                font = btn.font()
                font.setPointSize(int(self.emoji_size * 0.6))
                btn.setFont(font)

                # accessible name for testing/automation
                btn.setAccessibleName(f"emoji_btn_{index}")

                emoji_layout.addWidget(btn, r, c)
                btn.clicked.connect(self._make_on_click(emoji, btn))
                self._buttons.append(btn)
                index += 1

        self.label = QtWidgets.QLabel("Selected: None")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = self.label.font()
        font.setPointSize(14)
        self.label.setFont(font)
        vbox.addWidget(self.label)

        self.setLayout(vbox)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.emojiSelected.connect(self.on_select)

    def _make_on_click(self, emoji, btn):
        def on_click(checked=False):
            # btn.isChecked() is true because it's checkable & autoExclusive
            self._selected_btn: QtWidgets.QPushButton = btn
            self.emojiSelected.emit(emoji)
        return on_click
    
    def selectedEmoji(self):
        if self._selected_btn:
            return self._selected_btn.text()
        return None

    def selectEmoji(self, emoji: str) -> bool:
        """Programmatically select an emoji; returns True if found and selected."""
        btn: QtWidgets.QPushButton
        for btn in self._buttons:
            if btn.text() == emoji:
                self._selected_btn = btn
                self.emojiSelected.emit(emoji)
                return True
        return False

    def clearSelection(self):
        if self._selected_btn:
            # toggle off current (autoExclusive doesn't allow direct uncheck),
            # so temporarily disable exclusivity to uncheck.
            btn: QtWidgets.QPushButton
            for btn in self._buttons:
                btn.setAutoExclusive(False)
            self._selected_btn.setChecked(False)
            for btn in self._buttons:
                btn.setAutoExclusive(True)
            self._selected_btn = None

    def on_select(self, e):
        self.label.setText(f"Selected: {e}")
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(e)

