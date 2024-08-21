from typing import *
from parse_footprint import extract_footprint, Shape
from svg import *
from helpers import * # mainly just using create_r_zigzag
from embroidery import export_svg_to_brother

"""
This module is to represent a physical circuit with its connections and coordinates accurately

Classes:
Footprint => Represents the paths and pin coordinates of a footprint
ConnectionNode => Has the reference id of a component or a module, the pin number of the component or 
                    module that we want to connect to, and the coordinates of the node
Trace => Represents a connection between two ConnectionNodes and the via points in between them
Component => Represents either an electric component (like a resistor or chip) or a pad on the lilypad
Module => Represents a lilypad or a via point on the fabric
Layer => Represents one fabric layer that has has many modules
Circuit => Represents the whole circuit, and keeps track of the via points on the fabric

Function:
create_basic_circuit => Creates a simple circuit from the netlist and footprints 
                        with one component on each module, and no via points
"""

class Footprint:
    def __init__(self, paths: List[List[Shape]], width, height, pins: List[Position]):
        """
        Represents the visual footprint of a given schematic (resistor, chip, whatever)
        """
        self.paths = paths
        self.pins = pins

        self.width = width
        self.height = height

    def serialize(self):
        return {
            "pins": list(map(lambda pin: pin.serialize(),self.pins)),
            "paths": list(map(lambda path: list(map(lambda shape: shape.serialize(), path)),self.paths)),
            "width": self.width,
            "height": self.height
        }
    
class ConnectionNode:
    def __init__(self, ref: str, pin: int | str, pos: Position = Position(0, 0)):
        self.ref = ref
        self.pin = pin
        self.pos = pos
    def serialize(self):
        return {
            "ref": self.ref,
            "pin": self.pin,
            "pos": self.pos.serialize()
        }

class Trace:
    def __init__(self, a: ConnectionNode, b: ConnectionNode, vias = []):
        self.ref = f"{a.ref}-{a.pin}-{b.ref}-{b.pin}"
        self.a = a
        self.b = b
        self.points: List[Position] = []
    def add_via(self, pos: Position, idx: int):
        self.points.insert(idx, pos)
    def serialize(self):
        return {
            "ref": self.ref,
            "a": self.a.serialize(),
            "b": self.b.serialize(),
            "points": list(map(lambda p: p.serialize(), self.points))
        }

class Component:
    def __init__(self, ref: str, name: str, pins: int, pin_coords: List[Position], pos: Position, width: float, height: float, is_pad = False):
        if ref == "":
            raise Exception("no ref")
        if name == "":
            raise Exception("no name")
        if pins <= 0:
            raise Exception("a component needs at least 1 pin")

        self.ref = ref
        self.name = name
        self.pins = pins
        self.pin_coords = pin_coords
        self.pos = pos
        self.width = width
        self.height = height
        self.is_pad = is_pad
        self.angle = 0

    def get_pin_coord(self, pin_num: int):
        return self.pin_coords[pin_num - 1]

    def __eq__(self, other):
        return self.ref == other.ref # REFS SHOULD BE UNIQUE

    def serialize(self):
        return {
            "ref": self.ref,
            "name": self.name,
            "pins": self.pins,
            "pin_coords": list(map(lambda p: p.serialize(), self.pin_coords)),
            "pos": self.pos.serialize(),
            "width": self.width,
            "height": self.height,
            "is_pad": self.is_pad,
            "angle": self.angle
        }

def get_pad_pos(pad_pos: int, r: float):
    radius = r
    if pad_pos == 0: 
      return Position(radius * math.cos(math.pi / 4), radius * math.sin(math.pi / 4))
    if pad_pos == 1: 
      return Position(
        radius * math.cos((math.pi * 5) / 12),
        radius * math.sin((math.pi * 5) / 12),
      )
    if pad_pos == 2: 
      return Position(
        radius * math.cos((math.pi * 7) / 12),
        radius * math.sin((math.pi * 7) / 12),
      )
    if pad_pos == 3: 
      return Position(
        radius * math.cos((math.pi * 3) / 4),
        radius * math.sin((math.pi * 3) / 4),
      )
    if pad_pos == 4: 
      return Position(
        radius * math.cos((math.pi * 5) / 4),
        radius * math.sin((math.pi * 5) / 4),
      )
    if pad_pos == 5: 
      return Position(
        radius * math.cos((math.pi * 17) / 12),
        radius * math.sin((math.pi * 17) / 12),
      )
    if pad_pos == 6: 
      return Position(
        radius * math.cos((math.pi * 19) / 12),
        radius * math.sin((math.pi * 19) / 12),
      )
    if pad_pos == 7: 
      return Position(
        radius * math.cos((math.pi * 7) / 4),
        radius * math.sin((math.pi * 7) / 4),
      )


class Module:
    def __init__(self, components: List[Component], pos: Position, radius: float = 300.0, is_via=False, via_layers = [], ref = ""):
        if len(components) == 0 and not is_via:
            raise Exception("A module must either have a component or be a via.")
        self.ref = f"MODULE-{'-'.join(list(map(lambda c: c.ref, components)))}"
        if is_via:
            self.ref = ref
        if len(via_layers) == 1 and is_via:
            raise Exception("Via must connect multiple layers.")
        self.components: dict[str, Component] = dict(list(map(lambda c: (c.ref, c), components)))
        self.connections: dict[str, Trace] = dict()
        self.pads: List[Component] = []
        self.pad_refs: List[str] = []

        self.radius = radius
        self.angle = 0
        pad_num = 0
        for c in self.components.values():
            pad_num += c.pins

        conns = []
        
        for c in self.components.values():
            for j in range(c.pins):
                pin_num = j + 1
                new_pad_pos = get_pad_pos(j, radius)
                # TODO: calculate connection node pos
                new_pad_ref = f"PAD-{c.ref}-{pin_num}"
                new_pad = Component(new_pad_ref, f"PAD-{len(self.pads) + 1}",
                                    1, [Position(0.0, 0.0)], new_pad_pos, 8.0, 8.0, True)
                self.pads.append(new_pad)
                self.pad_refs.append(new_pad_ref)
                """
                Memo the connections to make, because pad is not added to components yet
                """
                conns.append([c.ref, pin_num, new_pad_ref, 1])
        for p in self.pads:
            self.components[p.ref] = p
        for c in conns:
            self.connect(c[0], c[1], c[2], c[3])

        self.pos = pos

    def connect(self, a_ref: str, a_pin: int, b_ref: str, b_pin: int, vias=[]):
        """
        Connect components `a` and `b` by pin `i` of `a` to pin `j` of `b`, with given via points.
        `a` and `b` must not be via points
        """
        # TODO: Calculate the connnode position here
        a_component = self.components[a_ref]
        b_component = self.components[b_ref]
        a = ConnectionNode(a_ref, a_pin, a_component.get_pin_coord(a_pin) + a_component.pos)
        b = ConnectionNode(b_ref, b_pin, b_component.get_pin_coord(b_pin) + b_component.pos)
        trace = Trace(a, b, vias)
        self.connections[trace.ref] = trace

    def connections_for_components(self, ref: str):
        """
        Return Trace objects that have the ref component in one of the vertices
        """
        ret = list(filter(lambda c: c[1].a.ref == ref or c[1].b.ref == ref, self.connections.items()))
        return ret
    
    def get_pad_ref_of_component_pin(self, component_ref: str, pin: int):
        ref = f"PAD-{component_ref}-{pin}"
        if self.components.get(ref):
            return ref
        return None
    
    def get_pad_num_of_component_pin(self, component_ref: str, pin: int):
        ref = f"PAD-{component_ref}-{pin}"
        if self.components.get(ref):
            """
            Pad number starts from 1
            """
            return self.pad_refs.index(ref) + 1
        return None
    
    def serialize(self):
        return {
            "ref": self.ref,
            "components": dict(list(map(lambda ref: (ref, self.components[ref].serialize()), self.components))),
            "connections": dict(list(map(lambda ref: (ref, self.connections[ref].serialize()), self.connections))),
            "pads": list(map(lambda p: p.serialize(), self.pads)),
            "radius": self.radius,
            "pos": self.pos.serialize(),
            "angle": self.angle
        }

    def __eq__(self, other):
        return self.ref == other.ref

class Layer:
    """
    a 'circuit' is defined to be a graph of layers.
    a 'layer' is defined to be a graph of modules.
    a 'module' is defined to be a graph of electrical components with spacial constraints and exit pins (a lilypad)
    an 'electrical component' is defined to be a representation with a ref(id), footprint, and pin declaration
    """
    def __init__(self, ref: str, modules: List[Module]):
        if len(modules) == 0:
            raise Exception("A module must have a component.")
        self.ref = ref
        self.modules: dict[str, Module] = dict(list(map(lambda m: (m.ref, m), modules)))
        self.connections: dict[str, Trace] = dict()
        self.vias: List[Module] = []

        self.component_to_module: dict[str, str] = {}
        for module in modules:
            for c_ref in module.components.keys():
                self.component_to_module[c_ref] = module.ref


    def connect(self, a_ref: str, a_pin: int, b_ref: str, b_pin: int):
        """
        Connect modules `a` and `b` by pin `i` of `a` to pin `j` of `b`, with given via points.
        `a` and `b` must not be via points
        """

        # TODO calculate node position
        a_module = self.modules[a_ref]
        b_module = self.modules[b_ref]

        a_pin_coord = Position(0.0, 0.0)
        b_pin_coord = Position(0.0, 0.0)

        """
        Pad number starts at 1
        """
        if isinstance(a_pin, int):
            a_pin_coord = a_module.pads[a_pin - 1].get_pin_coord(1) + a_module.pads[a_pin - 1].pos + a_module.pos
        if isinstance(b_pin, int):
            b_pin_coord = b_module.pads[b_pin - 1].get_pin_coord(1) + b_module.pads[b_pin - 1].pos + b_module.pos
        if isinstance(a_pin, str):
            a_pin_coord = a_module.components[a_pin].get_pin_coord(1) + a_module.components[a_pin].pos + a_module.pos
        if isinstance(b_pin, str):
            b_pin_coord = b_module.components[b_pin].get_pin_coord(1) + b_module.components[b_pin].pos + b_module.pos

        a = ConnectionNode(a_ref, a_pin, a_pin_coord)
        b = ConnectionNode(b_ref, b_pin, b_pin_coord)

        trace = Trace(a, b)
        self.connections[trace.ref] = trace

    def connections_for_modules(self, ref: str):
        """
        Get all the connections that go to/from module a.
        Returns {i, *V, j, b}[] where i is pin i of module a, V is any via points, to pin j of module b
        i, j are pins, ...V and j are module indexes.
        min length of any set is 3. (i,j,V=[],b)
        """
        return list(filter(lambda c: c[1].a.ref == ref or c[1].b.ref == ref, self.connections.items()))
    
    def add_via(self, new_via: Module):
        """
        Only call from Circuit add_via method
        """
        self.modules[new_via.ref] = new_via
        self.vias.append(new_via)

    def get_module(self, ref: str):
        return self.modules.get(ref)
    
    def get_module_ref_of_component(self, component_ref: str):
        return self.component_to_module[component_ref]
    
    def get_module_of_component(self, component_ref: str):
        mod_ref = self.component_to_module[component_ref]
        if mod_ref:
            return self.modules[mod_ref]
        return None

    def __eq__(self, other):
        return self.ref == other.ref
    
    def serialize(self):
        return {
            "ref": self.ref,
            "modules": dict(list(map(lambda ref: (ref, self.modules[ref].serialize()), self.modules))),
            "connections": dict(list(map(lambda ref: (ref, self.connections[ref].serialize()), self.connections))),
            "vias": list(map(lambda v: v.serialize(), self.vias)),
        }
        
