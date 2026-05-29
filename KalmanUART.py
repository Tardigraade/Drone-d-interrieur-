# Untitled - By: yannfraise - Fri May 29 2026

import sensor, image, time, math, machine, struct


UART_BAUDRATE = 115200
MAV_system_id = 1
MAV_component_id = 0x54
packet_sequence = 0

MAV_OPTICAL_FLOW_confidence_threshold = (0.1)

# Link Setup
uart = machine.UART(1, UART_BAUDRATE, timeout_char=1000)

def checksum(data, extra):
    output = 0xFFFF
    for i in range(len(data)):
        tmp = data[i] ^ (output & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        output = ((output >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    tmp = extra ^ (output & 0xFF)
    tmp = (tmp ^ (tmp << 4)) & 0xFF
    output = ((output >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    return output


MAV_OPTICAL_FLOW_message_id = 100
MAV_OPTICAL_FLOW_id = 0  # unused
MAV_OPTICAL_FLOW_extra_crc = 175

def send_optical_flow_packet(x, y, c):
    global packet_sequence
    temp = struct.pack(
        "<qfffhhbb", 0, 0, 0, 0, int(x), int(y), MAV_OPTICAL_FLOW_id, int(c * 255)
    )
    temp = struct.pack(
        "<bbbbb26s",
        26,
        packet_sequence & 0xFF,
        MAV_system_id,
        MAV_component_id,
        MAV_OPTICAL_FLOW_message_id,
        temp,
    )
    temp = struct.pack("<b31sh", 0xFE, temp, checksum(temp, MAV_OPTICAL_FLOW_extra_crc))
    packet_sequence += 1
    uart.write(temp)



FOV_X_RAD = 1.23
FOV_Y_RAD = 0.97

RES_X = 64.0
RES_Y = 64.0

# Radians par pixel
RAD_PER_PIXEL_X = FOV_X_RAD / RES_X
RAD_PER_PIXEL_Y = FOV_Y_RAD / RES_Y

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

    sub_pixel_x = int(-displacement.x_translation() * 35)
    sub_pixel_y = int(displacement.y_translation() * 53)

    # La méthode response() renvoie un float entre 0.0 et 1.0
    quality = math.floor(displacement.response() * 255)

    # 3. Conversion en Radians
    delta_rad_x = dx_pixels * RAD_PER_PIXEL_X
    delta_rad_y = dy_pixels * RAD_PER_PIXEL_Y

    dt_us = int(clock.avg() * 1000)


    print("Rad X: {:.4f}, Rad Y: {:.4f}, Qualité: {}, dt: {} us".format(delta_rad_x, delta_rad_y, quality, dt_us))

    send_optical_flow_packet(sub_pixel_x, sub_pixel_y, displacement.response())

    # 1. Trouver le centre de l'image
    center_x = img.width() // 2
    center_y = img.height() // 2

    # Grossis
    vis_scale = 10

    # 3. Coordonnes fleche
    end_x = int(center_x + (dx_pixels * vis_scale))
    end_y = int(center_y + (dy_pixels * vis_scale))

    # 4.  flèche
    img.draw_arrow(center_x, center_y, end_x, end_y, color=255, thickness=1)

    old_img = img.copy()
    print(clock.fps())
