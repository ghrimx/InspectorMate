import logging
from enum import Enum
from datetime import datetime
from qtpy import (Qt, QtCore, QtGui, QtWidgets, Slot, Signal)

from database.database import AppDatabase

from utilities.utils import (hexuuid, createFolder, queryFileID)
from utilities import config as mconf

logger = logging.getLogger(__name__)

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]

class ListStyle(Enum):
    LIST1 = 1
    LIST2 = 2

class HeadingStyle(Enum):
    P = 0
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6

class LineSpacing(Enum):
    NORMAL = 100
    NORMAL_HALF = 150
    DOUBLE = 200

class TextEdit(QtWidgets.QTextEdit):
    sigTextEdited = Signal(str)

    def __init__(self, parent = None):
        super(TextEdit, self).__init__(parent)

    def canInsertFromMimeData(self, source: QtCore.QMimeData):
        if source.hasImage():
            return source.hasImage()
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)
        
    def insertFromMimeData(self, source: QtCore.QMimeData):
        cursor = self.textCursor()
        document = self.document()

        if source.hasUrls():
            for url in source.urls():
                file_info = QtCore.QFileInfo(url.toLocalFile())
                if file_info.suffix().lower() in QtGui.QImageReader.supportedImageFormats():
                    image = QtGui.QImage(url.toLocalFile())
                    if not image.isNull():
                        document.addResource(QtGui.QTextDocument.ResourceType.ImageResource, url, image)
                        cursor.insertImage(url.toLocalFile())
                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break
        elif source.hasImage():
            image = source.imageData()
            uuid = hexuuid()

            image_dir = f"{AppDatabase.activeWorkspace().notebook_path}/.images"
            createFolder(image_dir)
            image_path = f'{image_dir}/{uuid}.png'

            image_saved = QtGui.QImage(image).save(image_path, "PNG", 100)
            if not image_saved:
                logger.error(f"Error saving image saved: {image_path}")
            
            img_url = QtCore.QUrl.fromLocalFile(f'.images/{uuid}.png')
            resolved_url = document.baseUrl().resolved(img_url)

            document.addResource(QtGui.QTextDocument.ResourceType.ImageResource, resolved_url, image)

            # insert image with relative path for web browser
            cursor.insertImage(QtGui.QImage(image), img_url.toString())

            # Add citation below the image
            # Get the Pixmap cacheKey from the Qsettings if cachekeys match then insert the citation along with the image
            image_cachekey = QtWidgets.QApplication.clipboard().image().cacheKey()
            capture = mconf.settings.value("capture", [], "QStringList")
            if len(capture) > 0:
                if str(image_cachekey) == capture[0]:
                    citation = capture[1]
                    cursor.insertBlock()
                    cursor.insertText(citation)
                    
                    # set a blue color to the foreground of the citation
                    cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)
                    fmt = QtGui.QTextCharFormat()
                    fmt.setForeground(QtGui.QColor(85, 0, 255))
                    cursor.mergeCharFormat(fmt)
                    self.mergeCurrentCharFormat(fmt)

        elif source.hasText():
            hyperlink = QtCore.QUrl(source.text())
            if not hyperlink.isRelative():
                link = QtGui.QTextCharFormat()
                link.setAnchor(True)
                link.setAnchorHref(f"{source.text()}")
                link.setAnchorNames([f"{source.text()}"])
                link.setForeground(Qt.GlobalColor.blue)
                link.setFontUnderline(True)
                cursor.insertText(source.text(), link)
            else:
                super(TextEdit, self).insertFromMimeData(source)
        else:
            super(TextEdit, self).insertFromMimeData(source)

    def focusInEvent(self, e):
        self._old_text = self.toHtml()
        return super().focusInEvent(e)
    
    def focusOutEvent(self, e):
        if self._old_text != self.toHtml():
            self.sigTextEdited.emit(self.toHtml())
        return super().focusOutEvent(e)

