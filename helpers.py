import os
from svg import *
from springs import PhysicalConnection
from typing import Tuple
import math

SIZE = 500
RADIUS = 50

class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    def serialize(self):
        return {
            "x": self.x,
            "y": self.y
        }


def create_n_zigzag(one, two, n, zig_size=1):
    """
    Given a diagonal from (x1,y1) <> (x2,y2), create an n-zigzag according to those diagonals.
    ref: https://www.desmos.com/calculator/b8tq1khfwd
    """
    (x1, y1) = one
    (x2, y2) = two
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx+dy*dy)
    stretch = int(length/500 * n) + 1
    step_x = dx/stretch
    step_y = dy/stretch
    angle = math.atan2(dy, dx)
    points = [(x1,y1)]
    for i in range(stretch):
        if i % 3 == 0:
            # no zig or zag :3
            x = (x1) + (i * step_x) 
            y = (y1) + (i * step_y)
        elif i % 3 == 1:
            # zag
            x = (x1) + (i * step_x) - zig_size*(step_y/2)*math.cos(angle) * sign(dy)
            y = (y1) + (i * step_y) + zig_size*(step_x/2)*math.sin(angle)*sign(dx)
        else:
            # zig
            x = (x1) + (i * step_x) + zig_size*(step_y/2)*math.cos(angle) * sign(dy)
            y = (y1) + (i * step_y) - zig_size*(step_x/2)*math.sin(angle)*sign(dx)
        points.append((x,y))
    points.append((x2,y2))
    return points

def create_r_zigzag(one, two, r, n,svg=None):
    """
    creates a zigzag from one to two, given ratio r and n.
    returns [I, x, y][] where I \in {M, L}
    """
    n = int(n)
    if not svg:
        svg = SVG(500, 500)
    (x1, y1) = one
    (x2, y2) = two
    dx = (x2-x1)/n
    dy = (y2-y1)/n
    dl = math.sqrt(dx**2 + dy**2)

    if r == 0: 
        triangle_angle = 0
    else: 
        triangle_angle = math.acos(1/r)
    offset_angle = math.atan2(dy,dx)
    svg.circle(x1,y1,2,"white")
    svg.circle(x2,y2,2,"white")
    inst = [(M, x1, y1)]
    points = [(x1, y1)]
    for i in range(0, n):
        if i % 4 == 0: 
            x = (x1 + i * dx) + r*math.cos(offset_angle-triangle_angle)*dl
            y = (y1 + i * dy) + r*math.sin(offset_angle-triangle_angle)*dl
        elif i % 4 == 1:
            # i % 3 == 2
            # x = x1+(i+1)*dl*math.cos(offset_angle)
            # y = y1+(i+1)*dl*math.sin(offset_angle)
            continue
        elif i % 4 == 2:
            x = (x1 + i * dx) + r*math.cos(offset_angle+triangle_angle)*dl
            y = (y1 + i * dy) + r*math.sin(offset_angle+triangle_angle)*dl
        else: 
            # x = x1+(i+1)*dl*math.cos(offset_angle)
            # y = y1+(i+1)*dl*math.sin(offset_angle)
            continue
        points.append((x,y))
        inst.append((L, x, y))
    points.append((x2, y2))
    inst.append((L, x2,y2))
    svg.path(inst)
    return inst

def total_energy(connections):
    s = 0
    for c in connections:
        s += c.spring_energy()
    return s



def render_graph(nodes, points):
    # -> how do we normalize coordinates to respect proportions without having an absurd size?
    svg = SVG(500, 500)
    for node in nodes:
        svg.circle(node.x,node.y,40
        ,fill='none')
        svg.text(node.x-14,node.y+8, node.ref)

    for path in points:
        inst = []
        inst.append((M, path[0][0], path[0][1]))
        for point in path:
            inst.append((L, point[0], point[1]))
        svg.path(inst)

    return svg

def find_duplicate_connections(connections: List[PhysicalConnection]) -> Tuple[List[List[PhysicalConnection]], List[PhysicalConnection]]:
    result = []
    for c in connections:
        flag = False
        for dupes in result:
            if c in dupes:
                dupes.append(c)
                flag = True
        if not flag:
            result.append([c])
    return result

def generate_star(x,y,r):
    angles = [0, 216,72,288,144]  # Angles in degrees
    
    star_points = []
    
    for angle in angles:
        theta = math.radians(angle)
        xi = int(x + r * math.cos(theta))
        yi = int(y + r * math.sin(theta))
        star_points.append((xi, yi))
    
    return star_points

def best_path(one, two, obstacles):
    (x1,y1) = one
    (x2,y2) = two

def segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    def on_segment(px, py, qx, qy, rx, ry):
        if (min(px, qx) <= rx <= max(px, qx)) and (min(py, qy) <= ry <= max(py, qy)):
            return True
        return False
    
    def orientation(px, py, qx, qy, rx, ry):
        val = (qy - py) * (rx - qx) - (qx - px) * (ry - qy)
        if val == 0:
            return 0  # collinear
        elif val > 0:
            return 1  # clockwise
        else:
            return 2  # counterclockwise

    o1 = orientation(x1, y1, x2, y2, x3, y3)
    o2 = orientation(x1, y1, x2, y2, x4, y4)
    o3 = orientation(x3, y3, x4, y4, x1, y1)
    o4 = orientation(x3, y3, x4, y4, x2, y2)

    if o1 != o2 and o3 != o4:
        return True

    if (o1 == 0 and on_segment(x1, y1, x2, y2, x3, y3)) or \
       (o2 == 0 and on_segment(x1, y1, x2, y2, x4, y4)) or \
       (o3 == 0 and on_segment(x3, y3, x4, y4, x1, y1)) or \
       (o4 == 0 and on_segment(x3, y3, x4, y4, x2, y2)):
        return True

    return False

def getNewConnections(nets, nodes):
    connections = []
    for conn in nets:
        for i in range(1, len(conn["pins"])):
            p1 = list(filter(lambda x: x.ref == conn["pins"][i - 1]["ref"],nodes))[0]
            p2 = list(filter(lambda x: x.ref == conn["pins"][i]["ref"],nodes))[0]
            c = PhysicalConnection(p1,p2,conn["pins"][i - 1]["num"], conn["pins"][i]["num"], conn["code"])
            connections.append(c)
    return connections

def getFootprintPath(id, folder):
    ids = id.split(":")
    if len(ids) == 2:
        ids[0] = ids[0] + ".pretty"
        ids[1] = ids[1] + ".kicad_mod"
    return os.path.join(".", folder, *ids)
        
