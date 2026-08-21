import logging
from importlib.metadata import version
from pathlib import Path

from listinsight import ListinsightWidget
from listinsight.gui import status_signal as listinsight_status_signal
from my_pyqt_widgets import (
    About,
    EmojiPickerWidget,
    FileSystem,
    LogViewer,
    create_action,
)
from pyqtspinner import WaitingSpinner
from qt_theme_manager import Theme, theme_icon_manager

from base_models import SummaryModel
from common import Document, Signage, SignageOrigin
from database.database import AppDatabase
from documentviewer.viewerfactory import ViewerFactory
from documentviewer.viewermanager import DockInDockWidget
from documentviewer.viewerwidget import ViewerWidget
from evidence.model import EvidenceModel
from evidence.view import EvidenceTab
from onenote.view import OnenotePickerDialog
from qtpy import Qt, QtAds, QtCore, QtGui, QtWidgets, Slot
from signage.connector_model import ConnectorModel
from signage.connector_widget import ConnectorManagerDialog
from signage.dialogs import OwnerDialog
from signage.model import SignageModel
from signage.view import SignageTab
from utilities import utils
from utilities.decorators import status_message, status_signal
from utilities.settings import get_settings
from widgets.app_updater import Updater, get_latest_release
from widgets.batch_renamer import BatchRenameWidget
from widgets.filedialog import ConcatExcelDialog, UnzipDialog
from widgets.richtexteditor import RichTextEditor
from widgets.summarydialog import SummaryDialog
from workspace.view import WorkspaceManagerDialog


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.force_close = False
        self.signage_treemodel = SignageModel()
        self.evidence_model = EvidenceModel()
        self.viewer_factory = ViewerFactory(self.evidence_model, self)
        self.workspace_manager = None
        self.connector_model = ConnectorModel()

        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.eConfigFlag.OpaqueSplitterResize, True
        )
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.eConfigFlag.XmlCompressionEnabled, False
        )
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.eConfigFlag.FocusHighlighting, True
        )
        QtAds.CDockManager.setAutoHideConfigFlag(
            QtAds.CDockManager.eAutoHideFlag.DefaultAutoHideConfig, True
        )
        self.dock_manager = QtAds.CDockManager(self)

    def initUI(self):
        """Initialize the MainWindow User Interface"""

        self.set_window_title(AppDatabase.activeWorkspace().name)

        # Workspace FileSystem Sidebar
        self.workspace_explorer_dock_widget = QtAds.CDockWidget("Workspace", self)
        self.workspace_explorer_dock_widget.setFeature(
            QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False
        )
        self.workspace_explorer = FileSystem(
            AppDatabase.activeWorkspace().rootpath, read_only=False
        )
        self.workspace_explorer_dock_widget.setWidget(self.workspace_explorer)
        self.workspace_explorer_dock_widget.setMinimumSize(200, 150)
        self.workspace_explorer_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize
        )
        self.workspace_doc_widget_container = self.dock_manager.addAutoHideDockWidget(
            QtAds.SideBarLocation.SideBarLeft, self.workspace_explorer_dock_widget
        )
        self.workspace_doc_widget_container.setMinimumWidth(250)

        # Evidence Explorer FileSystem Sidebar
        self.evidence_explorer_dock_widget = QtAds.CDockWidget("Evidence", self)
        self.evidence_explorer_dock_widget.setFeature(
            QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False
        )
        self.evidence_explorer = FileSystem(
            AppDatabase.activeWorkspace().evidence_path, read_only=False
        )
        self.evidence_explorer_dock_widget.setWidget(self.evidence_explorer)
        self.evidence_explorer_dock_widget.setMinimumSize(200, 150)
        self.evidence_explorer_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize
        )
        self.evidence_doc_widget_container = self.dock_manager.addAutoHideDockWidget(
            QtAds.SideBarLocation.SideBarLeft, self.evidence_explorer_dock_widget
        )
        self.evidence_doc_widget_container.setMinimumWidth(250)

        # Notebook Explorer FileSystem Sidebar
        self.notebook_explorer_dock_widget = QtAds.CDockWidget("Notebook", self)
        self.notebook_explorer_dock_widget.setFeature(
            QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False
        )
        self.notebook_explorer = FileSystem(
            AppDatabase.activeWorkspace().notebook_path, read_only=False
        )
        self.notebook_explorer_dock_widget.setWidget(self.notebook_explorer)
        self.notebook_explorer_dock_widget.setMinimumSize(200, 150)
        self.notebook_explorer_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize
        )
        self.notebook_doc_widget_container = self.dock_manager.addAutoHideDockWidget(
            QtAds.SideBarLocation.SideBarLeft, self.notebook_explorer_dock_widget
        )
        self.notebook_doc_widget_container.setMinimumWidth(250)

        # Emoji Sidebar
        self.emoji_widget_dock_widget = QtAds.CDockWidget("Emoji", self)
        self.emoji_widget = EmojiPickerWidget()
        self.emoji_widget_dock_widget.setWidget(self.emoji_widget)
        self.emoji_widget_dock_widget.setMinimumSize(200, 150)
        self.emoji_widget_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidgetMinimumSize
        )
        self.emoji_doc_widget_container = self.dock_manager.addAutoHideDockWidget(
            QtAds.SideBarLocation.SideBarLeft, self.emoji_widget_dock_widget
        )
        self.emoji_doc_widget_container.setMinimumWidth(250)
        self.emoji_widget_dock_widget.toggleView(False)

        # Signage
        self.signage_dock_widget = QtAds.CDockWidget("Signage")
        self.signage_tree_tab = SignageTab(
            self.signage_treemodel, self.startSpinner, self.stopSpinner
        )
        self.signage_dock_widget.setWidget(self.signage_tree_tab)
        self.signage_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget
        )
        self.signage_dock_widget.resize(250, 150)
        self.signage_dock_widget.setMinimumSize(200, 150)
        main_dock_area = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.CenterDockWidgetArea, self.signage_dock_widget
        )
        if theme_icon_manager.get_theme() == Theme.DARK:
            main_dock_area.setStyleSheet("color: white;")

        # Notebook widget
        self.notepad_tab = RichTextEditor(
            base_folder=AppDatabase.activeWorkspace().notebook_path,
            template_folder=f"{get_settings().APP_DATA_PATH}/template",
            settings=get_settings().qsettings,
            parent=self,
        )
        self.notepad_dock_widget = QtAds.CDockWidget("Notebook", self)
        self.notepad_dock_widget.setWidget(self.notepad_tab)
        self.notepad_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget
        )
        self.notepad_dock_widget.resize(250, 150)
        self.notepad_dock_widget.setMinimumSize(200, 150)
        self.notepad_area = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.CenterDockWidgetArea,
            self.notepad_dock_widget,
            main_dock_area,
        )
        self.notepad_tab.sigCreateSignage.connect(self.onCreateSignageFromNotepad)

        # Document widget
        self.evidence_tab = EvidenceTab(
            model=self.evidence_model,
            signage_model=self.signage_treemodel,
            startSpinner=self.startSpinner,
            stopSpinner=self.stopSpinner,
        )
        self.evidence_tab_dock_widget = QtAds.CDockWidget("Evidence", self)
        self.evidence_tab_dock_widget.setWidget(self.evidence_tab)
        self.evidence_tab_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget
        )
        self.evidence_tab_dock_widget.resize(250, 150)
        self.evidence_tab_dock_widget.setMinimumSize(200, 150)
        self.evidence_tab_area = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.CenterDockWidgetArea,
            self.evidence_tab_dock_widget,
            main_dock_area,
        )

        # Listinsight widget
        self.listinsight = ListinsightWidget(
            f"{AppDatabase.activeWorkspace().rootpath}/ListInsight", self
        )
        self.listinsight_tab_dock_widget = QtAds.CDockWidget("ListInsight")
        self.listinsight_tab_dock_widget.setWidget(self.listinsight)
        self.listinsight_tab_dock_widget.setMinimumSizeHintMode(
            QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget
        )
        self.listinsight_tab_dock_widget.resize(250, 150)
        self.listinsight_tab_dock_widget.setMinimumSize(200, 150)
        self.listinsight_tab_area = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.CenterDockWidgetArea,
            self.listinsight_tab_dock_widget,
            main_dock_area,
        )
        self.listinsight_tab_dock_widget.toggleView(False)

        # Viewer manager
        self.viewer_manager = DockInDockWidget(self)
        self.viewer_manager_cdock = QtAds.CDockWidget("Document Viewer", self)
        self.viewer_manager_cdock.setWidget(self.viewer_manager)
        self.dock_manager = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.CenterDockWidgetArea,
            self.viewer_manager_cdock,
            main_dock_area,
        )
        self.viewer_manager_cdock.toggleView(False)

        # Menubar
        self.createMenubar()
        self.connectSignals()
        self.setupDialogs()

        # StatusBar
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.setStyleSheet("""
                                      QStatusBar {
                                            border-top: 2px solid #0078d7;
                                        }
                                      """)
        self.setStatusBar(self.status_bar)
        status_signal.status_message.connect(self.status_bar.showMessage)
        self.status_bar.showMessage("✔️ Ready!", 30000)
        listinsight_status_signal.status_message.connect(self.status_bar.showMessage)

        self.spinner = WaitingSpinner(self, True, True)
        self.onWorkspaceChanged()

    def startSpinner(self, msg="", msec=7000):
        status_signal.status_message.emit(msg, msec)
        self.spinner.start()
        QtWidgets.QApplication.processEvents()

    def stopSpinner(self, msg="", msec=7000):
        self.spinner.stop()
        status_signal.status_message.emit(msg, msec)

    def checkUpdate(self):
        if not get_settings().get_update_show_option():
            return

        self.startSpinner("Checking for update...")
        release = get_latest_release()

        if release:
            self.updater = Updater(release, self)
            self.updater.show()
        else:
            msg = "No updates found!"
        self.stopSpinner(msg)

    def onCheckForUpdatesTriggered(self):
        get_settings().set_update_show_option(True)
        self.checkUpdate()

    def setupDialogs(self):
        self.concat_excel_dialog: ConcatExcelDialog = None
        self.onenote_manager: OnenotePickerDialog = None
        self.summary_dialogs: SummaryDialog = None
        self.log_viewer: LogViewer = None

    def createMenubar(self):
        """Create Application Menubar"""
        self.menubar = self.menuBar()
        self.setMenuBar(self.menubar)

        # File Menu
        self.file_menu = self.menubar.addMenu("File")
        self.action_workspace_manager = create_action(
            self,
            "manage_workspace",
            "Manage Workspace",
            self.openWorkspaceManager,
            theme_icon_manager.get_icon(":archive-2-line"),
            "Manage Workspace",
        )
        self.file_menu.addAction(self.action_workspace_manager)

        signage_source = SignageOrigin(get_settings().APP_NAME, "MainWindow")
        self.action_create_signage = create_action(
            self,
            "create_signage",
            "Create Signage",
            lambda: self.signage_tree_tab.createSignage(signage_source, ""),
            theme_icon_manager.get_icon(":signpost-line"),
            "Ctrl+R",
            context=Qt.ShortcutContext.ApplicationShortcut,
        )
        self.file_menu.addAction(self.action_create_signage)
        self.signage_tree_tab.toolbar.register_action(
            "create_signage", self.action_create_signage, "create_child_signage"
        )
        self.evidence_tab.toolbar.register_action(
            "create_signage", self.action_create_signage, "create_child_signage"
        )

        self.action_export_signage = create_action(
            self,
            "export_signage",
            "Export Signage",
            self.signage_tree_tab.onExportTriggered,
            theme_icon_manager.get_icon(":share-forward-2-line"),
        )
        self.file_menu.addAction(self.action_export_signage)

        self.action_import_signage = create_action(
            self,
            "import_signage",
            "Import Signage",
            self.signage_tree_tab.onImportTriggered,
            theme_icon_manager.get_icon(":download-2-line"),
        )
        self.file_menu.addAction(self.action_import_signage)

        # Edit Menu
        self.edit_menu = self.menubar.addMenu("Edit")

        self.action_file_open_option = create_action(
            self,
            "file_open_option",
            "Open document with system application",
            self.saveSettings,
            checkable=True,
        )
        self.edit_menu.addAction(self.action_file_open_option)

        self.action_onenote_test_connection = create_action(
            self,
            "onenote_test_connection",
            "OneNote Test connection",
            self.open_onenote_picker,
            theme_icon_manager.get_icon(":onenote"),
        )
        self.edit_menu.addAction(self.action_onenote_test_connection)

        self.action_edit_refkey_pattern = create_action(
            self,
            "edit_refkey_pattern",
            "Edit Refkey Detection Pattern",
            self.onEditRefkeyRegexTriggered,
            theme_icon_manager.get_icon(":key-2-line"),
        )
        self.edit_menu.addAction(self.action_edit_refkey_pattern)

        self.action_edit_owner = create_action(
            self,
            "edit_owner",
            "Add/Remove Owner",
            self.addRemoveOwner,
            theme_icon_manager.get_icon(":user-line"),
        )
        self.edit_menu.addAction(self.action_edit_owner)

        self.action_edit_signage_connectors = create_action(
            self,
            "edit_signage_connector",
            "Manage Signage Connectors",
            self.manageConnectors,
            theme_icon_manager.get_icon(":links-line"),
        )
        self.edit_menu.addAction(self.action_edit_signage_connectors)

        # View Menu
        self.view_menu = self.menubar.addMenu("View")
        self.view_menu.addAction(self.signage_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.evidence_tab_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.notepad_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.listinsight_tab_dock_widget.toggleViewAction())
        self.view_menu.addAction(self.viewer_manager_cdock.toggleViewAction())
        self.view_menu.addSeparator()

        self.action_close_all_viewer_tab = create_action(
            self,
            "close_all_viewer_tab",
            "Close all document viewer",
            self.viewer_manager.closeAllTabWidget,
        )
        self.view_menu.addAction(self.action_close_all_viewer_tab)

        self.action_close_all_other_tabs = create_action(
            self,
            "close_all_others",
            "Close all other document viewers",
            self.viewer_manager.closeAllOtherTabWidget,
        )
        self.view_menu.addAction(self.action_close_all_other_tabs)

        self.view_menu.addSeparator()

        self.action_set_alternating_color = create_action(
            self,
            "set_alternating_color",
            "Alternating table row color",
            self.saveSettings,
            checkable=True,
        )
        self.view_menu.addAction(self.action_set_alternating_color)

        self.font_menu = QtWidgets.QMenu("Application FontSize", self.menubar)

        self.font_menu.addAction(
            QtGui.QAction("Small", self, triggered=lambda: self.setAppFont(9.0))
        )
        self.font_menu.addAction(
            QtGui.QAction("Medium", self, triggered=lambda: self.setAppFont(10.0))
        )
        self.font_menu.addAction(
            QtGui.QAction("Large", self, triggered=lambda: self.setAppFont(11.0))
        )
        self.font_menu.addAction(
            QtGui.QAction("Extra Large", self, triggered=lambda: self.setAppFont(13.0))
        )
        self.view_menu.addMenu(self.font_menu)

        # Tools Menu
        self.tools_menu = self.menubar.addMenu("Tools")
        self.action_concat_excel = create_action(
            self,
            "concat_xls",
            "Concatenate Excel files",
            self.concatExcelFiles,
            theme_icon_manager.get_icon(":git-merge-line"),
        )
        self.tools_menu.addAction(self.action_concat_excel)
        self.tools_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":inbox-unarchive-line"),
                "Unzip archive",
                self.menubar,
                triggered=self.unzipArchive,
            )
        )
        self.tools_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":file-zip-line"),
                "Unpack PDF",
                self.menubar,
                triggered=self.unpackPDF,
            )
        )
        self.tools_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":input-field"),
                "Batch Rename file",
                self.menubar,
                triggered=self.batchRenameFile,
            )
        )
        self.action_toggle_emoji = create_action(
            self,
            "toggle_emoji",
            "Emoji Dialog",
            lambda: self.emoji_widget_dock_widget.toggleView(
                not self.emoji_widget_dock_widget.isVisible()
            ),
            theme_icon_manager.get_icon(":emoji-sticker-line"),
            "Ctrl+E",
            context=Qt.ShortcutContext.ApplicationShortcut,
        )
        self.tools_menu.addAction(self.action_toggle_emoji)

        # Help menu
        self.help_menu = self.menubar.addMenu("Help")
        self.help_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":table-2"),
                "Summary",
                self.menubar,
                triggered=self.showSummary,
            )
        )
        self.help_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":information-2-line"),
                "About InspectorMate",
                self.menubar,
                triggered=self.showAbout,
            )
        )
        self.help_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":bug-line"),
                "View Debug Output",
                self.menubar,
                triggered=self.showDebugOutput,
            )
        )
        self.help_menu.addAction(
            QtGui.QAction(
                theme_icon_manager.get_icon(":folder-open-line"),
                "Open App folder",
                self.menubar,
                triggered=self.openAppFolder,
            )
        )

        self.action_check_updates_onStartUp = create_action(
            self,
            "check_update_onStartUp",
            "Check for updates on StartUp",
            lambda: get_settings().set_update_show_option(
                self.action_check_updates_onStartUp.isChecked()
            ),
            checkable=True,
        )
        self.action_check_updates_onStartUp.setChecked(
            get_settings().get_update_show_option()
        )
        self.help_menu.addAction(self.action_check_updates_onStartUp)

        self.action_check_updates = create_action(
            self,
            "check_update",
            "Check for updates...",
            self.onCheckForUpdatesTriggered,
        )
        self.help_menu.addAction(self.action_check_updates)

    def connectSignals(self):
        self.signage_tree_tab.sigSignageDoubleClicked.connect(
            self.onSignageDoubleClicked
        )
        self.signage_tree_tab.sigOpenNote.connect(self.onOpenFileTriggered)
        self.evidence_model.modelReset.connect(self.onEvidenceModelReset)
        self.evidence_tab.sigOpenDocument.connect(self.onOpenEvidenceTriggered)
        self.evidence_tab.sigCreateChildSignage.connect(
            self.signage_tree_tab.createChildSignage
        )
        self.evidence_tab.sigCreateSignage.connect(self.signage_tree_tab.createSignage)
        self.evidence_tab.sigUpdateReviewProgress.connect(
            self.signage_tree_tab.updateReviewProgess
        )
        self.evidence_model.sigUpdateReviewProgress.connect(
            self.signage_tree_tab.updateReviewProgess
        )

        # Open files
        self.notebook_explorer.sigOpenFile.connect(self.onOpenFileTriggered)
        self.notebook_explorer.sigDoubleClicked.connect(self.onOpenFileTriggered)
        self.workspace_explorer.sigOpenFile.connect(self.onOpenFileTriggered)
        self.workspace_explorer.sigDoubleClicked.connect(self.onOpenFileTriggered)
        self.evidence_explorer.sigOpenFile.connect(self.onOpenFileTriggered)
        self.evidence_explorer.sigDoubleClicked.connect(self.onOpenFileTriggered)

    @Slot()
    def showAbout(self):
        text = f"""InspectorMate version {get_settings().APP_VERSION}
        Listinsight version {version("listinsight")}
        Instance ID: {get_settings().instance_id()}
        Author: {get_settings().APP_AUTHOR}\n
        Property of {get_settings().ORG_NAME}
        """
        about = About("About InspectorMate", text, ":mylogo", parent=self)
        about.setMinimumWidth(250)
        about.show()

    @Slot()
    def showDebugOutput(self):
        """Show Debug Output"""
        self.log_viewer = LogViewer.load_from_file(
            get_settings().LOG_PATH.as_posix(), "Debug log"
        )
        self.log_viewer.showMaximized()

    @Slot()
    def openAppFolder(self):
        """Open Application Folder"""
        utils.open_file(get_settings().APP_DATA_PATH)

    @Slot()
    def setAppFont(self, fontsize: float):
        font = QtGui.QFont()
        font.setPointSizeF(fontsize)
        QtWidgets.QApplication.setFont(font)
        get_settings().set_app_font_size(fontsize)

    @Slot()
    def addRemoveOwner(self):
        dlg = OwnerDialog()
        dlg.exec()

    @Slot()
    def manageConnectors(self):
        dlg = ConnectorManagerDialog(self.connector_model)
        dlg.exec()

    @Slot()
    def onEditRefkeyRegexTriggered(self):
        """Edit Refkey Detection RegEx Pattern"""
        regx = get_settings().get_signage_pattern()
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Signage/Evidence Refkey Detection Pattern",
            f"Actual RegEx pattern: {regx}\nNew RegEx:",
            QtWidgets.QLineEdit.EchoMode.Normal,
            regx,
        )
        if ok:
            get_settings().set_signage_pattern(text)

    def loadSettings(self):
        self.action_file_open_option.setChecked(get_settings().get_file_open_option())
        self.action_set_alternating_color.setChecked(
            get_settings().get_alternating_row_coloring()
        )
        self.onSettingsChanged()

    @Slot()
    def saveSettings(self):
        get_settings().set_file_open_option(self.action_file_open_option.isChecked())
        get_settings().set_alternating_row_coloring(
            self.action_set_alternating_color.isChecked()
        )
        self.onSettingsChanged()

    def onSettingsChanged(self):
        coloring = get_settings().get_alternating_row_coloring()
        self.signage_tree_tab.table.setAlternatingRowColors(coloring)
        self.evidence_tab.table.setAlternatingRowColors(coloring)

    @Slot(str)
    def onSignageDoubleClicked(self, refkey: str):
        self.evidence_tab.filterWithRefkey(refkey)
        self.evidence_tab_dock_widget.toggleView(True)

    @Slot(str)
    def onOpenFileTriggered(self, filepath, anchor: str = ""):
        fpath = Path(filepath)
        if not fpath.is_file() or fpath.is_dir():
            return

        if fpath.suffix == ".html":
            self.notepad_tab.loadfile(file_path=filepath, anchor=anchor)
            self.notepad_dock_widget.toggleView()
        else:
            utils.open_file(filepath)

    @Slot(object, QtCore.QModelIndex)
    def onOpenEvidenceTriggered(self, doc: Document, index):
        if self.action_file_open_option.isChecked():
            utils.open_file(doc.filepath)
            return

        self.viewer = self.viewer_factory.viewer(doc, index)

        if self.viewer is not None:
            self.viewer.sigCreateChildSignage.connect(
                self.signage_tree_tab.createChildSignage
            )
            self.viewer_manager.addTabWidget(self.viewer, doc.title)
            self.viewer_manager_cdock.toggleView(True)
        else:
            status_signal.status_message.emit(
                "Cannot open file with InspectorMate - Trying with system app...", 7000
            )
            utils.open_file(doc.filepath)

    @Slot(str, dict, str)
    def onCreateSignageFromNotepad(self, title, source: dict, anchor: str):
        """Create a signage from Notepad/Notebook"""
        if self.signage_tree_tab.createSignage(title, source):
            signage: Signage = self.signage_tree_tab.signage_dialog.signage()
            icon = AppDatabase.cache_signage_type.get(signage.type).icon
            color = AppDatabase.cache_signage_type.get(signage.type).color
            self.notepad_tab.insertSignage(
                icon, color, signage.type, signage.refkey, signage.title, anchor
            )

    def set_window_title(self, text=None):
        if text is not None:
            self.setWindowTitle(f"{get_settings().APP_NAME} - {text}")

    @Slot()
    def onEvidenceModelReset(self):
        """Reset the DataWidgetMapper index after loading file into the document model

        Index is lost after refreshing the model.
        Therefore, it's necessary to reset the index of the viewer mapper to keep mapper synchronization.
        """
        dw_list = self.viewer_manager.getManager().allDockWidgets(True, True)

        for row in range(self.evidence_model.rowCount()):
            index = self.evidence_model.index(row, self.evidence_model.Fields.ID.index)
            doc_id = index.data(Qt.ItemDataRole.DisplayRole)

            dw: QtAds.CDockWidget
            for _, dw in dw_list:
                widget: ViewerWidget = dw.widget()
                if isinstance(widget, ViewerWidget) and widget.document.id == doc_id:
                    widget.setMapperIndex(index)

    @Slot()
    def openWorkspaceManager(self):
        if self.workspace_manager is None:
            self.workspace_manager = WorkspaceManagerDialog()
            self.workspace_manager.sigWorkspaceChanged.connect(self.onWorkspaceChanged)
        self.workspace_manager.exec()

    @Slot()
    def concatExcelFiles(self):
        self.concat_excel_dialog = ConcatExcelDialog(
            start_process=self.startSpinner, process_ended=self.stopSpinner
        )
        self.concat_excel_dialog.exec()

    @Slot()
    def unzipArchive(self):
        self.unzip_dialog = UnzipDialog(
            source=AppDatabase.activeWorkspace().rootpath,
            dest=AppDatabase.activeWorkspace().evidence_path,
            start_process=self.startSpinner,
            process_ended=self.stopSpinner,
        )
        self.unzip_dialog.exec()

    @Slot()
    def batchRenameFile(self):
        self.dlg = BatchRenameWidget()
        self.dlg.show()

    @Slot()
    def unpackPDF(self):
        file = QtWidgets.QFileDialog.getOpenFileName(
            caption="Select file",
            directory=AppDatabase.activeWorkspace().evidence_path,
            filter="*.pdf",
        )

        if file[0] != "":
            err = utils.unpackPDF(file[0])

            if isinstance(err, Exception):
                QtWidgets.QMessageBox.critical(self, "unpackPDF -- Error", f"{err}")
            elif err:
                QtWidgets.QMessageBox.information(
                    self, "unpackPDF -- Success", "PDF successfully unpacked"
                )

    def disable_all(self):
        self.evidence_tab.setEnabled(False)
        self.signage_tree_tab.setEnabled(False)
        self.notebook_explorer.setEnabled(False)
        self.workspace_explorer.setEnabled(False)
        self.notepad_tab.setEnabled(False)
        for menu in self.menuBar().findChildren(QtWidgets.QMenu):
            for action in menu.actions():
                if action is not self.action_workspace_manager:
                    action.setEnabled(False)

    def enable_all(self):
        self.evidence_tab.setEnabled(True)
        self.signage_tree_tab.setEnabled(True)
        self.notebook_explorer.setEnabled(True)
        self.notepad_tab.setEnabled(True)
        self.workspace_explorer.setEnabled(True)
        for menu in self.menuBar().findChildren(QtWidgets.QMenu):
            for action in menu.actions():
                action.setEnabled(True)

    @status_message("Updating Workspace...", 10000)
    @Slot()
    def onWorkspaceChanged(self):
        if AppDatabase.activeWorkspace().id == 0:
            self.disable_all()
        else:
            self.enable_all()

        self.evidence_tab.refresh()
        self.signage_treemodel.rootModel().refresh()
        self.signage_treemodel.buildFromSqlModel()
        self.signage_treemodel.updateReviewProgess()
        self.connector_model.refresh()
        self.workspace_explorer.set_root_path(AppDatabase.activeWorkspace().rootpath)
        self.evidence_explorer.set_root_path(
            AppDatabase.activeWorkspace().evidence_path
        )
        self.notebook_explorer.set_root_path(
            AppDatabase.activeWorkspace().notebook_path
        )
        self.set_window_title(AppDatabase.activeWorkspace().name)
        self.notepad_tab.close_all()
        self.listinsight.setRootPath(
            f"{AppDatabase.activeWorkspace().rootpath}/ListInsight"
        )
        self.viewer_manager.closeAllTabWidget()

        status_signal.status_message.emit("Workspace changed!", 5000)

    @status_message("Connecting to OneNote...")
    @Slot()
    def open_onenote_picker(self):
        onenote_warning = QtWidgets.QMessageBox.warning(
            self,
            "Warning",
            (
                "Establishing a connection to OneNote before opening "
                "the application may put the application in a hang state"
                "\n\nIt's recommended to open OneNote app "
                "before establishing a connection"
            ),
            buttons=(
                QtWidgets.QMessageBox.StandardButton.Ignore
                | QtWidgets.QMessageBox.StandardButton.Cancel
            ),
        )

        if onenote_warning == QtWidgets.QMessageBox.StandardButton.Cancel:
            return

        if self.onenote_manager is None:
            self.onenote_manager = OnenotePickerDialog(self)

        self.onenote_manager.show()
        self.onenote_manager.connect()

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

    def closeDialogs(self):
        if self.concat_excel_dialog:
            self.concat_excel_dialog.close()
        if self.onenote_manager:
            self.onenote_manager.close()
        if self.summary_dialogs:
            self.summary_dialogs.close()
        if self.log_viewer:
            self.log_viewer.close()

    def closeEvent(self, event: QtCore.QEvent):
        # If forced programmatic close, skip confirmation

        if self.force_close:
            logging.shutdown()
            self.closeDialogs()
            self.evidence_tab.close()
            self.signage_tree_tab.close()
            self.notepad_tab.close_all()
            AppDatabase.close()
            event.accept()
            return

        # Normal behavior: ask user for confirmation
        msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(
            self,
            f"Closing {get_settings().APP_NAME}",
            msg,
            QtWidgets.QMessageBox.StandardButton.Ok
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Ok:
            logging.shutdown()
            self.closeDialogs()
            self.evidence_tab.close()
            self.signage_tree_tab.close()
            self.notepad_tab.close_all()
            AppDatabase.close()
            event.accept()
        else:
            event.ignore()
