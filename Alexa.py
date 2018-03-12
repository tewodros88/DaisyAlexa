# Import standard python modules.
import sys
import time
import serial

# Import Adafruit IO MQTT client.
from Adafruit_IO import MQTTClient

ADAFRUIT_IO_KEY      = '317bca24bd7a4e89ba35110c24190573'
ADAFRUIT_IO_USERNAME = 'tewodros'  

ser = serial.Serial('/dev/cu.usbmodem1411', 115200)

def passByte(b):
    print("Passing byte " + str(b))
    ser.write(bytes([int(b)]))

def halt():
    passByte(0)

def moveForward():
    passByte(1)

def turnRight():
    passByte(2)

def turnLeft():
    passByte(3)

def moveBackward():
    passByte(4)

def connected(client):
    print('Connected to Adafruit IO!  Listening for Daisy changes...')
    # Subscribe to changes on a feeds like daisy stop and move forward.
    client.subscribe('daisy-stop')
    client.subscribe('daisy-move-forward')

def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print('Disconnected from Adafruit IO!')
    sys.exit(1)

def message(client, feed_id, payload):
    
    case = int(payload)                               # associate payload value with daisy commands                   
    
    if case == 0:
        halt()          
        print('Daisy has now stopped moving')

    elif case == 1:
        moveForward()
        print('Daisy has now started moving forward')


# Create an MQTT client instance.
client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# Setup the callback functions defined above.
client.on_connect    = connected
client.on_disconnect = disconnected
client.on_message    = message

# Connect to the Adafruit IO server.
client.connect()

# Now the program needs to use a client loop function to ensure messages are
# sent and received. 
# Run a thread in the background so you can continue running script
client.loop_background()

while True:
    time.sleep(10)

if __name__ == "__main__":
    main()
