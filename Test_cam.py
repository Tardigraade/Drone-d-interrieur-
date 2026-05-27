# Untitled - By: yannfraise - Tue May 26 2026
# Pseudo-code architectural
import sensor, image, time, math

# Initialisation
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.B64X64) # ésolution carrée  pour l'optical flow

# Pour éviter les artefacts de lumière
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)


old_img = sensor.snapshot()
clock = time.clock()

while(True):
    clock.tick()
    img = sensor.snapshot()

    # 1. Calcul du déplacement en pixels
    displacement = img.find_displacement(old_img)
    old_img = img.copy() # l'image actuelle devient l'ancienne
    print(clock.fps())
