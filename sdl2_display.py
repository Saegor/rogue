import math
import random

import sdl2
import sdl2.ext

from tiles import *
from effects import NoiseOverlay, PixelGrid


class Sdl2DisplayAdapter:
    TILE_TEXTURE_MAPPING = {
        Tile: "tile",
        Floor: "floor",
        Wall: "wall",
        Rubble: "rubble",
        Water: "water",
        Door: ("door_closed", "door_open"),
        Trigger: "trigger",
        Stairs: "stairs",
        Bridge: "bridge",
        Grass: "grass",
        Bush: "bush",
        Tree: "tree",
        Stump: "stump",
        Path: "path",
    }

    def __init__(self):
        sdl2.ext.init()
        sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)
        self.window = sdl2.ext.Window("Roguelike", size=(0, 0), flags=sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
        self.window.show()
        self.renderer = sdl2.ext.Renderer(self.window)
        self.font_manager = sdl2.ext.FontManager("assets/terminus.ttf", size=24)
        self.sprite_factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=self.renderer)
        sdl2.SDL_SetRenderDrawBlendMode(self.renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
        self.textures = {}
        self.load_textures()
        self.noise_overlay = NoiseOverlay(self.renderer, self.window)
        self.pixel_grid = None
        random.seed(0)

    def load_textures(self):
        texture_files = {
            "tile": "tile.png",
            "floor": "floor.png",
            "wall": "wall.png",
            "rubble": "rubble.png",
            "water": "water.png",
            "door_closed": "door_closed.png",
            "door_open": "door_open.png",
            "player": "player.png",
            "object": "object.png",
            "trigger": "trigger.png",
            "stairs": "stairs.png",
            "bridge": "bridge.png",
            "grass": "grass.png",
            "bush": "bush.png",
            "tree": "tree.png",
            "stump": "stump.png",
            "path": "path.png",
        }
        assets_path = "assets/"
        for key, filename in texture_files.items():
            full_path = assets_path + filename
            try:
                self.textures[key] = self.sprite_factory.from_image(full_path)
            except Exception as e:
                print("Erreur lors du chargement de l'image {}: {}".format(full_path, e))

    def update_tile_dimensions(self, viewport_tile_count, pixel_grid=14):
        win_width, win_height = self.window.size
        raw_tile_size = min(win_width, win_height) // viewport_tile_count
        self.tile_size = (raw_tile_size // pixel_grid) * pixel_grid
        self.offset = ((win_width - self.tile_size * viewport_tile_count) // 2,
                       (win_height - self.tile_size * viewport_tile_count) // 2)
        if self.pixel_grid is None:
            self.pixel_grid = PixelGrid(self.renderer, self.tile_size, pixel_grid)
        else:
            self.pixel_grid.update_texture(self.tile_size)

    def grid_to_pixel_coords(self, grid_pos):
        x = self.offset[0] + grid_pos[0] * self.tile_size
        y = self.offset[1] + grid_pos[1] * self.tile_size
        return x, y

    def get_tile_sprite(self, tile):
        texture_mapping = Sdl2DisplayAdapter.TILE_TEXTURE_MAPPING.get(type(tile))
        
        if isinstance(tile, Door):
            texture_key = texture_mapping[1] if getattr(tile, "opened", False) else texture_mapping[0]
        else:
            texture_key = texture_mapping

        sprite = self.textures.get(texture_key)
        if not sprite:
            print("Sprite pour la clé {} introuvable.".format(texture_key))
        return sprite

    def draw_text(self, text, pos, color=(255, 255, 255)):
        text_sprite = self.sprite_factory.from_text(text, color=color, fontmanager=self.font_manager)
        dst_rect = sdl2.SDL_Rect(pos[0], pos[1], text_sprite.size[0], text_sprite.size[1])
        self.renderer.copy(text_sprite, dstrect=(dst_rect.x, dst_rect.y, dst_rect.w, dst_rect.h))

    def draw_log(self, log):
        messages = log.get_recent_messages()
        y_position = self.window.size[1] - (32 * len(messages) + 32)
        for message in messages:
            self.draw_text(message, pos=(32, y_position))
            y_position += 32
        log.clear()

    def draw_inventory(self, player):
        inventory_origin = (self.window.size[0] - 256, 32)
        y_offset = inventory_origin[1]
        sorted_items = sorted(player.inventory.items.items(), key=lambda x: x[0])
        for item, count in sorted_items:
            self.draw_text(f"{item} ({count})", (inventory_origin[0], y_offset))
            y_offset += 32

    def draw_frame(self, viewport_count):
        x = self.offset[0]
        y = self.offset[1]
        width = viewport_count * self.tile_size
        height = width
        self.renderer.color = sdl2.SDL_Color(255, 255, 255, 64)
        self.renderer.draw_rect((x, y, width, height))

    def _apply_daylight(self, texture, light):
        yellow = min(255, 255 + round(light * 64))
        blue = min(255, 255 - round(light * 32))
        sdl2.SDL_SetTextureColorMod(texture, yellow, yellow, blue)

    def show(self, state):
        self.renderer.clear((0, 0, 0))
        viewport_count = max(19, state.player.sight * 2 + 1)
        self.update_tile_dimensions(viewport_count)
        vp_half = viewport_count // 2
        view_origin = (
            state.player.position[0] - vp_half,
            state.player.position[1] - vp_half
        )

        for row in range(viewport_count):
            for col in range(viewport_count):
                map_pos = (view_origin[0] + col, view_origin[1] + row)
                if map_pos in state.visible_tiles:
                    dx = map_pos[0] - state.player.position[0]
                    dy = map_pos[1] - state.player.position[1]
                    ratio = math.hypot(dx, dy) / max(1, state.player.sight)
                    alpha_mod = int(255 * max(0.5, 1 - ratio * ratio))
                    if not state.player.effects:
                        alpha_mod = 255
                elif map_pos in state.seen_tiles:
                    alpha_mod = 32
                    if not state.player.effects:
                        alpha_mod = 0
                else:
                    alpha_mod = 0

                if alpha_mod > 0:
                    grid_pos = (col, row)
                    pixel_coords = self.grid_to_pixel_coords(grid_pos)
                    dst_rect = (pixel_coords[0], pixel_coords[1], self.tile_size, self.tile_size)
                    tile = state.tilemap.get_tile(map_pos)
                    sprite = self.get_tile_sprite(tile)
                    if sprite and not getattr(tile, "objects", None):
                        sdl2.SDL_SetTextureBlendMode(sprite.texture, sdl2.SDL_BLENDMODE_BLEND)
                        sdl2.SDL_SetTextureAlphaMod(sprite.texture, alpha_mod)
                        self._apply_daylight(sprite.texture, state.light)
                        self.renderer.copy(sprite, dstrect=dst_rect)
                    if getattr(tile, "objects", None):
                        object_sprite = self.textures.get("object")
                        if object_sprite:
                            sdl2.SDL_SetTextureBlendMode(object_sprite.texture, sdl2.SDL_BLENDMODE_BLEND)
                            sdl2.SDL_SetTextureAlphaMod(object_sprite.texture, alpha_mod)
                            self._apply_daylight(sprite.texture, state.light)
                            self.renderer.copy(object_sprite, dstrect=dst_rect)
                    
                    if map_pos == state.player.position:
                        player_sprite = self.textures.get("player")
                        if player_sprite:
                            sdl2.SDL_SetTextureBlendMode(player_sprite.texture, sdl2.SDL_BLENDMODE_BLEND)
                            self._apply_daylight(sprite.texture, state.light)
                            self.renderer.copy(player_sprite, dstrect=dst_rect)

                    if state.player.effects:
                        self.pixel_grid.render(dst_rect)

        if state.player.effects:
            self.noise_overlay.render()
            self.draw_frame(viewport_count)

        self.draw_text(f"position: {state.player.position}", (32, 32))
        self.draw_text(f"sight: {state.player.sight}", (32, 64))
        self.draw_text(f"time: {state.time}", (32, 96))
        self.draw_text(f"seed: {state.tilemap.seed}", (32, 128))
        self.draw_text(f"visible_tiles: {len(state.visible_tiles)}", (32, 160))
        self.draw_text(f"seen_tiles: {len(state.seen_tiles)}", (32, 192))

        hour = (round(state.time % 1024 / 1024 * 24) + 6) % 24 #
        self.draw_text(f"time: {hour}h", (32, 224)) #

        self.draw_inventory(state.player)
        self.draw_log(state.log)
        self.renderer.present()

    def quit(self):
        sdl2.ext.quit()
