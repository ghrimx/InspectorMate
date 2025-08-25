import sys, os, requests, subprocess
import logging
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel,
    QProgressBar, QMessageBox,
    QDialogButtonBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from utilities.config import config


logger = logging.getLogger(__name__)


GITHUB_RELEASES = "https://api.github.com/repos/ghrimx/InspectorMate/releases"
ALLOW_PRERELEASE = True

def get_latest_release() -> str | None:
    try:
        releases = requests.get(GITHUB_RELEASES, timeout=5).json()
        latest_release = releases[0]

        latest_version = latest_release["tag_name"]

        if latest_version != config.app_version:
            logger.info(f"New release available. Version: {latest_version}")
            return latest_release
        else:
            return None
    except Exception as e:
        logger.warning("Error", f"Update check failed: {e}")
        return None


class Downloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, dest):
        super().__init__()
        self.url = url
        self.dest = dest

    def run(self):
        try:
            r = requests.get(self.url, stream=True, timeout=10)
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(self.dest, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(int(downloaded * 100 / total))
            self.finished.emit(self.dest)
        except Exception as e:
            self.finished.emit("ERROR:" + str(e))


class Updater(QDialog):
    def __init__(self, release, parent = None):
        super().__init__(parent)
        self._parent = parent
        self.setModal(True)
        self.release = release
        self.setWindowTitle("Update Available")
        self.setFixedSize(350, 150)

        vbox = QVBoxLayout(self)
        self.label = QLabel(f"Version {release["tag_name"]} is available.\nDo you want to install it?")
        vbox.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        vbox.addWidget(self.progress)

        buttons = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox = QDialogButtonBox(buttons)

        buttonBox.accepted.connect(self.start_update)
        buttonBox.rejected.connect(self.reject)

        vbox.addWidget(buttonBox)

    def start_update(self):
        # find installer asset
        assets = self.release.get("assets", [])
        for a in assets:
            if a["name"].endswith(".exe"):
                url = a["browser_download_url"]
                installer = os.path.join(os.getenv("TEMP"), a["name"])
                self.progress.setVisible(True)
                self.downloader = Downloader(url, installer)
                self.downloader.progress.connect(self.progress.setValue)
                self.downloader.finished.connect(self.run_installer)
                self.downloader.start()
                self.label.setText("Downloading update...")
                return
        QMessageBox.warning(self, "Error", "No installer found in release.")

    def run_installer(self, path):
        if path.startswith("ERROR:"):
            QMessageBox.critical(self, "Download Failed", path)
            self.close()
            return

        self.label.setText("Running installer...")
        subprocess.Popen([path])
        self.label.setText("The installer is running.\nThe app will now close.")
        self._parent.force_close = True
        self._parent.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Updater()

    sys.exit(app.exec())
