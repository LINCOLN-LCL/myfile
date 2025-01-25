import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QLineEdit, QPushButton, QMessageBox, QTextEdit, QDialog, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

FILENAME_LEN = 256

class FileNode:
    def __init__(self, filename, isdir, parent=None):
        self.filename = filename
        self.isdir = isdir
        self.i_nlink = 1
        self.adr = 0
        self.parent = parent
        self.child = None
        self.sibling_prev = None
        self.sibling_next = None
        self.content = ""  # 添加文件内容属性

class Filesystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.root = FileNode("/", True)
        self.current_node = self.root
        self.initUI()
        self.updateTree()

    def initUI(self):
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(["Name", "Type"])
        self.treeWidget.itemSelectionChanged.connect(self.onSelectionChanged)

        self.pathLineEdit = QLineEdit()
        self.pathLineEdit.setPlaceholderText("Enter path")
        self.pathLineEdit.returnPressed.connect(self.onPathEntered)

        self.createDirButton = QPushButton("Create Directory")
        self.createDirButton.clicked.connect(self.onCreateDir)

        self.createFileButton = QPushButton("Create File")
        self.createFileButton.clicked.connect(self.onCreateFile)

        self.deleteButton = QPushButton("Delete")
        self.deleteButton.clicked.connect(self.onDelete)

        self.editButton = QPushButton("Edit")
        self.editButton.clicked.connect(self.onEdit)

        layout = QVBoxLayout()
        layout.addWidget(self.treeWidget)
        layout.addWidget(self.pathLineEdit)
        layout.addWidget(self.createDirButton)
        layout.addWidget(self.createFileButton)
        layout.addWidget(self.deleteButton)
        layout.addWidget(self.editButton)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setWindowTitle("Filesystem Simulation")
        self.setGeometry(300, 300, 600, 400)

    def updateTree(self, node=None):
        if node is None:
            node = self.root
        self.treeWidget.clear()
        self.addTreeItems(node, self.treeWidget.invisibleRootItem())

    def addTreeItems(self, node, parent_item):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, node.filename)
        item.setText(1, "Directory" if node.isdir else "File")
        if node.child:
            self.addTreeItems(node.child, item)
        sibling = node.sibling_next
        while sibling:
            self.addTreeItems(sibling, parent_item)
            sibling = sibling.sibling_next

    def onSelectionChanged(self):
        selected_item = self.treeWidget.currentItem()
        if selected_item:
            node = self.getNodeFromItem(selected_item)
            self.current_node = node

    def getNodeFromItem(self, item):
        path = []
        while item:
            path.append(item.text(0))
            item = item.parent()
        path.reverse()
        node = self.root
        for name in path[1:]:  # Skip the root '/'
            if node.child and node.child.filename == name:
                node = node.child
            else:
                sibling = node.child
                while sibling:
                    if sibling.filename == name:
                        node = sibling
                        break
                    sibling = sibling.sibling_next
        return node

    def onPathEntered(self):
        path = self.pathLineEdit.text()
        node = self.findNode(path)
        if node:
            self.current_node = node
            self.updateTree(node)
        else:
            QMessageBox.warning(self, "Error", "Directory not found")

    def findNode(self, path):
        names = path.split("/")
        node = self.root
        for name in names:
            if name == "":
                continue
            if node.child and node.child.filename == name:
                node = node.child
            else:
                sibling = node.child
                while sibling:
                    if sibling.filename == name:
                        node = sibling
                        break
                    sibling = sibling.sibling_next
                else:
                    return None
        return node

    def addChildNode(self, parent_node, new_node):
        if parent_node.child:
            new_node.sibling_next = parent_node.child
            parent_node.child.sibling_prev = new_node
        parent_node.child = new_node

    def onCreateDir(self):
        path = self.pathLineEdit.text()
        names = path.split("/")
        if len(names) > 1:
            dir_name = names[-1]
            parent_path = "/".join(names[:-1])
            parent_node = self.findNode(parent_path)
        else:
            dir_name = path
            parent_node = self.current_node

        if parent_node and parent_node.isdir:
            if not self.findNode(path):
                new_node = FileNode(dir_name, True, parent_node)
                self.addChildNode(parent_node, new_node)
                self.updateTree()
            else:
                QMessageBox.warning(self, "Error", "Directory already exists")
        else:
            QMessageBox.warning(self, "Error", "Parent is not a directory or not found")

    def onCreateFile(self):
        path = self.pathLineEdit.text()
        names = path.split("/")
        if len(names) > 1:
            file_name = names[-1]
            parent_path = "/".join(names[:-1])
            parent_node = self.findNode(parent_path)
        else:
            file_name = path
            parent_node = self.current_node

        if parent_node and parent_node.isdir:
            if not self.findNode(path):
                new_node = FileNode(file_name, False, parent_node)
                self.addChildNode(parent_node, new_node)
                self.updateTree()
            else:
                QMessageBox.warning(self, "Error", "File already exists")
        else:
            QMessageBox.warning(self, "Error", "Parent is not a directory or not found")

    def onDelete(self):
        selected_item = self.treeWidget.currentItem()
        if selected_item:
            node = self.getNodeFromItem(selected_item)
            if node.isdir:
                reply = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this directory and all its contents?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.deleteNode(node)
            else:
                self.deleteNode(node)

    def deleteNode(self, node):
        if node.parent:
            if node.parent.child == node:
                node.parent.child = node.sibling_next
                if node.sibling_next:
                    node.sibling_next.sibling_prev = None
            else:
                sibling = node.parent.child
                while sibling and sibling.sibling_next != node:
                    sibling = sibling.sibling_next
                if sibling:
                    sibling.sibling_next = node.sibling_next
                    if node.sibling_next:
                        node.sibling_next.sibling_prev = sibling
        if node.child:
            sibling = node.child
            while sibling:
                next_sibling = sibling.sibling_next
                self.deleteNode(sibling)
                sibling = next_sibling
        del node
        self.updateTree()

    def onEdit(self):
        selected_item = self.treeWidget.currentItem()
        if selected_item:
            node = self.getNodeFromItem(selected_item)
            if not node.isdir:
                self.editFile(node)

    def editFile(self, node):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit File: " + node.filename)
        layout = QVBoxLayout()

        textEdit = QTextEdit()
        textEdit.setText(node.content)
        layout.addWidget(textEdit)

        saveButton = QPushButton("Save")
        saveButton.clicked.connect(lambda: self.saveFile(node, textEdit, dialog))
        layout.addWidget(saveButton)

        dialog.setLayout(layout)
        dialog.exec_()

    def saveFile(self, node, textEdit, dialog):
        node.content = textEdit.toPlainText()
        QMessageBox.information(self, "Success", "File saved successfully")
        dialog.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fs = Filesystem()
    fs.show()
    sys.exit(app.exec_())