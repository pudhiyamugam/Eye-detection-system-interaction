import cv2
import dlib

# Load face detector and shape predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Open webcam (0 = default camera, 1 = external camera if connected)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to grayscale (better for detector)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = detector(gray)

    for face in faces:
        # Get landmarks
        landmarks = predictor(gray, face)

        # Draw landmarks
        for n in range(68):
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            cv2.putText(frame, str(n), (x, y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)  # put landmark index

    # Show the frame
    cv2.imshow("Webcam Landmarks", frame)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release webcam and close windows
cap.release()
cv2.destroyAllWindows()
