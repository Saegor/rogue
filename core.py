import math
import random

from fov import fov
from generator import WorldGenerator
import persistence
from tiles import *

# INVENTORY
class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item, quantity=1):
        self.items[item] = self.items.get(item, 0) + quantity

    def use_item(self, item, quantity=1):
        if self.items.get(item, 0) >= quantity:
            self.items[item] -= quantity
            if self.items[item] == 0:
                del self.items[item]
            return True
        return False

    def get(self, item, default=0):
        return self.items.get(item, default)

class TileMap:
    def __init__(self, seed=random.getrandbits(4)):
        self.tiles = {}
        self.seed = seed
        self.world_generator = WorldGenerator(seed)
        self.CHAR_TO_TILE = {
            "#": Wall,
            "%": Rubble,
            ".": Floor,
            "+": Door,
            "x": Trigger,
            "~": Water,
            ":": Path,
            ">": Stairs,
            "=": Bridge,
            ";": Grass,
            "*": Bush,
            "7": Tree,
        }
        
        self.set_init_camp()

    def get_tile(self, position):
        if position in self.tiles:
            return self.tiles[position]
        glyph = self.world_generator.get_terrain_symbol(*position)
        tile = self.CHAR_TO_TILE.get(glyph, Tile)()
        self.tiles[position] = tile
        self._generate_items(position) #
        return tile

    def _generate_items(self, position):
        random.seed("sword"+str(position))
        if not random.getrandbits(10): self.drop_item(position, "sword", 3)
        random.seed("axe"+str(position))
        if not random.getrandbits(10): self.drop_item(position, "axe", 3)
        random.seed("pickaxe"+str(position))
        if not random.getrandbits(10): self.drop_item(position, "pickaxe", 3)

    def set_tile(self, position, tile):
        self.tiles[position] = tile
        return

    def drop_item(self, position, item, quantity=1):
        tile = self.get_tile(position)
        if tile.is_walkable:
            tile.objects[item] = tile.objects.get(item, 0) + quantity

    def link_trigger_to_target(self, trigger_position, target_position):
        target = self.get_tile(target_position)
        if isinstance(target, Door):
            target.locked = True
        trigger = self.get_tile(trigger_position)
        if isinstance(trigger, Trigger):
            trigger.linked_object = target

    def set_init_camp(self):
        camp_map = [
            ";;;;;;;;;",
            ";~~~~~~~;",
            ";~#####~;",
            ";~#x..#~;",
            ";~##+##~;",
            ";~~~=~~~;",
            ";;~~=~~;;",
            ";;;:::;;;",
        ]

        player_glyph_pos = (4, 3)
        
        for y, row in enumerate(camp_map):
            for x, glyph in enumerate(row):
                pos = (x - player_glyph_pos[0], y - player_glyph_pos[1])
                tile_cls = self.CHAR_TO_TILE.get(glyph, Floor)
                self.set_tile(pos, tile_cls())
                
        self.link_trigger_to_target((-1, 0), (0, 1))

        self.drop_item((1, 0), "sword", 9)
        self.drop_item((1, 0), "axe", 6)
        self.drop_item((1, 0), "pickaxe", 3)

# PLAYER & GAME STATE
class Player:
    def __init__(self, position=(0, 0), sight=9):
        self.position = position
        self.inventory = Inventory()
        self.sight = sight
        self.effects = True

class GameState:
    def __init__(self, tilemap, player, log, running=True):
        self.tilemap = tilemap
        self.player = player
        self.log = log
        self.running = running
        self._time = 0
        self.cycle = 1024
        self.light = player.sight
        self._visible_tiles = set()
        self._seen_tiles = set()

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, new_time):
        if new_time < self._time:
            raise ValueError("Le temps ne peut pas reculer")
        self._time = new_time

    @property
    def visible_tiles(self):
        return self._visible_tiles

    @visible_tiles.setter
    def visible_tiles(self, tiles):
        if not all(isinstance(tile, tuple) for tile in tiles):
            raise ValueError("Les tuiles doivent être des tuples")
        self._visible_tiles = set(tiles)

    @property
    def seen_tiles(self):
        return self._seen_tiles

    @seen_tiles.setter
    def seen_tiles(self, tiles):
        if not all(isinstance(tile, tuple) for tile in tiles):
            raise ValueError("Les tuiles doivent être des tuples")
        self._seen_tiles = set(tiles)

