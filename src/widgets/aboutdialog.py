from qtpy import QtCore, QtWidgets, QtGui
from utilities import config as mconf
from importlib.metadata import version 


class About(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(About, self).__init__(parent)

        self.setWindowTitle("About InspectorMate")
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        icon_label = QtWidgets.QLabel()
        icon_label.setMargin(5)
        icon_label.setPixmap(QtGui.QIcon(":mylogo").pixmap(64, 64, QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On))
        layout.addWidget(icon_label, 0, 0, 3, 1)

        version_label = QtWidgets.QLabel(f"InspectorMate version {mconf.config.app_version}")
        listinsight_label = QtWidgets.QLabel(f"Listinsight version {version("listinsight")}")
        software_id_label = QtWidgets.QLabel(f"Instance ID: {mconf.settings.value("InstanceId")}")
        software_id_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(version_label, 0, 1)
        layout.addWidget(listinsight_label, 1, 1)
        layout.addWidget(software_id_label, 2, 1)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttonBox = QtWidgets.QDialogButtonBox(buttons)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox, 3, 1)