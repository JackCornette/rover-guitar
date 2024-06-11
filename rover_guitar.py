import threading
import time
import winsound
import hid
import socket
import queue

speed_lock = threading.Lock()

# Define the frequency and duration for the beep
BEEP_DURATION = 5  # milliseconds

# global FORWARD
# global REVERSE
NEUTRAL = 126
FORWARD = NEUTRAL
REVERSE = NEUTRAL

SPEED_CAP = int(NEUTRAL * 0.75)
ENTROPY = 6  # Speed adjustment increment
ENTROPY_SLEEP = 0.1 # smaller value makes rover slow down quicker
BOOST = 1 # larger value makes rover increase speed with fewer strums

# Button bit assignments
# byte 11 bit assignments
BUTTON_GREEN = 4
BUTTON_RED = 6
BUTTON_YELLOW = 3
BUTTON_BLUE = 5
BUTTON_ORANGE = 7
BUTTON_UP_STRUM = 0
# byte 10 bit assignments
BUTTON_DOWN_STRUM = 8

# Button frequency mappings (adjust as needed)
BUTTON_FREQUENCIES = {
    BUTTON_GREEN: 200,  # Hz
    BUTTON_RED: 400,
    BUTTON_YELLOW: 600,
    BUTTON_BLUE: 800,
    BUTTON_ORANGE: 1000,
    BUTTON_UP_STRUM: 1200,
    BUTTON_DOWN_STRUM: 1400
}

INCREMENT = 2  # Speed adjustment increment

""" THREAD """
# Function to continuously adjust speed towards NEUTRAL
def adjust_speed():
    global FORWARD, REVERSE
    
    while True:
        with speed_lock:
            # Adjust FORWARD speed towards NEUTRAL
            if FORWARD > NEUTRAL:
                FORWARD -= ENTROPY
            elif FORWARD < NEUTRAL:
                FORWARD = NEUTRAL  # Ensure FORWARD_SPEED doesn't go below NEUTRAL
            
            # Adjust REVERSE speed towards NEUTRAL
            if REVERSE < NEUTRAL:
                REVERSE += ENTROPY
            elif REVERSE > NEUTRAL:
                REVERSE = NEUTRAL  # Ensure REVERSE_SPEED doesn't go above NEUTRAL
        
        time.sleep(ENTROPY_SLEEP)  # Adjust speed every 0.1 second

# Function to play a beep with the specified frequency
# def play_beep(frequency):
#     def beep_thread():
#         winsound.Beep(frequency, BEEP_DURATION)
#     beep_thread = threading.Thread(target=beep_thread)
#     beep_thread.start()

""" LED UDP MSG """
# Function to send a message to the LED strip
def lights(r, g, b):
    msg = [0x01, 0x02, r & 0xFF, g & 0xFF, b & 0xFF]
    # print("Lights= ", list(msg))
    return msg

""" WHEEL UDP MSG """
# Function to make a wheel message
def wheel_message(leftwheels, rightwheels):
    msg = [0x01, 0x01] + leftwheels + rightwheels + [0x00]
    msg[8] = sum(msg[2:8]) & 0xFF  # calculate checksum
    # print("Wheels= ", list(msg))
    return msg

""" CONVERTS BUTTON PRESS TO ROVER COMMANDS """
# This is where you create notes that will control the rover when the guitar is strummed
def handle_button_press(pressed_buttons):

    global FORWARD, REVERSE

    # Determine LED color and wheel message based on button
    if pressed_buttons == {BUTTON_GREEN, BUTTON_YELLOW, BUTTON_BLUE}:
        # Forward drive (green LED)
        print("Forward ", FORWARD)
        return lights(0, 255, 0), wheel_message([FORWARD]*3, 
                                                [FORWARD]*3)
    elif pressed_buttons == {BUTTON_RED, BUTTON_YELLOW, BUTTON_BLUE}:
        # Reverse drive (red LED)
        print("Reverse ", REVERSE)
        return lights(255, 0, 0), wheel_message([REVERSE]*3, 
                                                [REVERSE]*3)
    elif pressed_buttons == {BUTTON_GREEN, BUTTON_YELLOW}:
        # Left wheel forward drive (yellow LED)
        print("Forward Left ", FORWARD)
        return lights(255, 255, 0), wheel_message([FORWARD]*3,
                                                  [NEUTRAL]*3)
    elif pressed_buttons == {BUTTON_GREEN, BUTTON_BLUE}:
        # Right wheel forward drive (blue LED)
        print("Forward Right ", FORWARD)
        return lights(0, 0, 255), wheel_message([NEUTRAL]*3,
                                                [FORWARD]*3)
    elif pressed_buttons == {BUTTON_RED, BUTTON_YELLOW}:
        # Left wheel reverse drive (yellow LED)
        print("Reverse Left ", REVERSE)
        return lights(255, 255, 0), wheel_message([REVERSE]*3,
                                                [NEUTRAL]*3)
    elif pressed_buttons == {BUTTON_RED, BUTTON_BLUE}:
        # Turn right drive (blue LED)
        print("Reverse Right ", REVERSE)
        return lights(0, 0, 255), wheel_message([NEUTRAL]*3,
                                                [REVERSE]*3)
    elif pressed_buttons == {BUTTON_GREEN, BUTTON_ORANGE}:
        # Pivot clockwise (purple LED since no orange)
        print("Clockwise pivot ", FORWARD, " ", 252-FORWARD)
        return lights(255, 0, 255), wheel_message([FORWARD]*3, 
                                                    [252-FORWARD]*3)
    elif pressed_buttons == {BUTTON_RED, BUTTON_ORANGE}:
        # Pivot clockwise (purple LED since no orange)
        print("Counter Clockwise pivot ", REVERSE, " ", 126+REVERSE)
        return lights(255, 0, 255), wheel_message([REVERSE]*3, 
                                                    [126+REVERSE]*3)
    
    return None, None  # No action for other buttons

