import dlib
import cv2

# Load face detector and shape predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Load an image
img = cv2.imread("img_1.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Detect faces
faces = detector(gray)

for face in faces:
    # Get the landmarks
    landmarks = predictor(gray, face)

    # Draw them on the image
    for n in range(68):
        x = landmarks.part(n).x
        y = landmarks.part(n).y
        cv2.circle(img, (x, y), 2, (0, 0, 255), -1)

cv2.imshow("Landmarks", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
