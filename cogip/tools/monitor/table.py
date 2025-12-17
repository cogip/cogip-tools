from PySide6.QtCore import QObject


class Table:
    def __init__(self, root: QObject):
        self.root = root
        self.node = self.root.findChild(QObject, "Scene")
        self.models = [m for m in self.node.children() if m.metaObject().className() == "QQuick3DModel"]
        for model in self.models:
            model.setObjectName(f"table_{model.objectName()}")
            model.setProperty("pickable", True)
