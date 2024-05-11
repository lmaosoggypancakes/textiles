from springs import *
from svg import *
from graphs import *
import math
import uuid
import time

RADIUS = 60
        
class PadConnection:
    def __init__(self, c: PhysicalConnection, path: list):
        self.connection = c
        self.path = path
    
    def __eq__(self, other) -> bool:
        return self.connection == other.connection and self.path == other.path

class Pad:
    def __init__(self,x,y,pins) -> None:
        self.x = x
        self.y = y
        self.pins = pins
        self.angle = 0
        self.stack = [None]*self.pins # the pin at index i of self.stack is pin#i
        for i in range(pins):
            angle = 2 * math.pi * i / pins
            self.stack[i] = PhysicalNode(self.x + RADIUS*math.cos(angle), self.y +RADIUS*math.sin(angle), uuid.uuid4())
        self.connections: List[PadConnection] = []
    
    def turn(self,r):
        # increases angle by r, and updates nodes accordingly
        self.angle = (self.angle + r)
        for (pin, node) in enumerate(self.stack):
            if node:
                node_angle = 2 * pin * math.pi/self.pins
                node.x = self.x+RADIUS*math.cos(node_angle+self.angle)
                node.y = self.y-RADIUS*math.sin(node_angle+self.angle)

    @staticmethod
    def connect(pad_one, pin_one: int, pad_two, pin_two: int):
        pc = PhysicalConnection(pad_one.stack[pin_one], pad_two.stack[pin_two], uuid.uuid1())
        # rotate pads so that their nodes face each other
       
        # c_angle = math.atan2((pad_one.y-pad_two.y),(pad_one.x-pad_two.x))
        # # if c_angle < 0: c_angle+=(2*math.pi)
        # angle_diff = pad_one.angle + c_angle
        # while (angle_diff < -0.5 or angle_diff > 0.5):
        #     pad_one.turn(-math.pi/12)
        #     angle_diff = pad_one.angle + c_angle

        # c_angle = math.pi - c_angle
        # # if c_angle < 0: c_angle+=(2*math.pi)
        # angle_diff = pad_two.angle + c_angle
        # while (angle_diff < -0.5 or angle_diff > 0.5):
        #     pad_two.turn(+math.pi/12)
        #     angle_diff = c_angle - pad_two.angle

        one = pad_one.stack[pin_one]
        two = pad_two.stack[pin_two]
        l = math.sqrt((two.x-one.x)**2 + (two.y-one.y)**2)
        angle = math.atan2((two.y-one.y), (two.x-one.x))
        new_one_x = one.x + (l/20)*math.cos(angle)
        new_one_y = one.y + (l/20)*math.sin(angle)

        new_two_x = two.x - (l/20)*math.cos(angle)
        new_two_y = two.y - (l/20)*math.sin(angle)

        path = create_r_zigzag((new_one_x, new_one_y), (new_two_x, new_two_y), 1.5, 40)
        path.insert(0, (M, one.x, one.y))
        path.insert(1, (L, new_one_x, new_one_y))

        path.append((L, two.x, two.y))
        c = PadConnection(pc, path)
        pad_one.connections.append(c)
        pad_two.connections.append(c)

def prepare_for_embroidery(pads):
    svg = SVG(2400, 1500)
    explored = []
    for pad in pads:
        r = 150+RADIUS
        p1 = (pad.x + r*math.cos(pad.angle), pad.y + r*math.sin(pad.angle))
        p2 = (pad.x + r*math.cos(pad.angle+math.pi), pad.y+r*math.sin(pad.angle+math.pi))
        svg.circle(pad.x, pad.y, RADIUS, "blue");
        for pin in pad.stack:
            if pin:
                svg.circle(pin.x, pin.y, 5, "green")
        for c in pad.connections:
            if c.connection not in explored:
                svg.path(c.path)
                explored.append(c.connection)
        # svg.circle(p1[0] + 20*math.cos(pad.angle+math.pi/2), p1[1] - 20*math.sin(pad.angle+math.pi/2), 3, "red")
        svg.path([
            (M, p1[0] + 50*math.cos(pad.angle+math.pi/2), p1[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p1[0] + 50*math.cos(pad.angle+math.pi/2), p1[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p1[0] + 50*math.cos(math.pi/2-pad.angle), p1[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p1[0] + 50*math.cos(pad.angle+math.pi/2), p1[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p1[0] + 50*math.cos(math.pi/2-pad.angle), p1[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p1[0] + 50*math.cos(pad.angle+math.pi/2), p1[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p1[0] + 50*math.cos(math.pi/2-pad.angle), p1[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p1[0] + 50*math.cos(pad.angle+math.pi/2), p1[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p1[0] + 50*math.cos(math.pi/2-pad.angle), p1[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p1[0] + 50*math.cos(pad.angle+math.pi/2), p1[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p1[0] + 50*math.cos(math.pi/2-pad.angle), p1[1] - 50*math.sin(math.pi/2-pad.angle))
        ])
        svg.path([
            (M, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(math.pi/2-pad.angle), p2[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(math.pi/2-pad.angle), p2[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(math.pi/2-pad.angle), p2[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(math.pi/2-pad.angle), p2[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(math.pi/2-pad.angle), p2[1] - 50*math.sin(math.pi/2-pad.angle)),
            (L, p2[0] + 50*math.cos(pad.angle+math.pi/2), p2[1] + 50*math.sin(pad.angle+math.pi/2)),
            (L, p2[0] + 50*math.cos(math.pi/2-pad.angle), p2[1] - 50*math.sin(math.pi/2-pad.angle))
        ])
    return svg
def render(pads: List[Pad], filename=None):
    """
    requires that the pads of any connection are in `pads`.
    """
    svg = SVG(2400, 1500)
    for pad in pads:
        svg.circle(pad.x, pad.y, RADIUS, "blue");
        for pin in pad.stack:
            if pin:
                print(pin.x,pin.y)
                svg.circle(pin.x, pin.y, 5, "green")
        for c in pad.connections:
            svg.path(c.path)
    if filename:
        svg.save(filename)
    return svg

        
if __name__ == "__main__":
    gemma = Pad(2100, 750, 4)

    ball_tilt = Pad(1600, 750, 12)

    thumb = Pad(800, 150, 8)
    index = Pad(150, 400, 12)
    middle = Pad(100,750, 4)
    ring = Pad(125,1050,8)
    pinky = Pad(450, 1400, 8)

    Pad.connect(gemma, 2, ball_tilt, 0)
    Pad.connect(ball_tilt, 9, thumb,1)
    Pad.connect(ball_tilt, 8, index, 1)
    Pad.connect(ball_tilt,7, middle, 0)
    Pad.connect(ball_tilt, 6, ring, 0)
    Pad.connect(ball_tilt, 5, pinky, 0)
    basic = render([gemma, ball_tilt, thumb, index, middle, ring, pinky])
    # prepared = prepare_for_embroidery([gemma, ball_tilt, thumb, index, middle, ring, pinky])
    basic.save("glove.svg")
    export_svg_to_vp3(basic, "glove.vp3")
    # prepared.save(".svg")
