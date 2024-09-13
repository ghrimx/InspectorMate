from qtpy import QtWidgets

def selectFilesDialog(filter: str = None, dir: str = None) -> list[str]:
    files = QtWidgets.QFileDialog.getOpenFileNames(caption="Select files", directory=dir, filter=filter)
    return files[0]