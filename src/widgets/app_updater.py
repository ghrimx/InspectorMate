import sys, os, requests, subprocess, feedparser
import logging
from packaging.version import Version
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel,
    QProgressBar, QMessageBox,
    QDialogButtonBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from utilities.config import config

logger = logging.getLogger(__name__)


GITHUB_RELEASES = "https://github.com/ghrimx/InspectorMate/releases/download/4.1.0a/inspectormate-4.1.0a.exe"

OWNER = "ghrimx"
REPO = "InspectorMate"
feed_url = f"https://github.com/{OWNER}/{REPO}/releases.atom"

def get_latest_release() -> str | None:
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            logger.info("No releases found")
            return None

        latest = feed.entries[0]
        # Extract version/tag from the entry ID (last part of the URL)
        tag = latest.id.rsplit("/", 1)[-1]

        if Version(tag) > Version(config.app_version):
            logger.info(f"\n\tCurrent version: {config.app_version}\n\tNew release available. Version: {tag}")
            return tag

    except Exception as e:
        logger.warning("Error", f"Update check failed: {e}")


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
        self.label = QLabel(f"Version {release} is available.\nDo you want to install it?")
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
        url = f"https://github.com/{OWNER}/{REPO}/releases/download/{self.release}/inspectormate-{self.release}.exe"
        installer = os.path.join(os.getenv("TEMP"),f"inspectormate-{self.release}.exe")
        self.progress.setVisible(True)
        self.downloader = Downloader(url, installer)
        self.downloader.progress.connect(self.progress.setValue)
        self.downloader.finished.connect(self.run_installer)
        self.downloader.start()
        self.label.setText("Downloading update...")


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
