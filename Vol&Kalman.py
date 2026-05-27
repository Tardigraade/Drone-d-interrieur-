# Untitled - By: yannfraise - Wed May 27 2026

import sensor, image, time, math

# --- Constantes Optiques (à ajuster selon ta lentille exacte) ---
# Valeurs approximatives pour une lentille standard OpenMV 2.8mm
FOV_X_RAD = 1.23  # Champ de vision horizontal en radians
FOV_Y_RAD = 0.97  # Champ de vision vertical en radians

RES_X = 64.0      # Largeur de l'image
RES_Y = 64.0      # Hauteur de l'image

# Calcul du facteur d'échelle (Radians par pixel)
RAD_PER_PIXEL_X = FOV_X_RAD / RES_X
RAD_PER_PIXEL_Y = FOV_Y_RAD / RES_Y

# --- Initialisation Capteur ---
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.B64X64)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

old_img = sensor.snapshot()
clock = time.clock()

while(True):
    clock.tick()
    img = sensor.snapshot()

    # 1. Calcul du déplacement
    displacement = img.find_displacement(old_img)

    # 2. Extraction des pixels et de la qualité
    dx_pixels = displacement.x_translation()
    dy_pixels = displacement.y_translation()

    # La méthode response() renvoie un float entre 0.0 et 1.0
    # MAVLink attend un entier entre 0 et 255
    quality = math.floor(displacement.response() * 255)

    # 3. Conversion en Radians
    # On inverse souvent les signes selon l'orientation de montage de la caméra
    # par rapport au repère (Forward-Right-Down) du drone.
    delta_rad_x = dx_pixels * RAD_PER_PIXEL_X
    delta_rad_y = dy_pixels * RAD_PER_PIXEL_Y

    # Temps d'intégration  (dt)
    dt_us = int(clock.avg() * 1000)


    print("Rad X: {:.4f}, Rad Y: {:.4f}, Qualité: {}, dt: {} us".format(delta_rad_x, delta_rad_y, quality, dt_us))



    # 1. Trouver le centre de l'image
    center_x = img.width() // 2
    center_y = img.height() // 2

    # Grossis
    vis_scale = 10

    # 3. Calculer les coordonnées de la pointe de la flèche
    # On utilise dx_pixels et dy_pixels déjà extraits
    end_x = int(center_x + (dx_pixels * vis_scale))
    end_y = int(center_y + (dy_pixels * vis_scale))

    # 4.  flèche
    img.draw_arrow(center_x, center_y, end_x, end_y, color=255, thickness=1)

    old_img = img.copy()
    print(clock.fps())
