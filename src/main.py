import logging
import logging.config
import sys

from qt_theme_manager import Theme, theme_icon_manager

from database.database import AppDatabase
from mainwindow import MainWindow
from qtpy import Qt, QtCore, QtGui, QtWidgets
from utilities.settings import get_settings
from utilities.utils import trim_file

logger = logging.getLogger(__name__)


def main() -> int:
    """Initializes the application and runs it.

    Returns:
        int: The exit status code.
    """
    # Initialize the App
    QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.Round
    )
    app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Init settings
    get_settings().ensure_files()
    get_settings().instance_id()

    app.setOrganizationName(get_settings().ORG_NAME)
    app.setOrganizationDomain(get_settings().ORG_DOMAIN)
    app.setApplicationName(get_settings().APP_NAME)
    app.setStyle(get_settings().app_style())
    app.setWindowIcon(QtGui.QIcon(get_settings().APP_LOGO))
    app.setApplicationVersion(get_settings().APP_VERSION)

    trim_file(get_settings().LOG_PATH.as_posix())

    app_font = app.font()
    app_font.setPointSizeF(get_settings().get_app_font_size())
    app.setFont(app_font)

    if theme_icon_manager.is_dark_mode(app):
        theme_icon_manager.set_theme(Theme.DARK)
    else:
        theme_icon_manager.set_theme(Theme.LIGHT)

    # Splashscreen
    pixmap = QtGui.QPixmap(get_settings().APP_LOGO)
    splash = QtWidgets.QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage(
        "Starting ...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white
    )

    app.processEvents()

    # Post init configuration
    splash.showMessage(
        "Post Init Config ...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white
    )

    app.processEvents()

    # Init logger
    logging.config.fileConfig(
        get_settings().CONFIG_PATH.as_posix(),
        disable_existing_loggers=False,
        defaults={"logfilepath": get_settings().LOG_PATH.as_posix()},
    )
    logger.info(f"Current logging level: {logging.getLevelName(logging.root.level)}")

    # Set Taskbar Icon
    try:
        from ctypes import windll

        appid = f"{get_settings().ORG_NAME}.{get_settings().APP_NAME}.{get_settings().APP_VERSION}"
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except ImportError:
        logger.error(ImportError.msg)

    splash.showMessage("Connecting to the database ...")

    logger.info("Starting InspectorMate...")

    # Connect to database
    AppDatabase.connect(get_settings().DB_PATH.as_posix())
    AppDatabase.setup()

    # Initialize the main window
    mainwindow: MainWindow = MainWindow()
    mainwindow.initUI()
    mainwindow.showMaximized()

    splash.finish(mainwindow)

    mainwindow.loadSettings()
    QtCore.QTimer.singleShot(500, mainwindow.checkUpdate)

    return sys.exit(app.exec())


if __name__ == "__main__":
    sys.exit(main())
