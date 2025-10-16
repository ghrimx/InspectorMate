import sys
import logging
import logging.config
from uuid import uuid4
from qtpy import (QtWidgets, QtGui, Qt)
from database.database import AppDatabase
from mainwindow import MainWindow
from utilities import config as mconf
from utilities.utils import trim_file
from qt_theme_manager import theme_icon_manager, Theme


logger = logging.getLogger(__name__)


def main() -> int:
    """Initializes the application and runs it.

    Returns:
        int: The exit status code.
    """
    # Initialize the App
    app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("FAMHP")
    app.setOrganizationDomain("famhp.net")
    app.setApplicationName(mconf.config.app_name)
    app.setStyle("Fusion") 
    app.setWindowIcon(QtGui.QIcon(":mylogo"))
    app.setApplicationVersion(mconf.config.app_version)

    if (mconf.settings.value("InstanceId") is None 
        or mconf.settings.value("InstanceId") == ""):
        mconf.settings.setValue("InstanceId", str(uuid4()))

    trim_file(mconf.config.log_path.as_posix())

    app_fontsize = mconf.settings.value("app_fontsize")
    if app_fontsize is not None:
        app_font = app.font()
        app_font.setPointSizeF(float(app_fontsize))
        app.setFont(app_font)

    if theme_icon_manager.is_dark_mode(app):
        theme_icon_manager.set_theme(Theme.DARK)
    else:
        theme_icon_manager.set_theme(Theme.LIGHT)

    # Splashscreen
    pixmap = QtGui.QPixmap(":mylogo")
    splash = QtWidgets.QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("Starting ...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)

    app.processEvents()

    # Post init configuration
    splash.showMessage("Post Init Config ...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)

    app.processEvents()

    # Init logger
    logging.config.fileConfig(mconf.config.config_path.as_posix(),
                              disable_existing_loggers=False,
                              defaults={'logfilepath': mconf.config.log_path.as_posix()})

    # Set Taskbar Icon
    try:
        from ctypes import windll
        appid = "fahmp.inspectormate.v1.0"
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except ImportError:
        logger.error(ImportError.msg)
        pass

    splash.showMessage("Connecting to the database ...")

    logger.info(f"Starting InspectorMate...")

    # Connect to database
    AppDatabase.connect(mconf.config.db_path.as_posix())
    AppDatabase.setup()

    # Initialize the main window
    mainwindow: MainWindow = MainWindow()
    mainwindow.initUI()
    mainwindow.showMaximized()

    splash.finish(mainwindow)

    mainwindow.loadSettings()
    mainwindow.checkUpdate()

    return sys.exit(app.exec())

if __name__ == '__main__':
    sys.exit(main())
