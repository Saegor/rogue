import numpy as np
import sdl2

class NoiseOverlay:
    def __init__(self, renderer, window, max_alpha=16):
        self.renderer = renderer
        self.window = window
        self.max_alpha = max_alpha
        self.last_window_size = window.size
        self.texture = self._generate_noise_texture()

    def _generate_noise_texture(self):
        win_width, win_height = self.window.size
        rng = np.random.default_rng(seed=0)
        alpha = rng.integers(0, self.max_alpha + 1, (win_height, win_width), dtype=np.uint8)
        final_texture = np.empty((win_height, win_width, 4), dtype=np.uint8)
        final_texture[..., :3] = 255
        final_texture[..., 3] = alpha

        if sdl2.SDL_BYTEORDER == sdl2.SDL_LIL_ENDIAN:
            pixel_format = sdl2.SDL_PIXELFORMAT_ABGR8888
        else:
            pixel_format = sdl2.SDL_PIXELFORMAT_RGBA8888

        texture = sdl2.SDL_CreateTexture(self.renderer.sdlrenderer, pixel_format,
                                           sdl2.SDL_TEXTUREACCESS_STREAMING,
                                           win_width, win_height)
        texture_buffer = final_texture.tobytes()
        pitch = final_texture.strides[0]
        sdl2.SDL_UpdateTexture(texture, None, texture_buffer, pitch)
        sdl2.SDL_SetTextureBlendMode(texture, sdl2.SDL_BLENDMODE_BLEND)
        return texture

    def update_texture(self):
        if self.window.size != self.last_window_size:
            sdl2.SDL_DestroyTexture(self.texture)
            self.texture = self._generate_noise_texture()
            self.last_window_size = self.window.size

    def render(self):
        self.update_texture()
        sdl2.SDL_RenderCopy(self.renderer.sdlrenderer, self.texture, None, None)

class PixelGrid:
    def __init__(self, renderer, tile_size, pixel_count=14):
        self.renderer = renderer
        self.tile_size = tile_size
        self.pixel_count = pixel_count
        self.last_tile_size = tile_size
        self.texture = self._generate_grid_texture()

    def _generate_grid_texture(self):
        tile = self.tile_size
        pixel_size = tile // self.pixel_count
        border_thickness = pixel_size // 3
        border_offset = border_thickness // 2

        grid = np.zeros((tile, tile, 4), dtype=np.uint8)
        grid[..., 3] = 0

        color = (0, 0, 0, 64)
        for i in range(1, self.pixel_count):
            x = i * pixel_size
            for b in range(border_thickness):
                x_pos = x + b - border_offset
                if 0 <= x_pos < tile:
                    grid[:, x_pos, :] = color
        for i in range(1, self.pixel_count):
            y = i * pixel_size
            for b in range(border_thickness):
                y_pos = y + b - border_offset
                if 0 <= y_pos < tile:
                    grid[y_pos, :, :] = color

        if sdl2.SDL_BYTEORDER == sdl2.SDL_LIL_ENDIAN:
            pixel_format = sdl2.SDL_PIXELFORMAT_ABGR8888
        else:
            pixel_format = sdl2.SDL_PIXELFORMAT_RGBA8888

        texture = sdl2.SDL_CreateTexture(self.renderer.sdlrenderer, pixel_format,
                                           sdl2.SDL_TEXTUREACCESS_STATIC, tile, tile)
        texture_buffer = grid.tobytes()
        pitch = grid.strides[0]
        sdl2.SDL_UpdateTexture(texture, None, texture_buffer, pitch)
        sdl2.SDL_SetTextureBlendMode(texture, sdl2.SDL_BLENDMODE_BLEND)
        return texture

    def update_texture(self, new_tile_size):
        if new_tile_size != self.last_tile_size:
            sdl2.SDL_DestroyTexture(self.texture)
            self.tile_size = new_tile_size
            self.texture = self._generate_grid_texture()
            self.last_tile_size = new_tile_size

    def render(self, dst_rect):
        sdl_rect = sdl2.SDL_Rect(dst_rect[0], dst_rect[1], dst_rect[2], dst_rect[3])
        sdl2.SDL_RenderCopy(self.renderer.sdlrenderer, self.texture, None, sdl_rect)
