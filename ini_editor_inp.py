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
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + [" ","SYS >"]  # 27 items
SYS_KEYS = ["ENTER", "TAB", "SAVE", "BACK"]

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

# ---------------- Optimized Geometry ----------------
WINDOW_W = 1200
WINDOW_H = 100  

# Let's make the grid take up 60% of the window height
GRID_W = WINDOW_W - 40
GRID_H = 60  

GRID_COLS = len(LETTERS)
GRID_ROWS = 1

CELL_H = GRID_H

# Calculation to center it vertically
START_X = 20
START_Y = (WINDOW_H - GRID_H) // 2  # This puts it in the middle

# ---------------- State ----------------
pointer_index = 0
active_list=LETTERS
current_menu="TEXT"
auto_move = False
last_move_time = time.time()

closed_start = None
last_short_blink_time = 0
short_blink_count = 0

# ---------------- Launch Notepad ----------------
print(">>> Opening Notepad...")
subprocess.Popen(["notepad.exe"])
time.sleep(2)  # wait for Notepad to ope

# bring Notepad to front
try:
    notepad = gw.getWindowsWithTitle("Untitled - Notepad")[0]
    notepad.activate()
except:
    print("⚠️ Could not focus Notepad window. Please click on it manually.")

# ---------------- VideoCapture ----------------
cap = cv2.VideoCapture(0)

def execute_system_command(cmd):
    print(f"executig system command{cmd}")
    try:
        time.sleep(0.1)
        if cmd=="SAVE":
            with pyautogui.hold('ctrl'):
                pyautogui.press('s')
        elif cmd=="ENTER":
            pyautogui.press('enter')

        elif cmd=="TAB":
            pyautogui.press('tab')
    except Exception as e:
        print(f"ERROR executing command {e}")

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

def draw_grid():
    # Create a solid dark grey background (No webcam feed)
    panel = np.zeros((WINDOW_H, WINDOW_W, 3), dtype=np.uint8)
    panel[:] = (30, 30, 30) # Dark theme

    current_column=len(active_list)
    dynamic_cell_width=GRID_W//current_column

    for idx, ch in enumerate(active_list):
        # Calculate box position
        x1 = START_X + (idx * dynamic_cell_width)
        y1 = START_Y
        x2 = x1 + dynamic_cell_width
        y2 = y1 + GRID_H
        
        # Color logic: Green for active, Light Grey for others
        color = (0, 255, 0) if idx == pointer_index else (150, 150, 150)
        thickness = 2 if idx == pointer_index else 1
        
        # Draw the key box
        cv2.rectangle(panel, (x1, y1), (x2, y2), color, thickness)
        
        # Draw the Letter (Centered inside the box)
        # We adjust the font scale (0.5) and thickness (1) for the small size
        text_size = cv2.getTextSize(ch, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = x1 + (dynamic_cell_width - text_size[0]) // 2
        text_y = y1 + (GRID_H + text_size[1]) // 2
        
        cv2.putText(panel, ch, (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
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
                    selected_key=active_list[pointer_index]

                    if selected_key=="SYS >":
                        active_list=SYS_KEYS
                        current_menu="SYS"
                        pointer_index=0
                        print("switeched to system control💀")

                    elif selected_key=="BACK":
                        active_list=LETTERS
                        current_menu="TEXT"
                        pointer_index=0

                    elif current_menu=="SYS":
                        execute_system_command(selected_key)

                    else:
                        type_character(selected_key)

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
        pointer_index = (pointer_index + 1) % len(active_list)
        last_move_time = now

    ui = draw_grid()
    cv2.imshow("Blink Keyboard", ui)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
