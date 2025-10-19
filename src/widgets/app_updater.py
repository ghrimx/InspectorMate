import sys, os, requests, subprocess, feedparser
import logging
from pathlib import Path
import shutil
import datetime
from packaging.version import Version
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel,
    QProgressBar, QMessageBox,
    QDialogButtonBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from utilities.config import config

logger = logging.getLogger(__name__)

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["ALL_PROXY"] = ""


OWNER = "ghrimx"
REPO = "InspectorMate"
feed_url = f"https://github.com/{OWNER}/{REPO}/releases.atom"
headers = {"User-Agent": "MyApp/1.0"}  

def get_latest_release() -> str | None:
    try:
        
        resp = requests.get(feed_url, headers=headers, proxies={})
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        if not feed.entries:
            logger.info(f"No releases found at {feed_url}")
            return None

        latest = feed.entries[0]
        # Extract version/tag from the entry ID (last part of the URL)
        tag = latest.id.rsplit("/", 1)[-1]

        if Version(tag) > Version(config.app_version):
            logger.info(f"\n\tCurrent version: {config.app_version}\n\tNew release available. Version: {tag}")
            return tag
        
        logger.info(f"Current version is latest")

    except Exception as e:
        logger.warning(f"Update check failed: {e}")

def backup_file(file_path: Path, backup_dir: Path):
    """
    Backup a single file to backup_dir with a timestamp.
    """
    if not file_path.exists():
        return  # nothing to backup

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{file_path.name}.{timestamp}.bak"
    shutil.copy2(file_path, backup_file)
    logger.error(f"Backed up {file_path} >>> {backup_file}")


class Downloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, dest):
        super().__init__()
        self.url = url
        self.dest = dest

    def run(self):
        try:
            r = requests.get(self.url, stream=True, timeout=10, proxies={}, headers=headers)
            
            logger.info(f"url:{self.url} - response:{r.status_code}")
            logger.debug(f"Proxy for 'https://github.com' = {requests.utils.get_environ_proxies("https://github.com")}")
            logger.debug(f"Proxy for 'https://api.github.com' = {requests.utils.get_environ_proxies("https://api.github.com")}")

            if r.status_code == 404:
                err = "ERROR: 404 - File not found"
                logger.error(err)
                self.finished.emit(err)
                return

            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(self.dest, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(int(downloaded * 100 / total))
            
            logger.info("Download completed")

            if os.path.getsize(self.dest) < 500_000:
                logger.error(f"ERROR: Downloaded file too small, probably not the installer\n\tfilepath:{self.dest}")
                self.finished.emit("ERROR: Downloaded file too small, probably not the installer")
                return

            self.finished.emit(self.dest)

        except Exception as e:
            err = f"ERROR: Download failed (HTTP {r.status_code}) - error = {e}"
            logger.error(err)
            self.finished.emit(err)


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

        self.buttons = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QDialogButtonBox(self.buttons)

        self.buttonBox.accepted.connect(self.start_update)
        self.buttonBox.rejected.connect(self.reject)

        vbox.addWidget(self.buttonBox)

    def start_update(self):
        self.buttonBox.hide()
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
        
        backup_file(config.db_path, config.app_data_path)

        logger.info("Running installer...")

        self.label.setText("Running installer...")
        try:
            subprocess.Popen([path],
                             close_fds=True,)
        except Exception as e:
            logger.error(e)

        self.label.setText("The installer is running.\nThe app will now close.")
        self._parent.force_close = True
        self._parent.close()
