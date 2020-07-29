import struct
from bluepy.btle import *
import pandas as pd

out = []

class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        d = struct.unpack('<Hhhhhhhhhh',data)
        r = {'Time': d[0], 'AX':d[1], 'AY':d[2], 'AZ':d[3],
             'GX':d[7], 'GY':d[8], 'GZ':d[9]}

        out.append(r)
        
        print(r)
        

p = Peripheral("C0:83:3A:30:5D:47","random")
chara_uuid = "00e00000-0001-11e1-ac36-0002a5d5c51b"
p.setDelegate(MyDelegate())

print("Connected")

notify = p.getCharacteristics(uuid=chara_uuid)[0]
notify_handle = notify.getHandle() +1
print(notify_handle)
try:
    p.writeCharacteristic(notify_handle, b"\x01\x00", withResponse=True)
    print("writing done")
    while True:
        if p.waitForNotifications(1.0):
            continue
        
except KeyboardInterrupt:
    p.disconnect()
    print("Disconnected")
    print("Done")
    out = pd.DataFrame(out)
    out.head()
    print('Saving')
    out.to_csv("./test_df.csv")
