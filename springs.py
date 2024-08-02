from __future__ import annotations
import math
from typing import Union, List

SPRING_EQUILIBRIUM = 25 # 50 m spring
SPRING_CONSTANT = 5  # 5 N/m

NODE_MASS = 0.5 # 0.5 kg per node
DT = 0.01 # 100 ticks per simulation second

RADIUS = 20 # "propulsion zone"
class Vector:
    """
    Represents a vector starting at (0,0) with a given x,y value.
    """
    def __init__(self, x,y) -> None:
        self.x = x
        self.y = y
        self.angle = math.atan2(y, x)
        self.mag = math.sqrt(x*x + y*y)
    def update(self,x,y):
        self.x = x
        self.y = y
        self.angle = math.atan2(y, x)
        self.mag = math.sqrt(x*x + y*y)
    
    def serialize(self): 
        return {"x": self.x, "y": self.y, "angle": self.angle, "mag": self.mag}
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector(self.x * other, self.y * other)
        
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Vector(self.x / other, self.y / other)

    def __str__(self):
        return f"({round(self.x, 2)}, {round(self.y, 2)})"
    

class PhysicalNode:
    def __init__(self, x,y, ref, angle=0):
        # stationary (accel and velocity both 0) object at (x,y) 
        self.ref = ref
        self.acc = Vector(0,0)
        self.vel = Vector(0,0)
        self.x = x
        self.y = y
        self.angle = angle
    
    @staticmethod
    def from_dict(node):
        return PhysicalNode(int(node["x"]),int(node["y"]), node["ref"])
    
    def next_state_peek(self, forces, constraint=None):
        f = resultant_force(forces)
        self.acc = f/NODE_MASS
        dv = self.acc * DT # change in velocity
        self.vel.update(self.vel.x + dv.x, self.vel.y + dv.y)
        ds = self.vel * DT # change in position
        return (self.x+ds.x, self.y+ds.y)

    

    def next_state(self, forces, constraint=None):
        f = resultant_force(forces)
        self.acc = f/NODE_MASS
        dv = self.acc * DT # change in velocity
        self.vel.update(self.vel.x + dv.x, self.vel.y + dv.y)
        ds = self.vel * DT # change in position
        if not constraint:
            self.x += ds.x
            self.y += ds.y
            return (self.x, self.y)
        w = ds.x
        h = ds.y

        new_x = self.x + w
        new_y = self.y + h

        shape = constraint["shape"]
        
        if len(shape) == 0 or point_inside_polygon(new_x,new_y, shape):
            self.x = new_x
            self.y = new_y
            return 
        
        closest_point = None
        min_distance = float('inf')
        for i in range(len(shape)):
            p1 = shape[i]
            p2 = shape[(i + 1) % len(shape)]
            # Calculate distance from new position to line segment (p1, p2)
            distance = distance_to_line_segment(new_x, new_y, p1[0], p1[1], p2[0], p2[1])
            if distance < min_distance:
                min_distance = distance
                closest_point = closest_point_on_line_segment(new_x, new_y, p1[0], p1[1], p2[0], p2[1])    
        self.x = closest_point[0]
        self.y = closest_point[1]

        return (self.x, self.y)

    def get_connections(self):
        found = []
        for c in PhysicalConnection.all_connections:
            if (c.one == self or c.two == self):
                found.append(c)
        return found

    def __eq__(self, other) -> bool:
        return (
            self.ref == other.ref
        )
    def __str__(self) -> str:
        return f"{self.ref}: {self.x, self.y}"

    def serialize(self):
        return {
            "ref": self.ref,
            "acc": self.acc.serialize(),
            "vel": self.vel.serialize(),
            "x": self.x,
            "y": self.y
        }

class PhysicalConnection:
    all_connections: List[PhysicalConnection] = []
    def __init__(self, one: PhysicalNode, two: PhysicalNode, pin_one, pin_two, ref, spring=SPRING_EQUILIBRIUM) -> None:
        self.spring = spring
        self.one = one
        self.pin_one = pin_one
        self.pin_two = pin_two
        self.two = two
        self.ref = ref
        ione = 0  
        itwo = 0
        for c in self.all_connections:
            if c.one == self.one or c.one == self.two:
                ione += 1
            if c.two == self.two or c.two == self.one:
                itwo += 1
        
        self.all_connections.append(self)
            

    
    def get_length(self):
        dx = self.one.x - self.two.x
        dy = self.one.y - self.two.y

        return math.sqrt(dx**2 + dy**2)

    def spring_energy(self):
        """
        Given the current length of a spring, calculate the elastic potential energy of that spring
        """
        length = self.get_length()
        return 0.5 * SPRING_CONSTANT * (length - SPRING_EQUILIBRIUM)**2

    def spring_force(self):
        """
        Given the current length of a spring, calculate the force the spring applies on it's connected endpoints.
        if spring_force() > 0, the spring is being compressed.
        if spring_force() < 0, the spring is being stretched.
        """
        length = self.get_length()
        return -(length - self.spring) * SPRING_CONSTANT

    def spring_force_vector(self, node):
        """
        Given a node (endpoint) of the connection, calculate the force vector of the spring force
        """
        if node != self.one and node != self.two:
            raise Exception("Node provided is not an endpoint of this connection")
        
        spring = self.spring_force()
        x_cm,y_cm = self.center_of_mass()
        
        dx = node.x - x_cm
        dy = node.y - y_cm

        m = math.sqrt(dx**2 + dy**2)

        return Vector(dx/m*spring,dy/m*spring)

    def center_of_mass(self):
        x = (self.one.x + self.two.x) / 2
        y = (self.two.y + self.two.y) / 2
        return x,y

    def serialize(self) -> Dict[str, Union[str, Dict]]: # type: ignore
        return {
            "one": self.one.serialize(),
            "pin_one": self.pin_one,
            "pin_two": self.pin_two,
            "two": self.two.serialize(),
            "ref": self.ref
        }
    def __str__(self): 
        return f"{self.one.ref} <> {self.two.ref}"

    def __repr__(self) -> str:
        return str(self)
    
    def __eq__(self, other) -> bool:
        return (self.one == other.one and self.two == other.two) or (self.one == other.two and self.two == other.one)
    
    @staticmethod
    def get_connections(node, connections):
        found = []
        for c in connections:
            if c.one == node or c.two == node:
                found.append(c)
        return found


def resultant_force(vectors):
    """
    Given a list of vectors acting on the same point (assuming (0,0)), returns the resultant force vector on that object.
    """
    x = 0
    y = 0
    for vector in vectors:
        x += vector.x
        y += vector.y
    return Vector(x,y)



def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def distance_to_line_segment(x, y, x1, y1, x2, y2):
    A = x - x1
    B = y - y1
    C = x2 - x1
    D = y2 - y1

    dot = A * C + B * D
    len_sq = C * C + D * D
    param = -1
    if len_sq != 0:  
        param = dot / len_sq

    if param < 0:
        xx = x1
        yy = y1
    elif param > 1:
        xx = x2
        yy = y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D

    dx = x - xx
    dy = y - yy
    return (dx * dx + dy * dy) ** 0.5

def closest_point_on_line_segment(x, y, x1, y1, x2, y2):
    A = x - x1
    B = y - y1
    C = x2 - x1
    D = y2 - y1

    dot = A * C + B * D
    len_sq = C * C + D * D
    param = -1
    if len_sq != 0:  
        param = dot / len_sq

    if param < 0:
        xx = x1
        yy = y1
    elif param > 1:
        xx = x2
        yy = y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D

    return xx, yy

def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside
