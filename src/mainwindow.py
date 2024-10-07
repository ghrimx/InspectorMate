from qtpy import (QtCore, Qt, QtGui, QtWidgets, QtAds, Slot)
from resources import qrc_resources

from models.model import ProxyModel

from signage.signagemodel import SignageTablelModel
from signage.signagetab import SignageTab
from signage.signagedialog import OwnerDialog

from evidence.evidencemodel import DocTableModel
from evidence.evidencetab import DocTab
from workspace.workspacedialog import (WorkspaceManager, WorkspaceEditDialog)
from onenote.onenotepickerdlg import OnenotePickerDialog

from documentviewer.viewerfactory import ViewerFactory
from documentviewer.viewerwidget import ViewerWidget

from widgets.filesystem import FileSystem
from widgets.richtexteditor import RichTextEditor
from widgets.filedialog import (MergeExcelDialog, UnzipDialog)

from utilities import utils
from utilities import config as mconf
from db.database import AppDatabase
from db.dbstructure import SignageType


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.signage_model = SignageTablelModel()
        self.document_model = DocTableModel()
        self.viewer_factory = ViewerFactory(self.document_model, self)
        self.doc_tabs = {}
        self.note_tabs = {}

    def initUI(self):

        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.eConfigFlag.OpaqueSplitterResize, True)
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.eConfigFlag.XmlCompressionEnabled, False)
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.eConfigFlag.FocusHighlighting, True)
        QtAds.CDockManager.setAutoHideConfigFlags(QtAds.CDockManager.eAutoHideFlag.DefaultAutoHideConfig)
        self.dock_manager = QtAds.CDockManager(self)

        self.setGeometry(100, 100, 800, 600)
        self.set_window_title(AppDatabase.active_workspace.name)

        # Workspace FileSystem Sidebar
        self.workspace_explorer_dock_widget = QtAds.CDockWidget("Explorer", self)
        self.workspace_explorer_dock_widget.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)
        self.workspace_explorer = FileSystem(AppDatabase.active_workspace.rootpath)
        self.workspace_explorer_dock_widget.setWidget(self.workspace_explorer)
        self.workspace_explorer_dock_widget.setMinimumSize(200, 150)
        self.workspace_explorer_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize)
        self.workspace_doc_widget_container = self.dock_manager.addAutoHideDockWidget(QtAds.SideBarLocation.SideBarLeft, self.workspace_explorer_dock_widget)
        self.workspace_doc_widget_container.setMinimumWidth(250)

        # Notebook Explorer FileSystem Sidebar
        self.notebook_explorer_dock_widget = QtAds.CDockWidget("Notebook", self)
        self.notebook_explorer_dock_widget.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)
        self.notebook_explorer = FileSystem(AppDatabase.active_workspace.notebook_path)
        self.notebook_explorer_dock_widget.setWidget(self.notebook_explorer)
        self.notebook_explorer_dock_widget.setMinimumSize(200, 150)
        self.notebook_explorer_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize)
        self.notebook_doc_widget_container = self.dock_manager.addAutoHideDockWidget(QtAds.SideBarLocation.SideBarLeft, self.notebook_explorer_dock_widget)
        self.notebook_doc_widget_container.setMinimumWidth(250)

        # Request widget
        self.request_tab = SignageTab(model=self.signage_model, signage_type='request')
        self.request_dock_widget = QtAds.CDockWidget("Request")
        self.request_dock_widget.setWidget(self.request_tab)
        self.request_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.request_dock_widget.resize(250, 150)
        self.request_dock_widget.setMinimumSize(200, 150)
        self.request_area = self.dock_manager.addDockWidget(QtAds.DockWidgetArea.LeftDockWidgetArea, self.request_dock_widget)

        # Signage widget
        self.signage_tab = SignageTab(model=self.signage_model, signage_type=R"(?!request\b)\b\w+")
        self.signage_dock_widget = QtAds.CDockWidget("Signage")
        self.signage_dock_widget.setWidget(self.signage_tab)
        self.signage_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.signage_dock_widget.resize(250, 150)
        self.signage_dock_widget.setMinimumSize(200, 150)
        self.signage_area = self.dock_manager.addDockWidgetTabToArea(self.signage_dock_widget, self.request_area)

        # Document widget
        self.doctab = DocTab(model=self.document_model)
        self.doctab_dock_widget = QtAds.CDockWidget("Evidence")
        self.doctab_dock_widget.setWidget(self.doctab)
        self.doctab_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.doctab_dock_widget.resize(250, 150)
        self.doctab_dock_widget.setMinimumSize(200, 150)
        self.doctab_area = self.dock_manager.addDockWidgetTabToArea(self.doctab_dock_widget, self.signage_area)

        self.doctab.createRefKeyFilterPane(self.signage_model)

        # TextEditor Area
        self.first_note_dockwidget = QtAds.CDockWidget("Note")
        self.first_note_dockwidget.setFeature(QtAds.CDockWidget.DockWidgetFeature.NoTab, True)
        self.note_area = self.dock_manager.addDockWidget(QtAds.DockWidgetArea.RightDockWidgetArea, self.first_note_dockwidget)
        self.first_note_dockwidget.toggleView(False)

        # Dialogs
        self.workspace_manager: WorkspaceManager = None
        self.workspace_editor: WorkspaceEditDialog = None
        self.merge_excel_dialog: MergeExcelDialog = None
        self.onenote_manager: OnenotePickerDialog = None

        # Menubar
        self.createMenubar()

        self.connectSignals()

        # StatusBar
        # self.status_bar = QtWidgets.QStatusBar(self)
        # self.setStatusBar(self.status_bar)
        # self.status_bar.showMessage('Ready', 5000)

    def createMenubar(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.menubar)

        # File Menu
        self.file_menu = self.menubar.addMenu("File")
        self.file_menu.addAction(QtGui.QAction("Manage Workspace",
                                               self.menubar,
                                               triggered=self.open_workspace_manager))
        self.file_menu.addAction(QtGui.QAction("Create Signage",
                                               self.menubar,
                                               shortcut=QtGui.QKeySequence("Ctrl+R"),
                                               triggered=lambda: self.signage_tab.createSignage("")))
        self.file_menu.addAction(QtGui.QAction("Export Signage",
                                               self.menubar,
                                               triggered=self.signage_tab.exportSignage))
        self.file_menu.addAction(QtGui.QAction("Import Signage",
                                               self.menubar,
                                               triggered=self.signage_tab.importRequest))

        # Edit Menu
        self.document_open_option = QtGui.QAction("Open document with system application",
                                                  self.menubar,
                                                  triggered=self.saveSettings)
        self.edit_menu = self.menubar.addMenu("Edit")
        self.document_open_option.setCheckable(True)
        self.document_open_option.setChecked(True)
        self.edit_menu.addAction(self.document_open_option)

        self.edit_menu.addAction(QtGui.QAction(QtGui.QIcon(":onenote"), "OneNote Test connection", self, triggered=self.open_onenote_picker))
        self.edit_menu.addAction(QtGui.QAction("Edit RefKey pattern", self.menubar, triggered=self.setRegexPattern))
        self.edit_menu.addAction(QtGui.QAction("Add/Remove Owner", self.menubar, triggered=self.addRemoveOwner))

        # View Menu
        self.view_menu = self.menubar.addMenu("View")
        self.view_menu.addAction(self.request_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.signage_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.doctab_dock_widget.toggleViewAction())

        # Tools Menu
        self.tools_menu = self.menubar.addMenu("Tools")
        self.tools_menu.addAction(QtGui.QAction("Merge Excel files",
                                                self.menubar,
                                                triggered=self.handleMergeExcelFiles))
        self.tools_menu.addAction(QtGui.QAction("Unzip archive",
                                                self.menubar,
                                                triggered=self.handleUnzipArchive))
        self.tools_menu.addAction(QtGui.QAction("Unpack PDF",
                                                self.menubar,
                                                triggered=self.handleUnpackPDF))
        
        # About
        self.about_menu = self.menubar.addMenu("Help")
        self.about_menu.addAction(QtGui.QAction("About InspectorMate",
                                                self.menubar,
                                                triggered=self.showAbout))

    def connectSignals(self):
        self.doctab.sig_open_document.connect(self.handle_sig_open_doc)
        self.doctab.sig_load_file.connect(self.handle_load_file)
        self.workspace_explorer.doubleClicked.connect(lambda: self.OnFilesystemDoubleClicked(self.workspace_explorer))
        self.notebook_explorer.doubleClicked.connect(lambda: self.OnFilesystemDoubleClicked(self.notebook_explorer))
        self.document_model.dataChanged.connect(self.signage_model.refresh)

        self.signage_model.rowsInserted.connect(self.doctab.request_filter_tab.updateCounter)
        self.signage_model.rowsRemoved.connect(self.doctab.request_filter_tab.updateCounter)

    def showAbout(self):
        about = QtWidgets.QMessageBox.information(self, "About InspectorMate", f"InspectorMate v{QtWidgets.QApplication.applicationVersion()}")

    @Slot()
    def addRemoveOwner(self):
        dlg = OwnerDialog()
        dlg.exec()

    @Slot()
    def setRegexPattern(self):
        if mconf.settings.value("regex") is None or mconf.settings.value("regex") == "":
            regex = mconf.default_regex
        else:
            regex = mconf.settings.value("regex")

        text, ok = QtWidgets.QInputDialog.getText(self,
                                                  "Signage/Evidence RegEx Pattern",
                                                  f"Actual RegEx pattern: {mconf.settings.value("regex")}\nNew RegEx:",
                                                  QtWidgets.QLineEdit.EchoMode.Normal,
                                                  regex)

        if ok:
            mconf.settings.setValue("regex", text)

    def loadSettings(self):
        if mconf.settings.value("USE_DEFAULT_FILEOPENER") == 'false':
            self.document_open_option.setChecked(False)
        else:
            self.document_open_option.setChecked(True)

    @Slot()
    def OnFilesystemDoubleClicked(self, filesystem: FileSystem):
        idx = filesystem.selectionModel().currentIndex()

        if filesystem.model().isDir(idx):
            return

        file_info: QtCore.QFileInfo = filesystem.model().fileInfo(idx)

        if file_info.isFile():
            if file_info.suffix() == "phv" and self.note_tabs.get(file_info.absoluteFilePath()) is None:
                self.notetab = RichTextEditor.fromFile(file_info.absoluteFilePath(), self)
                self.notetab.sig_create_request.connect(self.createSignageFromNote)

                if self.notetab is not None:
                    self.note_dockwidget = QtAds.CDockWidget(file_info.baseName())
                    self.note_dockwidget.setWidget(self.notetab)

                    self.dock_manager.addDockWidgetTabToArea(self.note_dockwidget, self.note_area)

                    self.note_tabs[file_info.absoluteFilePath()] = self.note_dockwidget
            elif file_info.suffix() == "phv" and self.note_tabs.get(file_info.absoluteFilePath()) is not None:
                self.note_tabs[file_info.absoluteFilePath()].toggleView(True)
            else:
                utils.open_file(file_info.absoluteFilePath())

    def createSignageFromNote(self, caller: RichTextEditor):

        title = caller.editor.textCursor().selectedText()

        val = self.signage_tab.createSignage(title)

        if val == 1:
            signage = self.signage_tab.create_dialog.getNewSignage()

            icon = None
            signage_type: SignageType
            for signage_type in AppDatabase.cache_signage_type.values():
                if signage_type.type_id == signage.type_id:
                    icon = signage_type.icon

            if icon != "":
                caller.editor.textCursor().insertHtml(f'<p><img alt="" src="data:image/png;base64,{icon}"/> {signage.refKey} {signage.title}</p>')
            else:
                caller.editor.textCursor().insertText(f'{signage.refKey} {signage.title}')

    @Slot()
    def saveSettings(self):
        mconf.settings.setValue("USE_DEFAULT_FILEOPENER", self.document_open_option.isChecked())

    def set_window_title(self, text=None):
        if text is not None:
            self.setWindowTitle(f'{mconf.config.app_name} - {text}')

    @Slot()
    def handle_sig_open_doc(self):
        doc = self.doctab.table.document()
        if self.document_open_option.isChecked():
            utils.open_file(doc.filepath)
        elif self.doc_tabs.get(doc.id) is not None:
            self.doc_tabs[doc.id].toggleView(True)
        else:
            self.viewer = self.viewer_factory.viewer(doc, self.doctab.selectedIndex())

            if self.viewer is not None:
                doc_dock_widget = QtAds.CDockWidget(doc.title[:15])
                doc_dock_widget.closed.connect(self.doctab_dock_widget.setAsCurrentTab) #  Activate Evidence tab after closing a document viewer
                doc_dock_widget.setWidget(self.viewer)
                self.dock_manager.addDockWidgetTabToArea(doc_dock_widget, self.request_area)
                self.doc_tabs[doc.id] = doc_dock_widget
            else:
                utils.open_file(doc.filepath)

    @Slot()
    def handle_load_file(self):
        """
        Re-set the mapper index after loading file into the document model

        Index is lost after refreshing the model.
        Therefore, it's necessary to re-set the index of the viewer mapper to keep mapper synchronization.
        """
        doctable_model: ProxyModel = self.doctab.table.proxy_model()
        for item in range(doctable_model.rowCount()):
            index = doctable_model.index(item, self.document_model.Fields.ID.index)
            doc_id = doctable_model.data(index, Qt.ItemDataRole.DisplayRole)

            dock_widget: QtAds.CDockWidget = self.doc_tabs.get(doc_id)
            if dock_widget:
                widget: ViewerWidget = dock_widget.widget()

                source_index = doctable_model.mapToSource(index)
                widget.setMapperIndex(source_index)

    @Slot()
    def handleMergeExcelFiles(self):
        self.merge_excel_dialog = MergeExcelDialog()
        self.merge_excel_dialog.exec()

    @Slot()
    def handleUnzipArchive(self):
        self.unzip_dialog = UnzipDialog(source=AppDatabase.active_workspace.rootpath, dest=AppDatabase.active_workspace.evidence_path)
        self.unzip_dialog.exec()

    @Slot()
    def handleUnpackPDF(self):
        file = QtWidgets.QFileDialog.getOpenFileName(caption="Select file", directory=AppDatabase.active_workspace.evidence_path, filter="*.pdf")

        if file[0] != "":
            err = utils.unpackPDF(file[0])

            if isinstance(err, Exception):
                QtWidgets.QMessageBox.critical(self, "unpackPDF -- Error", f"{err}")
            elif err:
                QtWidgets.QMessageBox.information(self, "unpackPDF -- Success", "PDF successfully unpacked")

    @Slot()
    def open_workspace_manager(self):
        if self.workspace_manager is None:
            self.workspace_manager = WorkspaceManager()
            self.workspace_manager.sig_workspace_updated.connect(self.refreshWidgets)
            self.workspace_manager.exec()

    @Slot()
    def refreshWidgets(self):
        self.doctab.refresh()
        self.signage_model.refresh()
        self.workspace_explorer.set_root_path(AppDatabase.active_workspace.rootpath)
        self.notebook_explorer.set_root_path(AppDatabase.active_workspace.notebook_path)
        self.set_window_title(AppDatabase.active_workspace.name)

    @Slot()
    def open_onenote_picker(self):
        onenote_warning = QtWidgets.QMessageBox.warning(self,
                                                        "Warning",
                                                        "Establishing a connection to OneNote before opening the application may put the application in a hang state\n\nIt's recommended to open OneNote app before establishing a connection",
                                                        buttons=QtWidgets.QMessageBox.StandardButton.Ignore | QtWidgets.QMessageBox.StandardButton.Cancel)

        if onenote_warning == QtWidgets.QMessageBox.StandardButton.Cancel:
            return

        if self.onenote_manager is None:
            self.onenote_manager = OnenotePickerDialog(self)

        self.onenote_manager.show()

    def closeEvent(self, event: QtCore.QEvent):
        msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self,
                                               f'Closing {mconf.config.app_name}',
                                               msg,
                                               QtWidgets.QMessageBox.StandardButton.Ok,
                                               QtWidgets.QMessageBox.StandardButton.No)

        if reply == QtWidgets.QMessageBox.StandardButton.Ok:
            err = self.request_tab.close()
            err = self.signage_tab.close()
            err = self.doctab.close()

            if not err:
                AppDatabase.close()
                event.accept()
            else:
                reply = QtWidgets.QMessageBox.warning(self,
                                                      'Error while closing!',
                                                      'An error occurred while closing the application.\nSome data might be lost.\nSee log for more details on the error',
                                                      QtWidgets.QMessageBox.StandardButton.Ok)
        else:
            event.ignore()
