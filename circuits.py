from typing import *
from svg import *
class Footprint:
    def __init__(self, paths: List[List[List[int|float]]], x_range: int|float, y_range: int|float, pins: List[List[int|float]]):
        """
        Represents the visual footprint of a given schematic (resistor, chip, whatever)
        """
        # if len(paths) == 0:
            # raise Exception("empty footprint")
        for path in paths:
            for (x,y) in path:
                if x < 0 or x > x_range or y < 0 or y > y_range:
                    raise Exception("path point out of bounds: " + (x,y))

        for (x,y) in pins:
            if x < 0 or x > x_range or y < 0 or y > y_range:
                raise Exception("pin out of bounds: " + (x,y))

        self.paths = paths
        self.x_range = x_range
        self.y_range = y_range
        self.pins = pins

    def serialize(self):
        return {
            "x_range": self.x_range,
            "y_range": self.y_range,
            "pins": self.pins,
            "path": self.path
        }
              
class Module:
    def __init__(self, ref: str, footprint: Footprint, name: str, pins: int, via=False, layers=[0]):
        if ref == "":
            raise Exception("no ref")
        if name == "":
            raise Exception("no name")
        if pins <= 0 and not via:
            raise Exception("a module needs at least 1 pin if it's not a via")
        if len(footprint.pins) != pins:
            raise Exception("footprint pins and module pins don't match")
        if len(layers) == 0:
            raise Exception("a module must be on a layer")
        if len(layers) == 1 and via:
            raise Exception("the whole point of a via is that it exists in multiple layers")
        self.ref = ref
        self.footprint = footprint
        self.name = name
        self.pins = pins
        self.via = via
        self.layers = layers

    def __eq__(self, other):
        return self.ref == other.ref # REFS SHOULD BE UNIQUE

    def serialize(self):
        return {
            "ref": self.ref,
            "footprint": self.footprint.serialize(),
            "name": self.name,
            "pins": self.pins,
            "via": self.via,
            "layers": self.layers
        }

class Circuit:
    def __init__(self, modules: List[Module]):
        refs = set(map(lambda m: m.ref, modules))
        if len(refs) != len(modules):
            raise Exception("duplicate refs somewhere. fix.")
        self.modules = modules
        self.graph = [None]*len(self.modules)
        for i in range(len(self.graph)):
            self.graph[i] = [None]*len(self.modules)

    def connect(self, a: Module, b: Module, i: int, j: int, vias=[]):
        """
        Connect modules `a` and `b` by pin `i` of `a` to pin `j` of `b`, with given via points.
        `a` and `b` must not be via points
        """
        a_i = self.modules.index(a)
        b_i = self.modules.index(b)
        if a.via or b.via:
            raise Exception("can you fucking read")
        if len(a.layers) != 1 or len(b.layers) != 1:
            raise Exception("this should not happen")
        if a.layers[0] != b.layers[0] and len(vias) == 0:
            raise Exception("you can't connect modules in different layers without vias dumbass")

        self.graph[a_i][b_i] = [i, *vias, j]
        self.graph[b_i][a_i] = [j, *reversed(vias), i]

    def connections_for_modules(self, a: Module):
        """
        Get all the connections that go to/from module a.
        Returns {i, *V, j, b}[] where i is pin i of module a, V is any via points, to pin j of module b
        i, j are pins, ...V and j are module indexes.
        min length of any set is 3. (i,j,V=[],b)
        """
        idx = self.modules.index(a)
        ret = []
        for j in range(self.graph):
            if self.graph[idx][j]:
                ret.append([*self.graph[idx][j], j])
        return ret


def render_circuit(circuit: Circuit) -> SVG :
    svg = SVG(800, 800)
    circle_radius = 300
    for (i, m) in enumerate(circuit.modules):
        # place them along a circle
        # first, place a circle representing the center of each module:
        angle = 2 * math.pi * i / len(circuit.modules)
        x = 400+circle_radius*math.cos(angle)
        y = 400+circle_radius*math.sin(angle)
        svg.circle(x, y, 10, "red")
        svg.text(x,y-20, m.name)
        for p in m.footprint.paths:
            # render each path with a center of (x,y)
            # so, the path should take up the space defined by
            # (x-x_range/2, x+_range/2) and (y-y_range/2, y+y_range/2)
            inst = []
            for (i, (x_p, y_p)) in enumerate(p):
                if i == 0: # M and L are just SVG things for move to/line-to (can move everything to one path as well)
                    inst.append((M, x-m.footprint.x_range+x_p, y-m.footprint.y_range+y_p))
                else:
                    inst.append((L, x-m.footprint.x_range+x_p, y-m.footprint.y_range+y_p))
            svg.path(inst, "green")
        
        for (x_p, y_p) in m.footprint.pins:
            svg.circle(x-m.footprint.x_range+x_p, y-m.footprint.y_range+y_p, 5, "white");
    
    for (i, row) in enumerate(circuit.graph):
        for (j, c) in enumerate(row):
            if c is not None:
                # connection between [i,j] exists
                # TODO: handle pins
                angle1 = 2 * math.pi * i / len(circuit.modules)
                xa = 400+circle_radius*math.cos(angle1)
                ya = 400+circle_radius*math.sin(angle1)

                angle2 = 2 * math.pi * j / len(circuit.modules)
                xb = 400+circle_radius*math.cos(angle2)
                yb = 400+circle_radius*math.sin(angle2)
                svg.path([(M, xa, ya), (L, xb, yb)], stroke="purple")
    return svg

if __name__ == "__main__":
    res_fp = Footprint(
        [[]], 50, 50, [[25,45], [5, 45]]
    )
    res = Module("R1", res_fp, "Resistor", 2);

    pow_fp = Footprint(
        [[]], 50, 50, [[45, 25]]
    )
    power = Module("VCC", pow_fp, "+5V", 1)

    gnd_fp = Footprint(
        [[]], 50, 50, [[25, 45]]
    )
    ground = Module("GND", gnd_fp, "GND", 1)

    circuit = Circuit([res, power, ground])
    circuit.connect(res, ground, 0, 0);
    circuit.connect(res, power, 1, 0)
    
    render_circuit(circuit).save("circuit.svg")