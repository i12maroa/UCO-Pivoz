import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import webbrowser
import time
import subprocess
from requests import session

URL1 = "https://www.ucopivoz.com/read_rfid/"

URL1_t = "http://192.168.43.83:8000/read_rfid/"
GPIO.setwarnings(False)

reader = SimpleMFRC522()
client = session()

while True:
    try:
        rfid = reader.read_id()
        print ("RFID: ", rfid)
        if rfid is not None:
            time.sleep(2)
            client.get(URL1)
            if 'csrftoken' in client.cookies:
                csrftoken = client.cookies['csrftoken']
            else:
                csrftoken = client.cookies['csrf']

            login_data = dict(rfid_id=rfid, csrfmiddlewaretoken=csrftoken, next='/')
            response = client.post(URL1, data=login_data, headers=dict(Referer=URL1))
            datos_recibidos = response.json()
            print(datos_recibidos)

            if (datos_recibidos['token'] != 0):
                URL3 = "https://www.ucopivoz.com/login/rfid/" + datos_recibidos['token'] + "/"
                URL3_t = "http://192.168.43.83:8000/login/rfid/" + datos_recibidos['token'] + "/"
                chromium_path = '/usr/bin/chromium-browser'
                #subprocess.call(["chromium-browser", URL3])
                subprocess.call(["pkill", "chromium"])
                webbrowser.open(URL3, new=0, autoraise = True)

    finally:
        GPIO.cleanup()
