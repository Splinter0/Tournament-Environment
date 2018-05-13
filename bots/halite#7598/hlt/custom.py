import logging
import math
from . import constants
from . import entity

class Velocity(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def calculate(self, angle, thrust):
        self.x = math.cos(angle) * thrust
        self.y = math.sin(angle) * thrust

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def angle(self):
        return math.atan2(self.y, self.x)

def euclidean(one, two):
    distance = math.sqrt((one.x - two.x)**2 + (one.y - two.y)**2)
    return distance

def collisionTime(ship1, ship2, radius):
    dx = ship1.x - ship2.x
    dy = ship1.y - ship2.y
    dvx = ship1.velocity.x - ship2.velocity.x
    dvy = ship1.velocity.y - ship2.velocity.y

    a = (dvx**2)+(dvy**2)
    b = 2 * (dx * dvx + dy * dvy)
    c = (dx**2) + (dy**2) - (radius**2)

    disc = (b**2) - 4*a*c

    if a == 0.0:
        if b == 0.0:
            if c <= 0.0:
                # Already colliding
                return True, 0.0

            return False, 0.0

        t = -c / b
        if t >= 0.0:
            return True, t

        return False, 0.0

    elif disc == 0.0:
        t = -b / (2*a)
        return True, t

    elif disc > 0:
        t1 = -b + math.sqrt(disc)
        t2 = -b - math.sqrt(disc)

        if t1 >= 0.0 and t2 >= 0.0:
            return True, min(t1, t2) / (2*a)
        elif t1 <= 0.0 and t2 <= 0.0:
            return True, max(t1, t2) / (2*a)
        else:
            return True, 0.0

    else :
        return False, 0.0


def mightAttack(ship1, ship2):
    return euclidean(ship1, ship2) <= ship1.velocity.magnitude() + ship2.velocity.magnitude() + ship1.radius + ship1.radius + constants.WEAPON_RADIUS

def mightCollide(ship1, ship2):
    distance = euclidean(ship1, ship2)
    vr = ship1.velocity.magnitude() + ship2.velocity.magnitude() + ship1.radius + ship1.radius

    if distance >= vr:
        return False

    return True

def closest(main, ent1, ent2):
    if euclidean(main, ent1) <= euclidean(main, ent2):
        return ent1

    return ent2

def furthest(main, ent1, ent2):
    if euclidean(main, ent1) >= euclidean(main, ent2):
        return ent1

    return ent2
