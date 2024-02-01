from svg import *
from helpers import *
from graphs import *
from springs import *
from uuid import uuid1
import time
def u():
    return str(uuid1())

def test_svg():
    svg = SVG(100, 100)
    svg.circle(10,10,2)
    instructions = [
        (M, 10, 10),
        (L, 15, 15),
        (L, 10, 20),
        (L, 15, 25),
        (L, 10, 30)
    ]
    svg.path(instructions)
    svg.circle(10,30,2)
    svg.save("funny.svg")

def test_connections():
    n1 = Node("NMOS", "Transistor", u())
    n2 = Node("PMOS", "Transistor", u())

    c1 = Connection(n1, n2, 1, 1)
    c2 = Connection(n2, n1, 1, 1)

    print(f"Connection equality based on node order: ")
    print("GOOD" if c1 == c2 else "FAIL")

    c3 = Connection(n1, n2, 2, 1)
    c4 = Connection(n2, n1, 1, 2)

    print(f"Connection equality based on pin order: ")
    print("GOOD" if c3 == c4 else "FAIL")

    c5 = Connection(n1, n2, 2, 2)
    c6 = Connection(n1, n2, 2, 1)

    print(f"Connection with same terminals but different pins:")
    print("GOOD" if c5 != c6 else "FAIL")

def test_vectors():
    particle = PhysicalNode(0,0)
    f1 = Vector(5,0)
    f2 = Vector(0,3)
    vectors = [f1, f2]
    # for i in range(50):
    # print(particle.next_state(vectors))

def test_physical_connections():
    p1 = PhysicalNode(0,0)
    p2 = PhysicalNode(0,3)
    c = PhysicalConnection(p1,p2)
    print(f"Connection Length: {c.get_length()}")
    print(f"Spring energy: {c.spring_energy()}J")
    for i in range(500):
        time.sleep(0.05)
        print(f"Iteration {i}: ------------")
        print(f"Spring Force: {c.spring_force()}")
        print(f"Spring Energy: {c.spring_energy()}")
        print(f"Positions: {p1.x, p1.y} {p2.x, p2.y}")
        force_mag = c.spring_force()
        # create a force vector parallel to the spring; this will be applied
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        m = math.sqrt(dx**2 + dy**2)
        force1 = Vector(dx * force_mag / m, dy * force_mag / m)
        force2 = Vector(-dx * force_mag / m, -dy * force_mag / m)
        p1.next_state([force1])
        p2.next_state([force2])

def test_better_points():
    x1,y1 = 100,100
    x2,y2 = 10,100
    SVG.create_n_zigzag((x1,y1), (x2,y2), 10).save("ziggs.svg")
def main():
    # test_svg()
    # create_n_zigzag(16, "", "").save("paths/funny.svg")
    # test_connections()
    # test_vectors()
    # test_physical_connections()
    test_better_points()

if __name__ == "__main__":
    main()
