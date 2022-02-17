import signal
import sys
import matplotlib
import cv2

from PySide2 import QtCore
from matplotlib import pyplot as plt
from PySide2.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.widgets import RectangleSelector
matplotlib.use('Qt5Agg')


class ImageDisplay(FigureCanvasQTAgg):
    def __init__(self, width=4, height=4, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class MainWindow(QMainWindow):
    resized = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # States before choosing options
        self.parametr1 = None
        self.parametr2 = None
        self.image = None
        self.imagePO = None
        self.thresh = None

        # Images will be shown by using axes (Matplotlib)
        self.right = ImageDisplay()
        self.left = ImageDisplay()

        # Adding empty axes, in which images will be shown
        layout = QHBoxLayout()
        layout.addWidget(self.left)
        layout.addWidget(self.right)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Adding buttons
        layout2 = QVBoxLayout()
        layout2.addLayout(layout, stretch=1)
        layout3 = QHBoxLayout()
        # Button for choosing an image
        open_btn = QPushButton("Open image")
        open_btn.clicked.connect(self.open_image)
        # Button for image analysis
        calculate_btn = QPushButton("Calculate")
        calculate_btn.clicked.connect(self.calculate)
        # Text field for results of analysis
        self.tekst = QLabel("")
        layout3.addWidget(open_btn)
        layout3.addWidget(calculate_btn)
        layout3.addWidget(self.tekst)
        layout2.addLayout(layout3)

        # Main window
        widget = QWidget()
        widget.setLayout(layout2)
        self.setCentralWidget(widget)
        self.show()

    # Function for length
    def p1(self, height):
        self.parametr1 = height

    # Function for width
    def p2(self, width):
        self.parametr2 = width

    # With pressing results are becoming printed
    def calculate(self):
        if self.imagePO is None:
            return
        # Text representing length and width of fissure
        message1 = "Length of fissure: "
        message2 = "\nWidth of fissure: "
        message = message1 + str(self.parametr1) + message2 + str(self.parametr2)
        self.tekst.setText(message)

    # The original image
    def show_image_left(self):
        # After choosing a part of the image onselect is running
        def on_select(eclick, erelease):
            # For coordinates
            extent = rect_selector.extents
            # x coordinate for left upper corner
            x1 = int(extent[0])
            # x coordinate for right upper corner
            x2 = int(extent[1])
            # Width of image
            w = x2 - x1
            # y coordinate for right upper corner
            y1 = int(extent[2])
            # y coordinate for right lower corner
            y2 = int(extent[3])
            # Length of image
            h = y2 - y1
            # Writing second image to self.imagePO
            self.imagePO = self.image[y1:y1 + h, x1:x1 + w]
            # Showing the right image
            self.show_image_right()

        # Checking if an image was chosen
        if self.image is None:
            return
        # Showing original image
        self.left.plot = plt.imshow(self.image)
        self.left.draw()
        # User can choose a part for analysis
        rect_selector = RectangleSelector(self.left.axes, on_select, button=[1])

    # Shows the chosen part of image
    def show_image_right(self):
        if self.imagePO is None:
            return
        # Turning to greyscale
        scale_gray = cv2.cvtColor(self.imagePO, cv2.COLOR_BGR2GRAY)
        ret, self.thresh = cv2.threshold(scale_gray, 4, 255, cv2.THRESH_TOZERO)
        contours, hierarchy = cv2.findContours(self.thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > 100]
        contours.sort(key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))
        cv2.rectangle(self.imagePO, cv2.boundingRect(contours[-1]), (0, 255, 0), 2)
        x, y, width, height = cv2.boundingRect(contours[-1])
        # Calculating length
        self.p1(height)
        # Calculating width
        self.p2(width)
        self.right.axes.imshow(self.thresh)
        self.right.draw()

    # Function for choosing the image
    def open_image(self):
        # Opens a window, which allows to choose an image
        image_path = QFileDialog.getOpenFileName(self, "Select file", filter="TIFF files (*.tif)")
        # Checking if the image is really chosen
        if image_path[0] == "":
            return
        # Reading the image to self.image
        self.image = cv2.imread(image_path[0], cv2.IMREAD_COLOR)
        # Checking self.image
        if self.image is None:
            QMessageBox.warning(self, "Warning", f"Cannot open file {image_path}")
            return
        # Changing type of color
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        # Showing the image
        self.show_image_left()


if __name__ == "__main__":
    # This allows to stop running by deleting
    # handler from QT
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    w = MainWindow()
    app.exec_()
