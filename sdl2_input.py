import sdl2
import sdl2.ext

class Sdl2InputAdapter:
    def __init__(self):
        self.movement_key_mapping = {
            sdl2.SDLK_UP: (0, -1),
            sdl2.SDLK_DOWN: (0, 1),
            sdl2.SDLK_LEFT: (-1, 0),
            sdl2.SDLK_RIGHT: (1, 0),
        }
        self.command_key_mapping = {
            sdl2.SDLK_RETURN: "quit",
            sdl2.SDLK_ESCAPE: "abandon",
            sdl2.SDLK_RIGHTPAREN: "dec_sight",
            sdl2.SDLK_EQUALS: "inc_sight",
            sdl2.SDLK_SPACE: "switch_effects",
        }
        self.movement_keys_pressed = set()
        self.accumulated_movement_vectors = set()

    def process_movement_keydown(self, key):
        if key not in self.movement_keys_pressed:
            self.movement_keys_pressed.add(key)
            self.accumulated_movement_vectors.add(self.movement_key_mapping[key])

    def process_command_keydown(self, key):
        return self.command_key_mapping.get(key)

    def process_movement_keyup(self, key):
        self.movement_keys_pressed.discard(key)
        if not self.movement_keys_pressed:
            return self.compute_final_movement()

    def compute_final_movement(self):
        if not self.accumulated_movement_vectors:
            return

        raw_dx = sum(vector[0] for vector in self.accumulated_movement_vectors)
        raw_dy = sum(vector[1] for vector in self.accumulated_movement_vectors)

        dx = max(-1, min(1, raw_dx))
        dy = max(-1, min(1, raw_dy))

        self.accumulated_movement_vectors.clear()
        if dx or dy:
            return "move", (dx, dy)

    def read_command(self):
        event = sdl2.SDL_Event()
        while True:
            if sdl2.SDL_WaitEvent(event) == 0:
                continue

            if event.type == sdl2.SDL_QUIT:
                return "quit"

            if event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key in self.movement_key_mapping:
                    self.process_movement_keydown(key)
                elif key in self.command_key_mapping:
                    cmd = self.process_command_keydown(key)
                    if cmd:
                        return cmd
                else:
                    return ("unmaped", key)

            elif event.type == sdl2.SDL_KEYUP:
                key = event.key.keysym.sym
                if key in self.movement_key_mapping:
                    cmd = self.process_movement_keyup(key)
                    if cmd:
                        return cmd