class Circuit:
    def __init__(self, layers: List[Layer], footprints: dict[str, Footprint]):
        self.layers = dict(list(map(lambda l: (l.ref, l), layers)))
        self.vias: List[Module] = []
        self.footprints: dict[str, Footprint] = footprints

    def add_via(self, pos: Position, layer_refs = []):
        new_ref = f"VIA-{'-'.join(layer_refs)}-{len(self.vias)}"
        new_via = Module([], pos, 0, True, layer_refs, new_ref)
        self.vias.append(new_via)
        for l_ref in layer_refs:
            layer = self.layers[l_ref]
            if layer:
                layer.add_via(new_via)

    def serialize(self):
        return {
            "layers": dict(list(map(lambda ref: (ref, self.layers[ref].serialize()), self.layers))),
            "vias": list(map(lambda v: v.serialize(), self.vias)),
            "footprints": dict(list(map(lambda ref: (ref, self.footprints[ref].serialize()), self.footprints)))
        }


"""
nets: list[{name: str, code: str, pins: list[{ref: str, pin: str}]}]
parts: list[{ref: str, value: str, name: str, footprint: str}]
"""

def create_simple_circuit(nets, parts):
    footprints: dict[str, Footprint] = {}
    modules: list[Module] = []
    circuit_radius = 150

    """
    Footprint for pad
    """
    shape_path: List[List[Position]] = []
    for i in range(1, 25):
        shape_path.append([
          Position((4.0) * math.cos((i % 24) * 2 * math.pi/24), 
           (4.0) * math.sin((i % 24) * 2 * math.pi/24)),
          Position((4.0) * math.cos(((i+1) % 24) * 2 * math.pi/24), 
           (4.0) * math.sin(((i+1) % 24) * 2 * math.pi/24)),
        ])
    footprints["pad"] = Footprint([[], [], [Shape(shape_path)]], 8.0, 8.0, [Position(0.0, 0.0)])

    for (i, part) in enumerate(parts):
        """
        Load footprints from ./kicad-footprints directory
        If there is an error here, check if the directory exists
        """
        path = getFootprintPath(part["footprint"], "kicad-footprints")
        (paths, x_range, y_range, pins) = extract_footprint(path)
        footprint = Footprint(paths, x_range, y_range, pins)
        footprints[part["ref"]] = footprint

        new_component = Component(part["ref"], part["name"], len(footprint.pins), 
                                  footprint.pins, Position(0.0, 0.0), footprint.width, footprint.height, False)
        angle = 2 * math.pi * i/len(parts)
        new_pos = Position(100+circuit_radius*(1 + math.cos(angle)), 100+circuit_radius*(1 + math.sin(angle)))
        modules.append(Module([new_component], new_pos, 30.0, False))
    
    layer = Layer("LAYER-1", modules)

    for net in nets:
        for i in range(1, len(net["pins"])):
            a_component_ref = net["pins"][i - 1]["ref"]
            b_component_ref = net["pins"][i]["ref"]
            a_module = layer.get_module_of_component(a_component_ref)
            b_module = layer.get_module_of_component(b_component_ref)

            layer.connect(a_module.ref, a_module.get_pad_ref_of_component_pin(a_component_ref, net["pins"][i - 1]["num"]), 
                          b_module.ref, b_module.get_pad_ref_of_component_pin(b_component_ref, net["pins"][i]["num"]))

    circuit = Circuit([layer], footprints)

    return circuit
