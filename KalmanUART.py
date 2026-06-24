# Untitled - By: yannfraise - Fri May 29 2026

import sensor, image, time, math, machine, struct


UART_BAUDRATE = 115200
MAV_system_id = 1
MAV_component_id = 0x54  # MAV_COMP_ID_VISION_POSITION
packet_sequence = 0

# Initialisation de l'UART
uart = machine.UART(1, UART_BAUDRATE, timeout_char=1000)


def checksum(data, extra):
    output = 0xFFFF
    for byte in data:
        tmp = byte ^ (output & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        output = ((output >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    tmp = extra ^ (output & 0xFF)
    tmp = (tmp ^ (tmp << 4)) & 0xFF
    output = ((output >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    return output


MAV_HEARTBEAT_message_id = 0
MAV_HEARTBEAT_extra_crc = 50

def send_heartbeat():
    global packet_sequence

    # Payload MAVLink de HEARTBEAT (9 octets)
    # custom_mode (uint32), type (uint8), autopilot (uint8), base_mode (uint8), system_status (uint8), mavlink_version (uint8)
    payload = struct.pack("<IBBBBB", 0, 0, 0, 0, 0, 3)

    header = struct.pack(
        "<bbbbb9s",
        9,                            # Longueur payload
        packet_sequence & 0xFF,       # Séquence
        MAV_system_id,                # System ID
        MAV_component_id,             # Component ID
        MAV_HEARTBEAT_message_id,     # Message ID (0)
        payload
    )

    packet = struct.pack("<b14sh", 0xFE, header, checksum(header, MAV_HEARTBEAT_extra_crc))
    packet_sequence += 1
    uart.write(packet)


MAV_OPTICAL_FLOW_message_id = 100
MAV_OPTICAL_FLOW_id = 0
MAV_OPTICAL_FLOW_extra_crc = 175

def send_optical_flow_packet(flow_x_pixels, flow_y_pixels, quality_float):
    global packet_sequence

    time_usec = time.ticks_us()
    flow_comp_m_x = 0.0
    flow_comp_m_y = 0.0

   # ground_distance = 1.2

    flow_x = int(flow_x_pixels * 10)
    flow_y = int(flow_y_pixels * 10)
    quality = int(quality_float * 255)

    payload = struct.pack(
        "<qfffhhbb",
        time_usec,
        flow_comp_m_x,
        flow_comp_m_y,
        #ground_distance,
        flow_x,
        flow_y,
        MAV_OPTICAL_FLOW_id,
        quality
    )

    header = struct.pack(
        "<bbbbb26s",
        26,
        packet_sequence & 0xFF,
        MAV_system_id,
        MAV_component_id,
        MAV_OPTICAL_FLOW_message_id,
        payload
    )

    packet = struct.pack("<b31sh", 0xFE, header, checksum(header, MAV_OPTICAL_FLOW_extra_crc))
    packet_sequence += 1
    uart.write(packet)


FOV_X_RAD = 1.23
FOV_Y_RAD = 0.97
RES_X = 64.0
RES_Y = 64.0

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

last_heartbeat_time = time.ticks_ms()


while(True):
    clock.tick()
    img = sensor.snapshot()

    displacement = img.find_displacement(old_img)

    dx_pixels = displacement.x_translation()
    dy_pixels = displacement.y_translation()
    quality = displacement.response()

    send_optical_flow_packet(dx_pixels, dy_pixels, quality)

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_heartbeat_time) >= 1000:
        send_heartbeat()
        last_heartbeat_time = current_time
        print(">> Heartbeat envoyé au Pixhawk")

    # debug
    delta_rad_x = dx_pixels * RAD_PER_PIXEL_X
    delta_rad_y = dy_pixels * RAD_PER_PIXEL_Y
    print("Rad X: {:.4f}, Rad Y: {:.4f}, Qualité: {}, FPS: {:.1f}".format(delta_rad_x, delta_rad_y, int(quality*255), clock.fps()))

    #Fleche
    center_x = img.width() // 2
    center_y = img.height() // 2
    vis_scale = 10

    end_x = int(center_x + (dx_pixels * vis_scale))
    end_y = int(center_y + (dy_pixels * vis_scale))

    img.draw_arrow(center_x, center_y, end_x, end_y, color=255, thickness=1)


    old_img = img.copy()
