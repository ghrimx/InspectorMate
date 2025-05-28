from qtpy import QtWidgets

#TODO
class Preference(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)

        formbox = QtWidgets.QFormLayout()
        self.setLayout(formbox)

        
