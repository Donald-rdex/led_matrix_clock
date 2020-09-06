#!/usr/bin/env python3
import logging
import time
from datetime import datetime
import random
from random import randint

from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text
# from luma.core.virtual import viewport
from luma.core.legacy.font import proportional, LCD_FONT
from luma.led_matrix.device import max7219

logging.basicConfig(level=logging.WARNING)

serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, width=32, height=16, block_orientation=-90)

# when to reduce the brightness for overnight
# TODO move to a config file, at the least the interval specifically
display_intensity = {'min': 16, 'max': 200}
awake_interval = {'start': 7, 'stop': 20}


def set_brightness(current_dt):
    """ Use the current time from a datetime object to set the brightness of the leds"""
    if awake_interval['start'] < current_dt.hour >= awake_interval['stop']:
        device.contrast(64)
    else:
        device.contrast(231)


def draw_date():
    current_dt = datetime.now()
    top_line = current_dt.strftime("%a")
    bot_line = current_dt.strftime("%m/%d")
    set_brightness(current_dt)
    with canvas(device) as draw:
        # draw.rectangle(device.bounding_box, outline="white")
        text(draw, (1, 1), top_line, fill="white", font=proportional(LCD_FONT))
        text(draw, (1, 9), bot_line, fill="white", font=proportional(LCD_FONT))


def draw_time():
    current_dt = datetime.now()
    top_line = current_dt.strftime("%H:%M")
    bot_line = current_dt.strftime("%a")
    set_brightness(current_dt)
    with canvas(device) as draw:
        # draw.rectangle(device.bounding_box, outline="white")
        text(draw, (1, 1), top_line, fill="white", font=proportional(LCD_FONT))
        text(draw, (1, 9), bot_line, fill="white", font=proportional(LCD_FONT))


def draw_life():
    # Copied from the luma example for their implementation of Conway's Life
    # https://github.com/rm-hull/luma.examples/blob/master/examples/game_of_life.py
    current_dt = datetime.now()
    set_brightness(current_dt)

    scale = 1
    cols = device.width // scale
    rows = device.height // scale
    initial_population = int(cols * rows * 0.33)
    count = 1

    while count < 5:
        board = set((randint(0, cols), randint(0, rows)) for _ in range(initial_population))
        count += 1

        for i in range(500):
            with canvas(device, dither=True) as draw:
                for x, y in board:
                    left = x * scale
                    top = y * scale

                    if scale == 1:
                        draw.point((left, top), fill="white")
                        logging.debug("L: {}({}), T: {}({}), scale: {}".format(left, cols, top, rows, scale))
                    else:
                        right = left + scale
                        bottom = top + scale
                        draw.rectangle((left, top, right, bottom), fill="white", outline="black")

                if i == 0:
                    w, h = draw.textsize("Life")
                    left = (device.width - w) // 2
                    top = (device.height - h) // 2
                    draw.rectangle((left - 1, top, left + w + 1, top + h), fill="black", outline="white")
                    draw.text((left + 1, top), text="Life", fill="white")

            if i == 0:
                time.sleep(3)

            board = life_iterate(board)


def life_neighbors(cell):
    x, y = cell
    yield x - 1, y - 1
    yield x, y - 1
    yield x + 1, y - 1
    yield x - 1, y
    yield x + 1, y
    yield x - 1, y + 1
    yield x, y + 1
    yield x + 1, y + 1


def life_iterate(board):
    new_board = set([])
    candidates = board.union(set(n for cell in board for n in life_neighbors(cell)))
    for cell in candidates:
        count = sum((n in board) for n in life_neighbors(cell))
        if count == 3 or (count == 2 and cell in board):
            new_board.add(cell)
    return new_board


def snow():
    # TODO gentle led snow falling...
    scale = 1
    cols = device.width // scale
    rows = device.height // scale
    logging.debug(cols, rows)
    pass


def random_walk():
    # random dots walk randomly around the screen
    current_dt = datetime.now()
    set_brightness(current_dt)
    do_we_fill = random.choice([1, 2])

    scale = 1
    cols = device.width // scale
    rows = device.height // scale
    nodes = {}

    how_many_nodes = random.randint(0, 10) + 1
    device.clear()

    for i in range(1, how_many_nodes):
        dst_x = random.randint(0, cols)
        dst_y = random.randint(0, rows)
        nodes[i] = [dst_x, dst_y]
        with canvas(device) as draw:
            draw.point((dst_x, dst_y), fill="white")

    walks = 4 * 120  # 4 steps per second for 120 seconds.
    while walks > 0:
        logging.info(walks)
        with canvas(device) as draw:
            for i in range(1, how_many_nodes):
                where_to = random.choice([0, 1, 2, 3, 4])
                cur_x = nodes[i][0]
                cur_y = nodes[i][1]
                if where_to == 4:
                    dst_y = nodes[i][1] + 1
                    dst_x = nodes[i][0]
                    if dst_y > device.height:
                        dst_y = 0
                elif where_to == 3:
                    dst_y = nodes[i][1]
                    dst_x = nodes[i][0] + 1
                    if dst_x > device.width:
                        dst_x = 0
                elif where_to == 2:
                    dst_y = nodes[i][1]-1
                    dst_x = nodes[i][0]
                    if dst_y < 0:
                        dst_y = device.height
                elif where_to == 1:
                    dst_y = nodes[i][1]
                    dst_x = nodes[i][0]-1
                    if dst_x < 0:
                        dst_x = device.width
                else:
                    dst_y = nodes[i][1]
                    dst_x = nodes[i][0]

                if do_we_fill == 1:
                    draw.point((cur_x, cur_y), fill="white")
                nodes[i] = [dst_x, dst_y]
                draw.point((dst_x, dst_y), fill="white")
        walks -= 1
        # NOTE 1 sec is slow... and jerky,
        # 0.3 secs feels like bad video
        time.sleep(0.1)


def slow_fill():
    # one dot walks across the screen, useful for testing.
    current_dt = datetime.now()
    set_brightness(current_dt)
    scale = 1
    cols = device.width // scale
    rows = device.height // scale

    device.clear()

    for i in range(0, cols):
        for j in range(0, rows):
            with canvas(device) as draw:
                logging.info("{}({}), {}({})".format(i, cols, j, rows))
                draw.point((i, j), fill="white")
                time.sleep(0.25)


if __name__ == "__main__":
    default_sleep = 30
    while True:
        rand_display = random.randint(0, 100)

        if rand_display <= 35:
            draw_date()
            time.sleep(default_sleep)
        if 35 < rand_display <= 85:
            draw_time()
            time.sleep(default_sleep)
        if rand_display > 85:
            if random.choice([0, 1, 2]) == 0:
                draw_life()
            else:
                # slow_fill()
                random_walk()