# GAME ENGINE (Logique de jeu)
class GameEngine:
    def __init__(self, state):
        self.state = state
        self.commands = {
            "quit": self._cmd_quit,
            "abandon": self._cmd_abandon,
            "switch_effects": self._cmd_switch_effects,
            "inc_sight": self._cmd_increase_sight,
            "dec_sight": self._cmd_decrease_sight,
        }
        self._update_fov()

    def process_command(self, command):
        if isinstance(command, tuple) and command and command[0] == "move":
            self._process_move(command[1])
        elif command in self.commands:
            self.commands[command]()
        else:
            self.state.log.add(f"Commande inconnue: {command}")

        self._update_fov()
        self._check_stairs()

    def _check_stairs(self):      
        position = self.state.player.position
        current_tile = self.state.tilemap.get_tile(position)
        if isinstance(current_tile, Stairs):
            print("Vous descendez les escaliers.")
            print("Un dragon vous dévore.")
            print("Vous êtes mort.")
            print("Temps écoulé :", self.state.time, "tours.")
            self.state.running = False
            self.state.log.add("Fin du jeu.")

    def _process_move(self, delta):
        dx, dy = delta
        player = self.state.player
        tilemap = self.state.tilemap

        cost = 0
        new_pos = (player.position[0] + dx, player.position[1] + dy)
        target_tile = tilemap.get_tile(new_pos)

        if target_tile.is_walkable:
            player.position = new_pos
            cost = round(math.hypot(dx, dy) * 2)

        result = target_tile.interact(self.state, player)
        cost += result.get("cost", 0)

        if "transform" in result:
            tilemap.set_tile(new_pos, result["transform"])

        self._pickup_items(player.position)
        self._advance_time(cost)

    def _pickup_items(self, position):
        tile = self.state.tilemap.get_tile(position)
        player = self.state.player
        for item, quantity in list(tile.objects.items()):
            self.state.log.add(f"Vous ramassez '{item}' ({quantity}).")
            player.inventory.add_item(item, quantity)
        tile.objects.clear()

    def _advance_time(self, cost):
        self.state.time += cost

    def _update_light(self):
        time = self.state.time
        cycle = self.state.cycle
        self.state.light = math.sin((time % cycle) / cycle * 2 * math.pi)        

    def _update_sight(self):
        self._update_light()
        self.state.player.sight = min(9, round(9 + 3 * self.state.light))

    def _update_fov(self):

        self._update_sight()
        
        new_visible_tiles = fov(
            self.state.tilemap,
            self.state.player.position,
            self.state.player.sight
        )
        self.state.visible_tiles = new_visible_tiles
        self.state._seen_tiles.update(new_visible_tiles)

    def _cmd_increase_sight(self):
        self.state.player.sight += 1
        self.state.log.add("La portée de vision augmente.")

    def _cmd_decrease_sight(self):
        self.state.player.sight = max(1, self.state.player.sight - 1)
        self.state.log.add("La portée de vision diminue.")

    def _cmd_switch_effects(self):
        self.state.player.effects = not self.state.player.effects
        self.state.log.add("Le mode effects est basculé.")

    def save_state(self):
        persistence.save_gamestate(self.state)
        self.state.log.add("Partie sauvegardée.")

    def load_state(self):
        loaded_state = persistence.load_gamestate()
        if loaded_state is None:
            self.state.log.add("Impossible de charger l'état de jeu.")
            return

        self.state.tilemap = loaded_state.tilemap
        self.state.player = loaded_state.player
        self.state.log = loaded_state.log
        self.state.running = loaded_state.running
        self.state._time = loaded_state._time
        self.state._seen_tiles = loaded_state._seen_tiles.copy()
        self.state._visible_tiles = loaded_state._visible_tiles.copy()

        self.state.log.add("Partie chargée.")
        persistence.delete_gamestate()
        self.state.log.add("Sauvegarde supprimée.")

    def _cmd_quit(self):
        self.save_state()
        self.state.running = False
        self.state.log.add("Quitter le jeu.")

    def _cmd_abandon(self):
        self.state.running = False
        self.state.log.add("Vous abandonnez la partie")
