import sys
import logging
import logging.config

from qtpy import (QtWidgets, QtGui, Qt)

from db.database import AppDatabase

from mainwindow import MainWindow

from utilities.config import config

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
    app.setApplicationName(config.app_name)
    app.setStyle("Fusion")
    app.setWindowIcon(QtGui.QIcon(":mylogo"))
    app.setApplicationVersion('1.2.1-alpha')
    app_font = app.font()
    app_font.setPointSizeF(10.0)
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
    logging.config.fileConfig(config.config_path.as_posix(),
                              disable_existing_loggers=False,
                              defaults={'logfilepath': config.log_path.as_posix()})

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
    db.connect(config.db_path.as_posix())
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
