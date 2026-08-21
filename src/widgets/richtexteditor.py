from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtCore import pyqtSlot as Slot
from PyQt6.QtGui import (
    QColor,
    QFont,
    QTextCharFormat,
    QTextImageFormat,
)
from pyqt6_richtexteditor import RichTextEditManager, create_action

from common import SignageOrigin
from utilities.settings import get_settings
from utilities.utils import timeuuid


class RichTextEditor(RichTextEditManager):
    sigCreateSignage = Signal(str, object, str)

    def __init__(self, base_folder="", template_folder="", settings=None, parent=None):
        super().__init__(base_folder, template_folder, settings, parent)

        self.action_insertSignage = create_action(
            self,
            "insert_signage",
            ":signpost-line",
            "Insert Signage",
            "Ctrl+Alt+R",
            self.createSignage,
        )

        self.toolbar.insertAction(self.action_spacer, self.action_insertSignage)

    @Slot()
    def createSignage(self):
        textedit = self.active_mdi_child()
        if textedit is None:
            return

        title = textedit.textCursor().selectedText()
        anchor = str(timeuuid())
        source = SignageOrigin(
            get_settings().APP_NAME,
            "RichTextEditor",
            "RichTextEdit",
            textedit.userFriendlyFilename(),
            textedit.filepath(),
            anchor
        )
        self.sigCreateSignage.emit(title, source, anchor)

    def insertSignage(
        self,
        icon: str,
        color: str,
        signage_type: str,
        refkey: str,
        title: str,
        anchor: str,
    ):

        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref("")
        fmt.setAnchorNames([f"signage_type={signage_type}; id={anchor}", anchor])
        fmt.setForeground(QColor(color))
        fmt.setFontUnderline(False)
        fmt.setFontWeight(QFont.Weight.Bold)

        textedit = self.active_mdi_child()
        if textedit is None:
            return

        if icon != "":
            img = QTextImageFormat()
            img.setWidth(24.0)
            img.setHeight(24.0)
            img.setName(f"data:image/svg+xml;base64,{icon}")
            textedit.textCursor().insertImage(img)
            textedit.textCursor().insertText(f" {refkey} {title}", fmt)
        else:
            textedit.textCursor().insertText(f"{refkey} {title}", fmt)
