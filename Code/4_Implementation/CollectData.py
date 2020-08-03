import struct
from bluepy.btle import *
import pandas as pd
import time
import os


def CollectData(mac):
    '''
    Function that collects data from the sensor
    '''

    out = []

    class MyDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

        def handleNotification(self, cHandle, data):
            d = struct.unpack('<Hhhhhhhhhh', data)
            r = {'Time': d[0], 'AX': d[1], 'AY': d[2], 'AZ': d[3],
                 'GX': d[7], 'GY': d[8], 'GZ': d[9]}

            out.append(r)

            print(r)

    p = Peripheral(mac, "random")
    chara_uuid = "00e00000-0001-11e1-ac36-0002a5d5c51b"
    p.setDelegate(MyDelegate())

    os.system('spd-say "Connected"')
    print("Connected")

    # Start notifications
    notify = p.getCharacteristics(uuid=chara_uuid)[0]
    notify_handle = notify.getHandle() + 1
    print(notify_handle)

    # Continue record
    time.sleep(4)

    os.system('spd-say "Ready"')
    for i in range(3, 1, -1):
        print('Ready', i + 1)
        time.sleep(3)

    os.system('spd-say "Go"')

    p.writeCharacteristic(notify_handle, b"\x01\x00", withResponse=True)
    print("writing done")

    # Record for 3 seconds
    t = 0
    start = time.time()
    while t < 3.0:
        t = time.time() - start
        if p.waitForNotifications(1.0):
            continue

    os.system('spd-say "Stop"')
    print("Disconnected")
    out = pd.DataFrame(out)
    out.to_csv('test_4.csv')
    return(out)
