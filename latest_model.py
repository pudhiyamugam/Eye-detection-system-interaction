import cv2
import dlib
import time
import pyautogui
import numpy as np
import pygetwindow as gw  
import sys
import os

# --- CRASH FIX ---
pyautogui.FAILSAFE = False 

# ---------------- Config ----------------
EAR_THRESHOLD = 0.20        
LONG_BLINK_TIME = 0.7       
DOUBLE_MAX_INTERVAL = 0.4   

# Speed Settings
NORMAL_INTERVAL = 1.0       
SLOW_INTERVAL = 3.0         

# Geometry
SCREEN_W, SCREEN_H = pyautogui.size() 

# --- SIZE SETTINGS ---
KEYBOARD_W = 800    # Width (Small, on the left)
KEYBOARD_H = 100    # Height (Top strip)

# --- POSITION SETTINGS ---
KEYBOARD_X = 0      # Left
KEYBOARD_Y = 0      # Top

# ---------------- Setup ----------------
model_path = "shape_predictor_68_face_landmarks.dat"
if not os.path.exists(model_path):
    print(f"ERROR: '{model_path}' not found!")
    sys.exit()

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(model_path)

# ---------------- Window Docker (The Fix) ----------------
def snap_active_window():
    """
    Forces the active window (Browser) to start exactly 
    where the keyboard ends.
    """
    try:
        window = gw.getActiveWindow()
        if window and window.title != "Blink Keyboard" and window.title != "":
            
            # The browser should start at Y = 150 (Right below keyboard)
            target_y = KEYBOARD_H 
            # It should take up the rest of the screen height
            target_h = SCREEN_H - KEYBOARD_H 
            
            # If the window is too high (overlapping keyboard), move it down
            if window.top < target_y or abs(window.height - target_h) > 50:
                if window.isMaximized:
                    window.restore()
                
                # Move to (0, 150)
                window.moveTo(0, target_y)
                # Resize to fill the rest of the screen
                window.resizeTo(SCREEN_W, target_h)
    except Exception:
        pass 

# ---------------- Variables ----------------
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + [" ", "SYS"]
SYS_KEYS = ["ENTER", "BS", "TAB", "SAVE", "WIN", "BACK"]
active_list = LETTERS
current_menu = "TEXT" 
pointer_index = 0
auto_move = False
last_move_time = time.time()

# Blink Logic
closed_start = None
last_short_blink_time = 0
short_blink_count = 0
last_dock_check = 0

# ---------------- Helpers ----------------
def eye_aspect_ratio(eye):
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    return (A + B) / (2.0 * C)

# ---------------- Main Loop ----------------
cap = cv2.VideoCapture(0)
window_name = "Blink Keyboard"

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1) # Keep Keyboard on Top
cv2.resizeWindow(window_name, KEYBOARD_W, KEYBOARD_H)
cv2.moveWindow(window_name, KEYBOARD_X, KEYBOARD_Y)

# Layout Calculation
GRID_W = KEYBOARD_W - 20
GRID_H = KEYBOARD_H - 20 
START_X = 10
START_Y = 10

while True:
    ret, frame = cap.read()
    if not ret: break
    now = time.time()
    
    # --- DOCKING LOGIC (Run every 1s) ---
    if now - last_dock_check > 1.0:
        snap_active_window()
        last_dock_check = now
        # Force keyboard position to stay at Top-Left
        cv2.moveWindow(window_name, KEYBOARD_X, KEYBOARD_Y)
        cv2.resizeWindow(window_name, KEYBOARD_W, KEYBOARD_H)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    
    if len(faces) > 0:
        landmarks = predictor(gray, faces[0])
        left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
        right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]
        avg_EAR = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

        if avg_EAR < EAR_THRESHOLD:
            if closed_start is None: closed_start = now
        else:
            if closed_start is not None:
                duration = now - closed_start
                closed_start = None
                
                if duration >= LONG_BLINK_TIME:
                    # CLICK ACTION
                    key = active_list[pointer_index]
                    if key == "SYS":
                        active_list = SYS_KEYS
                        current_menu = "SYS"
                        pointer_index = 0
                    elif key == "BACK":
                        active_list = LETTERS
                        current_menu = "TEXT"
                        pointer_index = 0
                    elif current_menu == "SYS":
                        if key == "SAVE": 
                             with pyautogui.hold('ctrl'): pyautogui.press('s')
                        elif key == "ENTER": pyautogui.press('enter')
                        elif key == "TAB": pyautogui.press('tab')
                        elif key == "BS": pyautogui.press('backspace')
                        elif key == "WIN": pyautogui.press('win')
                    else:
                        if key == " ": pyautogui.press('space')
                        else: pyautogui.write(key.lower())
                    
                    short_blink_count = 0
                    time.sleep(0.5)

                else:
                    # SHORT BLINK
                    if now - last_short_blink_time <= DOUBLE_MAX_INTERVAL:
                        short_blink_count += 1
                    else:
                        short_blink_count = 1
                    last_short_blink_time = now
                    
                    if short_blink_count == 2:
                        short_blink_count = 0
                        auto_move = not auto_move
                        print(f"Double blink -> Auto: {auto_move}")
                        last_move_time = now

    # Auto Move
    if auto_move:
        current_key = active_list[pointer_index]
        wait_time = SLOW_INTERVAL if current_key in ["SYS"] else NORMAL_INTERVAL
        if (now - last_move_time) >= wait_time:
            pointer_index = (pointer_index + 1) % len(active_list)
            last_move_time = now

    # --- Draw UI ---
    panel = np.zeros((KEYBOARD_H, KEYBOARD_W, 3), dtype=np.uint8)
    panel[:] = (30, 30, 30) 
    
    cell_w = GRID_W // len(active_list)

    for idx, ch in enumerate(active_list):
        x1 = START_X + (idx * cell_w)
        y1 = START_Y
        x2 = x1 + cell_w
        y2 = y1 + GRID_H
        
        if idx == pointer_index:
            color = (0, 255, 0)
            if closed_start and (now - closed_start) > 0.1:
                color = (0, 165, 255) 
            cv2.rectangle(panel, (x1, y1), (x2, y2), color, -1)
            text_col = (0, 0, 0)
        else:
            color = (50, 50, 50) 
            cv2.rectangle(panel, (x1, y1), (x2, y2), color, -1)
            cv2.rectangle(panel, (x1, y1), (x2, y2), (100, 100, 100), 2)
            text_col = (255, 255, 255)

        # Font
        font_scale = 0.6
        thickness = 2
        s = cv2.getTextSize(ch, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        
        tx = x1 + (cell_w - s[0]) // 2
        ty = y1 + (GRID_H + s[1]) // 2
        cv2.putText(panel, ch, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_col, thickness)

    cv2.imshow(window_name, panel)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
