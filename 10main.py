# 중간 백업
# 현재 기능
"""

첫페이지 - 동영상 출력
두번째페이지 - 다음창으로 이동 또는 처음페이지로이동 버튼
세번째페이지 - 카메라 띄우고 화면캡쳐하는 화면
    실시간 영상출력 및
    처음으로 가는버튼
    화면캡쳐 버튼 및 기능구현

capture 버튼 누르면 5초 카운트다운이 시작되며 5초뒤에 캡에 찍힌 사진이 촬영되고 일정

"""

# PyQt5 Video player
#!/usr/bin/env python

"""

1. pyqt5 jetson환경에서 돌아가는지 확인
2. pyqt5랑 로봇과 ros topic 통신 되는지 확인하기
3. 사진 또는 동영상 촬영?
4. 사진 또는 동영상 촬영시 카메라 껐다 켰다해야하는지?


"""
# from PyQt.QtCore import *
# timerVar = QTimer()


# ros 관련 import

####

from os import walk

import cv2
import threading
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5 import QtWidgets
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Timer
import time
import os
import rospy
from std_msgs.msg import String
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction
VERSION = "Cam_display v0.10"

try:
    from PyQt5.QtCore import Qt
    pyqt5 = True
except:
    pyqt5 = False
if pyqt5:
    from PyQt5.QtCore import QTimer, QPoint, pyqtSignal
    from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLabel
    from PyQt5.QtWidgets import QWidget, QAction, QVBoxLayout, QHBoxLayout
    from PyQt5.QtGui import QFont, QPainter, QImage, QTextCursor
else:
    from PyQt4.QtCore import Qt, pyqtSignal, QTimer, QPoint
    from PyQt4.QtGui import QApplication, QMainWindow, QTextEdit, QLabel
    from PyQt4.QtGui import QWidget, QAction, QVBoxLayout, QHBoxLayout
    from PyQt4.QtGui import QFont, QPainter, QImage, QTextCursor
try:
    import Queue as Queue
except:
    import queue as Queue

IMG_SIZE = 1280, 720       # 640,480 or 1280,720 or 1920,1080
IMG_FORMAT = QImage.Format_RGB888
DISP_SCALE = 2                  # Scaling factor for display image
DISP_MSEC = 50                # Delay between display cycles
CAP_API = cv2.CAP_ANY       # API: CAP_ANY or CAP_DSHOW etc...
EXPOSURE = 0                 # Zero for automatic exposure
TEXT_FONT = QFont("Courier", 10)

camera_num = 1                 # Default camera (first in list)
image_queue = Queue.Queue()     # Queue to hold images
capturing = True              # Flag to indicate capturing

# PATH = "/home/source/catkin_ws/src/pyqt_test/drawer/wave.mp4"
PATH = "/home/source/catkin_ws/src/pyqt_test/script/output.avi"

mypath = "/home/source/catkin_ws/src/pyqt_test/file_test"

# number = 0
global number
number = 0
cap = cv2.VideoCapture(1-1 + CAP_API)
MAIN_COLOR = "background-color: #92c1dd;"




# Grab images from the camera (separate thread)
def grab_images(cam_num, queue):

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_SIZE[1])
    if EXPOSURE:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        cap.set(cv2.CAP_PROP_EXPOSURE, EXPOSURE)
    else:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    while capturing:
        if cap.grab():
            retval, image = cap.retrieve(0)
            if image is not None and queue.qsize() < 2:
                queue.put(image)
            else:
                time.sleep(DISP_MSEC / 1000.0)
        else:
            print("Error: can't grab camera image")
            break
    cap.release()

# Image widget


class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.setMinimumSize(image.size())
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()

# Main window


