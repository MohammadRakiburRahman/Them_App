

import libusb as usb
import sys
import threading

from device import ThermappDevice
from generate_auto_annotations import AnnotationApp  #  detector app

def keyboard_input(app, device):
    try:
        while True:
            if input("Press 'q' + Enter to stop: ").lower() == 'q':
                app.stop()
                device.close()
                break
    except KeyboardInterrupt:
        app.stop()
        device.close()

def main():
    # 1) Init libusb
    r = usb.init(None)
    if r < 0:
        print(f"Failed to initialize libusb: {r} - {usb.strerror(r)}")
        sys.exit(1)

    # 2) Open the Thermapp device
    device = ThermappDevice()
    try:
        device.open()
    except Exception as e:
        print("Could not open Therm-App device:", e)
        sys.exit(1)

    # 3) Instantiate & start your annotation app
    app = AnnotationApp(device)
    app.start()

    # 4) Let user press 'q' to exit cleanly
    kb_thread = threading.Thread(target=keyboard_input, args=(app, device))
    kb_thread.start()
    kb_thread.join()

if __name__ == "__main__":
    main()
