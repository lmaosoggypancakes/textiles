from typing import *

class Footprint:
    def __init__(self, path: List[List[int|float]], x_range: int|float, y_range: int|float, pins: List[List[int|float]]):
        """
        Represents the visual footprint of a given schematic (resistor, chip, whatever)
        """
        if len(path) == 0:
            raise Exception("empty footprint")
        for (x,y) in path:
            if x < 0 or x > x_range or y < 0 or y > y_range:
                raise Exception("path point out of bounds: " + (x,y))

        for (x,y) in pins:
            if x < 0 or x > x_range or y < 0 or y > y_range:
                raise Exception("pin out of bounds: " + (x,y))

        self.path = path
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

    def __eq__(self, other: Module):
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
        for i in range(self.graph):
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