class MyWindow2(QtWidgets.QMainWindow):

    text_update = pyqtSignal(str)

    # Create main window
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setStyleSheet(MAIN_COLOR)
        self.cap = None
        rospy.init_node('pyqt', anonymous=True)
        self.pub = rospy.Publisher('TerminalToPyqt', String, queue_size=10)
        self.listener()
        self._image_counter = 0
        self.start()
        self.central = QWidget(self)
        self.central2 = QWidget(self)
        self.textbox = QTextEdit(self.central)
        self.textbox2 = QTextEdit(self.central2)
        self.textbox.setFont(TEXT_FONT)
        self.textbox.setMinimumSize(100, 100)
        self.text_update.connect(self.append_text)
        self.count = 5

       
        sys.stdout = self
        print("Camera number %u" % camera_num)
        print("Image size %u x %u" % IMG_SIZE)
        if DISP_SCALE > 1:
            print("Display scale %u:1" % DISP_SCALE)

        self.vlayout = QVBoxLayout()        # Window layout
        self.displays = QHBoxLayout()
        self.disp = ImageWidget(self)
        self.displays.addWidget(self.disp)
        self.vlayout.addLayout(self.displays)
        # self.label = QLabel(self)
        # self.vlayout.addWidget(self.label)
        # self.vlayout.addWidget(self.textbox)
        # self.vlayout.addWidget(self.textbox2)
        self.central.setLayout(self.vlayout)
        self.setCentralWidget(self.central)

        self.mainMenu = self.menuBar()      # Menu bar
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.fileMenu.addAction(exitAction)

        self.button = QtWidgets.QPushButton("go to init screen", self)
        self.button.clicked.connect(self.stack_reset)
        self.vlayout.addWidget(self.button)

        self.button1 = QtWidgets.QPushButton("agree", self)
        self.button1.clicked.connect(self.sendmessage1)
        self.vlayout.addWidget(self.button1)

        self.button2 = QtWidgets.QPushButton("disagree", self)
        self.button2.clicked.connect(self.sendmessage2)
        self.vlayout.addWidget(self.button2)

        self.button3 = QtWidgets.QPushButton("capture", self)
        self.button3.clicked.connect(self.showtime)
        # self.button3.clicked.connect(self.start_webcam)
        # self.button3.clicked.connect(self.capture_image)
        self.vlayout.addWidget(self.button3)

        # self.str = self.count + "뒤 촬영시작"
        # self.label = QtWidgets.QLabel(str(self.count), self)
        self.label = QtWidgets.QLabel("ready", self)

        # self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(500, 300, 800, 600) #(,down,,right)
        self.label.setAttribute(Qt.WA_TranslucentBackground, True) # 배경 투명
        self.label.setFont(QFont('Arial', 100)) # 글자 폰트, 사이즈 수정
        # self.label.setAlignment(Qt.AlignCenter)

        self.layout1 = QVBoxLayout()
        self.layout1.addWidget(self.label)
        # self.vlayout.addWidget(self.label)

    def showtime(self):

        if(self.count > 0):
            timer = Timer(1, self.showtime)
            timer.start()
            self.count = self.count - 1
        else:

            self.start_webcam()
            self.capture_image()
            self.count = 5

        if(self.count == 5):
            self.label.setText(str("ready"))
        else:
            self.label.setText(str(self.count))

        print("now count : " + str(self.count))

        # # 1970년 1월 1일 0시 0분 0초 부터 현재까지 경과시간 (초단위)
        # t = time.time()
        # # 한국 시간 얻기
        # kor = time.localtime(t)
        # # LCD 표시
        # self.year.display("TIME")
        # self.month.display("LFT")
        # self.day.display("IS")
        # self.hour.display("MIN")
        # self.min.display(":")
        # self.sec.display(self.now)

        # # 타이머 설정  (1초마다, 콜백함수)
    def make_filename(self):
        for (dirpath, dirnames, filenames) in walk(mypath):
            #print(len(filenames))
            name = "Camera_" + str(len(filenames)) + ".jpg"
        return name
            # f.extend(filenames)
            # break
        # return "aaa"

    @QtCore.pyqtSlot()
    def start_webcam(self):
        if cap is None:
            # self.cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        # self.timer.start()

    @QtCore.pyqtSlot()
    def capture_image(self):
        flag, frame = cap.read()
        # path = r'D:\_Qt\Test\testtest'                         #
        # path = "/home/source/catkin_ws/src/pyqt_test/drawer"
        path = mypath
        if flag:
            QtWidgets.QApplication.beep()
            name = self.make_filename()
            # name = "newfile.jpg"
            cv2.imwrite(os.path.join(path, name), frame)
            self._image_counter += 1



    def callback(self, data):
        if(data.data == "3"):
            self.stack_reset()
        # rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.data)

    def listener(self):
        rospy.init_node('pyqt', anonymous=True)
        rospy.Subscriber('chatter', String, self.callback)

    def stack_reset(self):
        self.parent().stack.setCurrentIndex(0)

    def sendmessage1(self):
        msg = "agree"
        self.pub.publish(msg)

    def sendmessage2(self):
        msg = "disagree"
        self.pub.publish(msg)

    # Start image capture & display
    def start(self):
        self.timer = QTimer(self)           # Timer to trigger display
        self.timer.timeout.connect(lambda:
                                   self.show_image(image_queue, self.disp, DISP_SCALE))
        self.timer.start(DISP_MSEC)
        self.capture_thread = threading.Thread(target=grab_images,
                                               args=(camera_num, image_queue))
        self.capture_thread.start()         # Thread to grab images

    # Fetch camera image from queue, and display it
    def show_image(self, imageq, display, scale):
        if not imageq.empty():
            image = imageq.get()
            if image is not None and len(image) > 0:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.display_image(img, display, scale)

    # Display an image, reduce size if required
    def display_image(self, img, display, scale=1):
        # disp_size = img.shape[1]//scale, img.shape[0]//scale
        disp_size = 3080, 1680
        # print(disp_size)
        # disp_size = 640//scale,480//scale
        disp_bpl = disp_size[0] * 3
        if scale > 1:
            img = cv2.resize(img, disp_size,
                             interpolation=cv2.INTER_CUBIC)
        qimg = QImage(img.data, disp_size[0], disp_size[1],
                      disp_bpl, IMG_FORMAT)
        display.setImage(qimg)

    # Handle sys.stdout.write: update text display
    def write(self, text):
        self.text_update.emit(str(text))

    def flush(self):
        pass

    # Append to text display
    def append_text(self, text):
        cur = self.textbox.textCursor()     # Move cursor to end of text
        cur.movePosition(QTextCursor.End)
        s = str(text)
        while s:
            head, sep, s = s.partition("\n")  # Split line at LF
            cur.insertText(head)            # Insert text at cursor
            if sep:                         # New line if LF
                cur.insertBlock()
        self.textbox.setTextCursor(cur)     # Update visible cursor

    # Window is closing: stop video capture
    def closeEvent(self, event):
        global capturing
        capturing = False
        self.capture_thread.join()


class FirstWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.setStyleSheet(MAIN_COLOR)
        self.listener()

        # layout = QtWidgets.QVBoxLayout(self)
        layout = QtWidgets.QHBoxLayout(self)

        self.label = QtWidgets.QLabel("촬영에 동의합니까?",self)
        # self.label.setAlignment(Qt.AlignCenter)
        # self.label.setGeometry(500, 300, 800, 600) #(,down,,right)
        # self.label.setAttribute(Qt.WA_TranslucentBackground, True) # 배경 투명
        self.label.setFont(QFont('Arial', 30)) # 글자 폰트, 사이즈 수정



        self.button = QtWidgets.QPushButton("동의", self)
        self.button.resize(200,300)
        # self.button.setStyleSheet(MAIN_COLOR)
        # self.button.setStyleSheet(
        #     "border-style : solid;"
        #     "border-width : 2px;"
        #     "border-radius :3px;"
        #     )
        self.button.setStyleSheet("color : white;""background : blue;""border:1px solid;""border-width :5px;""border-radius : 3px;")
        # self.button.QLineEdit("margin : 30px")
        self.button.clicked.connect(self.change_stack)
        self.button2 = QtWidgets.QPushButton("거절", self)
        self.button2.resize(200,300)
        # self.button2.setStyleSheet(MAIN_COLOR)
        self.button.setStyleSheet("color : white;""background : red;")
        self.button2.clicked.connect(self.stack_reset)

        self.text = QtWidgets.QTextEdit
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)

    # ros 메세지 받는 부분
    def callback(self, data):
        if(data.data == "2"):
            self.change_stack()

        # rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.data)

    def listener(self):
        rospy.init_node('pyqt', anonymous=True)
        rospy.Subscriber('chatter', String, self.callback)

    def change_stack(self):
        self.parent().stack.setCurrentIndex(2)

    def stack_reset(self):
        self.parent().stack.setCurrentIndex(0)


class VideoWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setStyleSheet(MAIN_COLOR)

        self.listener()

        self.setWindowTitle(
            "PyQt Video Player Widget Example - pythonprogramminglanguage.com")

        # self.statusbar = QtWidgets.QStatusBar()
        # self.setStatusBar(self.statusbar)
        # self.progressbar = QtWidgets.QProgressBar()
        # self.progressbar.setValue(24)
        # self.statusbar.addWidget(self.progressbar)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        # filepath = "/home/source/catkin_ws/src/pyqt_test/drawer/wave.mp4"
        filepath = "/home/source/catkin_ws/src/pyqt_test/drawer/wave.mp4"

        self.mediaPlayer.setMedia(
            QMediaContent(QUrl.fromLocalFile(filepath)))
        self.playButton.setEnabled(True)
        openAction.triggered.connect(self.openFile)
        self.mediaPlayer.setPlaybackRate(1.0)
        self.mediaPlayer.play()

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        # Create menu bar and add action
        # menuBar = self.menuBar()
        # fileMenu = menuBar.addMenu('&File')
        # #fileMenu.addAction(newAction)
        # fileMenu.addAction(openAction)
        # fileMenu.addAction(exitAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        # controlLayout.addWidget(self.playButton)
        # controlLayout.addWidget(self.positionSlider)

        layout = QVBoxLayout()
        layout.addWidget(videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        # layout = QtWidgets.QVBoxLayout(self)
        self.button = QtWidgets.QPushButton("Show Second Stack", self)
        self.button.setStyleSheet("border: 5px solid black;")

        self.button.setMaximumHeight(200)
        self.button.clicked.connect(self.change_stack)

        self.text = QtWidgets.QTextEdit
        layout.addWidget(self.button)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    # ros 메세지 받는 부분
    def callback(self, data):
        if(data.data == "1"):
            self.change_stack()
        # rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.data)

    def listener(self):
        rospy.init_node('pyqt', anonymous=True)
        rospy.Subscriber('chatter', String, self.callback)

    # ros end

    def change_stack(self):
        self.parent().stack.setCurrentIndex(1)

    def openFile(self):
        print("openfile")
        fileName, _ = QFileDialog.getOpenFileName(self, "video_test.mp4",
                                                  QDir.homePath())
        print(fileName)

        if fileName != '':
            self.mediaPlayer.setMedia(
                QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)
        print("openfile end")

    def exitCall(self):
        print("end video")
        self.mediaPlayer.play()
        # sys.exit(app.exec_())

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        print("enter mediastatechagned")
        # print(self.mediaPlayer.mediaStatus())
        if(self.mediaPlayer.mediaStatus() == 7):
            self.mediaPlayer.play()
            print("end1")

        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        if len(sys.argv) > 1:
            try:
                camera_num = int(sys.argv[1])
            except:
                camera_num = 0
        self.stack = QtWidgets.QStackedLayout(self)
        self.stack0 = VideoWindow(self)
        self.stack1 = FirstWidget(self)
        self.stack2 = MyWindow2(self)
        # self.stack3 = VideoWindow2(self)
        # print(self.stack2)
        self.stack.addWidget(self.stack0)
        self.stack.addWidget(self.stack1)
        self.stack.addWidget(self.stack2)
        # self.stack.addWidget(self.stack3)
        self.show()


app = QtWidgets.QApplication([])
main = MainWindow()
main.resize(1280, 880)
# main.showFullScreen()
app.exec()


# class SecondWidget(QtWidgets.QWidget):

#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         layout = QtWidgets.QVBoxLayout(self)
#         self.button = QtWidgets.QPushButton("next", self)
#         self.button.clicked.connect(self.change_stack)
#         self.button2 = QtWidgets.QPushButton("reset", self)
#         self.button2.clicked.connect(self.stack_reset)

#         self.text = QtWidgets.QTextEdit
#         layout.addWidget(self.button)
#         layout.addWidget(self.button2)
#     def change_stack(self):
#         self.parent().stack.setCurrentIndex(0)
#     def stack_reset(self):
#         self.parent().stack.setCurrentIndex(0)

# class FirstWidget(QtWidgets.QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)

#         self.listener()

#         layout = QtWidgets.QVBoxLayout(self)
#         self.button = QtWidgets.QPushButton("next", self)
#         self.button.clicked.connect(self.change_stack)
#         self.button2 = QtWidgets.QPushButton("reset", self)
#         self.button2.clicked.connect(self.stack_reset)

#         self.text = QtWidgets.QTextEdit
#         layout.addWidget(self.button)
#         layout.addWidget(self.button2)
