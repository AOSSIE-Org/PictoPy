#! /usr/bin/env python3

'''
Simple Photo Collage application
Author: Oxben <oxben@free.fr>

-*- coding: utf-8 -*-
'''

import getopt
import json
import logging
import os
import signal
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QStyle
from PyQt5.QtWidgets import QBoxLayout, QVBoxLayout, QSpacerItem
from PyQt5.QtWidgets import QToolBar, QLabel, QComboBox
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsView, QGraphicsScene
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QOpenGLWidget, QColorDialog

from PyQt5.QtGui import QPainter, QPen, QBrush, QPixmap, QImage, QIcon, QDrag, QColor, QPalette

from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, QPointF, QMimeData

RotOffset   = 5.0
ScaleOffset = 0.05
SmallScaleOffset = 0.01
MaxZoom     = 2.0
FrameRadius = 15
MaxFrameRadius = 60
FrameWidth  = 10.0
CollageAspectRatio = (3.0 / 2.0)
CollageSize = QRectF(0, 0, 2048, 2048 * (1 / CollageAspectRatio))
LimitDrag   = True
OutFileName = ''
FrameColor = Qt.white
FrameBgColor = QColor(216, 216, 216)
LastDirectory = None
DefaultPhoto = 'icon-photo-128x128.png'
DarkTheme = False

OpenGLRender = False

filenames = []
app = None

