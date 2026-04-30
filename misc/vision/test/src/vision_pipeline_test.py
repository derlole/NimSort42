import cv2 as cv
import time
from vision_pipeline_homographie import OpencvPipeline


pipeline = OpencvPipeline()
pipeline.captureImage()
data = pipeline.getImageData()


X_w, Y_w, Z_w, timestamp, image = data

print("=== Ergebnisse ===")
print(f"X_c       : {X_w:.6f}")
print(f"Y_c       : {Y_w:.6f}")
print(f"Z_c       : {Z_w:.6f}")
print(f"Timestamp : {timestamp} ms")

cv.imshow("Ergebnis", image)
print("\nBild wird angezeigt – beliebige Taste drücken zum Beenden.")
cv.waitKey(0)
cv.destroyAllWindows()