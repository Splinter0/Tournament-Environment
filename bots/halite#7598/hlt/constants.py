#: Max number of units of distance a ship can travel in a turn
MAX_SPEED = 7
#: Radius of a ship
SHIP_RADIUS = 0.5
#: Starting health of ship, also its max
MAX_SHIP_HEALTH = 255
#: Starting health of ship, also its max
BASE_SHIP_HEALTH = 255
#: Weapon cooldown period
WEAPON_COOLDOWN = 2
#: Weapon damage radius
WEAPON_RADIUS = 4.0
#: Weapon damage
WEAPON_DAMAGE = 80
#: Radius in which explosions affect other entities
EXPLOSION_RADIUS = 25.0
#: Distance from the edge of the planet at which ships can try to dock
DOCK_RADIUS = 4.5
#: Number of turns it takes to dock a ship
DOCK_TURNS = 6
#: Number of production units per turn contributed by each docked ship
BASE_PRODUCTIVITY = 6
#: Distance from the planets edge at which new ships are created
SPAWN_RADIUS = 3.0

# CUSTOM #

#: If planet resources are limited or not
LIMITED_RESOURCES = True
#: Range to detect rush
RUSH_RANGE = 40
#: Range to attack
ATTACK_RANGE = 20
#: Range of collisions
COLLISON_RANGE = 10
#: Angular step for nav
ANGULAR_STEP = 1
#: Max corrections
MAX_CORRECTIONS = 360/ANGULAR_STEP
