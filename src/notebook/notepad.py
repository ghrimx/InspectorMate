import logging
from qtpy import QtWidgets, QtCore, QtGui
from db.database import AppDatabase

logger = logging.getLogger(__name__)


class TextEdit(QtWidgets.QTextEdit):

    def __init__(self, filename=str, text=str, parent=None):
        super(TextEdit, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.filename: str = filename
        self.setHtml(text)

        self.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse | QtCore.Qt.TextInteractionFlag.TextEditorInteraction)
        self.document().setModified(False)
        self.setWindowTitle(QtCore.QFileInfo(self.filename).fileName())
    
    def closeEvent(self, event):
        if self.document().isModified():
            try:
                self.save()
            except (IOError, OSError) as e:
                QtWidgets.QMessageBox.warning(self,
                                              "RichTextEditor -- Save Error",
                                              f"Failed to save {self.filename}: {e}")

    def isModified(self):
        return self.document().isModified()

    def save(self):
        try:
            fh = QtCore.QFile(self.filename)
            if not fh.open(QtCore.QIODevice.OpenModeFlag.WriteOnly):
                logger.error(IOError(fh.errorString()))
            stream = QtCore.QTextStream(fh)
            stream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            stream << self.toHtml()
            fh.close()
        except EnvironmentError as e:
            logger.error(f"RichTextEditor -- Save Error:\nFailed to save {self.filename}: {e}")
            QtWidgets.QMessageBox.warning(self, "RichTextEditor -- Save Error", f"Failed to save {self.filename}: {e}")

            self.document().setModified(False)

    @classmethod
    def createNote(cls, filename: str = ""):
        if filename == "":
            filename = f"Untitled.html"
            fname = QtWidgets.QFileDialog.getSaveFileName(parent=None,
                                                          caption="RichTextEditor -- Save File As",
                                                          directory=f"{AppDatabase.active_workspace.notebook_path}/{filename}",
                                                          filter="Text files (*.html *.*)")
        if fname[0] == "":
            return
        
        with open(fname[0], "w") as f:
            text = ""
            f.write(text)
            f.close()
        
        return cls(fname[0], text)

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

class Notepad(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        # Toolbar
        toolbar = QtWidgets.QToolBar(self)
        vbox.addWidget(toolbar)

        action_addnote = QtGui.QAction(QtGui.QIcon(':file_add'), "add note", self, triggered=self.addNote)
        action_editnote = QtGui.QAction(QtGui.QIcon(':file-edit-line'), "edit note", self, triggered=self.editNote)

        viewmenu_toolbutton = QtWidgets.QToolButton(self)
        viewmenu_toolbutton.setIcon(QtGui.QIcon(':eye-line'))
        viewmenu_toolbutton.setText("Views")
        viewmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        viewmenu = QtWidgets.QMenu("View", self)
        viewmenu.addAction(QtGui.QAction(QtGui.QIcon(':stack-line'), "Cascade", self, triggered=self.setCascadeView))
        viewmenu.addAction(QtGui.QAction(QtGui.QIcon(':layout-grid-line'), "Tile", self, triggered=self.setTileView))
        viewmenu.addAction(QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Tabbed", self, triggered=self.setTabbedView))
        viewmenu_toolbutton.setMenu(viewmenu)
        
        toolbar.addAction(action_addnote)
        toolbar.addAction(action_editnote)
        toolbar.addWidget(viewmenu_toolbutton)

        # MdiArea
        self.mdi = QtWidgets.QMdiArea()
        self.mdi.setTabsMovable(True)
        self.mdi.setTabsClosable(True)
        
        vbox.addWidget(self.mdi)

    def loadfile(self, filename):
        textedit = TextEdit.load(filename)
        if textedit is not None:
            subwindow = self.mdi.addSubWindow(textedit)
            subwindow.show()

    def addNote(self):
        filename = f"Untitled.html"
        fname = QtWidgets.QFileDialog.getSaveFileName(parent=None,
                                                          caption="RichTextEditor -- Save File As",
                                                          directory=f"{AppDatabase.active_workspace.notebook_path}/{filename}",
                                                          filter="Text files (*.html *.*)")
        if fname[0] == "":
            return
        
        with open(fname[0], "w") as f:
            text = ""
            f.write(text)
            f.close()

        self.loadfile(fname[0])

    def editNote(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(parent=None,
                                                      caption="RichTextEditor -- Select file",
                                                      directory=f"{AppDatabase.active_workspace.notebook_path}",
                                                      filter="Text files (*.html *.*)")
        
        if fname[0] == "":
            return

        for subwindow in self.mdi.subWindowList():
            textedit: TextEdit = subwindow.widget()
            if textedit.filename == fname[0]:
                self.mdi.setActiveSubWindow(subwindow)
                break
        else:
            self.loadfile(fname[0])

    def setTabbedView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)

    def setCascadeView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.cascadeSubWindows()
    
    def setTileView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.tileSubWindows()
