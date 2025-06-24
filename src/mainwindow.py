from qtpy import (QtCore, Qt, QtGui, QtWidgets, QtAds, Slot)
from resources import qrc_resources
from theme_manager import theme_icon_manager, Theme
import logging
 
from signage.signage_model import SignageTreeModel
from signage.signage_tab import SignageTab as SignageTreeTab
from signage.signage_dialogs import OwnerDialog

from evidence.evidencemodel import EvidenceModel
from evidence.evidencetab import EvidenceTab, Document
from workspace.workspace_dialogs import WorkspaceManagerDialog
from onenote.msonenote import OnenotePickerDialog

from documentviewer.viewerfactory import ViewerFactory
from documentviewer.viewerwidget import ViewerWidget

from richtexteditor.notepad import Notepad

from widgets.filesystem import FileSystem
from widgets.richtexteditor import RichTextEditor
from widgets.filedialog import (MergeExcelDialog, UnzipDialog)
from widgets.summarydialog import SummaryDialog
from widgets.aboutdialog import About
from widgets.debuglogviewer import DebugLogViewer
from widgets.batch_renamer import BatchRenameWidget

from utilities import utils
from utilities import config as mconf
from database.database import AppDatabase
from database.dbstructure import SignageType
from models.model import SummaryModel

from listinsight import ListinsightWidget


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.signage_treemodel = SignageTreeModel()
        self.evidence_model = EvidenceModel()
        self.viewer_factory = ViewerFactory(self.evidence_model, self)
        self.workspace_manager =  None
        self.doc_viewers = {}

    def initUI(self):
        """Initialize the MainWindow User Interface"""

        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.eConfigFlag.OpaqueSplitterResize, True)
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.eConfigFlag.XmlCompressionEnabled, False)
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.eConfigFlag.FocusHighlighting, True)
        QtAds.CDockManager.setAutoHideConfigFlags(QtAds.CDockManager.eAutoHideFlag.DefaultAutoHideConfig)
        self.dock_manager = QtAds.CDockManager(self)
       
        self.setGeometry(100, 100, 800, 600)
        self.set_window_title(AppDatabase.activeWorkspace().name)

        # Workspace FileSystem Sidebar
        self.workspace_explorer_dock_widget = QtAds.CDockWidget("Explorer", self)
        self.workspace_explorer_dock_widget.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)
        self.workspace_explorer = FileSystem(AppDatabase.activeWorkspace().rootpath)
        self.workspace_explorer.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.workspace_explorer_dock_widget.setWidget(self.workspace_explorer)
        self.workspace_explorer_dock_widget.setMinimumSize(200, 150)
        self.workspace_explorer_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize)
        self.workspace_doc_widget_container = self.dock_manager.addAutoHideDockWidget(QtAds.SideBarLocation.SideBarLeft, self.workspace_explorer_dock_widget)
        self.workspace_doc_widget_container.setMinimumWidth(250)

        # Notebook Explorer FileSystem Sidebar
        self.notebook_explorer_dock_widget = QtAds.CDockWidget("Notebook", self)
        self.notebook_explorer_dock_widget.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)
        self.notebook_explorer = FileSystem(AppDatabase.activeWorkspace().notebook_path)
        self.notebook_explorer_dock_widget.setWidget(self.notebook_explorer)
        self.notebook_explorer_dock_widget.setMinimumSize(200, 150)
        self.notebook_explorer_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize)
        self.notebook_doc_widget_container = self.dock_manager.addAutoHideDockWidget(QtAds.SideBarLocation.SideBarLeft, self.notebook_explorer_dock_widget)
        self.notebook_doc_widget_container.setMinimumWidth(250)

        # Signage Tree Widget        
        self.signage_dock_widget = QtAds.CDockWidget("Signage", self)
        self.signage_tree_tab = SignageTreeTab(model=self.signage_treemodel)
        self.signage_dock_widget.setWidget(self.signage_tree_tab)
        self.signage_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.signage_dock_widget.resize(250, 150)
        self.signage_dock_widget.setMinimumSize(200, 150)
        self.signage_area = self.dock_manager.addDockWidget(QtAds.DockWidgetArea.LeftDockWidgetArea, self.signage_dock_widget)
        if theme_icon_manager.get_theme() == Theme.DARK:
            self.signage_area.setStyleSheet("color: white;")

        # Notebook widget
        self.notepad_tab = Notepad(self)
        self.notepad_dock_widget = QtAds.CDockWidget("Notebook", self)
        self.notepad_dock_widget.setWidget(self.notepad_tab)
        self.notepad_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.notepad_dock_widget.resize(250, 150)
        self.notepad_dock_widget.setMinimumSize(200, 150)
        self.notepad_area = self.dock_manager.addDockWidgetTabToArea(self.notepad_dock_widget, self.signage_area)
        self.notepad_tab.sigCreateSignage.connect(self.onCreateSignageFromNotepad)

        # Document widget
        self.evidence_tab = EvidenceTab(model=self.evidence_model)
        self.evidence_tab_dock_widget = QtAds.CDockWidget("Evidence", self)
        self.evidence_tab_dock_widget.setWidget(self.evidence_tab)
        self.evidence_tab_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.evidence_tab_dock_widget.resize(250, 150)
        self.evidence_tab_dock_widget.setMinimumSize(200, 150)
        self.evidence_tab_area = self.dock_manager.addDockWidgetTabToArea(self.evidence_tab_dock_widget, self.signage_area)
        self.evidence_tab.createRefKeyFilterPane(self.signage_treemodel)

        # Listinsight widget
        self.listinsight = ListinsightWidget(f"{AppDatabase.activeWorkspace().rootpath}/ListInsight", AppDatabase.activeWorkspace().name, self)
        self.listinsight_tab_dock_widget = QtAds.CDockWidget("ListInsight")
        self.listinsight_tab_dock_widget.setWidget(self.listinsight)
        self.listinsight_tab_dock_widget.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)
        self.listinsight_tab_dock_widget.resize(250, 150)
        self.listinsight_tab_dock_widget.setMinimumSize(200, 150)
        self.listinsight_tab_area = self.dock_manager.addDockWidgetTabToArea(self.listinsight_tab_dock_widget, self.signage_area)
        self.listinsight_tab_dock_widget.toggleView(False)

        # Menubar
        self.createMenubar()
        self.connectSignals()
        self.setupDialogs()

        # StatusBar
        # self.status_bar = QtWidgets.QStatusBar(self)
        # self.setStatusBar(self.status_bar)
        # self.status_bar.showMessage('Ready', 5000)

    def setupDialogs(self):
        self.merge_excel_dialog: MergeExcelDialog = None
        self.onenote_manager: OnenotePickerDialog = None
        self.summary_dialogs: SummaryDialog = None

    def createMenubar(self):
        """Create Application Menubar"""
        self.menubar = self.menuBar()
        self.setMenuBar(self.menubar)

        # File Menu
        self.file_menu = self.menubar.addMenu("File")
        self.file_menu.addAction(QtGui.QAction("Manage Workspace",
                                               self.menubar,
                                               triggered=self.openWorkspaceManager))
        self.file_menu.addAction(QtGui.QAction("Create Signage",
                                               self.menubar,
                                               shortcut=QtGui.QKeySequence("Ctrl+R"),
                                               triggered=lambda: self.signage_tree_tab.createSignage("", '{"application":"InspectorMate", "module":"MainWindow"}')))
        self.file_menu.addAction(QtGui.QAction("Export Signage",
                                               self.menubar,
                                               triggered=self.signage_tree_tab.onExportTriggered))
        self.file_menu.addAction(QtGui.QAction("Import Signage",
                                               self.menubar,
                                               triggered=self.signage_tree_tab.onImportTriggered))

        # Edit Menu
        self.file_open_option = QtGui.QAction("Open document with system application",
                                                  self.menubar,
                                                  triggered=self.saveSettings)
        self.edit_menu = self.menubar.addMenu("Edit")
        self.file_open_option.setCheckable(True)
        self.file_open_option.setChecked(True)
        self.edit_menu.addAction(self.file_open_option)

        self.edit_menu.addAction(QtGui.QAction(theme_icon_manager.get_icon(":onenote"),
                                               "OneNote Test connection",
                                               self,
                                               triggered=self.open_onenote_picker))
        self.edit_menu.addAction(QtGui.QAction("Edit Refkey Detection Pattern",
                                               self.menubar,
                                               triggered=self.onEditRefkeyRegexTriggered))
        self.edit_menu.addAction(QtGui.QAction("Add/Remove Owner",
                                               self.menubar,
                                               triggered=self.addRemoveOwner))

        # View Menu
        self.view_menu = self.menubar.addMenu("View")
        self.view_menu.addAction(self.signage_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.evidence_tab_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.notepad_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.listinsight_tab_dock_widget.toggleViewAction())
        self.view_menu.addSeparator()

        app_menu = QtWidgets.QMenu("Application FontSize", self.menubar)
        app_menu.addAction(QtGui.QAction("Small", self, triggered=lambda: self.setAppFont(9.0)))
        app_menu.addAction(QtGui.QAction("Medium", self, triggered=lambda: self.setAppFont(10.0)))
        app_menu.addAction(QtGui.QAction("Large", self, triggered=lambda: self.setAppFont(11.0)))
        app_menu.addAction(QtGui.QAction("Extra Large", self, triggered=lambda: self.setAppFont(13.0)))
        self.view_menu.addMenu(app_menu) 

        color_theme_menu = QtWidgets.QMenu("Color Theme", self.menubar)
        self.light_action = QtGui.QAction("Light", self, triggered=lambda: self.setColorTheme(Theme.LIGHT))
        self.light_action.setCheckable(True)
        self.dark_action = QtGui.QAction("Dark", self, triggered=lambda: self.setColorTheme(Theme.DARK))
        self.dark_action.setCheckable(True)

        if theme_icon_manager.get_theme() == Theme.DARK:
            self.dark_action.setChecked(True)
        else:
            self.light_action.setChecked(True)

        color_theme_menu.addAction(self.light_action)
        color_theme_menu.addAction(self.dark_action)
        self.view_menu.addMenu(color_theme_menu)


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
        self.tools_menu.addAction(QtGui.QAction("Batch Rename file",
                                                self.menubar,
                                                triggered=self.handleBatchRenameFile))
        
        # Help menu
        self.help_menu = self.menubar.addMenu("Help")
        self.help_menu.addAction(QtGui.QAction("Summary",
                                                self.menubar,
                                                triggered=self.showSummary))
        self.help_menu.addAction(QtGui.QAction("About InspectorMate",
                                                self.menubar,
                                                triggered=self.showAbout))
        self.help_menu.addAction(QtGui.QAction("View Debug Output",
                                                self.menubar,
                                                triggered=self.showDebugOutput))
        self.help_menu.addAction(QtGui.QAction("Open App folder",
                                                self.menubar,
                                                triggered=self.openAppFolder))

    def connectSignals(self):
        self.signage_tree_tab.sigSignageTreemodelChanged.connect(self.evidence_tab.refresh)
        self.signage_tree_tab.sigSignageDoubleClicked.connect(self.onSignageDoubleClicked)
        self.evidence_tab.sigOpenDocument.connect(self.onOpenEvidenceTriggered)
        self.evidence_tab.sigDocUploaded.connect(self.onEvidenceModelReset)
        self.evidence_tab.sigDocUploaded.connect(self.signage_tree_tab.onEvidenceModelUpdate)
        self.evidence_tab.sigStatusUpdated.connect(self.signage_tree_tab.onEvidenceModelUpdate)
        self.evidence_tab.sigRefkeyUpdated.connect(self.signage_tree_tab.onEvidenceModelUpdate)
        self.evidence_tab.sigCreateChildSignage.connect(self.signage_tree_tab.createChildSignage)
        self.evidence_tab.sigCreateSignage.connect(self.signage_tree_tab.createSignage)
        self.notebook_explorer.sigOpenFile.connect(self.onOpenFileTriggered)
        self.notebook_explorer.sigOpenNote.connect(self.onOpenNoteTriggered)
        self.workspace_explorer.sigOpenFile.connect(self.onOpenFileTriggered)
        self.workspace_explorer.sigOpenNote.connect(self.onOpenNoteTriggered)
        
        # self.signage_model.rowsInserted.connect(self.evidence_tab.request_filter_tab.updateCounter)
        # self.signage_model.rowsRemoved.connect(self.evidence_tab.request_filter_tab.updateCounter)

    @Slot()
    def showAbout(self):
        about = About()
        about.exec()

    @Slot()
    def showDebugOutput(self):
        """
        Show Debug Output
        """
        self.log_viewer = DebugLogViewer()
        self.log_viewer.showMaximized()
    
    @Slot()
    def openAppFolder(self):
        """
        Open Application Folder
        """
        utils.open_file(mconf.config.app_data_path)

    @Slot()
    def setAppFont(self, fontsize: float):
        font = QtGui.QFont()
        font.setPointSizeF(fontsize)
        QtWidgets.QApplication.setFont(font)
        mconf.settings.setValue("app_fontsize", fontsize)

    @Slot()
    def setColorTheme(self, theme: Theme):
        if theme == Theme.DARK:
            self.light_action.setChecked(False)
        elif theme == Theme.LIGHT:
            self.dark_action.setChecked(False)

        mconf.settings.setValue("app_color_theme", theme.value)
        theme_icon_manager.set_theme(theme)

    @Slot()
    def addRemoveOwner(self):
        dlg = OwnerDialog()
        dlg.exec()

    @Slot()
    def onEditRefkeyRegexTriggered(self):
        """Edit Refkey Detection RegEx Pattern"""
        if mconf.settings.value("regex") is None or mconf.settings.value("regex") == "":
            regex = mconf.default_regex
        else:
            regex = mconf.settings.value("regex")

        text, ok = QtWidgets.QInputDialog.getText(self,
                                                  "Signage/Evidence Refkey Detection Pattern",
                                                  f"Actual RegEx pattern: {mconf.settings.value("regex")}\nNew RegEx:",
                                                  QtWidgets.QLineEdit.EchoMode.Normal,
                                                  regex)
        if ok:
            mconf.settings.setValue("regex", text)

    def loadSettings(self):
        if mconf.settings.value("USE_DEFAULT_FILEOPENER") == 'false':
            self.file_open_option.setChecked(False)
        else:
            self.file_open_option.setChecked(True)

    @Slot(str)
    def onSignageDoubleClicked(self, refkey: str):
        self.evidence_tab.filterWithRefkey(refkey)
        self.evidence_tab_dock_widget.toggleView(True)

    @Slot(str)
    def onOpenFileTriggered(self, filepath):
        utils.open_file(filepath)

    @Slot(object, QtCore.QModelIndex)
    def onOpenEvidenceTriggered(self, doc: Document, index):
        if self.file_open_option.isChecked():
            utils.open_file(doc.filepath)
            return

        if doc.id in self.doc_viewers:
            self.doc_viewers[doc.id].toggleView(True)
            return

        self.viewer = self.viewer_factory.viewer(doc, index)

        if self.viewer is not None:
            doc_dock_widget = QtAds.CDockWidget(doc.title[:15])
            doc_dock_widget.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetDeleteOnClose, True)
            doc_dock_widget.closed.connect(self.evidence_tab_dock_widget.setAsCurrentTab) #  Activate Evidence tab after closing a document viewer
            doc_dock_widget.setWidget(self.viewer)
            self.dock_manager.addDockWidgetTabToArea(doc_dock_widget, self.evidence_tab_area)
            self.doc_viewers[doc.id] = doc_dock_widget
            self.viewer.sigCreateChildSignage.connect(self.signage_tree_tab.createChildSignage)
            doc_dock_widget.closed.connect(lambda: self.onViewerClosed(doc_dock_widget.widget().document.id))
            # self.viewer.note_tab.sig_create_request.connect(self.createSignageFromNote)

    @Slot(str)
    def onOpenNoteTriggered(self, filepath):
        self.notepad_tab.loadfile(filepath)
        self.notepad_dock_widget.toggleView()

    @Slot(str, str, str)
    def onCreateSignageFromNotepad(self, title, source: str, hanchor: str):
        """Create a signage from Notepad/Notebook"""
        if self.signage_tree_tab.createSignage(title, source):
            signage = self.signage_tree_tab.signage_dialog.getNewSignage()
            self.notepad_tab.insertSignage(signage, hanchor)           

    #TODO
    @Slot(object)
    def createSignageFromNote(self, caller: RichTextEditor):
        """Create signage from note editor"""
        title = caller.editor.textCursor().selectedText()

        citation = caller._parent.citation()

        val = self.signage_tree_tab.createSignage(title, citation)

        if val == 1:
            signage = self.signage_tree_tab.create_dialog.getNewSignage()

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
        mconf.settings.setValue("USE_DEFAULT_FILEOPENER", self.file_open_option.isChecked())

    def set_window_title(self, text=None):
        if text is not None:
            self.setWindowTitle(f'{mconf.config.app_name} - {text}')
    
    @Slot()
    def onViewerClosed(self, id: int):
        """Remove the document viewer from the dict when tab is closed"""
        self.doc_viewers.pop(id)

    @Slot()
    def onEvidenceModelReset(self):
        """Reset the DataWidgetMapper index after loading file into the document model

        Index is lost after refreshing the model.
        Therefore, it's necessary to reset the index of the viewer mapper to keep mapper synchronization.
        """
        for row in range(self.evidence_model.rowCount()):
            index = self.evidence_model.index(row, self.evidence_model.Fields.ID.index)
            doc_id = index.data(Qt.ItemDataRole.DisplayRole)

            if doc_id in self.doc_viewers:
                dock_widget: QtAds.CDockWidget = self.doc_viewers.get(doc_id)
                if dock_widget:
                    widget: ViewerWidget = dock_widget.widget()
                    widget.setMapperIndex(index)

    @Slot()
    def openWorkspaceManager(self):
        if self.workspace_manager is None:
            self.workspace_manager = WorkspaceManagerDialog()
            self.workspace_manager.sigWorkspaceChanged.connect(self.onWorkspaceChanged)
        self.workspace_manager.exec()

    @Slot()
    def handleMergeExcelFiles(self):
        self.merge_excel_dialog = MergeExcelDialog()
        self.merge_excel_dialog.exec()

    @Slot()
    def handleUnzipArchive(self):
        self.unzip_dialog = UnzipDialog(source=AppDatabase.activeWorkspace().rootpath, dest=AppDatabase.activeWorkspace().evidence_path)
        self.unzip_dialog.exec()

    @Slot()
    def handleBatchRenameFile(self):
        self.dlg = BatchRenameWidget()
        self.dlg.show()

    @Slot()
    def handleUnpackPDF(self):
        file = QtWidgets.QFileDialog.getOpenFileName(caption="Select file", directory=AppDatabase.activeWorkspace().evidence_path, filter="*.pdf")

        if file[0] != "":
            err = utils.unpackPDF(file[0])

            if isinstance(err, Exception):
                QtWidgets.QMessageBox.critical(self, "unpackPDF -- Error", f"{err}")
            elif err:
                QtWidgets.QMessageBox.information(self, "unpackPDF -- Success", "PDF successfully unpacked")

    @Slot()
    def onWorkspaceChanged(self):
        self.evidence_tab.refresh()
        self.signage_tree_tab.refresh()
        self.workspace_explorer.set_root_path(AppDatabase.activeWorkspace().rootpath)
        self.notebook_explorer.set_root_path(AppDatabase.activeWorkspace().notebook_path)
        self.set_window_title(AppDatabase.activeWorkspace().name)
        self.notepad_tab.close_all()
        self.signage_treemodel.cacheOESignage()

        # Close all viewer tabs
        dockwidget: QtAds.CDockWidget
        for dockwidget in self.doc_viewers.copy().values():
            dockwidget.closeDockWidget()

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

    @Slot()
    def showSummary(self):
        if self.summary_dialogs is None:
            self.summary_dialogs = SummaryDialog()
            self.summary_dialogs.sigReload.connect(self.refreshSummary)
            self.signage_summary_model = SummaryModel()
            self.evidence_summary_model = SummaryModel()
            self.summary_dialogs.signagetable.setModel(self.signage_summary_model)
            self.summary_dialogs.evidencetable.setModel(self.evidence_summary_model)

        self.refreshSummary()
        self.summary_dialogs.adjust_size()
        self.summary_dialogs.show()
    
    def refreshSummary(self):
        s_data, s_vheaders, s_hheaders = self.signage_treemodel.summary()
        e_data, e_vheaders, e_hheaders = self.evidence_model.summary()
        self.signage_summary_model.loadData(s_data, s_vheaders, s_hheaders)
        self.evidence_summary_model.loadData(e_data, e_vheaders, e_hheaders)


    def closeEvent(self, event: QtCore.QEvent):
        msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self,
                                               f'Closing {mconf.config.app_name}',
                                               msg,
                                               QtWidgets.QMessageBox.StandardButton.Ok,
                                               QtWidgets.QMessageBox.StandardButton.No)

        if reply == QtWidgets.QMessageBox.StandardButton.Ok:
            logging.shutdown()
            self.evidence_tab.close()
            self.signage_tree_tab.close()
            self.notepad_tab.close_all()
            AppDatabase.close()
            event.accept()
        else:
            event.ignore()
