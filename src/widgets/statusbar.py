from qtpy import QtWidgets

class Statusbar(QtWidgets.QStatusBar):
    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.message = None
        self.progressbar = None

    def updateProgressbar(self, progress):
        if progress < 100:
            self.progressbar = QtWidgets.QProgressBar(self)
            self.progressbar.setVisible(progress)
            self.progressbar.setValue(progress)

            self.status_bar.addWidget(self.page_load_pb)
            self.status_bar.addWidget(self.page_load_label)
        else:
            self.status_bar.removeWidget(self.page_load_pb)
            self.status_bar.removeWidget(self.page_load_label)


    def updateMessage(self, message, timeout = 5000):
        self.message = message
        self.showMessage(self.message, timeout)