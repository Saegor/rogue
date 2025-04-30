import pickle
import os

def save_gamestate(gamestate, filename="gamestate.sav"):
    try:
        with open(filename, "wb") as f:
            pickle.dump(gamestate, f)
        # ~ print(f"GameState sauvegardé dans {filename}.")
    except Exception as e:
        print("Erreur lors de la sauvegarde du GameState :", e)

def load_gamestate(filename="gamestate.sav"):
    try:
        with open(filename, "rb") as f:
            gamestate = pickle.load(f)
        # ~ print(f"GameState chargé depuis {filename}.")
        return gamestate
    except Exception as e:
        # ~ print("Erreur lors du chargement du GameState :", e)
        return None

def delete_gamestate(filename="gamestate.sav"):
    try:
        os.remove(filename)
        # ~ print(f"Le fichier {filename} a été supprimé.")
    except Exception as e:
        print("Erreur lors de la suppression du fichier :", e)
        pass
