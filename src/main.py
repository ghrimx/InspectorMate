import sys
import logging
import logging.config

from qtpy import (QtWidgets, QtGui, Qt)

from db.database import AppDatabase

from mainwindow import MainWindow

from utilities import config as mconf

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

    app_fontsize = mconf.settings.value("app_fontsize")
    if app_fontsize is not None:
        app_font = app.font()
        app_font.setPointSizeF(float(app_fontsize))
        app.setFont(app_font)

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

    # Connect to database
    db = AppDatabase()
    db.connect(mconf.config.db_path.as_posix())
    db.setup()

    # Initialize the main window
    mainwindow: MainWindow = MainWindow()
    mainwindow.initUI()
    mainwindow.showMaximized()

    splash.finish(mainwindow)

    mainwindow.loadSettings()

    return sys.exit(app.exec())


if __name__ == '__main__':
    sys.exit(main())
