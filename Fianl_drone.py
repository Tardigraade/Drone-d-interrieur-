import sensor, image, time, math, machine, struct

UART_BAUDRATE = 115200
MAV_system_id = 1
MAV_component_id = 0x54
packet_sequence = 0

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

def build_mavlink_packet(msg_id, extra_crc, payload):
    global packet_sequence
    payload_len = len(payload)

    # Header : STX + len + seq + sysid + compid + msgid
    header = struct.pack(
        "<BBBBBB",
        0xFE,
        payload_len,
        packet_sequence & 0xFF,
        MAV_system_id,
        MAV_component_id,
        msg_id
    )
    packet_sequence += 1

    # CRC calculé sur header[1:] + payload (on exclut STX)
    crc_data = header[1:] + payload
    crc = checksum(crc_data, extra_crc)

    return header + payload + struct.pack("<H", crc)

#  HEARTBEAT (msg #0, extra_crc=50)
MAV_HEARTBEAT_extra_crc = 50

def send_heartbeat():
    # custom_mode(I) + type(B) + autopilot(B) + base_mode(B) +
    # system_status(B) + mavlink_version(B) = 9 octets
    payload = struct.pack("<IBBBBB", 0, 6, 8, 0, 4, 3)
    # type=6 (GCS), autopilot=8 (INVALID), system_status=4 (ACTIVE)
    pkt = build_mavlink_packet(0, MAV_HEARTBEAT_extra_crc, payload)
    uart.write(pkt)
    print(">> Heartbeat envoyé")

#  OPTICAL FLOW (msg #100, extra_crc=175)
MAV_OPTICAL_FLOW_extra_crc = 175

def send_optical_flow_packet(flow_x_pixels, flow_y_pixels, quality_float):
    time_usec = time.ticks_us()
    flow_comp_m_x = 0.0
    flow_comp_m_y = 0.0
    ground_distance = 0.0          # ← remettre à ta vraie valeur (sonar/lidar)
    flow_x = int(flow_x_pixels)    # déjà en 1/10 rad ? → adapter si besoin
    flow_y = int(flow_y_pixels)
    sensor_id = 0
    quality = max(0, min(255, int(quality_float * 255)))

    # q(8) + f(4) + f(4) + f(4) + h(2) + h(2) + B(1) + B(1) = 26 octets ✓
    payload = struct.pack(
        "<qfffhhBB",
        time_usec,
        flow_comp_m_x,
        flow_comp_m_y,
        ground_distance,           # ← ne pas commenter, sinon 24 octets ≠ 26
        flow_x,
        flow_y,
        sensor_id,
        quality
    )
    pkt = build_mavlink_packet(100, MAV_OPTICAL_FLOW_extra_crc, payload)
    uart.write(pkt)

#  Caméra
FOV_X_RAD = 1.23
FOV_Y_RAD = 0.97
RES_X = 64.0
RES_Y = 64.0
RAD_PER_PIXEL_X = FOV_X_RAD / RES_X
RAD_PER_PIXEL_Y = FOV_Y_RAD / RES_Y

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.B64X64)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

old_img = sensor.snapshot()
clock = time.clock()
last_heartbeat_time = time.ticks_ms()

while True:
    clock.tick()
    img = sensor.snapshot()

    displacement = img.find_displacement(old_img)
    dx_pixels = displacement.x_translation()
    dy_pixels = displacement.y_translation()
    quality = displacement.response()

    send_optical_flow_packet(dx_pixels, dy_pixels, quality)

    if time.ticks_diff(time.ticks_ms(), last_heartbeat_time) >= 1000:
        send_heartbeat()
        last_heartbeat_time = time.ticks_ms()

    # Debug
    print("Rad X: {:.4f}, Rad Y: {:.4f}, Q: {}, FPS: {:.1f}".format(
        dx_pixels * RAD_PER_PIXEL_X,
        dy_pixels * RAD_PER_PIXEL_Y,
        int(quality * 255),
        clock.fps()
    ))

    # Visualisation flèche
    cx, cy = img.width() // 2, img.height() // 2
    img.draw_arrow(cx, cy,
                   int(cx + dx_pixels * 10),
                   int(cy + dy_pixels * 10),
                   color=255, thickness=1)

    old_img = img.copy()