HelpCommands = [
    ('Left Button',   'Drag image'),
    ('Right Button',  'Drag to swap two images'),
    ('Wheel',         'Zoom image'),
    ('Shift + Wheel', 'Rotate image'),
    ('Double Click',  'Load new image'),
    ('+/-',           'Increase/Decrease photo frame'),
    ('Shift + S',     'Save as collage'),
    ('S',             'Save collage'),
    ('R',             'Rotate photo by 90° clockwise'),
    ('Shift + R',     'Rotate photo by 90° counter-clockwise'),
    ('F',             'Fit photo into frame (fill frame)'),
    ('Shitf + F',     'Fit photo into frame (fit both dimensions)'),
    ('Numpad /',      'Reset photo position, scale and rotation'),
    ('D',             'Toggle dark theme'),
]

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------
class PhotoFrameItem(QGraphicsItem):
    '''The frame around a photo'''

    def __init__(self, rect, parent=None):
        super(PhotoFrameItem, self).__init__(parent)
        self.rect = rect
        self.photo = None
        # Set flags
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemClipsChildrenToShape |
                      QGraphicsItem.ItemIsFocusable)
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

    #-------------------------------------------------------
    def setPhoto(self, photo, reset=True):
        '''Set PhotoItem associated to this frame'''
        self.photo = photo
        self.photo.setParentItem(self)
        if reset:
            self.photo.reset()
            self.fitPhoto()
        self.update()

    #-------------------------------------------------------
    def fitPhoto(self, fillAllFrame=True):
        '''Fit photo to frame'''
        photoWidth = self.photo.pixmap().width()
        photoHeight = self.photo.pixmap().height()
        frameWidth = self.rect.width()
        frameHeight = self.rect.height()
        widthRatio = 0
        heightRatio = 0
        if photoWidth > frameWidth:
            widthRatio = photoWidth / frameWidth
        if photoHeight > frameHeight:
            heightRatio = photoHeight / frameHeight
        if fillAllFrame:
            # Fill all the frame, scaling based on the smallest dimension
            if widthRatio > 1 and heightRatio > 1:
                if widthRatio < heightRatio:
                    self.photo.setScale(frameWidth / photoWidth)
                else:
                    self.photo.setScale(frameHeight / photoHeight)
        else:
            # Make both dimensions fit in the frame, scaling based on the biggest dimension
            if widthRatio > 1 and widthRatio > heightRatio:
                self.photo.setScale(frameWidth / photoWidth)
            elif heightRatio > 1:
                self.photo.setScale(frameHeight / photoHeight)

    #-------------------------------------------------------
    def boundingRect(self):
        '''Return bouding rectangle'''
        return QRectF(self.rect)

    #-------------------------------------------------------
    def paint(self, painter, option, widget=None):
        '''Paint widget'''
        pen = painter.pen()
        pen.setColor(FrameColor)
        #pen.setWidth(FrameWidth)
        pen.setWidth(FrameRadius)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRoundedRect(self.rect.left(), self.rect.top(),
                                self.rect.width(), self.rect.height(),
                                FrameRadius, FrameRadius)

    #-------------------------------------------------------
    def hoverEnterEvent(self, event):
        '''Handle mouse hover event'''
        # Request keyboard events
        self.setFocus()

    #-------------------------------------------------------
    def hoverLeaveEvent(self, event):
        '''Handle mouse leave event'''
        self.clearFocus()

    #-------------------------------------------------------
    def keyReleaseEvent(self, event):
        '''Handle key release event'''
        logger.debug(str(event.key()))
        modifiers = event.modifiers()
        if event.key() == Qt.Key_Slash:
            # Reset photo pos, scale and rotation
            self.photo.reset()
        elif event.key() == Qt.Key_F:
            # Fit photo into frame
            if modifiers == Qt.NoModifier:
                self.photo.reset()
                self.fitPhoto()
            elif modifiers == Qt.ShiftModifier:
                self.photo.reset()
                self.fitPhoto(False)
        elif event.key() == Qt.Key_R:
            # Rotate by 90 degrees
            if modifiers == Qt.NoModifier:
                rotInc = 1
            elif modifiers == Qt.ShiftModifier:
                rotInc = -1
            rot = ((self.photo.rotation() // 90) + rotInc) * 90
            self.photo.setRotation(rot)

    #-------------------------------------------------------
    def mouseDoubleClickEvent(self, event):
        '''Handle mouse double-click event'''
        global LastDirectory
        if not LastDirectory:
            LastDirectory = os.getcwd()
        filename, filetype = QFileDialog.getOpenFileName(None, 'Open File', LastDirectory, \
            "Images (*.png *.gif *.jpg);;All Files (*)")
        logger.info('Open image file: %s', filename)
        self.photo.setPhoto(filename)
        if filename:
            LastDirectory = os.path.dirname(filename)

    #-------------------------------------------------------
    def dragEnterEvent(self, event):
        '''Handle mouse drag event'''
        logger.debug('dragEnterEvent')
        mimeData = event.mimeData()
        if (mimeData.hasUrls() and len(mimeData.urls()) == 1) or mimeData.hasText():
            event.accept()
        else:
            event.ignore()

    #-------------------------------------------------------
    def dropEvent(self, event):
        '''Handle mouse drop event'''
        mimeData = event.mimeData()
        logger.debug('dropEvent: mimeData=%s', str(mimeData.urls()))
        logger.debug('dropEvent: dict=%s pos=%s', dir(event), str(event.scenePos()))
        if event.proposedAction() == Qt.CopyAction and mimeData.hasUrls():
            # New photo
            filePath = mimeData.urls()[0].toLocalFile()
            logger.debug("File dragged'n'dropped: %s", filePath)
            self.photo.setPhoto(filePath)
            self.fitPhoto()
        elif event.proposedAction() == Qt.MoveAction and mimeData.hasText():
            # Swap photos
            # Get source PhotoFrameItem and swap its photo
            logger.debug('mimeData.text=%s', mimeData.text())
            try:
                sourcePos = json.loads(mimeData.text())
                items = self.scene().items(QPointF(sourcePos['pos']['x'], sourcePos['pos']['y']))
                if items:
                    for srcItem in items:
                        if isinstance(srcItem, PhotoFrameItem):
                            photoItem = srcItem.photo
                            srcItem.setPhoto(self.photo, reset=False)
                            self.setPhoto(photoItem, reset=False)
            except Exception:
                logger.debug('dropEvent: not a "photo swap" event: %s', mimeData.text())


#-------------------------------------------------------------------------------
class PhotoItem(QGraphicsPixmapItem):
    '''A photo item'''

    #-------------------------------------------------------
    def __init__(self, filename):
        self.filename = filename
        super(PhotoItem, self).__init__(QPixmap(self.filename), parent=None)
        self.dragStartPosition = None
        self.reset()
        # Use bilinear filtering
        self.setTransformationMode(Qt.SmoothTransformation)
        # Set flags
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemStacksBehindParent)

    #-------------------------------------------------------
    def setPhoto(self, filename):
        pixmap = QPixmap(filename)
        if pixmap.width() > 0:
            logger.debug('SetPhoto(): %d %d', pixmap.width(), pixmap.height())
            self.filename = filename
            super(PhotoItem, self).setPixmap(pixmap)
            self.reset()

    #-------------------------------------------------------
    def setPixmap(self, pixmap):
        super(PhotoItem, self).setPixmap(pixmap)
        self.reset()

    #-------------------------------------------------------
    def reset(self):
        # Center photo in frame
        if self.parentItem() != None:
            frameRect = self.parentItem().boundingRect()
            self.setPos((frameRect.width() / 2) - (self.pixmap().width() / 2),
                        (frameRect.height() / 2) - (self.pixmap().height() / 2))
        # Set transform origin to center of pixmap
        origx = self.pixmap().width() / 2
        origy = self.pixmap().height() / 2
        self.setTransformOriginPoint(origx, origy)
        # Reset transformation
        self.setScale(1.0)
        self.setRotation(0.0)

    #-------------------------------------------------------
    def mouseDoubleClickEvent(self, event):
        if self.parentItem():
            # Forward event to parent frame
            self.parentItem().mouseDoubleClickEvent(event)

    #-------------------------------------------------------
    def wheelEvent(self, event):
        scale = self.scale()
        rot = self.rotation()
        if event.delta() > 0:
            logger.debug('Zoom')
            rot += RotOffset
            if scale < MaxZoom:
                if round(scale, 2) < round(ScaleOffset * 2, 2):
                    scale += SmallScaleOffset
                else:
                    scale += ScaleOffset
        else:
            logger.debug('Unzoom')
            rot -= RotOffset
            if scale >= ScaleOffset * 2:
                scale -= ScaleOffset
            elif scale >= SmallScaleOffset * 2:
                scale -= SmallScaleOffset
        # Transform based on mouse position
        # XXX: doesn't work well
        #self.setTransformOriginPoint(event.pos())
        modifiers = event.modifiers()
        if modifiers == Qt.NoModifier:
            self.setScale(scale)
            logger.debug('scale=%f', scale)
        elif modifiers == Qt.ShiftModifier:
            self.setRotation(rot)
            logger.debug('rotation=%f', rot)
        elif modifiers == (Qt.ShiftModifier|Qt.ControlModifier):
            self.setScale(scale)
            self.setRotation(rot)
            logger.debug('scale=%f rotation=%f', scale, rot)

    #-------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragStartPosition = event.pos()
        else:
            super(PhotoItem, self).mousePressEvent(event)

    #-------------------------------------------------------
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.RightButton:
            if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
                return
            else:
                # Initiate "swap photos" action
                # Pass source PhotoFrameItem coordinates in json format
                drag = QDrag(event.widget())
                mimeData = QMimeData()
                mimeData.setText('{ "pos": { "x" : %f, "y" : %f }}' % (event.scenePos().x(), event.scenePos().y()))
                drag.setMimeData(mimeData)
                dropAction = drag.exec_(Qt.MoveAction)
                logger.debug('dropAction=%s', str(dropAction))
        else:
            super(PhotoItem, self).mouseMoveEvent(event)


#-------------------------------------------------------------------------------
class AspectRatioWidget(QWidget):
    '''Widget that keeps the aspect ratio of child widget on resize'''
    def __init__(self, widget, aspectRatio):
        super(AspectRatioWidget, self).__init__()
        self.layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        self.layout.addItem(QSpacerItem(0, 0))
        self.layout.addWidget(widget)
        self.layout.addItem(QSpacerItem(0, 0))
        self.setAspectRatio(aspectRatio)

    #-------------------------------------------------------
    def setAspectRatio(self, aspectRatio):
        '''Set new aspect ratio'''
        self.aspectRatio = aspectRatio
        self.updateAspectRatio()

    #-------------------------------------------------------
    def updateAspectRatio(self):
        '''
        Update layout direction and stretch of spacer items, based on current
        size and aspect ratio, to keep the child widget's aspect ratio correct
        '''
        newAspectRatio = self.size().width() / self.size().height()
        if newAspectRatio > self.aspectRatio:
            # Too wide : set spacers at left and right
            self.layout.setDirection(QBoxLayout.LeftToRight)
            widgetStretch = self.height() * self.aspectRatio
            outerStretch = (self.width() - widgetStretch) / 2 + 0.5
        else:
            # Too tall : set spacers at top and botton
            self.layout.setDirection(QBoxLayout.TopToBottom)
            widgetStretch = self.width() * (1 / self.aspectRatio)
            outerStretch = (self.height() - widgetStretch) / 2 + 0.5

        self.layout.setStretch(0, int(outerStretch))
        self.layout.setStretch(1, int(widgetStretch))
        self.layout.setStretch(2, int(outerStretch))

    #-------------------------------------------------------
    def resizeEvent(self, event):
        '''Event received on window resize'''
        self.updateAspectRatio()


#-------------------------------------------------------------------------------
class ImageView(QGraphicsView):
    '''GraphicsView containing the scene'''

    #-------------------------------------------------------
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.helpItem = None

    #-------------------------------------------------------
    def save(self, filename):
        '''Save scene to image file'''
        self.scene().clearSelection()
        image = QImage(CollageSize.width(), CollageSize.height(), QImage.Format_RGB32)
        image.fill(Qt.black)
        painter = QPainter(image)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.render(painter)
        image.save(OutFileName)
        # Explicitely delete painter to avoid the following error:
        # "QPaintDevice: Cannot destroy paint device that is being painted" + SIGSEV
        del painter
        logger.info("Collage saved to file: %s", OutFileName)

    #-------------------------------------------------------
    def keyReleaseEvent(self, event):
        global FrameRadius
        global OutFileName
        global DarkTheme

        logger.debug('Key event: %d', event.key())
        modifiers = event.modifiers()
        key = event.key()
        if key == Qt.Key_Plus:
            # Increase frame width
            FrameRadius = min(MaxFrameRadius, FrameRadius + 1)
            self.viewport().update()

        elif key == Qt.Key_Minus:
            # Decrease frame width
            FrameRadius = max(0, FrameRadius - 1)
            self.viewport().update()

        elif key == Qt.Key_D:
            # Switch dark theme
            app.setDarkTheme(not DarkTheme)

        elif key == Qt.Key_H:
            # Show help
            if self.helpItem:
                self.helpItem.setVisible(not self.helpItem.isVisible())
            else:
                self.helpItem = HelpItem(QPoint(50, 50))
                self.scene().addItem(self.helpItem)

        elif key == Qt.Key_S:
            # Save collage to output file
            saveas = False
            if (modifiers == Qt.NoModifier and not OutFileName) or \
                modifiers == Qt.ShiftModifier:
                saveas = True
            elif modifiers == Qt.ControlModifier:
                return
            app.saveCollage(saveas)
        else:
            # Pass event to default handler
            super(ImageView, self).keyReleaseEvent(event)

    #-------------------------------------------------------
    def heightForWidth(self, w):
        logger.debug('heightForWidth(%d)', w)
        return w

    #-------------------------------------------------------
    def resizeEvent(self, event):
        self.fitInView(CollageSize, Qt.KeepAspectRatio)

    #-------------------------------------------------------
    def wheelEvent(self, event):
        # Filter wheel events
        items = self.items(event.pos())
        logger.debug('Wheel event: %s', str(items))
        if items:
            for item in items:
                if isinstance(item, PhotoItem):
                    super(ImageView, self).wheelEvent(event)


#-------------------------------------------------------------------------------
class HelpItem(QGraphicsItem):
    '''Online help'''

    #-------------------------------------------------------
    def __init__(self, point, parent=None):
        super(HelpItem, self).__init__(parent)
        lines = len(HelpCommands) + 3
        self.rect = QRect(point.x(), point.y(), 700, lines * 32)

    #-------------------------------------------------------
    def boundingRect(self):
        return QRectF(self.rect)

    #-------------------------------------------------------
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        pen = painter.pen()
        pen.setColor(QColor(128, 128, 128, 200))
        pen.setWidth(3)
        painter.setPen(pen)
        brush = painter.brush()
        brush.setColor(QColor(0, 0, 0, 200))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        painter.drawRoundedRect(self.rect.left(), self.rect.top(),
                                self.rect.width(), self.rect.height(),
                                15, 15)

        font = painter.font()
        font.setPixelSize(32)
        painter.setFont(font)
        pen = painter.pen()
        pen.setColor(QColor(255, 255, 255, 232))
        painter.setPen(pen)
        point = self.rect.topLeft() + QPoint(20, 40)
        painter.drawText(point, 'Help')

        font.setPixelSize(24)
        painter.setFont(font)
        point += QPoint(0, 16)
        for cmd, desc in HelpCommands:
            point += QPoint(0, 32)
            painter.drawText(point, cmd)
            painter.drawText(point + QPoint(200, 0), desc)


#-------------------------------------------------------------------------------
class CollageScene(QGraphicsScene):
    '''Scene containing the frames and the photos'''

    def __init__(self):
        super(CollageScene, self).__init__()
        self.bgRect = None
        self._initBackground()

    #-------------------------------------------------------
    def addPhoto(self, rect, filepath):
        '''Add a photo item to the scene'''
        logger.info('Add image: %s', filepath)
        frame = PhotoFrameItem(QRect(0, 0, rect.width(), rect.height()))
        frame.setPos(rect.x(), rect.y())
        photo = PhotoItem(filepath)
        frame.setPhoto(photo)
        # Add frame to scene
        self.addItem(frame)

    #-------------------------------------------------------
    def clear(self):
        '''Remove all items from the scene'''
        super(CollageScene, self).clear()
        self._initBackground()

    #-------------------------------------------------------
    def _initBackground(self):
        '''Add rect to provide background for PhotoFrameItem's'''
        pen = QPen(FrameBgColor)
        brush = QBrush(FrameBgColor)
        self.bgRect = QRectF(FrameWidth/2, FrameWidth/2,
                             CollageSize.width() - FrameWidth, CollageSize.height() - FrameWidth)
        self.addRect(self.bgRect, pen, brush)

    #-------------------------------------------------------
    def getPhotosPaths(self):
        '''Return list containing the paths of all the photos in the scene'''
        paths = []
        items = self.items(order=Qt.AscendingOrder)
        if items:
            for item in items:
                if isinstance(item, PhotoItem):
                    paths.append(item.filename)
        logger.debug("Current photos: %s", str(paths))
        return paths


#-------------------------------------------------------------------------------
class LoopIter:
    '''Infinite iterator: loop on list elements, wrapping to first element when last element is reached'''

    def __init__(self, l):
        self.i = 0
        self.l = l

    def __iter__(self):
        return self

    def __next__(self):
        item = self.l[self.i]
        self.i = (self.i + 1)  % len(self.l)
        return item

    def next(self):
        return self.__next__()


#-------------------------------------------------------------------------------
class PyView(QApplication):
    '''PyView class'''

    def __init__(self, argv):
        '''Constructor. Parse args and build UI.'''
        super(PyView, self).__init__(argv)
        self.win = None
        self.scene = None
        self.gfxView = None
        self.layoutCombo = None
        self.appPath = os.path.abspath(os.path.dirname(argv[0]))
        self.currentLayout = ('createColumnCollage', ('3/2B/3',))
        # Init GUI
        self.initUI()
        self.win.show()

    #-------------------------------------------------------
    def initUI(self):
        '''Init UI of the PyView application'''
        # The QWidget widget is the base class of all user interface objects in PyQt5.
        self.win = QWidget()

        # Set window title
        self.win.setWindowTitle("PyView")
        self.win.setWindowIcon(QIcon(os.path.join(self.appPath, 'icons', DefaultPhoto)))
        self.win.resize(800, 800 * round(1 / CollageAspectRatio))

        vbox = QVBoxLayout()
        self.win.setLayout(vbox)

        # Add toolbar
        toolbar = QToolBar()
        toolbar.setStyleSheet('QToolBar{spacing:5px;}')
        vbox.addWidget(toolbar)
        # Standard Qt Pixmaps: http://doc.qt.io/qt-5/qstyle.html#StandardPixmap-enum
        icon = self.style().standardIcon(getattr(QStyle, 'SP_FileIcon'))
        toolbar.addAction(icon, 'New', getattr(self, 'newCollage'))
        icon = self.style().standardIcon(getattr(QStyle, 'SP_DialogSaveButton'))
        toolbar.addAction(icon, 'Save', getattr(self, 'saveCollage'))
        # Layout combobox
        toolbar.addSeparator()
        label = QLabel('Layout: ')
        toolbar.addWidget(label)
        self.layoutCombo = QComboBox()
        self.layoutCombo.addItem('Grid 2x2', ('createGridCollage', (2, 2)))
        self.layoutCombo.addItem('Grid 3x3', ('createGridCollage', (3, 3)))
        self.layoutCombo.addItem('Grid 3x4', ('createGridCollage', (3, 4)))
        self.layoutCombo.addItem('Grid 4x3', ('createGridCollage', (4, 3)))
        self.layoutCombo.addItem('Grid 4x4', ('createGridCollage', (4, 4)))
        self.layoutCombo.addItem('Grid 5x5', ('createGridCollage', (5, 5)))
        self.layoutCombo.addItem('Grid 7x1', ('createGridCollage', (7, 1)))
        self.layoutCombo.addItem('Columns 1B/3', ('createColumnCollage', ('1B/3',)))
        self.layoutCombo.addItem('Columns 2/2B/2', ('createColumnCollage', ('2/2B/2',)))
        self.layoutCombo.addItem('Columns 3/1B/3', ('createColumnCollage', ('3/1B/3',)))
        self.layoutCombo.addItem('Columns 3/2B/3', ('createColumnCollage', ('3/2B/3',)))
        self.layoutCombo.addItem('Rows 1B/2/3/2B', ('createRowCollage', ('1B/2/3/2B',)))
        self.layoutCombo.setCurrentIndex(8)
        self.layoutCombo.currentIndexChanged[str].connect(self.layoutChangedHandler)
        toolbar.addWidget(self.layoutCombo)
        # Aspect ratio combobox
        label = QLabel('Aspect Ratio: ')
        toolbar.addWidget(label)
        self.aspectRatioCombo = QComboBox()
        self.aspectRatioCombo.addItem('1:1')
        self.aspectRatioCombo.insertSeparator(99)
        self.aspectRatioCombo.addItem('3:2')
        self.aspectRatioCombo.addItem('4:3')
        self.aspectRatioCombo.addItem('16:9')
        self.aspectRatioCombo.addItem('16:10')
        self.aspectRatioCombo.insertSeparator(99)
        self.aspectRatioCombo.addItem('2:3')
        self.aspectRatioCombo.addItem('3:4')
        self.aspectRatioCombo.setCurrentIndex(2)
        self.aspectRatioCombo.currentIndexChanged[str].connect(self.aspectRatioChangedHandler)
        toolbar.addWidget(self.aspectRatioCombo)
        # Frame color button
        toolbar.addSeparator()
        icon = QIcon(os.path.join(self.appPath, 'icons', 'frame-color.svg'))
        toolbar.addAction(icon, 'Choose frame color', getattr(self, 'setFrameColor'))

        # Create GraphicsView
        self.gfxView = ImageView()
        self.arWidget = AspectRatioWidget(self.gfxView, CollageAspectRatio)
        vbox.addWidget(self.arWidget)
        self.gfxView.setBackgroundBrush(QBrush(FrameColor))

        # Set OpenGL renderer
        if OpenGLRender:
            self.gfxView.setViewport(QOpenGLWidget())

        # Add scene
        self.scene = CollageScene()

        # Create initial collage
        funcname, args = self.currentLayout
        self.setLayout(funcname, *args)

        self.gfxView.setScene(self.scene)

    #-------------------------------------------------------
    def setLayout(self, funcname, *args):
        '''Set collage new layout'''
        logger.debug('funcname=%s *args=%s', funcname, str(args))
        # Clear all items from scene
        self.scene.clear()
        # Create new collage
        func = getattr(self, funcname)
        if args:
            func(self.scene, *args)
        else:
            func(self.scene)

    #-------------------------------------------------------
    def setDarkTheme(self, enabled):
        '''Set dark theme palette'''
        global DarkTheme
        DarkTheme = enabled
        self.setStyle("Fusion")
        if DarkTheme:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.black)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            self.setPalette(palette)
        else:
            self.setPalette(self.style().standardPalette())

    #-------------------------------------------------------
    def createGridCollage(self, scene, numx, numy):
        '''Create a collage with specified number of rows and columns'''
        f = LoopIter(filenames)
        photoWidth  = round(CollageSize.width() / numx)
        photoHeight =  round(CollageSize.height() / numy)
        for x in range(0, numx):
            for y in range(0, numy):
                scene.addPhoto(QRect(x * photoWidth, y * photoHeight, photoWidth, photoHeight), f.next())

    #-------------------------------------------------------
    def createColumnCollage(self, scene, desc):
        '''Create a collage based on the string passed in'''
        columns = desc.split('/')
        # Calculate base width
        # - Big photos are twice as wide as normal ones
        baseWidth = round(CollageSize.width() / (len(columns) + desc.count('B')))
        # Loop through all columns
        f = LoopIter(filenames)
        x = 0
        for col in columns:
            logger.debug('col=%s', col)
            photoCount = int(col.replace('B', ''))
            if 'B' in col:
                photoWidth = baseWidth * 2
            else:
                photoWidth = baseWidth
            photoHeight =  round(CollageSize.height() / photoCount)
            for y in range(0, photoCount):
                scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())
            x += photoWidth

    #-------------------------------------------------------
    def createRowCollage(self, scene, desc):
        '''Create a collage based on the string passed in'''
        rows = desc.split('/')
        # Calculate base height
        # - Big photos are twice as high as normal ones
        baseHeight = round(CollageSize.height() / (len(rows) + desc.count('B')))
        # Loop through all columns
        f = LoopIter(filenames)
        y = 0
        for row in rows:
            logger.debug('row=%s', row)
            photoCount = int(row.replace('B', ''))
            if 'B' in row:
                photoHeight = baseHeight * 2
            else:
                photoHeight = baseHeight
            photoWidth =  round(CollageSize.width() / photoCount)
            for x in range(0, photoCount):
                scene.addPhoto(QRect(x * photoWidth, y, photoWidth, photoHeight), f.next())
            y += photoHeight

    #-------------------------------------------------------
    def layoutChangedHandler(self, desc):
        '''Handler for layoutCombo signal'''
        global filenames
        self.currentLayout = self.layoutCombo.currentData()
        # Save list of displayed photos
        filenames = self.scene.getPhotosPaths()
        # Set new layout
        funcname, args = self.currentLayout
        self.setLayout(funcname, *args)

    #-------------------------------------------------------
    def aspectRatioChangedHandler(self, desc):
        '''Handler for aspectRatioCombo signal'''
        global CollageAspectRatio
        global CollageSize
        global filenames
        width, height = [int(i) for i in desc.split(':')]
        CollageAspectRatio = width / height
        CollageSize = QRectF(0, 0, 2048, 2048 * (1 / CollageAspectRatio))
        self.win.resize(self.win.width(), self.win.width() * round(1 / CollageAspectRatio))
        self.arWidget.setAspectRatio(CollageAspectRatio)
        # Save list of displayed photos
        filenames = self.scene.getPhotosPaths()
        # Clear scene
        self.scene.clear()
        # Re-create collage
        funcname, args = self.currentLayout
        self.setLayout(funcname, *args)
        #self.gfxView.setScene(self.scene)

    #-------------------------------------------------------
    def newCollage(self):
        '''New collage'''
        ret = QMessageBox.question(self.win,
                                   'New collage',
                                   'Are you sure you want to reset your collage?',
                                   defaultButton=QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            self.scene.clear()
            funcname, args = self.currentLayout
            self.setLayout(funcname, *args)

    #-------------------------------------------------------
    def saveCollage(self, saveas=True):
        '''Save action handler'''
        global OutFileName
        global LastDirectory
        if saveas or not OutFileName:
            if not LastDirectory:
                LastDirectory = os.getcwd()
            OutFileName, filetype = QFileDialog.getSaveFileName(None,
                                                                'Save Collage',
                                                                LastDirectory,
                                                                "Images (*.png *.gif *.jpg);;All Files (*)")
        if OutFileName:
            LastDirectory = os.path.dirname(OutFileName)
            self.win.setWindowTitle('PyView - %s' % OutFileName)
            self.gfxView.save(OutFileName)

    #-------------------------------------------------------
    def setFrameColor(self):
        '''Set color of the photo frames'''
        global FrameColor
        FrameColor = QColorDialog.getColor()
        self.gfxView.setBackgroundBrush(QBrush(FrameColor))


#-------------------------------------------------------------------------------
def usage():
    '''Display usage of the application'''
    print('Usage: ' +  os.path.basename(sys.argv[0]) + \
          ' [image1...imageN]')
    print("\nOptions:\n")
    print("  -h         This help message")
    print("\nCommands:\n")
    for cmd, desc in HelpCommands:
        print('  %-16s  %s' % (cmd, desc))


#-------------------------------------------------------------------------------
def parse_args():
    '''Parse application arguments. Build list of filenames.'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'Dh', ['help'])
    except getopt.GetoptError as err:
        logger.error(str(err))
        usage()
        sys.exit(1)

    for o, a in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)
        elif o == '-D':
            logger.setLevel(logging.DEBUG)

    if args:
        for f in args:
            filenames.append(os.path.abspath(f))
            logger.debug(str(filenames))
    else:
        appPath = os.path.abspath(os.path.dirname(sys.argv[0]))
        filenames.append(os.path.join(appPath, 'icons', DefaultPhoto))


#-------------------------------------------------------------------------------
def main():
    '''Main function'''
    global app
    parse_args()

    # Quit application on Ctrl+C
    # https://stackoverflow.com/questions/5160577/ctrl-c-doesnt-work-with-pyqt
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = PyView(sys.argv)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
