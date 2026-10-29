
import cv2
img = cv2.imread('cat.png')
cv2.imshow('Cat Image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()