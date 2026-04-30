import cv2 as cv
import numpy as np
import time 
import matplotlib.pyplot as plt

cam = cv.VideoCapture(4)

success, cap = cam.read()
if success:
    cap_gray = cv.cvtColor(cap, cv.COLOR_BGR2GRAY)
    cv.imwrite("bild_2.jpg", cap)
    plt.imshow(cap, cmap='gray')
    plt.show()