def pressed(data, byte_num, bit_num):
    return data[byte_num] & (1 << bit_num) == 0


# Function to print the pressed buttons
def get_pressed_buttons(data):
    pressed_buttons = []

    for button in BUTTON_FREQUENCIES:
        if button == BUTTON_DOWN_STRUM and pressed(data, 10, 6):
            # print("DOWN")
            pressed_buttons.append(BUTTON_DOWN_STRUM)
        elif pressed(data, 11, button):
            pressed_buttons.append(button)

    return pressed_buttons

# Function to find and open the Wii remote device
def find_wii_remote():
    devices = hid.enumerate()
    # print(devices)
    for device in devices:
        if device['product_string'] == 'Nintendo RVL-CNT-01':
            return device
    return None

def open_wii_remote(wii_remote_info):
    device = hid.device()
    device.open_path(wii_remote_info['path'])
    return device

def main():
    global data, FORWARD, REVERSE
    # try:
    device = hid.device()
    device.open(0x057E, 0x0306)  # Nintendo Wii Remote (RVL-CNT-01)

    wii_remote_info = find_wii_remote()
    if wii_remote_info:
        wii_remote_device = open_wii_remote(wii_remote_info)
        print(wii_remote_device)
    else:
        print("Wii remote not found.")

    # UDP configuration
    UDP_IP = "192.168.1.101"  # Example IP address of the rover
    UDP_PORT = 1001  # Example UDP port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Start the speed adjustment thread
    speed_adjust_thread = threading.Thread(target=adjust_speed)
    speed_adjust_thread.daemon = True  # Make it a daemon thread so it stops when the main thread stops
    speed_adjust_thread.start()

    data = [255]*12
    udp_messages = [[0x01, 0x02, 0, 0, 0], [0x01, 0x01, 126, 126, 126, 126, 126, 126, 126]]
    pressed_buttons = []
    last_strummed_buttons = pressed_buttons

    while True:
        try: 
            data = device.read(64, timeout_ms=0.02)
            # Check for button presses and handle actions
            pressed_buttons = get_pressed_buttons(data)
            
        except queue.Empty:
            pass

    
        # if user strummed, incriment or decriment the speed
        if BUTTON_GREEN in pressed_buttons and (pressed(data, 10, 6) or BUTTON_UP_STRUM in pressed_buttons):
            with speed_lock:
                # print(FORWARD)
                FORWARD += BOOST
                if FORWARD > NEUTRAL + SPEED_CAP:
                    FORWARD = NEUTRAL + SPEED_CAP
        if BUTTON_RED in pressed_buttons and (pressed(data, 10, 6) or BUTTON_UP_STRUM in pressed_buttons):
            with speed_lock:
                REVERSE -= BOOST
                if REVERSE < NEUTRAL - SPEED_CAP:
                    REVERSE = NEUTRAL - SPEED_CAP

        # save list of last strummed buttons 
        if pressed(data, 10, 6) or pressed(data, 11, BUTTON_UP_STRUM):
            last_strummed_buttons = list(set(pressed_buttons) - {BUTTON_DOWN_STRUM, BUTTON_UP_STRUM})

        # if no buttons were pressed, use the ones that were last strummed
        if len(pressed_buttons) == 0:
            pressed_buttons = last_strummed_buttons

        udp_messages = handle_button_press(set(last_strummed_buttons))
        if udp_messages[0] == None:
            continue

        # print(data)
        # print(pressed_buttons)
        # print(last_strummed_buttons)
        # print(udp_messages)

        # Send UDP messages
        for msg in udp_messages:
            print(msg)
            sock.sendto(bytearray(msg), (UDP_IP, UDP_PORT))
        time.sleep(0.01)


if __name__ == "__main__":
    main()