class NoteEditor(QtWidgets.QWidget):
    sig_create_request = Signal(object)

    def __init__(self, path: str = None, text: str = None, saveMode = 1, uid: str = None,  bar: bool = True, parent = None):
        super(NoteEditor, self).__init__(parent=parent)
        self._parent = parent
        self.text = text
        self.editor = TextEdit()
        self.editor.setHtml(self.text)
        self.cursor = self.editor.textCursor() 

        self.editor.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse | Qt.TextInteractionFlag.TextEditorInteraction)

        base_url = QtCore.QUrl(f"file:///{AppDatabase.activeWorkspace().notebook_path}/")
        self.editor.document().setBaseUrl(base_url)

        # Define CSS for blockquote
        # Set the CSS to the QTextEdit
        blockquote_css = """ 
                        blockquote {
                            border-left: 5px solid #ccc;
                            margin-left: 20px; 
                            padding-left: 20px; 
                            background: #eee;
                            border-radius: 5px; margin-bottom:0px;
                        }"""
        self.editor.document().setDefaultStyleSheet(blockquote_css)

        self.initUI()
            
        self.createShortcuts()
        self.createTextActions()
        self.createToolbar()
        self.connectSignals()


    def initUI(self):
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vbox)

        self.editor.setAutoFormatting(QtWidgets.QTextEdit.AutoFormattingFlag.AutoAll)

        # Initialize default font size.
        font = QtGui.QFont("Segoe UI", 12)
        font.setStyleHint(QtGui.QFont.StyleHint.SansSerif)
        self.editor.setFont(font)
        self.editor.setFontPointSize(12)

        # Add to layout
        self.vbox.addWidget(self.editor)

                
    # Signals
    def connectSignals(self):
        self.editor.currentCharFormatChanged.connect(self.current_char_format_changed)
        self.editor.cursorPositionChanged.connect(self.cursor_position_changed)

    def createTextActions(self):
        # Bold
        self.bold_action = QtGui.QAction(QtGui.QIcon(':bold'), "Bold (Ctrl+B)", self, triggered=self.text_bold, checkable=True)

        # Italic
        self.italic_action = QtGui.QAction(QtGui.QIcon(':italic'), "Italic (Ctrl+I)", self, triggered=self.text_italic, checkable=True)

        # Underline
        self.underline_action = QtGui.QAction(QtGui.QIcon(':underline'), "Underline (Ctrl+U)", self, triggered=self.text_underline, checkable=True)
        
        # StrikeOut
        self.strikeout_action = QtGui.QAction(QtGui.QIcon(':strikeout'), "StrikeOut (Ctrl+-)", self, triggered=self.text_strikeout, checkable=True)
        
        # Date/Time
        self.action_date = QtGui.QAction(QtGui.QIcon(":calendar-line"), "Date (Ctrl+Alt+D)", self, triggered = self.insert_date)
        self.action_time = QtGui.QAction(QtGui.QIcon(":time-line"), " Time (Ctrl+Alt+T)", self, triggered = self.insert_time)
        
        # Headings
        self.action_paragraph = QtGui.QAction(QtGui.QIcon(":paragraph"), "Paragraph", self, triggered = lambda:self.text_syle(HeadingStyle.P))
        self.action_h1 = QtGui.QAction(QtGui.QIcon(":h-1"), "Heading 1", self, triggered = lambda:self.text_syle(HeadingStyle.H1))
        self.action_h2 = QtGui.QAction(QtGui.QIcon(":h-2"), "Heading 2", self, triggered = lambda:self.text_syle(HeadingStyle.H2))
        self.action_h3 = QtGui.QAction(QtGui.QIcon(":h-3"), "Heading 3", self, triggered = lambda:self.text_syle(HeadingStyle.H3))
        self.action_h4 = QtGui.QAction(QtGui.QIcon(":h-4"), "Heading 4", self, triggered = lambda:self.text_syle(HeadingStyle.H4))

        # # Highlight
        # action_quick_highlight = QtGui.QAction("Highlight", self, triggered = self.quick_highlight)
        # self.addAction(action_quick_highlight)
        self.action_highlight = QtGui.QAction(QtGui.QIcon(":mark_pen"), "Highlight (Ctrl+Alt+H)", self, triggered= self.text_highlight)

        # Quoteblock
        self.action_blockquote = QtGui.QAction(QtGui.QIcon(':double-quotes'),"Block quote", self, triggered=self.blockquote)       

        # Horizontal line
        self.action_horizontal_line = QtGui.QAction(QtGui.QIcon(':horizontal-line'), "Horizontal line (Ctrl+Alt+L)", self, triggered=self.add_horizontal_line)

        # Clear formatting
        self.action_clear_formatting = QtGui.QAction(QtGui.QIcon(':format-clear'),"Clear formatting (Ctrl+Shift+N)", self, triggered=self.clear_formatting)

        pix = QtGui.QPixmap(16, 16)
        pix.fill(Qt.GlobalColor.black)

        self.color_action = QtGui.QAction(QtGui.QIcon(pix),"Color Text", self, triggered=self.text_color)

        # Bullet List
        self.action_bullet = QtGui.QAction(QtGui.QIcon(":list-unordered"), "Bullet list (ctrl+;)", self, triggered=self.bulletList)

        # Line Spacing
        self.action_line_spacing_normal = QtGui.QAction("1.0", self, triggered=lambda: self.setLineSpacing(LineSpacing.NORMAL))
        self.action_line_spacing_1_5 = QtGui.QAction("1.5", self, triggered=lambda: self.setLineSpacing(LineSpacing.NORMAL_HALF))
        self.action_line_spacing_double = QtGui.QAction("2.0", self, triggered=lambda: self.setLineSpacing(LineSpacing.DOUBLE))

        self.action_help = QtGui.QAction(QtGui.QIcon(':question-line'), "Help", self, triggered=self.helpClicked, checkable=False)

    def createToolbar(self):
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
        self.vbox.insertWidget(0, self.toolbar)

        spacer = QtWidgets.QWidget(self)
        spacer.setContentsMargins(0,0,0,0)
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.action_spacer = self.toolbar.addWidget(spacer)

        self.toolbar.addAction(self.action_help)

    def createShortcuts(self):
        self.shortcut_quick_highlight = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+H"), self.editor, self.quick_highlight, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_date = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+D"), self.editor, self.insert_date, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_time = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+T"), self.editor, self.insert_time, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_h1 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+1"), self.editor, lambda:self.text_syle(HeadingStyle.H1), ambiguousMember=lambda:self.text_syle(HeadingStyle.H1), context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_h2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+2"), self.editor, lambda:self.text_syle(HeadingStyle.H2), ambiguousMember=lambda:self.text_syle(HeadingStyle.H2),context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_h3 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+3"), self.editor, lambda:self.text_syle(HeadingStyle.H3), ambiguousMember=lambda:self.text_syle(HeadingStyle.H3),context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_h4 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+4"), self.editor, lambda:self.text_syle(HeadingStyle.H4), ambiguousMember=lambda:self.text_syle(HeadingStyle.H4),context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_P = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+P"), self.editor, lambda:self.text_syle(HeadingStyle.P), ambiguousMember=lambda:self.text_syle(HeadingStyle.P), context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_request = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+R"), self.editor, self.insert_request, ambiguousMember=self.insert_request, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_clearformatting = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+N"), self.editor, self.clear_formatting, ambiguousMember=self.clear_formatting, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_blockquote = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+B"), self.editor, self.blockquote, ambiguousMember=self.blockquote, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_blod = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+B"), self.editor, self.text_bold, ambiguousMember=self.text_bold, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_italic = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+I"), self.editor, self.text_italic, ambiguousMember=self.text_italic, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_strikeout = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self.editor, self.text_strikeout, ambiguousMember=self.text_strikeout, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_underline = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+U"), self.editor, self.text_underline, ambiguousMember=self.text_underline, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_insertLine = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Alt+L"), self.editor, self.add_horizontal_line, ambiguousMember=self.add_horizontal_line, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_bulletList = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+;"), self.editor, self.bulletList, ambiguousMember=self.bulletList, context=Qt.ShortcutContext.WidgetShortcut)

    @Slot()
    def helpClicked(self):
        dlg = QtWidgets.QDialog(parent=self.toolbar)
        dlg.setWindowTitle("Help")

        form = QtWidgets.QFormLayout()
        dlg.setLayout(form)

        form.addRow("Insert Request:", QtWidgets.QLabel("Ctrl+Alt+R"))
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

        dlg.exec()

    @Slot()
    def insert_request(self):
        self.sig_create_request.emit(self)

    @Slot()
    def text_bold(self):
        cursor = self.editor.textCursor()

        fmt = QtGui.QTextCharFormat()
        weight = QtGui.QFont.Weight.Bold if cursor.charFormat().fontWeight() == QtGui.QFont.Weight.Normal else QtGui.QFont.Weight.Normal
        fmt.setFontWeight(weight)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def text_italic(self):
        cursor = self.editor.textCursor()

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontItalic() else True
        fmt.setFontItalic(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def text_underline(self):
        cursor = self.editor.textCursor()

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontUnderline() else True
        fmt.setFontUnderline(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def text_strikeout(self):
        cursor = self.editor.textCursor()

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontStrikeOut() else True
        fmt.setFontStrikeOut(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def text_size(self, p):
        font_size = float(p)
        if font_size > 0:
            fmt = QtGui.QTextCharFormat()
            fmt.setFontPointSize(font_size)
            self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def text_color(self):
        color = QtWidgets.QColorDialog.getColor(self.editor.textColor(), self)
        if not color.isValid():
            return

        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(color)
        self.merge_format_on_word_or_selection(fmt)
        self.color_changed(color)

    def color_changed(self, c):
        pix = QtGui.QPixmap(16, 16)
        pix.fill(c)
        self.color_action.setIcon(QtGui.QIcon(pix))

    def current_char_format_changed(self, fmt: QtGui.QTextCharFormat):
        self.format_changed(fmt.font())
        self.color_changed(fmt.foreground().color())

    def cursor_position_changed(self):
        self.cursor: QtGui.QTextCursor = self.editor.textCursor()

    def merge_format_on_word_or_selection(self, fmt: QtGui.QTextCharFormat):
        if not self.cursor.hasSelection():
            self.cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)

        self.cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def merge_format_on_line_or_selection(self, fmt: QtGui.QTextCharFormat):
        if not self.cursor.hasSelection():
            self.cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)

        self.cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
        self.cursor.clearSelection()

    def format_changed(self, current_font: QtGui.QFont):
        self.bold_action.setChecked(current_font.bold())
        self.italic_action.setChecked(current_font.italic())
        self.underline_action.setChecked(current_font.underline())
        self.strikeout_action.setChecked(current_font.strikeOut())
        # self.textsize_selector.setCurrentIndex(self.textsize_selector.findText(str(current_font.pointSize())))

    @Slot()
    def saveFile(self):
        try:
            fh = QtCore.QFile(self.path)
            if not fh.open(QtCore.QIODevice.OpenModeFlag.WriteOnly):
                logger.error(IOError(fh.errorString()))
            stream = QtCore.QTextStream(fh)
            stream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            stream << self.editor.toHtml()
        except EnvironmentError as e:
            logger.error(f"RichTextEditor -- Save Error:\nFailed to save {self.path}: {e}")
            QtWidgets.QMessageBox.warning(self, "RichTextEditor -- Save Error", f"Failed to save {self.path}: {e}")

    @Slot()
    def insert_date(self):
        today = datetime.now().strftime("%d-%m-%Y")
        self.editor.textCursor().insertText(today)
    
    @Slot()
    def insert_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.editor.textCursor().insertText(now)

    @Slot()
    def clear_formatting(self):
        cursor = self.editor.textCursor()

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
    def blockquote(self):
        cursor = self.editor.textCursor()

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.BlockUnderCursor)

        cursor.beginEditBlock()
 
        frame_fmt = cursor.currentFrame().frameFormat()
        frame_fmt.setBorderStyle(QtGui.QTextFrameFormat.BorderStyle.BorderStyle_None)
        frame_fmt.setLeftMargin(40)
        frame_fmt.setRightMargin(40)
        frame_fmt.setPadding(10)
        frame_fmt.setBackground(QtGui.QColor("#e6f2ff"))

        cursor.insertFrame(frame_fmt)
 
        cursor.endEditBlock()

    @Slot()
    def add_horizontal_line(self):
        cursor = self.editor.textCursor()

        # Save the cursor position and selection
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        if not cursor.hasSelection():
            # Select the current line if no text is selected
            cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)

        selected_text = cursor.selectedText()

        # Wrap the selected text in blockquote tags
        hr = r'<hr style="width=2px;">'

        if selected_text == "":
            formatted_text = hr
        else:
            formatted_text = f'<p>{selected_text}</p>{hr}'

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertHtml(formatted_text)
        cursor.endEditBlock()

        # Restore the cursor position
        cursor.setPosition(start, QtGui.QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(end, QtGui.QTextCursor.MoveMode.KeepAnchor)
        self.editor.setFocus()
        self.editor.setTextCursor(cursor)

    @Slot()
    def text_highlight(self):       
        color = QtWidgets.QColorDialog.getColor(self.editor.textColor(), self)
        if not color.isValid():
            return

        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(color)
        self.merge_format_on_word_or_selection(fmt)

        self.editor.setFocus()

    @Slot()
    def text_syle(self, style):
        cursor = self.editor.textCursor()

        cursor.beginEditBlock()

        block_fmt = cursor.blockFormat()

        if isinstance(style, HeadingStyle):
            block_fmt.setObjectIndex(-1)
            block_fmt.setHeadingLevel(style.value)
            cursor.setBlockFormat(block_fmt)
            fmt = QtGui.QTextCharFormat()
            fmt.setFontWeight(QtGui.QFont.Weight.Bold if style.value > 0 else QtGui.QFont.Weight.Normal)
            fmt.setProperty(QtGui.QTextFormat.Property.FontSizeAdjustment, 4 - style.value if style.value > 0 else 0)
            self.merge_format_on_line_or_selection(fmt)

        cursor.endEditBlock()

    @Slot()
    def quick_highlight(self):
        cursor = self.editor.textCursor()
        color = QtGui.QColor("#ffcccc")

        cursor.beginEditBlock()

        if self.editor.currentCharFormat().background().color() == QtGui.QColor("#ffcccc"):
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(Qt.GlobalColor.transparent)
            self.merge_format_on_line_or_selection(fmt)
        else:
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(color)
            self.merge_format_on_line_or_selection(fmt)

        cursor.endEditBlock()

    @Slot()
    def bulletList(self):
        cursor = self.editor.textCursor()
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
    def setLineSpacing(self, spacing: LineSpacing):
        cursor = self.editor.textCursor()

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.BlockUnderCursor)

        block_fmt = cursor.blockFormat()
        block_char_fmt = cursor.blockCharFormat()

        cursor.beginEditBlock()
        block_fmt.setLineHeight(spacing.value, QtGui.QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)

        cursor.mergeBlockCharFormat(block_char_fmt)
        cursor.mergeBlockFormat(block_fmt)
        cursor.endEditBlock()

    def focusInEvent(self, a0):
        return super().focusInEvent(a0)
    
    def focusOutEvent(self, a0):
        return super().focusOutEvent(a0)