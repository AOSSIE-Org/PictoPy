#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Create an PyQT4 application object.
a = QApplication(sys.argv)

# The QWidget widget is the base class of all user interface objects in PyQt4.
w = QWidget()

# Set window size.
w.resize(320, 240)

# Set window title
w.setWindowTitle("TreeWidget")

# Add layout
layout = QVBoxLayout()
w.setLayout(layout)

OneGB = (1024.0 * 1024.0 * 1024.0)
OneMB = (1024.0 * 1024.0)
OneKB = 1024.0

def hsize(size):
    '''returns human-readable size'''
    if size >= OneGB:
        return '%.1f GB' % (size/OneGB)
    elif size >= OneMB:
        return '%.1f MB' % (size/OneMB)
    elif size >= OneKB:
        return '%.1f KB' % (size/OneKB)
    else:
        return '%d B ' % (size)

# Add a tree widget
tree = QTreeWidget()
tree.setHeaderLabels(["Name", "Size"])
tree.setSortingEnabled(True)
tree.sortByColumn(0, Qt.AscendingOrder)
items = []
for f in os.listdir("/usr/share/pixmaps/"):
    fpath = os.path.join("/usr/share/pixmaps", f)
    if os.path.isfile(fpath):
        fstat = os.stat(fpath)
        item = QTreeWidgetItem([f, hsize(fstat.st_size)])
        item.setTextAlignment(1, Qt.AlignRight)
        items.append(item)
tree.insertTopLevelItems(0, items)
tree.resizeColumnToContents(0)
layout.addWidget(tree)

# Show window
w.show()

sys.exit(a.exec_())
