#!/usr/bin/env python3
import random
import noise
import tkinter as tk
from tkinter import font


class WorldGenerator:
    def __init__(self, base=0):
        self.base = base

    def get_terrain_symbol(self, world_x, world_y):
        scale = 16
        noise_1 = noise.pnoise2(
            world_x / scale,
            world_y / scale,
            base=self.base,
        )
        noise_2 = noise.pnoise2(
            world_x / scale,
            world_y / scale,
            base=self.base + 1,
        )

        noise_1 *= 256
        noise_2 *= 256

        tile = "?"

        if -128 <= noise_1 < -64:
            tile = "~"
        if -64 <= noise_1 < -48:
            tile = "7"
        if -48 <= noise_1 < -32:
            tile = "*"
        if -32 <= noise_1 < -16:
            tile = ";"
        if -16 <= noise_1 < 16:
            tile = ":"
        if 16 <= noise_1 < 32:
            tile = ";"
        if 32 <= noise_1 < 128:
            tile = "#"
            if -16 <= noise_2 < 16:
                tile = "."
                if 32 <= noise_1 < 48:
                    tile = "%"

        return tile

if __name__ == "__main__":

    seed = random.getrandbits(8)
    generator = WorldGenerator(seed)
    print(seed)

    root = tk.Tk()
    root.attributes("-fullscreen", True)

    def destroy(event):
        root.destroy()
    root.bind("<Return>", destroy)

    view_width = 120
    view_height = 96
    cell_size = 16
    canvas_width = view_width * cell_size
    canvas_height = view_height * cell_size
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="black")
    canvas.pack(expand=True, fill="both")

    fixed_font = font.Font(family="Courier", size=int(cell_size * 0.7), weight="bold")
 
    player_world_x, player_world_y = 0, 0
    start_world_x = player_world_x - view_width // 2
    start_world_y = player_world_y - view_height // 2

    for local_y in range(view_height):
        for local_x in range(view_width):
            world_x = start_world_x + local_x
            world_y = start_world_y + local_y
            glyph = generator.get_terrain_symbol(world_x, world_y)
            x = local_x * cell_size + cell_size // 2
            y = local_y * cell_size + cell_size // 2
            canvas.create_text(x, y, text=glyph, font=fixed_font, fill="white")

    root.mainloop()
