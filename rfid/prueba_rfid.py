import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

while True:
    try:
        rfid = reader.read_id()
        print ("RFID: ", rfid)
            
    finally:
        GPIO.cleanup()