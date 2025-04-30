from core import TileMap, Player, GameState, GameEngine
from log import GameLog
from sdl2_input import Sdl2InputAdapter
from sdl2_display import Sdl2DisplayAdapter


def main():
    
    display = Sdl2DisplayAdapter()
    input_adapter = Sdl2InputAdapter()
    tilemap = TileMap()
    player = Player()
    log = GameLog()
    game_state = GameState(tilemap, player, log)
    engine = GameEngine(game_state)
    engine.load_state()

    while game_state.running:
        
        display.show(game_state)
        cmd = input_adapter.read_command()
        engine.process_command(cmd)

    display.quit()


if __name__ == "__main__":
    main()
