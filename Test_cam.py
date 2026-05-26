# Untitled - By: yannfraise - Tue May 26 2026

import csi
import time

csi0 = csi.CSI()
csi0.reset()
csi0.pixformat(csi.RGB565)
csi0.framesize(csi.VGA)
csi0.snapshot(time=2000)

clock = time.clock()

while True:
    clock.tick()
    img = csi0.snapshot()
    print(clock.fps())
