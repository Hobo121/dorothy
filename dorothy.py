# ----------------------------#
# Read me:
# Find voren - This is the lead character to follow. Screen shot the name from the D2R game, black out the background and save as voren.png in the Images/follow folder. Adjust the threshold if needed.
# Alter 'Voren' if needed to match the name in your game. Doesn't have to be the name, just a unique image that can be found on the screen.

#Start a game with your main character. 
#Once in the game, open a portal, have your second character enter the portal. 
#Run the script on your second character, and it should follow your main character around.
#Map needs to be turned on for the second character to follow the main character. - Turn it off if you want to stop following and move freely.
#Dorothy will follow the lead character around, clicking on them every 0.4 seconds. Adjust the click cooldown and move speed if needed.
#Dorothy is dumb, she will get stuck on terrain and objects. If that happens, just move the lead character to a different location and she should follow
#Dorothy also doesnt take care of her health, so be careful if you are following a character that is taking damage.

#Basically good if you're a tank with great auras on you and your merc. 

import cv2
import numpy as np
import pyautogui
import mss
import time
import win32gui
import keyboard
import os

WINDOW_NAME = "Diablo II: Resurrected"

#This is the colour code of the players name in the D2R map
LOWER_GREEN = np.array([35, 80, 80])
UPPER_GREEN = np.array([90, 255, 255])

CLICK_COOLDOWN = 0.4
MOVE_SPEED = 0.03
DEBUG = True

SCAN_RATIO = 0.6

last_click = 0
running = True

#Define user. 
pc_user =os.path.expanduser("~")
folder_path = os.path.join(pc_user, "OneDrive", "Documents", "D2R_Game_Name")

# ============================
# GLOBAL STOP HOTKEY
# ============================

def stop_script():
    global running
    running = False
    print("Ctrl+C detected — stopping script")

keyboard.add_hotkey('ctrl+c', stop_script)


# ============================
# FIND D2R WINDOW
# ============================

def get_d2r_window():

    hwnd = win32gui.FindWindow(None, WINDOW_NAME)

    if hwnd == 0:
        print("D2R window not found")
        exit()

    rect = win32gui.GetWindowRect(hwnd)

    x = rect[0]
    y = rect[1]
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]

    return x, y, w, h


# ----------------------------#
# Find voren - This is the lead character to follow. Screen shot the name from the D2R game, black out the background and save as voren.png in the Images/follow folder. Adjust the threshold if needed.
# Alter 'Voren' if needed to match the name in your game. Doesn't have to be the name, just a unique image that can be found on the screen.
TEMPLATE = cv2.imread(os.path.join(folder_path, "Images", "follow", "voren.png"), cv2.IMREAD_GRAYSCALE)
THRESHOLD = 0.8

# ============================
# DETECT GREEN MARKERS
# ============================

def detect_voren(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(gray, TEMPLATE, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= THRESHOLD)

    targets = []

    h, w = TEMPLATE.shape

    for pt in zip(*locations[::-1]):

        cx = pt[0] + w // 2
        cy = pt[1] + h // 2
        score = result[pt[1], pt[0]]

        targets.append((cx, cy, score))

    return targets

def detect_green(frame):

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

    kernel = np.ones((3,3),np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)

    contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    targets = []

    for c in contours:

        area = cv2.contourArea(c)

        if area < 200:
            continue

        x,y,w,h = cv2.boundingRect(c)

        cx = x + w//2
        cy = y + h//2

        targets.append((cx,cy,area))

    return targets, mask


# ============================
# MAIN LOOP
# ============================

def run():

    global last_click
    global running

    win_x, win_y, win_w, win_h = get_d2r_window()

    scan_w = int(win_w * SCAN_RATIO)
    scan_h = int(win_h * SCAN_RATIO)

    scan_x = win_x + (win_w - scan_w) // 2
    scan_y = win_y + (win_h - scan_h) // 2

    monitor = {
        "top": scan_y,
        "left": scan_x,
        "width": scan_w,
        "height": scan_h
    }

    with mss.mss() as sct:

        while running:

            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            #targets, mask = detect_green(frame)
            targets = detect_voren(frame)

            if targets:

                targets.sort(key=lambda t: t[2], reverse=True)

                x,y,_ = targets[0]

                screen_x = scan_x + x
                screen_y = scan_y + y

                pyautogui.moveTo(screen_x,screen_y,duration=MOVE_SPEED)

                if time.time() - last_click > CLICK_COOLDOWN:

                    pyautogui.click()
                    last_click = time.time()

                    print("Clicked target")

                if DEBUG:
                    cv2.circle(frame,(x,y),12,(0,0,255),2)

            if DEBUG:

                cv2.imshow("D2R Scan Area",frame)
                #cv2.imshow("Mask",mask)

                if cv2.waitKey(1)==27:
                    running = False

            time.sleep(0.01)

    cv2.destroyAllWindows()



run()
