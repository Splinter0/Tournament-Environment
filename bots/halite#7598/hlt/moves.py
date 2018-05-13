from . import constants
from . import custom
from enum import Enum
import logging

class Move(object):
    class MoveType(Enum):
        FLEE = 0 #run away
        RUSH = 1 #rush enemy
        ATTACK = 2 #attack a ship
        SNEAK = 3 #more tactic attack
        EXPLORE = 4 #find a new planet and dock
        KAMIKAZE = 5 #blow up a planet
        LEAVE = 6 #leave a docked planet
        AVOID_RUSH = 7 #avoid rush from enemy
        STALL = 8 #don't do anything
        DOCK = 9 #just simply dock

    def __init__(self, ship, move, target, needed, game_map, enemies=None, fleet=None):
        self.move = move
        self.target = target
        self.needed = needed
        self.game_map = game_map
        self.enemies = enemies
        self.fleet = fleet
        self.turn = 0

        self.ships = []
        self.angles = []

        if ship != None:
            self.ships.append(ship)
            self.id = str(ship.id)+"-"+str(self.move)
        else:
            self.id = str(self.move)

    def log(self):
        ids = [i.id for i in self.ships]
        logging.info("Move : "+str(self.id)+" assigned to ships : "+str(ids)+" targeting : "+str(self.target.id if self.target != None else "None"))

    def getId(self):
        return self.id

    def assign(self, ship):
        if self.isPart(ship):
            return True

        if len(self.ships) < self.needed:
            self.ships.append(ship)
            self.needed -= 1
            return True
        else:
            return False

    def isPart(self, ship):
        for s in self.ships:
            if s.id == ship.id:
                return True

        return False

    def changeMove(self, move):
        self.move = move

    def addTurn(self):
        self.turn += 1
        return self.turn

    def retireMove(self):
        self.ships = []
        self.needed = 0
        self.target = None

    def execute(self, ship):
        self.addTurn()
        if self.move == self.MoveType.AVOID_RUSH:
            if self.turn <= 20:
                top, bottom = self.game_map.getWalls(ship)
                corners = self.game_map.getCorners()

                if custom.euclidean(ship, top) >= custom.euclidean(ship, bottom) :
                    if self.target is None:
                        self.target = bottom
                    else:
                        if self.target == corners[2] and custom.euclidean(ship, corners[2]) <= 3:
                            self.target = corners[0]
                        elif self.target == corners[3] and custom.euclidean(ship, corners[3]) <= 3:
                            self.target = corners[1]
                        else:
                            self.target = custom.closest(ship, corners[2], corners[3])
                else:
                    if self.target is None:
                        self.target = top
                    else:
                        if self.target == corners[0] and custom.euclidean(ship, corners[0]) <= 3:
                            self.target = corners[3]
                        elif self.target == corners[3] and custom.euclidean(ship, corners[3]) <= 3:
                            self.target = corners[2]
                        else:
                            self.target = custom.closest(ship, corners[0], corners[1])

                navigate_command = ship.navigate(
                            ship.closest_point_to(self.target),
                            self.game_map,
                            speed=int(constants.MAX_SPEED),
                            ignore_ships=False)

            else:
                navigate_command = ship.navigate(
                            ship.closest_point_to(self.target),
                            self.game_map,
                            speed=int(constants.MAX_SPEED),
                            ignore_ships=False)

            if navigate_command:
                return navigate_command

        elif self.move == self.MoveType.DOCK:
            return ship.dock(self.target)

        elif self.move == self.MoveType.EXPLORE:
            if ship.can_dock(self.target):
                return ship.dock(self.target)

            else:
                navigate_command = ship.navigate(
                            ship.closest_point_to(self.target),
                            self.game_map,
                            speed=int(constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    return navigate_command

        elif self.move == self.MoveType.ATTACK:
            navigate_command = ship.navigate(
                        ship.closest_point_to(self.target),
                        self.game_map,
                        speed=int(constants.MAX_SPEED),
                        ignore_ships=False)

            if navigate_command:
                return navigate_command

        elif self.move == self.MoveType.FLEE:
            top, bottom = self.game_map.getWalls(ship)
            corners = self.game_map.getCorners()

            if custom.euclidean(ship, top) >= custom.euclidean(ship, bottom) :
                if self.target is None:
                    self.target = bottom
                else:
                    if self.target == corners[2] and custom.euclidean(ship, corners[2]) <= 3:
                        self.target = corners[0]
                    elif self.target == corners[3] and custom.euclidean(ship, corners[3]) <= 3:
                        self.target = corners[1]
                    else:
                        self.target = custom.closest(ship, corners[2], corners[3])
            else:
                if self.target is None:
                    self.target = top
                else:
                    if self.target == corners[0] and custom.euclidean(ship, corners[0]) <= 3:
                        self.target = corners[3]
                    elif self.target == corners[3] and custom.euclidean(ship, corners[3]) <= 3:
                        self.target = corners[2]
                    else:
                        self.target = custom.closest(ship, corners[0], corners[1])

            navigate_command = ship.navigate(
                        ship.closest_point_to(self.target),
                        self.game_map,
                        speed=int(constants.MAX_SPEED),
                        ignore_ships=False)

            if navigate_command:
                return navigate_command

        elif self.move == self.MoveType.SNEAK:
            self.target = None
            for s in self.enemies:
                if s.docking_status != s.DockingStatus.UNDOCKED and custom.euclidean(s, ship) <= 40:
                    self.target = s
                    break

            if self.target is None:
                navigate_command = ship.navigate(
                                ship.closest_point_to(self.enemies[0]),
                                self.game_map,
                                speed=int(constants.MAX_SPEED),
                                ignore_ships=False)

            else:
                navigate_command = ship.navigate(
                                ship.closest_point_to(self.target),
                                self.game_map,
                                speed=int(constants.MAX_SPEED),
                                ignore_ships=False)

            return navigate_command

        elif self.move == self.MoveType.KAMIKAZE:
            pass

        elif self.move == self.MoveType.LEAVE:
            return ship.undock()

        elif self.move == self.MoveType.STALL:
            navigate_command = ship.navigate(
                        ship.closest_point_to(ship),
                        self.game_map,
                        speed=int(constants.MAX_SPEED),
                        ignore_ships=False)

            if navigate_command:
                return navigate_command
