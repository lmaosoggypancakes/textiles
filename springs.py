import math
from typing import Union

SPRING_EQUILIBRIUM = 50 # 50 m spring
SPRING_CONSTANT = 5  # 5 N/m

NODE_MASS = 0.5 # 0.5 kg per node
DT = 0.1 # 10 ticks per simulation second
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
    def __init__(self, x,y, ref):
        # stationary (accel and velocity both 0) object at (x,y) 
        self.ref = ref
        self.acc = Vector(0,0)
        self.vel = Vector(0,0)
        self.x = x
        self.y = y
    
    def next_state(self, forces):
        f = resultant_force(forces)
        self.acc = f/NODE_MASS
        dv = self.acc * DT # change in velocity
        self.vel.update(self.vel.x + dv.x, self.vel.y + dv.y)
        ds = self.vel * DT # change in position
        self.x += ds.x
        self.y += ds.y
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
    def __init__(self, one: PhysicalNode, two: PhysicalNode, ref) -> None:
        self.one = one
        self.two = two
        self.ref = ref
    
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
        return -(length - SPRING_EQUILIBRIUM) * SPRING_CONSTANT

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

    def serialize(self) -> dict[str, Union[str, dict]]: # type: ignore
        return {
            "one": self.one.serialize(),
            "two": self.two.serialize(),
            "ref": self.ref
        }
    def __str__(self): 
        return f"{self.one.ref} <> {self.two.ref}"

    def __eq__(self, other) -> bool:
        return self.ref == other.ref
    
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

