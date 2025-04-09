import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import random
import platform
import sys

# Platform-specific setup
OS = platform.system()
WINDOWS = OS == 'Windows'
LINUX = OS == 'Linux'

window = tk.Tk()
window.overrideredirect(True)

if WINDOWS:
    window.wm_attributes('-transparentcolor', 'black')
    window.wm_attributes('-topmost', True)
elif LINUX:
    window.wm_attributes('-type', 'splash')  # Helps with transparency on some Linux window managers
    window.wm_attributes('-alpha', 0)  # Slight transparency as fallback

animations = {
    'walk': [1, 1, 2, 2, 1, 1, 3, 2],
    'fall': [4],
    'sit': [11],
    'sit up': [26],
    'dangle legs': [31, 31, 32, 32, 31, 31, 33, 33],
    'lay down': [21],
    'lie down swing legs': [20, 20, 21, 21],
    'grab ceiling': [32],
    'climb ceiling': [25, 25, 23, 23, 23, 23, 23, 25],
    'grab wall': [13],
    'climb wall': [14, 14, 12, 13, 13, 13, 12, 14],
    'dragging': [4]
}

state = 'fall'
current_frame = 0
x, y = 1400, 100
direction = -1
velocity_y = 0
gravity = 0.8
grounded = False
char_height = 0
drag_start_x = 0
drag_start_y = 0
start_x = 0
start_y = 0
last_x = 0
shime = 'Len'
frames = {}

# Load images with transparency handling
for state_frames in animations.values():
    for frame in state_frames:
        img = Image.open(f"{shime}/shime{frame}.png")
        if not char_height:
            char_height = img.height
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # For Linux, we'll need to handle transparency differently
        if LINUX:
            # Create a transparent background
            data = img.getdata()
            new_data = []
            for item in data:
                # Change all black pixels to transparent
                if item[0] == 0 and item[1] == 0 and item[2] == 0:
                    new_data.append((0, 0, 0, 0))
                else:
                    new_data.append(item)
            img.putdata(new_data)
        
        frames[frame] = {
            'original': ImageTk.PhotoImage(img),
            'flipped': ImageTk.PhotoImage(ImageOps.mirror(img))
        }

# For Linux, we need to use a canvas with transparent background
if LINUX:
    canvas = tk.Canvas(window, width=100, height=100, bg='black', highlightthickness=0, bd=0)
    canvas.pack()
    img_container = canvas.create_image(0, 0, anchor='nw')
else:
    label = tk.Label(window, bd=0, bg='black')
    label.pack()

if WINDOWS:
    shimeji_hwnd = window.winfo_id()

def on_click(event):
    global drag_start_x, drag_start_y, start_x, start_y, last_x
    drag_start_x = event.x_root
    drag_start_y = event.y_root
    start_x = window.winfo_x()
    start_y = window.winfo_y()
    last_x = event.x_root

def on_drag(event):
    global x, y, grounded, state, start_x, start_y, drag_start_x, drag_start_y, direction, last_x
    state = 'dragging'
    new_x = start_x + (event.x_root - drag_start_x)
    new_y = start_y + (event.y_root - drag_start_y)
    delta_x = event.x_root - last_x
    if delta_x > 0:
        direction = 1
    elif delta_x < 0:
        direction = -1
    last_x = event.x_root
    x = new_x
    y = new_y
    window.geometry(f"+{int(x)}+{int(y)}")

def get_windows():
    if WINDOWS:
        return get_windows_windows()
    else:
        # Linux fallback - returns just the screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        return [(0, 0, screen_width, screen_height)]

def get_windows_windows():
    windows = []
    def callback(hwnd, ctx):
        if hwnd == shimeji_hwnd or not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.IsIconic(hwnd):
            return
        rect = win32gui.GetWindowRect(hwnd)
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if (rect[2] - rect[0] == 0 or rect[3] - rect[1] == 0 or 
            ex_style & win32con.WS_EX_TOOLWINDOW or style & win32con.WS_MINIMIZE):
            return
        if not win32gui.GetWindowText(hwnd):
            return
        point_x = rect[0] + (rect[2] - rect[0]) // 2
        point_y = rect[1] + 25
        target_hwnd = win32gui.WindowFromPoint((point_x, point_y))
        root_target = win32gui.GetAncestor(target_hwnd, win32con.GA_ROOT)
        root_current = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
        if root_target != root_current:
            return
        windows.append(rect)
    win32gui.EnumWindows(callback, None)
    return windows

def check_collision():
    global y, velocity_y, grounded, state
    new_y = y + velocity_y
    char_bottom = new_y + char_height

    closest_platform = None
    for win in get_windows():
        win_top = win[1]
        win_bottom = win[1] + 50
        win_left = win[0]
        win_right = win[2]

        if win_top > 0 and (char_bottom >= win_top and char_bottom <= win_bottom and
                x + char_height >= win_left and x <= win_right):
            if not closest_platform or win_top < closest_platform[1]:
                closest_platform = win

    if closest_platform:
        velocity_y = 0
        grounded = True
        return True

    if char_bottom >= window.winfo_screenheight() - 40:
        y = window.winfo_screenheight() - char_height - 40
        velocity_y = 0
        grounded = True
        return True

    grounded = False
    return False

def update_animation():
    global current_frame, state
    anim_frames = animations[state]
    current_frame = (current_frame + .5) % len(anim_frames)
    frame_number = anim_frames[int(current_frame)]
    img_key = 'flipped' if direction > 0 else 'original'
    
    if LINUX:
        canvas.itemconfig(img_container, image=frames[frame_number][img_key])
        canvas.config(width=frames[frame_number][img_key].width(), 
                     height=frames[frame_number][img_key].height())
    else:
        label.config(image=frames[frame_number][img_key])
    
    if state == 'dangle legs':
        window.geometry(f"+{int(x)}+{int(y)+15}")
    else:
        window.geometry(f"+{int(x)}+{int(y)}")

def update():
    global x, y, direction, velocity_y, state
    if not grounded and state not in ['climb wall', 'dragging', 'climb ceiling']:
        velocity_y += gravity
        y += velocity_y
        x += 5 * direction

    if check_collision() and state == 'fall':
        state = random.choice(['dangle legs', 'lie down swing legs', 'walk'])

    if state == 'walk' and grounded:
        x += 5 * direction
        if x <= -50 or x >= window.winfo_screenwidth() - 75:
            if random.randint(1, 5) != 2:
                direction *= -1
            else:
                state = 'climb wall'
    elif state == 'climb wall':
        y -= 5
        if y <= -50:
            direction *= -1
            if random.randint(1, 5) != 2:
                state = 'fall'
            else:
                state = 'climb ceiling'
    elif state == 'climb ceiling':
        x += 5 * direction
        if random.randint(0, 100) == 72:
            state = 'fall'
    elif state in ['sit', 'sit up', 'dangle legs', 'lay down', 'lie down swing legs']:
        if random.randint(0, 100) == 72:
            state = 'walk'
    elif not grounded:
        state = 'fall'

    update_animation()
    window.after(30, update)

window.bind("<Button-1>", on_click)
window.bind("<B1-Motion>", on_drag)

update_animation()
update()

# Linux-specific transparency workaround
if LINUX:
    try:
        window.wait_visibility(window)
        window.wm_attributes('-alpha', 0.99)  # Some window managers need this
    except:
        pass

window.mainloop()