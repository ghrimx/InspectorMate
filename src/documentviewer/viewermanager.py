import PyQt6Ads as QtAds
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon


class DockInDockManager(QtAds.CDockManager):
    def __init__(self, parent: 'DockInDockWidget'):
        super().__init__()
        self.__parent = parent

    def parent(self) -> 'DockInDockWidget':
        return self.__parent
         
    def getGroupName(self) -> str:
        return self.parent().objectName()
        
    @staticmethod
    def dockInAManager(widget) -> 'DockInDockManager':
        
        dock_widget =  widget.widget() if widget else None
        return dock_widget.getManager() if isinstance(dock_widget, DockInDockWidget) else None
        
    def childManagers(self, managers: 'list[DockInDockManager]', rec: bool) -> None:
        widgets = self.getWidgetsInGUIOrder()
        for widget in widgets:
            as_mgr = DockInDockManager.dockInAManager(widget)
            if as_mgr:
                managers.append(as_mgr)
                if rec:
                    as_mgr.childManagers(managers, rec)
                    
    def allManagers(self, include_self: bool, rec: bool) -> 'list[DockInDockManager]':
        managers = []
        if include_self:
            managers.append(self)
        self.childManagers(managers, rec)
        return managers
        
    def getWidgetsInGUIOrder(self) -> 'list[QtAds.CDockWidget]':
        result = []
        for i in range(self.dockAreaCount()):
            for widget in self.dockArea(i).dockWidgets():
                result.append(widget)
        return result    

    def allDockWidgets(self, include_self: bool, rec: bool) -> 'list[tuple[DockInDockManager, QtAds.CDockWidget]]':
        widgets = []
        for mgr in self.allManagers(include_self, rec):
            for widget in mgr.getWidgetsInGUIOrder():
                widgets.append((mgr, widget))
        return widgets            


class DockInDockWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.__mgr = DockInDockManager(self)
        self.__mgr.setConfigFlag(QtAds.CDockManager.eConfigFlag.HideSingleCentralWidgetTitleBar, False)
        self.__mgr.setConfigFlag(QtAds.CDockManager.eConfigFlag.DockAreaHasCloseButton, False)
        layout.addWidget(self.__mgr)
        
    def getManager(self) -> 'DockInDockManager':
        return self.__mgr
    
    def ensure_center_anchor(self):
        if getattr(self, "_center_anchor", None) is None:
            anchor = QtAds.CDockWidget("CENTER_ANCHOR")
            anchor.setObjectName("CENTER_ANCHOR")
            anchor.setWidget(QWidget())  # empty
            anchor.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetDeleteOnClose, False)
            anchor.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)
            anchor.setFeature(QtAds.CDockWidget.DockWidgetFeature.NoTab, True)
            anchor.setMinimumSizeHintMode(QtAds.CDockWidget.eMinimumSizeHintMode.MinimumSizeHintFromDockWidget)

            area = self.__mgr.addDockWidget(QtAds.DockWidgetArea.CenterDockWidgetArea, anchor)
            self._center_anchor = anchor
            self._center_area = area
            area.destroyed.connect(lambda: setattr(self, "_center_area", None))

    def addTabWidget(self, widget: QWidget, name: str, icon=QIcon()):
        self.ensure_center_anchor()

        # show if already exists
        for _, existing in self.getManager().allDockWidgets(True, True):
            if existing.objectName() == name:
                existing.toggleView(True)
                return self._center_area

        dock = QtAds.CDockWidget(name)
        dock.setObjectName(name)
        dock.setWidget(widget)
        dock.setIcon(icon)
        dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetDeleteOnClose, True)

        # Always tab into the anchor area
        return self.__mgr.addDockWidget(QtAds.DockWidgetArea.CenterDockWidgetArea, dock, self._center_area)
    
    def closeAllTabWidget(self):     
        to_close = []

        dw: QtAds.CDockWidget
        for _, dw in self.__mgr.allDockWidgets(True, True):
            to_close.append(dw)

        for dw in to_close:
            if hasattr(dw, "closeDockWidget"):
                dw.closeDockWidget()
            else:
                # Fallback: request closing via QWidget API
                dw.close()
