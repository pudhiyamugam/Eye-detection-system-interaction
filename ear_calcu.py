import cv2
import dlib
import numpy as np

# ----------------- EAR Helper Functions -----------------
def euclidean_dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def eye_aspect_ratio(eye):
    # eye = [(x1,y1), ... (x6,y6)]
    A = euclidean_dist(eye[1], eye[5])  # p2-p6
    B = euclidean_dist(eye[2], eye[4])  # p3-p5
    C = euclidean_dist(eye[0], eye[3])  # p1-p4
    return (A + B) / (2.0 * C)

# ----------------- Dlib Setup -----------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# ----------------- Webcam -----------------
cap = cv2.VideoCapture("video_2.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)

        # ----------------- Eye landmarks only -----------------
        left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
        right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]

        # Draw both eyes in green
        for (x, y) in left_eye + right_eye:
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        # ----------------- EAR Calculation -----------------
        left_EAR = eye_aspect_ratio(left_eye)
        right_EAR = eye_aspect_ratio(right_eye)
        avg_EAR = (left_EAR + right_EAR) / 2.0

        # ----------------- Display EAR -----------------
        cv2.putText(frame, f"EAR: {avg_EAR:.2f}", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Eye Landmarks + EAR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
