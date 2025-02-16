from krita import *

class APEKritaTools(Extension):

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def system_check(self):
        # QMessageBox creates quick popup with information
        messageBox = QMessageBox()
        messageBox.setInformativeText(Application.version())
        messageBox.setWindowTitle('Open ZT1 Graphic')
        messageBox.setStandardButtons(QMessageBox.Close)
        messageBox.setIcon(QMessageBox.Information)
        messageBox.exec()

    def createActions(self, window):
        action = window.createAction("", "Open ZT1 Graphic")
        action.triggered.connect(self.system_check)