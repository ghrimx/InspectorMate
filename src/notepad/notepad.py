import json
import enum
import logging
from pathlib import Path
from functools import partial
from datetime import datetime

from qtpy import (QtWidgets, QtCore, QtGui, Slot, Signal)

from database.database import AppDatabase
from common import Signage

from utilities.decorators import status_signal
from utilities.utils import (hexuuid, timeuuid, createFolder, html2pdf)
from utilities import config as mconf
from qt_theme_manager import theme_icon_manager

logger = logging.getLogger(__name__)


FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]


class ListStyle(enum.Enum):
    LIST1 = 1
    LIST2 = 2


class HeadingStyle(enum.Enum):
    P = 0
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


class LineSpacing(enum.Enum):
    NORMAL = 100
    NORMAL_HALF = 150
    DOUBLE = 200


class TableMimeType:
    # TODO
    def __init__(self):
        self._headers = []
        self._rows = []

    def convertBiff12(self, biff: str):
        data_list = [biff.split('\n') for x in biff.split('\t')]
        html_table = '<table>\n' + '\n'.join(['  <tr>' + ''.join(f'<td>{item}</td>' for item in row) + '</tr>' for row in data_list]) + '\n</table>'


class LinkEditor(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Link Editor")
        formlayout = QtWidgets.QFormLayout()
        self.setLayout(formlayout)

        self.display_text = QtWidgets.QLineEdit()
        self.url_link = QtWidgets.QLineEdit()

        formlayout.addRow(QtWidgets.QLabel("Text"), self.display_text)
        formlayout.addRow(QtWidgets.QLabel("Link"), self.url_link)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        formlayout.addRow(QtWidgets.QLabel(), self.buttonBox)


class LinkEditorDialog(QtWidgets.QDialog):
    """Dialog to insert or edit a hyperlink"""

    def __init__(self, parent=None, display_text="", href=""):
        super().__init__(parent)
        self.setWindowTitle("Edit Link" if href else "Insert Link")
        self.setMinimumWidth(430)

        # Save initial values
        self._orig_text = display_text or "link"
        self._orig_href = href.strip()

        self.url_radio = QtWidgets.QRadioButton("Web URL")
        self.file_radio = QtWidgets.QRadioButton("Local File")

        self.text_edit = QtWidgets.QLineEdit(self._orig_text)
        self.target_edit = QtWidgets.QLineEdit(self._orig_href)

        self.file_btn = QtWidgets.QPushButton("Browse…")

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # Display text
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Display Text:"))
        row.addWidget(self.text_edit)
        layout.addLayout(row)

        # Radio buttons
        r = QtWidgets.QHBoxLayout()
        r.addWidget(self.url_radio)
        r.addWidget(self.file_radio)
        layout.addLayout(r)

        # Target
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(QtWidgets.QLabel("Target:"))
        row2.addWidget(self.target_edit)
        row2.addWidget(self.file_btn)
        layout.addLayout(row2)

        layout.addWidget(btns)

        # Signals
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.url_radio.toggled.connect(self._on_mode_changed)
        self.file_btn.clicked.connect(self._browse_file)

        self._init_mode()

    def _init_mode(self):
        """
        Decide URL vs File mode based on the initial href.
        """
        href = self._orig_href.lower()

        # Check if it's likely a URL
        if href[:3] in ['htt', 'www']:
            self.url_radio.setChecked(True)
            self.file_btn.setEnabled(False)
        else:
            # Likely a local file path or file:// url
            self.file_radio.setChecked(True)
            self.file_btn.setEnabled(True)

    def _on_mode_changed(self, checked: bool):
        """
        Enable/disable file picker when switching modes.
        """
        if checked:
            # URL mode
            self.file_btn.setEnabled(False)
            self.target_edit.setPlaceholderText("https://example.com")
        else:
            # File mode
            self.file_btn.setEnabled(True)
            self.target_edit.setPlaceholderText("Choose a file...")

    def _browse_file(self):
        """
        File chooser for local paths.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File")
        if path:
            self.target_edit.setText(path)

    def get_link_html(self):
        """
        Returns:
            <a href="href">text</a>
        """
        from pathlib import Path
        from urllib import parse
        text = self.text_edit.text().strip() or self._orig_text or "link"
        raw_target = self.target_edit.text().strip()

        # Convert local file path to file:// URL
        if self.file_radio.isChecked():
            try:
                href = Path(raw_target).absolute().as_uri()
            except Exception:
                # Fallback: treat as literal path
                href = "file://" + parse.quote(raw_target)
        else:
            href = raw_target

        return f'<a href="{href}">{text}</a>'

    def get_link_markdown(self):
        """
        Returns:
            [text](href)
        """
        text = self.text_edit.text().strip() or "link"
        href = self.target_edit.text().strip()
        return f"[{text}]({href})"


class TextEdit(QtWidgets.QTextEdit):

    def __init__(self, filename=str, text=str, parent=None):
        super(TextEdit, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAutoFormatting(QtWidgets.QTextEdit.AutoFormattingFlag.AutoAll)
 
        self.filename: str = filename
        base_url = QtCore.QUrl.fromLocalFile(AppDatabase.activeWorkspace().notebook_path + "/")
        self.document().setBaseUrl(base_url)

        self.search_text: str = ""
        self.zoom_factor = 0 #TEST

        # Initialize default font size.
        self.base_fontsize = 12
        font : QtGui.QFont = self.document().defaultFont()
        font.setPointSize(self.base_fontsize)
        self.document().setDefaultFont(font)

        self.setHtml(text)

        self._cursor = self.textCursor()

        self.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse | 
                                     QtCore.Qt.TextInteractionFlag.TextEditorInteraction)
        self.document().setModified(False)
        self.setWindowTitle(QtCore.QFileInfo(self.filename).fileName()[:30])
        self.setObjectName(self.userFriendlyFilename())

        self.connectSignals()

    def mouseMoveEvent(self, e):
        self.anchor = self.anchorAt(e.pos())
        if self.anchor:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        else:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.ArrowCursor)
        return super().mouseMoveEvent(e)
    
    def mouseReleaseEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.anchor:
                status_signal.status_message.emit("Trying to open the link...", 3000)
                if QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.anchor)):
                    status_signal.status_message.emit("Link opened", 3000)
                else:
                    status_signal.status_message.emit("⚠️ Failed to open the link!", 3000)
                self.anchor = None
        return super().mouseReleaseEvent(e)
    
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        """Supplemented the standard context menu"""
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(QtGui.QAction(QtGui.QIcon(), "Paste as Table", self, triggered=self.pasteTable))
        menu.addAction(QtGui.QAction(QtGui.QIcon(), "Paste Text Only", self, triggered=self.pasteTextOnly))
        menu.exec(event.globalPos())

    def userFriendlyFilename(self):
        return QtCore.QFileInfo(self.filename).fileName()
    
    def cursor_position_changed(self):
        self._cursor: QtGui.QTextCursor = self.textCursor()

    def connectSignals(self):
        self.cursorPositionChanged.connect(self.cursor_position_changed)
        self.textChanged.connect(self.save)

    def convertBiff12(self, biff: str) -> list:
        """Convert a string to nested list"""
        table_content = [x.split('\t') for x in biff.split('\n')]
        return table_content
    
    def setTitle(self, title: str):
        self.setDocumentTitle(title)
        cursor = self.textCursor()
        cursor.setPosition(0)
        cursor.insertText(title)
        self.textHeading(HeadingStyle.H1)
    
    def pasteTable(self):
        """Insert table from Clipboard"""
        cursor = self.textCursor()
        source = QtWidgets.QApplication.clipboard().text()

        # Normalize line endings and strip trailing spaces
        source = source.replace('\r\n', '\n').replace('\r', '\n').strip()
        if not source:
            return  # Nothing to paste

        # Convert the clipboard text into a 2D list
        table_content = self.convertBiff12(source)  # You already have this function
        if not table_content:
            return
        
        while table_content and all(not cell.strip() for cell in table_content[-1]):
            table_content.pop()
        
        if not table_content:
            return

        # Ensure all rows have the same number of columns (pad empty cells)
        max_cols = max(len(row) for row in table_content)
        for row in table_content:
            while len(row) < max_cols:
                row.append("")  # Fill missing cells with empty string

        rows, cols = len(table_content), max_cols

        # Create the table format
        table_fmt = QtGui.QTextTableFormat()
        table_fmt.setCellPadding(3.0)
        table_fmt.setCellSpacing(0)
        table_fmt.setBorder(0.5)
        table_fmt.setBorderStyle(QtGui.QTextFrameFormat.BorderStyle.BorderStyle_Solid)
        table_fmt.setBorderBrush(QtCore.Qt.GlobalColor.black)
        table_fmt.setBorderCollapse(False)

        # Insert table
        table = cursor.insertTable(rows, cols, table_fmt)

        # Fill table cells
        for r, row in enumerate(table_content):
            for c, value in enumerate(row):
                cell_cursor = table.cellAt(r, c).firstCursorPosition()
                cell_cursor.insertText(str(value))

    def pasteTextOnly(self):
        clipboard = QtWidgets.QApplication.clipboard()
        text = clipboard.text()  # Plain text only
        self.insertPlainText(text)
    
    def canInsertFromMimeData(self, source: QtCore.QMimeData):
        if source.hasImage():
            return source.hasImage()
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)   

    def _persist_image(self, image: QtGui.QImage) -> str:
        image_dir = f"{AppDatabase.activeWorkspace().notebook_path}/.images"
        dir_path: Path = createFolder(image_dir)

        filename = f"{hexuuid()}.png"
        path = dir_path.joinpath(filename).as_posix()

        image.save(path, "PNG")
        return path
    
    def _insert_image_from_file(self, image_path: str, caption: str = ""):
        url = QtCore.QUrl.fromLocalFile(image_path).toString()
        html = f"<img src='{url}'>"
        if caption:
            html = html + f'<p>{caption}</p>'
        self.textCursor().insertHtml(html)

    def insertFromMimeData(self, source: QtCore.QMimeData):
        
        # Image + URL > link image to file
        if source.hasImage() and source.hasUrls():
            
            caption = source.text()
            url = source.urls()[0]
            image = source.imageData()
            image_path = self._persist_image(image)
            href = url.toString()          

            if source.hasFormat("application/x-inspectormate-anchor"):
                anchor = json.loads(
                    bytes(source.data("application/x-inspectormate-anchor"))
                )
                page = anchor.get("page", "?")
                hlink = f'<a href="{href}#page={page}">{caption}</a>'
            else:
                hlink = f'<a href="{href}">{caption}</a>'

            if url.isLocalFile():
                self._insert_image_from_file(image_path, hlink)
                return
            
        # HTML already present > let Qt handle it
        if source.hasHtml():
            super().insertFromMimeData(source)
            return

        # Image only > persist and link
        if source.hasImage():
            image = source.imageData()
            path = self._persist_image(image)
            self._insert_image_from_file(path)
            return

        # Fallback
        super().insertFromMimeData(source)

    def closeEvent(self, event):
        if self.zoom_factor != 0:
            self.resetZoom()

        if self.document().isModified():
            err = self.save()

            if err is not None:
                QtWidgets.QMessageBox.warning(self,
                                              "RichTextEditor -- Save Error",
                                              f"Failed to save {self.filename}: {err}")

    def isModified(self):
        return self.document().isModified()

    def save(self) -> Exception | bool:
        try:
            fh = QtCore.QFile(self.filename)
            if not fh.open(QtCore.QIODevice.OpenModeFlag.WriteOnly):
                err = IOError(fh.errorString())
                logger.error(f"Failed to open '{self.filename}': {err}")
            stream = QtCore.QTextStream(fh)
            stream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            stream << self.toHtml()
        except EnvironmentError as e:
            logger.error(f"RichTextEditor -- Save Error:\nFailed to save {self.filename}: {e}")
            return e
        finally:
            self.document().setModified(False)
            return None

    def merge_format_on_word_or_selection(self, fmt: QtGui.QTextCharFormat):
        if not self._cursor.hasSelection():
            self._cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)

        self._cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def merge_format_on_line_or_selection(self, fmt: QtGui.QTextCharFormat):
        if not self._cursor.hasSelection():
            self._cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)

        self._cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)
        self._cursor.clearSelection()

    @classmethod
    def load(cls, filename: str):
        fh = None
        try:
            fh = QtCore.QFile(filename)
            if not fh.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
                logger.error(f"RichTextEditor -- Open Error:\nFailed to open {filename}: {IOError(fh.errorString())}")
                QtWidgets.QMessageBox.warning(cls,
                                              "RichTextEditor -- Open Error",
                                              f"Failed to open {cls.filename}: {IOError(fh.errorString())}")
                return
            stream = QtCore.QTextStream(fh)
            stream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            text = stream.readAll()
        except EnvironmentError as e:
            QtWidgets.QMessageBox.warning(cls,
                                          "RichTextEditor -- Load Error",
                                          f"Failed to load {filename}: {e}")
            return
        finally:
            if fh is not None:
                fh.close()
            return cls(filename, text)
    
    @Slot()
    def textBold(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        weight = QtGui.QFont.Weight.Bold if cursor.charFormat().fontWeight() == QtGui.QFont.Weight.Normal else QtGui.QFont.Weight.Normal
        fmt.setFontWeight(weight)
        self.merge_format_on_word_or_selection(fmt)
    
    @Slot()
    def textItalic(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontItalic() else True
        fmt.setFontItalic(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def textUnderline(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontUnderline() else True
        fmt.setFontUnderline(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def textStrikeout(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontStrikeOut() else True
        fmt.setFontStrikeOut(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def textSize(self, p):
        font_size = float(p)
        if font_size > 0:
            fmt = QtGui.QTextCharFormat()
            fmt.setFontPointSize(font_size)
            self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def insertDate(self):
        today = datetime.now().strftime("%d-%m-%Y")
        self._cursor.insertText(today)
    
    @Slot()
    def insertTime(self):
        now = datetime.now().strftime("%H:%M:%S")
        self._cursor.insertText(now)

    @Slot()
    def textHeading(self, style):
        cursor = self._cursor

        cursor.beginEditBlock()

        block_fmt = cursor.blockFormat()

        if isinstance(style, HeadingStyle):
            block_fmt.setObjectIndex(-1)
            block_fmt.setHeadingLevel(style.value)
            cursor.setBlockFormat(block_fmt)
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QColor("#0055ff"))
            fmt.setFontWeight(QtGui.QFont.Weight.Bold if style.value > 0 else QtGui.QFont.Weight.Normal)
            fmt.setProperty(QtGui.QTextFormat.Property.FontSizeAdjustment, 4 - style.value if style.value > 0 else 0)
            self.merge_format_on_line_or_selection(fmt)

        cursor.endEditBlock()
    
    @Slot()
    def textHighlight(self):
        color = QtWidgets.QColorDialog.getColor(self.textColor(), self)
        if not color.isValid():
            return

        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(color)
        self.merge_format_on_word_or_selection(fmt)

        self.setFocus()

    @Slot()
    def quickHighlight(self):
        cursor = self._cursor
        color = QtGui.QColor("#ffcccc")

        cursor.beginEditBlock()

        if self.currentCharFormat().background().color() == QtGui.QColor("#ffcccc"):
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(QtCore.Qt.GlobalColor.transparent)
            self.merge_format_on_line_or_selection(fmt)
        else:
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(color)
            self.merge_format_on_line_or_selection(fmt)

        cursor.endEditBlock()

    @Slot()
    def bulletList(self):
        cursor = self._cursor
        marker = QtGui.QTextBlockFormat.MarkerType.NoMarker

        if cursor.currentList():
            style = cursor.currentList().format().style()
        else:
            style = QtGui.QTextListFormat.Style.ListDisc

        cursor.beginEditBlock()
        block_fmt = cursor.blockFormat()

        block_fmt.setMarker(marker)
        cursor.setBlockFormat(block_fmt)
        list_fmt = QtGui.QTextListFormat()
        if cursor.currentList():
            list_fmt = cursor.currentList().format()
        else:
            list_fmt.setIndent(block_fmt.indent() + 1)
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
        list_fmt.setStyle(style)
        cursor.createList(list_fmt)

        cursor.endEditBlock()

    @Slot()
    def addCheckbox(self):
        cursor = self._cursor
        marker = QtGui.QTextBlockFormat.MarkerType.Unchecked

        if cursor.currentList():
            style = cursor.currentList().format().style()
        else:
            style = QtGui.QTextListFormat.Style.ListDisc

        cursor.beginEditBlock()
        block_fmt = cursor.blockFormat()

        block_fmt.setMarker(marker)
        cursor.setBlockFormat(block_fmt)
        list_fmt = QtGui.QTextListFormat()
        if cursor.currentList():
            list_fmt = cursor.currentList().format()
        else:
            list_fmt.setIndent(block_fmt.indent() + 1)
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
        list_fmt.setStyle(style)
        cursor.createList(list_fmt)

        cursor.endEditBlock()

    @Slot()
    def setLineSpacing(self, spacing: LineSpacing):
        cursor = self._cursor

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.BlockUnderCursor)

        block_fmt = cursor.blockFormat()
        block_char_fmt = cursor.blockCharFormat()

        cursor.beginEditBlock()
        block_fmt.setLineHeight(spacing.value, QtGui.QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)

        cursor.mergeBlockCharFormat(block_char_fmt)
        cursor.mergeBlockFormat(block_fmt)
        cursor.endEditBlock()
    
    @Slot()
    def clearFormatting(self):
        cursor = self._cursor

        default_format = QtGui.QTextCharFormat()
        block_format = QtGui.QTextBlockFormat()

        cursor.beginEditBlock()

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
            cursor_frame = cursor.currentFrame()

            if cursor_frame.parentFrame() is not None:
                cursor.select(QtGui.QTextCursor.SelectionType.BlockUnderCursor)
                cursor.setBlockFormat(block_format)
                start = cursor.selectionStart()
                selected_text = cursor.selectedText()
                cursor.removeSelectedText()
                cursor.setPosition(start, QtGui.QTextCursor.MoveMode.MoveAnchor)
                cursor.insertText(selected_text, QtGui.QTextCharFormat())

        cursor.setCharFormat(default_format)
        cursor.setBlockFormat(block_format)
        cursor.endEditBlock()
        cursor.clearSelection()

    @Slot()
    def insertBlockquote(self):
        cursor = self._cursor

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.BlockUnderCursor)

        cursor.beginEditBlock()

        tablefmt = QtGui.QTextTableFormat()
        tablewidth = QtGui.QTextLength(QtGui.QTextLength.Type.VariableLength, 100.0)
        tablefmt.setColumnWidthConstraints([tablewidth])
        tablefmt.setCellPadding(10.0)
        tablefmt.setBackground(QtGui.QColor("#e6f2ff"))
        tablefmt.setBorderStyle(QtGui.QTextFrameFormat.BorderStyle.BorderStyle_None)
        tablefmt.setBorderCollapse(False)
 
        table = cursor.insertTable(1, 1, tablefmt)

        cellfmt = QtGui.QTextTableCellFormat()
        cellfmt.setBackground(QtGui.QColor("#e6f2ff"))
        cellfmt.setPadding(10.0)
        table.cellAt(0, 0).setFormat(cellfmt)
 
        cursor.endEditBlock()

    @Slot()
    def addHorizontalLine(self):
        cursor = self._cursor
        if not cursor.hasSelection():
            # Select the current line if no text is selected
            cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)

        selected_text = cursor.selectedText()

        hr = '<hr style="height:0px; border:1px solid gray; border-width: 100%;" />'

        if selected_text.strip() == "":
            cursor.insertHtml(hr)
        else:
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfLine, QtGui.QTextCursor.MoveMode.MoveAnchor, 1)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down, QtGui.QTextCursor.MoveMode.MoveAnchor, 1)
            cursor.insertHtml(hr)

    @Slot()
    def text_color(self):
        color = QtWidgets.QColorDialog.getColor(self.textColor(), self)
        if not color.isValid():
            return

        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(color)
        self.merge_format_on_word_or_selection(fmt)
        self.color_changed(color)

    def color_changed(self, c):
        pix = QtGui.QPixmap(16, 16)
        pix.fill(c)
        # self.color_action.setIcon(QtGui.QIcon(pix))

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        #Zoom : CTRL + wheel
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_factor += 1
                self._update_font_sizes()
            else:
                self.zoom_factor -= 1
                self._update_font_sizes()
        else:
            super().wheelEvent(event)

    def _update_font_sizes(self):
        """Update font sizes for all text elements in the document."""
        scale_factor = max(1, self.base_fontsize + self.zoom_factor * 2)  # Adjust scale dynamically

        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.Document)
        char_format = QtGui.QTextCharFormat()
        char_format.setFontPointSize(scale_factor)
        cursor.mergeCharFormat(char_format)

        font = self.document().defaultFont()
        font.setPointSize(scale_factor)
        self.document().setDefaultFont(font)

    def resetZoom(self):
        # reset zoom
        self.zoom_factor = 0
        font = self.document().defaultFont()
        font.setPointSize(12)
        self.document().setDefaultFont(font)
        self._update_font_sizes()

    def findNext(self):
        self.findText(forward=True)

    def findPrev(self):
        self.findText(forward=False)

    def findText(self, forward=True):
        text = self.search_text
        if not text:
            return

        flags = self.document().FindFlag(0)
        if not forward:
            flags |= QtGui.QTextDocument.FindFlag.FindBackward

        found = self.find(text, flags)
        if not found:
            # wrap around
            cursor = self.textCursor()
            if forward:
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
            else:
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            found = self.find(text, flags)

    def highlightFoundAll(self):
        """Highlight all occurrences of the search term."""
        text = self.search_text
        extra_selections = []

        if text:
            # Highlight format
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(QtGui.QColor("yellow"))
            fmt.setForeground(theme_icon_manager.get_theme_color())

            cursor = self.document().find(text, 0)
            while not cursor.isNull():
                selection = QtWidgets.QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = fmt
                extra_selections.append(selection)
                cursor = self.document().find(text, cursor)

        self.setExtraSelections(extra_selections)


class Notebook(QtWidgets.QWidget):
    sigCreateSignage = Signal(str, str, str)

    class LayoutStrategy(enum.Enum):
        Cascade = 0
        Tile = 1
        Tabbed = 2

    layout_strategy: LayoutStrategy = LayoutStrategy.Cascade.name

    def __init__(self, parent=None):
        super().__init__(parent)

        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        # MdiArea
        self.mdi = QtWidgets.QMdiArea()
        self.mdi.setTabsMovable(True)
        self.mdi.setTabsClosable(True)
        
        self.createActions()
        self.createToolbar()
        self.createShortcuts()
        
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.mdi)

        QtCore.QTimer.singleShot(0, self.loadFiles)
        self.loadSettings()

        self.mdi.subWindowActivated.connect(self.onSubWindowActivated)

    def createActions(self):
        self.action_addnote = QtGui.QAction(theme_icon_manager.get_icon(':file_add'), "Add note (Ctrl+N)", self, triggered=self.addNote)
        self.action_editnote = QtGui.QAction(theme_icon_manager.get_icon(':file-edit-line'), "Edit note (Ctrl+O)", self, triggered=self.editNote)

        self.action_minimizeAll = QtGui.QAction(theme_icon_manager.get_icon(':folder-2-line'), "Minimize", self, triggered=self.minimizeAll)
        self.action_showNormalAll = QtGui.QAction(theme_icon_manager.get_icon(':folder-2-line'), "Normal", self, triggered=self.showNormalAll)
        self.action_showMaximizeAll = QtGui.QAction(theme_icon_manager.get_icon(':folder-2-line'), "Maximized", self, triggered=self.showMaximizeAll)
        self.action_setTileView = QtGui.QAction(theme_icon_manager.get_icon(':layout-grid-line'), "Tile", self, triggered=self.setTileView)
        self.action_setTabbedView = QtGui.QAction(theme_icon_manager.get_icon(':folder-2-line'), "Tabbed", self, triggered=self.setTabbedView)

        self.action_close = QtGui.QAction("Cl&ose", self, statusTip="Close the active window", triggered=self.close)
        self.action_closeall = QtGui.QAction("Close &All", self, statusTip="Close all the windows", triggered=self.close_all)

        # Text actions
        self.action_bold = QtGui.QAction(theme_icon_manager.get_icon(':bold'), "Bold (Ctrl+B)", self, triggered=self.textBold ,checkable=True)
        self.action_italic =  QtGui.QAction(theme_icon_manager.get_icon(':italic'), "Italic (Ctrl+I)", self, triggered=self.textItalic, checkable=True)
        self.action_underline = QtGui.QAction(theme_icon_manager.get_icon(':underline'), "Underline (Ctrl+U)", self, triggered=self.textUnderline, checkable=True)
        self.action_strikeout = QtGui.QAction(theme_icon_manager.get_icon(':strikeout'), "StrikeOut (Ctrl+-)", self, triggered=self.textStrikeout, checkable=True)

        # Date/Time
        self.action_date = QtGui.QAction(theme_icon_manager.get_icon(":calendar-line"), "Date (Ctrl+Alt+D)", self, triggered=self.insertDate)
        self.action_time = QtGui.QAction(theme_icon_manager.get_icon(":time-line"), "Time (Ctrl+Alt+T)", self, triggered=self.insertTime)

        # Headings
        self.action_paragraph = QtGui.QAction(theme_icon_manager.get_icon(":paragraph"), "Paragraph", self, triggered = lambda:self.textHeading(HeadingStyle.P))
        self.action_h1 = QtGui.QAction(theme_icon_manager.get_icon(":h-1"), "Heading 1", self, triggered = lambda:self.textHeading(HeadingStyle.H1))
        self.action_h2 = QtGui.QAction(theme_icon_manager.get_icon(":h-2"), "Heading 2", self, triggered = lambda:self.textHeading(HeadingStyle.H2))
        self.action_h3 = QtGui.QAction(theme_icon_manager.get_icon(":h-3"), "Heading 3", self, triggered = lambda:self.textHeading(HeadingStyle.H3))
        self.action_h4 = QtGui.QAction(theme_icon_manager.get_icon(":h-4"), "Heading 4", self, triggered = lambda:self.textHeading(HeadingStyle.H4))

        # Highlight
        self.action_highlight = QtGui.QAction(theme_icon_manager.get_icon(":mark_pen"), "Highlight (Ctrl+Alt+H)", self, triggered= self.textHighlight)

        # Quoteblock
        self.action_blockquote = QtGui.QAction(theme_icon_manager.get_icon(':double-quotes'), "Block quote (Ctrl+Alt+B)", self, triggered=self.insertBlockquote)       

        # Horizontal line
        self.action_horizontal_line = QtGui.QAction(theme_icon_manager.get_icon(':horizontal-line'), "Horizontal line (Ctrl+Alt+L)", self, triggered=self.addHorizontalLine)

        # Clear formatting
        self.action_clear_formatting = QtGui.QAction(theme_icon_manager.get_icon(':format-clear'), "Clear formatting (Ctrl+Shift+N)", self, triggered=self.clearFormatting)

        pix = QtGui.QPixmap(16, 16)
        pix.fill(QtCore.Qt.GlobalColor.black)
        self.action_color = QtGui.QAction(QtGui.QIcon(pix),"Color Text", self, triggered=self.textColor)

        # Bullet List
        self.action_bullet = QtGui.QAction(theme_icon_manager.get_icon(":list-unordered"), "Bullet list (Ctrl+;)", self, triggered=self.bulletList)

        # Checkbox
        self.action_checkbox = QtGui.QAction(theme_icon_manager.get_icon(":list-check-3"), "Checkbox (Ctrl+Alt+;)", self, triggered=self.addCheckbox)

        # Line Spacing
        self.action_line_spacing_normal = QtGui.QAction("1.0", self, triggered=lambda: self.setLineSpacing(LineSpacing.NORMAL))
        self.action_line_spacing_1_5 = QtGui.QAction("1.5", self, triggered=lambda: self.setLineSpacing(LineSpacing.NORMAL_HALF))
        self.action_line_spacing_double = QtGui.QAction("2.0", self, triggered=lambda: self.setLineSpacing(LineSpacing.DOUBLE))

        # Link
        self.action_edit_link = QtGui.QAction(theme_icon_manager.get_icon(":link-m"),
                                              "Insert link (Ctrl+Alt+K)",
                                              self,
                                              triggered=self.editLink)

        self.action_insertSignage = QtGui.QAction(theme_icon_manager.get_icon(':signpost-line'),
                                                  "Insert Signage",
                                                  self,
                                                  triggered=self.createSignage)

        self.action_export2pdf = QtGui.QAction(theme_icon_manager.get_icon(':share-forward-2-line'),
                                               "Export to PDF",
                                               self,
                                               triggered=self.export2pdf)

        self.action_help = QtGui.QAction(theme_icon_manager.get_icon(':question-line'), "Help", self, triggered=self.helpClicked, checkable=False)



    def createToolbar(self):
        self.toolbar = QtWidgets.QToolBar(self)

        # View menu
        viewmenu_toolbutton = QtWidgets.QToolButton(self)
        viewmenu_toolbutton.setIcon(theme_icon_manager.get_icon(':eye-line'))
        viewmenu_toolbutton.setText("Views")
        viewmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        viewmenu = QtWidgets.QMenu("View", self)

        cascade_menu = QtWidgets.QMenu("Cascade", self)
        cascade_menu.setIcon(theme_icon_manager.get_icon(':stack-line'))
        cascade_menu.addAction(self.action_minimizeAll)
        cascade_menu.addAction(self.action_showNormalAll)
        cascade_menu.addAction(self.action_showMaximizeAll)
        viewmenu.addMenu(cascade_menu)

        viewmenu.addAction(self.action_setTileView)
        viewmenu.addAction(self.action_setTabbedView)
        viewmenu_toolbutton.setMenu(viewmenu)
        
        # Window selection menu
        self.window_menu = QtWidgets.QMenu("Window", self)

        self.windowmenu_toolbutton = QtWidgets.QToolButton(self)
        self.windowmenu_toolbutton.setIcon(theme_icon_manager.get_icon(':window-2-line'))
        self.windowmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.windowmenu_toolbutton.setMenu(self.window_menu)
        self.update_window_menu()
        self.window_menu.aboutToShow.connect(self.update_window_menu)
        
        # DateTime menu
        self.datetime_menu = QtWidgets.QMenu(self)
        self.datetime_menu.addAction(self.action_date)
        self.datetime_menu.addAction(self.action_time)
        self.datetime_toolbutton = QtWidgets.QToolButton(self)
        self.datetime_toolbutton.setIcon(theme_icon_manager.get_icon(":calendar-schedule-line"))
        self.datetime_toolbutton.setToolTip("Insert date/time")
        self.datetime_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)       
        self.datetime_toolbutton.setMenu(self.datetime_menu)

        # Headings menu
        self.heading_toolbutton = QtWidgets.QToolButton(self)
        self.heading_toolbutton.setText("Headings")
        self.heading_toolbutton.setIcon(theme_icon_manager.get_icon(":heading"))
        self.heading_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        self.heading_menu = QtWidgets.QMenu(self)
        self.heading_menu.addAction(self.action_paragraph)
        self.heading_menu.addAction(self.action_h1)
        self.heading_menu.addAction(self.action_h2)
        self.heading_menu.addAction(self.action_h3)
        self.heading_menu.addAction(self.action_h4)
        self.heading_toolbutton.setMenu(self.heading_menu)

        # Line Spacing
        self.line_spacing_toolbutton = QtGui.QAction(self)
        self.line_spacing_toolbutton.setText("Line Spacing")
        self.line_spacing_toolbutton.setToolTip("Line Spacing")
        self.line_spacing_toolbutton.setIcon(theme_icon_manager.get_icon(":line-height"))

        self.line_spacing_menu = QtWidgets.QMenu("Line spacing", self)
        self.line_spacing_menu.addAction(self.action_line_spacing_normal)
        self.line_spacing_menu.addAction(self.action_line_spacing_1_5)
        self.line_spacing_menu.addAction(self.action_line_spacing_double)
        self.line_spacing_toolbutton.setMenu(self.line_spacing_menu)
        
        # Add to Toolbar
        self.toolbar.addAction(self.action_addnote)
        self.toolbar.addAction(self.action_editnote)
        self.toolbar.addWidget(viewmenu_toolbutton)
        self.toolbar.addWidget(self.windowmenu_toolbutton)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_bold)
        self.toolbar.addAction(self.action_italic)
        self.toolbar.addAction(self.action_underline)
        self.toolbar.addAction(self.action_strikeout)
        self.toolbar.addAction(self.action_clear_formatting)
        self.toolbar.addWidget(self.heading_toolbutton)
        self.toolbar.addAction(self.action_highlight)
        self.toolbar.addAction(self.action_color)
        self.toolbar.addAction(self.line_spacing_toolbutton)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.datetime_toolbutton)
        self.toolbar.addAction(self.action_horizontal_line)
        self.toolbar.addAction(self.action_blockquote)
        self.toolbar.addAction(self.action_bullet)
        self.toolbar.addAction(self.action_checkbox)
        self.toolbar.addAction(self.action_edit_link)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_insertSignage)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_export2pdf)

        spacer = QtWidgets.QWidget(self)
        spacer.setContentsMargins(0,0,0,0)
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.action_spacer = self.toolbar.addWidget(spacer)

        # Search widget
        self.search_widget = QtWidgets.QLineEdit()
        self.search_widget.setPlaceholderText("Search...")
        self.search_widget.setFixedWidth(180)
        self.search_widget.textChanged.connect(self.searchText)

        self.toolbar.addWidget(self.search_widget)
        self.toolbar.addAction(self.action_help)
    
    def createShortcuts(self):
        self.shortcut_add_note = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"), self, self.addNote, ambiguousMember=self.addNote, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_edit_note = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), self, self.editNote, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_quick_highlight = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+H"), self, self.quickHighlight, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_date = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+D"), self, self.insertDate, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_time = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+T"), self, self.insertTime, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_h1 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+1"), self, lambda:self.textHeading(HeadingStyle.H1), ambiguousMember=lambda:self.textHeading(HeadingStyle.H1), context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_h2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+2"), self, lambda:self.textHeading(HeadingStyle.H2), ambiguousMember=lambda:self.textHeading(HeadingStyle.H2),context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_h3 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+3"), self, lambda:self.textHeading(HeadingStyle.H3), ambiguousMember=lambda:self.textHeading(HeadingStyle.H3),context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_h4 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+4"), self, lambda:self.textHeading(HeadingStyle.H4), ambiguousMember=lambda:self.textHeading(HeadingStyle.H4),context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_P = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+P"), self, lambda:self.textHeading(HeadingStyle.P), ambiguousMember=lambda:self.textHeading(HeadingStyle.P), context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_signage = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+R"), self, self.createSignage, ambiguousMember=self.createSignage, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_clearformatting = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+N"), self, self.clearFormatting, ambiguousMember=self.clearFormatting, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_blockquote = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+B"), self, self.insertBlockquote, ambiguousMember=self.insertBlockquote, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_blod = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+B"), self, self.textBold, ambiguousMember=self.textBold, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_italic = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+I"), self, self.textItalic, ambiguousMember=self.textItalic, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_strikeout = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self, self.textStrikeout, ambiguousMember=self.textStrikeout, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_underline = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+U"), self, self.textUnderline, ambiguousMember=self.textUnderline, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_insertLine = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+L"), self, self.addHorizontalLine, ambiguousMember=self.addHorizontalLine, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_bulletList = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+;"), self, self.bulletList, ambiguousMember=self.bulletList, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_checkbox = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+;"), self, self.addCheckbox, ambiguousMember=self.addCheckbox, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_link = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+K"), self, self.editLink, ambiguousMember=self.editLink, context=QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)

    @Slot()
    def onSubWindowActivated(self):
        active_sub_window = self.mdi.activeSubWindow()
        
        if active_sub_window is None:
            return
        
        current_textedit: TextEdit = active_sub_window.widget()

        self.search_widget.setText(current_textedit.search_text)

    @Slot()
    def update_window_menu(self):
        self.window_menu.clear()
        self.window_menu.addAction(self.action_close)
        self.window_menu.addAction(self.action_closeall)
        self.window_menu.addSeparator()

        windows = self.mdi.subWindowList()
        
        for i, window in enumerate(windows):
            child: TextEdit = window.widget()

            f = child.userFriendlyFilename()
            text = f'{i + 1} {f}'
            if i < 9:
                text = '&' + text

            action = self.window_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(window is self.mdi.activeSubWindow())
            slot_func = partial(self.set_active_sub_window, window=window)
            action.triggered.connect(slot_func)

    def set_active_sub_window(self, window):
        if window:
            self.mdi.setActiveSubWindow(window)

    def close(self):
        active_sub_window = self.mdi.activeSubWindow()
        
        if active_sub_window is None:
            return
        
        current_textedit: TextEdit = active_sub_window.widget()

        err = current_textedit.save()
        if err:
            return

        self.mdi.closeActiveSubWindow()

    def close_all(self):
        err = self.saveAll()

        if err:
            return

        self.saveSettings()
        self.mdi.closeAllSubWindows()
    
    def saveSettings(self):
        # Save opened files
        files = []
        for subwindows in self.mdi.subWindowList():
            textedit: TextEdit = subwindows.widget()
            files.append(textedit.filename)

        mconf.settings.beginGroup("notepad")
        mconf.settings.setValue("NotebookCurrentFiles", files)

        # Save layout strategy
        mconf.settings.setValue("LayoutStrategy", self.layout_strategy.name)
        mconf.settings.endGroup()
    
    def loadSettings(self):
        # Restore layout strategy
        mconf.settings.beginGroup("notepad")
        try:
            layout_strategy = mconf.settings.value("LayoutStrategy", self.layout_strategy, str)
        except:
            layout_strategy = self.LayoutStrategy.Cascade.name

        if layout_strategy == self.LayoutStrategy.Cascade.name:
            self.setCascadeView()
        elif layout_strategy == self.LayoutStrategy.Tile.name:
            self.setTileView()
        elif layout_strategy == self.LayoutStrategy.Tabbed.name:
            self.setTabbedView()
        mconf.settings.endGroup()

    def loadfile(self, filename, title: str = "", anchor: str = ""):
        for subwindow in self.mdi.subWindowList():
            textedit: TextEdit = subwindow.widget()
            if textedit.filename == filename:
                self.mdi.setActiveSubWindow(subwindow)
                textedit.scrollToAnchor(anchor)
                return

        textedit = TextEdit.load(filename)
        if textedit is not None:
            textedit.currentCharFormatChanged.connect(self.updateToolbarState)
            subwindow = self.mdi.addSubWindow(textedit)
            subwindow.show()

        if title != "":
            textedit.setTitle(QtCore.QFileInfo(title).completeBaseName())

        textedit.scrollToAnchor(anchor)
    
    def active_mdi_child(self) -> TextEdit:
        active_sub_window = self.mdi.activeSubWindow()
        if active_sub_window:
            return active_sub_window.widget()
        return None
    
    @Slot(QtGui.QTextCharFormat)
    def updateToolbarState(self, fmt: QtGui.QTextCharFormat):
        font = fmt.font()
        self.action_bold.setChecked(font.bold())
        self.action_italic.setChecked(font.italic())
        self.action_underline.setChecked(font.underline())
        self.action_strikeout.setChecked(font.strikeOut())
        
        color = fmt.foreground().color()
        pix = QtGui.QPixmap(16, 16)
        pix.fill(color)
        self.action_color.setIcon(QtGui.QIcon(pix))

    @Slot()
    def textBold(self):
        if self.active_mdi_child():
            self.active_mdi_child().textBold()
    
    @Slot()
    def textItalic(self):
        if self.active_mdi_child():
            self.active_mdi_child().textItalic()

    @Slot()
    def textStrikeout(self):
        if self.active_mdi_child():
            self.active_mdi_child().textStrikeout()

    @Slot()
    def textUnderline(self):
        if self.active_mdi_child():
            self.active_mdi_child().textUnderline()

    @Slot()
    def insertDate(self):
        if self.active_mdi_child():
            self.active_mdi_child().insertDate()

    @Slot()
    def insertTime(self):
        if self.active_mdi_child():
            self.active_mdi_child().insertTime()

    @Slot()
    def textHeading(self, style):
        if self.active_mdi_child():
            self.active_mdi_child().textHeading(style)

    @Slot()
    def textHighlight(self):
        if self.active_mdi_child():
            self.active_mdi_child().textHighlight()
    
    @Slot()
    def quickHighlight(self):
        if self.active_mdi_child():
            self.active_mdi_child().quickHighlight()

    @Slot()
    def insertBlockquote(self):
        if self.active_mdi_child():
            self.active_mdi_child().insertBlockquote()

    @Slot()
    def addHorizontalLine(self):
        if self.active_mdi_child():
            self.active_mdi_child().addHorizontalLine()
    
    @Slot()
    def clearFormatting(self):
        if self.active_mdi_child():
            self.active_mdi_child().clearFormatting()
    
    @Slot()
    def textColor(self):
        if self.active_mdi_child():
            self.active_mdi_child().text_color()

    @Slot()
    def bulletList(self):
        if self.active_mdi_child():
            self.active_mdi_child().bulletList()

    @Slot()
    def addCheckbox(self):
        if self.active_mdi_child():
            self.active_mdi_child().addCheckbox()

    @Slot()
    def setLineSpacing(self, spacing):
        if self.active_mdi_child():
            self.active_mdi_child().setLineSpacing(spacing)

    @Slot()
    def helpClicked(self):
        dlg = QtWidgets.QDialog(parent=self.toolbar)
        dlg.setWindowTitle("Help")

        form = QtWidgets.QFormLayout()
        dlg.setLayout(form)

        form.addRow("Add Note:", QtWidgets.QLabel("Ctrl+N"))
        form.addRow("Edit Note:", QtWidgets.QLabel("Ctrl+O"))
        form.addRow("Insert Signage:", QtWidgets.QLabel("Ctrl+Alt+R"))
        form.addRow("Select all text:", QtWidgets.QLabel("Ctrl+A"))
        form.addRow("Undo:", QtWidgets.QLabel("Ctrl+Z"))
        form.addRow("Redo:", QtWidgets.QLabel("Ctrl+Y"))
        form.addRow("Bold:", QtWidgets.QLabel("Ctrl+B"))
        form.addRow("Italic:", QtWidgets.QLabel("Ctrl+I"))
        form.addRow("Underline:", QtWidgets.QLabel("Ctrl+U"))
        form.addRow("Strikethrough:", QtWidgets.QLabel("Ctrl+-"))
        form.addRow("Insert Date:", QtWidgets.QLabel("Ctrl+Alt+D"))
        form.addRow("Insert Time:", QtWidgets.QLabel("Ctrl+Alt+T"))
        form.addRow("Insert Blockquote:", QtWidgets.QLabel("Ctrl+Alt+B"))
        form.addRow("Insert Horizontal line:", QtWidgets.QLabel("Ctrl+Alt+L"))
        form.addRow("Highlight in red:", QtWidgets.QLabel("Ctrl+Alt+H"))
        form.addRow("Clear Formatting:", QtWidgets.QLabel("Ctrl+Shift+N"))
        form.addRow("Heading 1:", QtWidgets.QLabel("Ctrl+Alt+1"))
        form.addRow("Heading 2:", QtWidgets.QLabel("Ctrl+Alt+2"))
        form.addRow("Heading 3:", QtWidgets.QLabel("Ctrl+Alt+3"))
        form.addRow("Heading 4:", QtWidgets.QLabel("Ctrl+Alt+4"))
        form.addRow("Paragraph:", QtWidgets.QLabel("Ctrl+Alt+P"))
        form.addRow("Insert Bullet list:", QtWidgets.QLabel("Ctrl+;"))
        form.addRow("Insert Checkbox:", QtWidgets.QLabel("Ctrl+Alt+;"))
        form.addRow("Insert Link:", QtWidgets.QLabel("Ctrl+Alt+K"))

        dlg.exec()

    @Slot()
    def editLink(self):
        cursor = self.active_mdi_child().textCursor()
        fmt: QtGui.QTextCharFormat = cursor.charFormat()

        if fmt.isAnchor():
            href = fmt.anchorHref()
            text = cursor.selectedText() or fmt.anchorNames()[0]
        else:
            href = ""
            text = cursor.selectedText()

        dlg = LinkEditorDialog(self,  text, href)
        if dlg.exec():
            link_html = dlg.get_link_html()
            cursor.insertHtml(link_html)

    @Slot()
    def createSignage(self):
        title = self.active_mdi_child().textCursor().selectedText()
        anchor = str(timeuuid())
        source = (f'{{"application":"InspectorMate", "module":"Notebook", "item":"Note", '
                  f'"item_title":"{self.active_mdi_child().userFriendlyFilename()}", "anchor":"{anchor}"}}')

        self.sigCreateSignage.emit(title, source, anchor)

    def insertSignage(self, signage: Signage, anchor: str):
        icon = AppDatabase.cache_signage_type.get(signage.type).icon
        color = AppDatabase.cache_signage_type.get(signage.type).color

        fmt = QtGui.QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref("")
        fmt.setAnchorNames([f"signage_type={signage.type}; id={anchor}"])
        fmt.setAnchorNames([anchor])
        qcolor = QtGui.QColor(color)
        fmt.setForeground(qcolor)
        # fmt.setForeground((QtCore.Qt.GlobalColor.blue))
        fmt.setFontUnderline(False)
        fmt.setFontWeight(QtGui.QFont.Weight.Bold)
        if icon != "":
            img = QtGui.QTextImageFormat()
            img.setWidth(24.0)
            img.setHeight(24.0)
            img.setName(f"data:image/svg+xml;base64,{icon}")
            self.active_mdi_child().textCursor().insertImage(img)
            self.active_mdi_child().textCursor().insertText(f" {signage.refkey} {signage.title}", fmt)
        else:
            self.active_mdi_child().textCursor().insertText(f'{signage.refkey} {signage.title}', fmt)

    @Slot()
    def loadFiles(self):
        mconf.settings.beginGroup("notepad")
        files = mconf.settings.value("NotebookCurrentFiles", [], "QStringList")
        mconf.settings.endGroup()
        
        for filename in files:
            if QtCore.QFile.exists(filename):
                self.loadfile(filename)
                QtWidgets.QApplication.processEvents()
        
    def saveAll(self):
        errors = []
        for subwindows in self.mdi.subWindowList():
            textedit: TextEdit = subwindows.widget()
            if textedit.isModified():
                err = textedit.save()
                if err is not None:
                    errors.append(f"{textedit.filename}: {err}")
        
        if errors:
            QtWidgets.QMessageBox.warning(self, "RichTextEditor -- Save All Error", f"Failed to save\n {"\n".join(errors)}")
        
        return errors

    def addNote(self):
        filename = f"Untitled.html"
        fname = QtWidgets.QFileDialog.getSaveFileName(parent=None,
                                                      caption="Create new Note",
                                                      directory=f"{AppDatabase.activeWorkspace().notebook_path}/{filename}",
                                                      filter="Text files (*.html *.*)")
        if fname[0] == "":
            return
        
        with open(fname[0], "w") as f:
            text = ""
            f.write(text)
            f.close()

        self.loadfile(fname[0], fname[0])

    def editNote(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(parent=None,
                                                      caption="Select Note",
                                                      directory=f"{AppDatabase.activeWorkspace().notebook_path}",
                                                      filter="Text files (*.html *.*)")
        
        if fname[0] == "":
            return

        self.loadfile(fname[0])

    def export2pdf(self):
        textedit: TextEdit = self.active_mdi_child()
        if not textedit:
            return
        
        fname = QtWidgets.QFileDialog.getSaveFileName(parent=None,
                                                      caption="Export Note to PDF",
                                                      directory=f"{AppDatabase.activeWorkspace().notebook_path}",
                                                      filter="Pdf files (*.pdf)")

        output_pdf = fname[0]
        if output_pdf == "":
            return
        
        try:
            html2pdf(textedit.filename, output_pdf)
        except Exception as e:
            m = '❌ An error occured when exporting to PDF'
            logger.error(e)
        else:
            m = '✔️ Note exported to PDF'
        finally:
            status_signal.status_message.emit(m, 5000)

    def setTabbedView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)
        self.layout_strategy = self.LayoutStrategy.Tabbed

    def setCascadeView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.cascadeSubWindows()
        self.layout_strategy = self.LayoutStrategy.Cascade
    
    def setTileView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        for subwindow in self.mdi.subWindowList():
            subwindow.showMaximized()
        self.mdi.tileSubWindows()
        self.layout_strategy = self.LayoutStrategy.Tile

    def minimizeAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showMinimized()
    
    def showNormalAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showNormal()

    def showMaximizeAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showMaximized()

    @Slot(str)
    def searchText(self, text):
        if self.active_mdi_child():
            self.active_mdi_child().search_text = text
            self.active_mdi_child().highlightFoundAll()
