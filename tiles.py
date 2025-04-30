# TILES & TILEMAP
class Tile:
    def __init__(self, is_walkable=False, is_transparent=False):
        self.is_walkable = is_walkable
        self.is_transparent = is_walkable or is_transparent
        self.objects = {}

    def interact(self, state, player):
        return {"cost": 0}


class Wall(Tile):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        state.log.add("Ce mur a l'air très solide.")
        return {"cost": 0}


class Tree(Tile):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        if player.inventory.get("axe") > 0:
            player.inventory.use_item("axe", 1)
            state.log.add("Vous coupez l'arbre !")
            return {"cost": 16, "transform": Stump()}
        state.log.add("Cet arbre est très beau.")
        return {"cost": 0}


class Rubble(Wall):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        if player.inventory.get("pickaxe") > 0:
            player.inventory.use_item("pickaxe", 1)
            state.log.add("Vous cassez les décombres !")
            return {"cost": 16, "transform": Floor()}
        state.log.add("Ces décombres semblent fragiles, mais il vous faut une pioche.")
        return {"cost": 0}


class Floor(Tile):
    def __init__(self):
        super().__init__(is_walkable=True)

    def interact(self, state, player):
        return {"cost": 0}


class Grass(Floor):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        return {"cost": 0}


class Path(Floor):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        return {"cost": 0}


class Stump(Floor):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        state.log.add("Cette souche est tout ce qui reste de l'arbre.")
        return {"cost": 0}


class Bush(Tile):
    def __init__(self):
        super().__init__(is_transparent=True)

    def interact(self, state, player):
        if player.inventory.get("sword") > 0:
            player.inventory.use_item("sword", 1)
            state.log.add("Vous tranchez le buisson !")
            return {"cost": 8, "transform": Grass()}
        state.log.add("Ce buisson est très dense.")
        return {"cost": 0}


class Bridge(Floor):
    def __init__(self):
        super().__init__()

    def interact(self, state, player):
        state.log.add("Vous avancez prudemment sur le sol en bois.")
        return {"cost": 0}


class Stairs(Floor):
    def __init__(self):
        super().__init__()


class Water(Tile):
    def __init__(self):
        super().__init__(is_transparent=True)

    def interact(self, state, player):
        state.log.add("Cette eau semble profonde !")
        return {"cost": 0}


class Door(Tile):
    def __init__(self):
        super().__init__()
        self.opened = False
        self.locked = False

    def open(self):
        self.opened = True
        self.is_walkable = True
        self.is_transparent = True

    def interact(self, state, player):
        if not self.opened:
            if self.locked:
                state.log.add("La porte est verrouillée.")
                return {"cost": 0}
            else:
                self.open()
                state.log.add("Vous ouvrez la porte.")
                return {"cost": 4}
        state.log.add("Vous traversez la porte ouverte.")
        return {"cost": 0}

    def activate(self, state, actor):
        if self.locked:
            self.locked = False
            state.log.add("Une porte se déverrouille quelque part.")
        else:
            state.log.add("Rien ne se passe.")


class Trigger(Floor):
    def __init__(self, linked_object=None):
        super().__init__()
        self.linked_object = linked_object
        self.activated = False

    def interact(self, state, player):
        if self.linked_object and hasattr(self.linked_object, "activate") and not self.activated:
            state.log.add("La plaque s'enfonce !")
            self.activated = True
            self.linked_object.activate(state, player)
        else:
            state.log.add("La plaque ne bouge pas.")
        return {"cost": 0}


