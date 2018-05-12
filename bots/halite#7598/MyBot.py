import os
import hlt
import hlt.custom as custom
import logging
from collections import OrderedDict
import sys

class Plan(object):
    def __init__(self, ship, vector, target):
        self.ship = ship
        self.vector = vector
        self.target = target

class Border(hlt.entity.Entity):
    def __init__(self, *args, **kwargs):
        super(Border, self).__init__(*args, **kwargs)

class Raffaello(object):
    def __init__(self, version, debug=True):
        self.version = version
        self.debug = debug

        self.id = 0

        self.game = hlt.Game("HTBot-v{}".format(self.version))
        logging.info("HTBot-v{} Start".format(self.version))

    def start(self):
        self.turn = 1
        self.tactic = None
        # dict with Move.id key and Move object
        self.moves = {}

        while True:
            self.queue = []
            self.map = self.game.update_map()
            self.fleet = self.map.get_me().all_ships()
            self.enemies = [ship for ship in self.map._all_ships() if ship not in self.fleet]

            if self.turn == 1:
                self.corners = self.map.getCorners()
                self.id = self.map.get_me().id

            self.planets = [planet for planet in self.map.all_planets() if planet != None]
            self.empty = [planet for planet in self.planets if planet != None and not planet.is_owned() and planet.remaining_resources > 0]
            try:
                self.my_planets = [planet for planet in self.planets if planet != None and planet.owner.id == self.id]
            except :
                self.my_planets = []
            try:
                self.enemy_planets = [planet for planet in self.planets if planet != None and planet not in self.my_planets and planet not in self.empty]
            except :
                self.enemy_planets = []

            self.my_dock = 0
            for s in self.fleet:
                if s.docking_status != s.DockingStatus.UNDOCKED:
                    self.my_dock += 1

            self.enemy_dock = 0
            for e in self.enemies:
                if e.docking_status != e.DockingStatus.UNDOCKED:
                    self.enemy_dock += 1

            planet_queue = []

            for ship in self.fleet:
                try:
                    if ship.docking_status != ship.DockingStatus.UNDOCKED:
                            leaving = False
                            if hlt.constants.LIMITED_RESOURCES and ship.planet.remaining_resources == 0:
                                found = False
                                for k, m in self.moves.items():
                                    if m.move == m.MoveType.LEAVE and m.target.id == ship.planet.id:
                                        if m.needed > 0 and m.assign(ship):
                                            move = m
                                            self.moves[move.getId()] = move
                                            leaving = True
                                            found = True
                                        else:
                                            leaving = False
                                            found = True
                                        break

                                if not found:
                                    move = hlt.moves.Move.MoveType.LEAVE
                                    move = hlt.moves.Move(ship, move, ship.planet, len(ship.planet._docked_ships)-1, self.map)
                                    self.moves[move.getId()] = move

                            if leaving:
                                move.log()
                                self.queue.append(move.execute(ship))

                            continue

                    move = None
                    for k,v in self.moves.items():
                        if v.isPart(ship):
                            if v.move == hlt.moves.Move.MoveType.LEAVE:
                                move = None
                            else:
                                move = v
                            break

                    entities_by_distance = self.map.nearby_entities_by_distance(ship)
                    entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))

                    closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in self.empty]
                    closest_my_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in self.my_planets]
                    closest_enemy_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in self.enemy_planets]
                    closest_team_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in self.fleet]
                    closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in self.enemies]

                    #order planets for our needs
                    dockable = self.orderPlanets(ship, closest_my_planets+closest_empty_planets)

                    rushing = False
                    # if we just started or a ship is already avoiding rush
                    if self.turn <= 8 or (move != None and move.move == move.MoveType.AVOID_RUSH):
                        # check if enemy is (still) rushing or not
                        rushing = self.detectRush(ship)

                    if rushing : # check for rush
                        logging.info("Detected rush by enemy by ship:"+str(ship.id))
                        if (move is not None and move.move != move.MoveType.AVOID_RUSH) or move is None:
                            if move is not None:
                                del self.moves[move.getId()]
                            move = hlt.moves.Move.MoveType.AVOID_RUSH
                            friends = []
                            for s in self.fleet:
                                if custom.euclidean(s, closest_enemy_ships[0]) <= hlt.constants.RUSH_RANGE+5:
                                    friends.append(s)

                            move = hlt.moves.Move(ship, move, closest_enemy_ships[0], len(friends), self.map)
                            for f in friends:
                                move.assign(ship)

                            self.moves[move.getId()] = move

                    else:
                        # if we were avoiding rush but there's no need now
                        if move != None and move.move == move.MoveType.AVOID_RUSH:
                            move = None

                        if len(closest_enemy_ships) > 0 and custom.euclidean(ship, closest_enemy_ships[0]) <= hlt.constants.ATTACK_RANGE:
                            enemy_facing = 0
                            friendly = 1
                            for s in self.enemies:
                                if custom.euclidean(s, ship) <= hlt.constants.ATTACK_RANGE:
                                    enemy_facing += 1
                                    for f in self.fleet:
                                        if custom.euclidean(s, f) <= hlt.constants.ATTACK_RANGE and f.docking_status == ship.DockingStatus.UNDOCKED:
                                            friendly += 1

                            if enemy_facing > friendly+2:
                                move = hlt.moves.Move.MoveType.FLEE
                                move = hlt.moves.Move(ship, move, None, 1, self.map)
                                self.moves[move.getId()] = move

                            else:
                                move = hlt.moves.Move.MoveType.ATTACK
                                move = hlt.moves.Move(ship, move, closest_enemy_ships[0], 2, self.map)
                                self.moves[move.getId()] = move

                        elif len(dockable) and custom.euclidean(ship, dockable[0]) <= 10 and len(self.my_planets) <= len(self.enemy_planets):
                            found = False
                            targets = [t.target for k, t in self.moves.items()]
                            for k, m in self.moves.items():
                                if m.move == m.MoveType.EXPLORE and m.needed > 0 and m.target == dockable[0]:
                                    found = True
                                    if m.assign(ship):
                                        move = m
                                        self.moves[move.getId()] = move
                                    break

                            if not found:
                                move = hlt.moves.Move.MoveType.EXPLORE
                                move = hlt.moves.Move(ship, move, dockable[0], dockable[0].num_docking_spots, self.map)
                                self.moves[move.getId()] = move

                        elif (len(self.enemies) < len(self.fleet)-5 or len(self.enemies)-self.enemy_dock < len(self.fleet)-self.my_dock) and (move is None or move.move == move.MoveType.SNEAK):
                            move = hlt.moves.Move.MoveType.SNEAK
                            move = hlt.moves.Move(ship, move, closest_enemy_ships[0], 2, self.map, enemies=closest_enemy_ships, fleet=closest_team_ships)
                            self.moves[move.getId()] = move

                        elif len(dockable) > 0 and move is None:
                            found = False
                            targets = [t.target for k, t in self.moves.items()]
                            for k, m in self.moves.items():
                                if m.move == m.MoveType.EXPLORE and m.needed > 0 and m.target is not None and custom.euclidean(ship, m.target) <= 45:
                                    if m.assign(ship):
                                        move = m
                                        found = True
                                        self.moves[move.getId()] = move
                                        break

                            if not found:
                                target = None
                                for d in dockable:
                                    if d not in targets:
                                        target = d
                                        break

                                if target is None:
                                    move = hlt.moves.Move.MoveType.SNEAK
                                    move = hlt.moves.Move(ship, move, closest_enemy_ships[0], 2, self.map, enemies=closest_enemy_ships, fleet=closest_team_ships)
                                    self.moves[move.getId()] = move
                                else:
                                    move = hlt.moves.Move.MoveType.EXPLORE
                                    move = hlt.moves.Move(ship, move, target, target.num_docking_spots, self.map)
                                    self.moves[move.getId()] = move

                        if move is None:
                            move = hlt.moves.Move.MoveType.SNEAK
                            move = hlt.moves.Move(ship, move, closest_enemy_ships[0], 2, self.map, enemies=closest_enemy_ships, fleet=closest_team_ships)
                            self.moves[move.getId()] = move

                    move.log()
                    self.queue.append(move.execute(ship))

                except Exception as e:
                    logging.info("Ship level exception ship : "+str(ship.id)+", Exception : "+str(e))
                    move = hlt.moves.Move.MoveType.STALL
                    move = hlt.moves.Move(ship, move, None, 0, self.map)
                    self.moves[move.getId()] = move
                    move.log()
                    self.queue.append(move.execute(ship))

            self.game.send_command_queue(self.queue)
            logging.info("Done turn, n."+str(self.turn))
            self.turn += 1

    def detectRush(self, ship):
        if self.enemy_dock > len(self.enemies)-1:
            return False

        facing = 0
        for e in self.enemies:
            if custom.euclidean(ship, e) <= hlt.constants.RUSH_RANGE:
                facing += 1

        if facing >= len(self.enemies)-2:
            return True

        return False

    def orderPlanets(self, ship, entities):
        dockable = [p for p in entities if len(p._docked_ships) < p.num_docking_spots and p.remaining_resources > 0]
        return dockable

    def kamikaze(self, ship, planets):
        planets = sorted(planets, key=lambda x: len(x._docked_ship_ids))
        target = None
        for p in planets:
            if len(p._docked_ship_ids) < 1:
                continue
            elif p.remaining_resources == 0:
                continue
            elif len(p._docked_ship_ids) >= 2:
                target = p
                break

        if target != None:
            navigate_command = ship.navigate(
                            planets[0],
                            self.map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=True)

            if navigate_command :
                self.queue.append(navigate_command)

        else:
            self.attack(ship, None)

if __name__ == '__main__':
    r = Raffaello(1, debug=False)
    r.start()
