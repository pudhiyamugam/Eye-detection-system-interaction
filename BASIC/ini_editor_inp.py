# blink_keyboard_notepad.py
import cv2, dlib, time, pyautogui, numpy as np
import subprocess, pygetwindow as gw

# ---------------- Config ----------------
EAR_THRESHOLD = 0.18
LONG_BLINK_TIME = 0.8
DOUBLE_MAX_INTERVAL = 0.4
MOVE_INTERVAL = 0.9
GRID_COLS = 9
GRID_ROWS = 3
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + [" "]  # 27 items

# ---------------- Helpers ----------------
def euclidean_dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def eye_aspect_ratio(eye):
    A = euclidean_dist(eye[1], eye[5])
    B = euclidean_dist(eye[2], eye[4])
    C = euclidean_dist(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# ---------------- dlib setup ----------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# ---------------- UI / grid params ----------------
WINDOW_W, WINDOW_H = 900, 400
GRID_W = WINDOW_W - 20
GRID_H = 200
CELL_W = GRID_W // GRID_COLS
CELL_H = GRID_H // GRID_ROWS

# ---------------- State ----------------
pointer_index = 0
auto_move = False
last_move_time = time.time()

closed_start = None
last_short_blink_time = 0
short_blink_count = 0

# ---------------- Launch Notepad ----------------
print(">>> Opening Notepad...")
subprocess.Popen(["notepad.exe"])
time.sleep(2)  # wait for Notepad to open

# bring Notepad to front
try:
    notepad = gw.getWindowsWithTitle("Untitled - Notepad")[0]
    notepad.activate()
except:
    print("⚠️ Could not focus Notepad window. Please click on it manually.")

# ---------------- VideoCapture ----------------
cap = cv2.VideoCapture(0)

def type_character(ch):
    """Send keystroke directly to Notepad"""
    try:
        notepad.activate()   # make sure Notepad is focused
    except:
        pass
    if ch == " ":
        pyautogui.press('space')
    else:
        pyautogui.typewrite(ch)

def draw_grid(frame):
    # Overlay grid on camera feed
    panel = cv2.resize(frame, (WINDOW_W, WINDOW_H))
    start_x, start_y = 20, 100
    idx = 0
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = start_x + c * CELL_W
            y = start_y + r * CELL_H
            rect_color = (80, 80, 80)
            thickness = 1
            if idx == pointer_index:
                rect_color = (0, 255, 0)
                thickness = 3
            cv2.rectangle(panel, (x, y), (x+CELL_W, y+CELL_H), rect_color, thickness)
            if idx < len(LETTERS):
                ch = LETTERS[idx]
                display = 'SPACE' if ch == ' ' else ch
                cv2.putText(panel, display, (x+10, y+CELL_H//2+10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230,230,230), 2)
            idx += 1
    return panel

while True:
    ret, frame = cap.read()
    if not ret:
        break
    now = time.time()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    if len(faces) > 0:
        face = faces[0]
        landmarks = predictor(gray, face)
        left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
        right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]
        avg_EAR = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

        if avg_EAR < EAR_THRESHOLD:
            if closed_start is None:
                closed_start = now
        else:
            if closed_start is not None:
                duration = now - closed_start
                closed_start = None
                if duration >= LONG_BLINK_TIME:
                    ch = LETTERS[pointer_index]
                    print(f"Selected: {ch}")
                    type_character(ch)  # 🔥 goes into Notepad
                    time.sleep(0.5)
                else:
                    if now - last_short_blink_time <= DOUBLE_MAX_INTERVAL:
                        short_blink_count += 1
                    else:
                        short_blink_count = 1
                    last_short_blink_time = now

                    if short_blink_count == 2:
                        short_blink_count = 0
                        auto_move = not auto_move
                        print("Double blink -> Auto toggled:", auto_move)
                        time.sleep(0.3)

    if auto_move and (now - last_move_time) >= MOVE_INTERVAL:
        pointer_index = (pointer_index + 1) % len(LETTERS)
        last_move_time = now

    ui = draw_grid(frame)
    cv2.imshow("Blink Keyboard", ui)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
