import network
import time
from machine import Pin, I2C
import urequests

import ujson
import ahtx0
import microcoapy
import coap_macros

# HARDWARE
LED = Pin(16, Pin.OUT)
LED.value(0)

BUTT_SEND = Pin(20, Pin.IN)
BUTT_PIR = Pin(21, Pin.IN)

button2 = Pin(22, Pin.IN, machine.Pin.PULL_UP)
button2_state = False

#PIR CONN
#grovepi.pinMode(pir_sensor,"INPUT")


button_pressed = False
pir_active = False


# Set Wi-Fi network to Station Interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True) # enable Wi-Fi interface


#COAP
_MY_SSID = 'LPWAN-IoT-07' # fill your hotspot SSID
_MY_PASS = 'LPWAN-IoT-07-WiFi' # fill your hotspot password
_SERVER_IP ='86.49.182.194'
_SERVER_PORT = 36105  #5683 36105 default CoAP port
_COAP_POST_URL = 'api/v1/IoT_07/telemetry' # fill your Device name, select based on your workstation
_COAP_GET_REQ_URL = 'api/v1/IoT_07/attributes' # fill your Device name, select based on your workstation
_COAP_PUT_REQ_URL = 'led/turnOn'
_COAP_AUT_PASS = 'authorization=IoT_07' # fill your Device name, select based on your workstation


def handle_interrupt(pin):
    global button_pressed
    if pin == BUTT_SEND:
        button_pressed = True
    else:
        print("Not right button")
        print(pin)
        
def handle_pir_data(pin):
    global pir_active
    pir_active = True
    global interrupt_pin
    interrupt_pin = pin
        

#Coap POST Message function.
def sendPostRequest(client, json):
    messageId = client.post(_SERVER_IP, _SERVER_PORT, _COAP_POST_URL, json,
                                   None, coap_macros.COAP_CONTENT_FORMAT.COAP_APPLICATION_JSON)
    print("[POST] Message Id: ", messageId)


#Coap PUT Message function.
def sendPutRequest(client):
    messageId = client.put(_SERVER_IP, _SERVER_PORT, _COAP_PUT_REQ_URL, "test",
                                   _COAP_AUT_PASS,
                                   coap_macros.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN)
    print("[PUT] Message Id: ", messageId)


#Coap GET Message function.
def sendGetRequest(client):
    messageId = client.get(_SERVER_IP, _SERVER_PORT, _COAP_GET_REQ_URL)
    print("[GET] Message Id: ", messageId)

#On message callback. Called each time when message that is not ACK is received.
def receivedMessageCallback(packet, sender):
    print('Message received:', packet.toString(), ', from: ', sender)
    print('Packet info received:', packet.messageid, ', from: ', sender)
    #Process the message content here. TODO

#Creates JSON from the available peripherals
def createJSON():
    json_string={"temperature":tmp_sensor.temperature,"humidity":tmp_sensor.relative_humidity,"20":BUTT_SEND.value()!=True}
    json = ujson.dumps(json_string)
    return json


def send_data():
    print("Sending data....")
    json = createJSON()
    sendPostRequest(client, json)


i2c1 = I2C(id = 1, scl=machine.Pin(3), sda=machine.Pin(2)) # Grove 2 connector
tmp_sensor = ahtx0.AHT10(i2c1) # Init I2C sensor

# print Wi-Fi Scan of APs around
aps_scan = wlan.scan() # store last Wi-Fi AP scan
countAPs = len(aps_scan) # get number of APs found
for i in range(countAPs): # iterate over whole scan one-by-one
    print(aps_scan[i]) # print information about AP



wlan.connect("LPWAN-IoT-07", "LPWAN-IoT-07-WiFi") # example for teacher station with number 00

# while Wi-Fi is not connected
while not wlan.isconnected():
    print("WIFI STATUS CONNECTED: " + str(wlan.isconnected())) # print current status aka False=Not connect, True=Connected
    time.sleep_ms(500) # check period set to 500 ms
    

LED.value(1)
print("Wifi connected!")
#print(wlan.ifconfig())


#Create a CoAP client
client = microcoapy.Coap()
client.debug = True
client.responseCallback = receivedMessageCallback

client.start()

BUTT_SEND.irq(trigger=machine.Pin.IRQ_FALLING, handler = handle_interrupt)
BUTT_PIR.irq(trigger=machine.Pin.IRQ_RISING, handler = handle_pir_data)


ticks_start = time.ticks_ms()
get_ticks_start = time.ticks_ms()
get_period = 6500
send_period = 1500#ms

sendGetRequest(client)

while(1):
    
    if button2.value() == 0:
        button2_state = True
        send_data()
        print(button2_state)
        time.sleep(1)
    else:
        button2_state = False

    
 
    
    """
    if (time.ticks_diff(time.ticks_ms(), ticks_start) >= send_period):
        ticks_start=time.ticks_ms()
        json = createJSON()
        print(json)
        sendPostRequest(client, json)
    
    #Let the client do it's thing - send and receive CoAP messages.
    client.poll(10000, pollPeriodMs=1)
    """
    
    if button_pressed:
        send_data()
        print("sendin data succes")
        button_pressed = False
        
    if pir_active:
        print("pir active")
        json = createJSON()
        print(json)
        sendPostRequest(client, json)
        pir_active = False
  



client.stop()



