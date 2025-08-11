
import libusb as usb
import sys
import threading
from application import ThermappApplication
from device import ThermappDevice

if __name__ == '__main__':
    def keyboard_input(connector, device):
        try:
            while True:
                key = input("Press 'q' to stop the device: ")
                if key.lower() == 'q':
                    connector.stop()
                    device.close()
                    break
        except KeyboardInterrupt:
            connector.stop()
            device.close()

    def main():
        # Initialize libusb
        r = usb.init(None)
        if r < 0:
            print(f"Failed to initialize libusb: {r} - {usb.strerror(r)}")
            sys.exit(1)

        try:
            # Open Thermapp device
            device = ThermappDevice()
            device.open()

            # Start Thermapp application
            connector = ThermappApplication(device=device)
            connector.start()

            # Start keyboard input monitoring thread
            keyboard_thread = threading.Thread(target=keyboard_input, args=(connector, device,))
            keyboard_thread.start()
            keyboard_thread.join()

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    main()