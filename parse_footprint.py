import logging
from circuits import Footprint
from pyparsing import *
import math
from typing import List

def _parse_footprint(text):
  def _paren_clause(keyword, subclause):
    """
    Create a parser for a parenthesized list with an initial keyword.
    """
    lp = Literal('(').suppress()
    rp = Literal(')').suppress()
    kw = CaselessKeyword(keyword).suppress()
    clause = lp + kw + subclause + rp
    return clause
  
  #++++++++++++++++++++++++++++ Parser Definition +++++++++++++++++++++++++++

  # Basic elements.
  string = ZeroOrMore(White()).suppress() + CharsNotIn('()') + ZeroOrMore(White()).suppress()
  qstring = dblQuotedString() ^ sglQuotedString()
  qstring.addParseAction(removeQuotes)
  anystring = Optional(qstring ^ string) # Don't know why Optional() is necessary to make the parser work.
  word = anystring
  inum = anystring

  plusorminus = Literal('+') | Literal('-')
  decimal = Word(nums)
  number = ZeroOrMore(White()).suppress() + Combine(Optional(plusorminus) + decimal + Optional(Literal('.') + decimal)) + ZeroOrMore(White()).suppress()

  keyword = ZeroOrMore(White()).suppress() + Word(alphas + '-' + '_') + ZeroOrMore(White()).suppress()

  # Header
  version = _paren_clause('version', word('version'))
  generator = _paren_clause('generator', qstring('generator'))
  generator_version = _paren_clause('generator_version', qstring('generator_version'))
  layer = _paren_clause('layer', qstring('layer'))
  layers = _paren_clause('layers', OneOrMore(qstring('layer'))('layers'))
  descr = _paren_clause('descr', qstring('descr'))
  tags = _paren_clause('tags', OneOrMore(qstring('tag'))('tags'))

  # Property
  at = Group(_paren_clause('at', number('x') + number('y') + number('z')))('at')
  uuid = _paren_clause('uuid', anystring('uuid'))
  size = Group(_paren_clause('size', number('width') + number('height')))('size')
  thickness = _paren_clause('thickness', number('thickness'))
  unlocked = _paren_clause('unlocked', word('bool'))
  hide = _paren_clause('hide', word('bool'))
  font = _paren_clause('font', Optional(size) & Optional(thickness))
  effects = _paren_clause('effects', font)
  property = Group(_paren_clause('property', qstring("type") + qstring("text") + (at & Optional(unlocked) & layer & Optional(hide) & uuid & effects)))
  properties = ZeroOrMore(property)('properties')

  # Attribute
  attr = _paren_clause('attr', word('attr'))

  # Shape Descriptor
  at_2d = Group(_paren_clause('at', number('x') + number('y')))('at')
  start = Group(_paren_clause('start', number('x') + number('y')))('start')
  end = Group(_paren_clause('end', number('x') + number('y')))('end')
  width = _paren_clause('width', number('width'))
  type = _paren_clause('type', anystring('type'))
  stroke = Group(_paren_clause('stroke', width & type))('stroke')
  drill = _paren_clause('drill', number('drill'))
  remove_unused_layers = _paren_clause('remove_unused_layers', keyword('bool'))
  xyz = Group(_paren_clause('xyz', number('x') + number('y') + number('z')))
  center = Group(_paren_clause('center', number('x') + number('y')))('center_pos')
  fill = _paren_clause('fill', anystring('fill'))

  # Shapes
  fp_line = Group(_paren_clause('fp_line', start & end & stroke & layer & uuid))
  fp_text = Group(_paren_clause('fp_text', keyword('author') + qstring('text') + (at & layer & uuid & effects)))
  fp_circle = Group(_paren_clause('fp_circle', center('center_pos') & end & stroke & fill & layer & uuid))
  lines = ZeroOrMore(fp_line)('lines')
  texts = ZeroOrMore(fp_text)('texts')
  circles = ZeroOrMore(fp_circle)('circles')

  # Pad
  pad = Group(_paren_clause('pad', qstring('number') + keyword('type') + keyword('shape') + (at_2d & size & drill & layers & remove_unused_layers & uuid)))
  pads = ZeroOrMore(pad)('pads')

  # Model
  offset = _paren_clause('offset', xyz)
  scale = _paren_clause('scale', xyz)
  rotate = _paren_clause('rotate', xyz)
  model = _paren_clause('model', qstring('source') & offset & scale & rotate)

  end_of_file = ZeroOrMore(White()) + stringEnd
  parser = _paren_clause('footprint', qstring('name') + version + (
    Optional(generator) & 
    Optional(generator_version) & 
    Optional(layer) & 
    Optional(descr) & 
    Optional(tags) &
    properties &
    Optional(attr) &
    lines & 
    texts &
    circles &
    pads &
    Optional(model))) + end_of_file.suppress()
  return parser.parse_string(text)

def parse_footprint(src, tool='kicad'):
  """
  Return a pyparsing object storing the contents of a netlist.

  Args:
      src: Either a text string, or a filename, or a file object that stores
          the netlist.

  Returns:
      A pyparsing object that stores the netlist contents.

  Exception:
      PyparsingException.
  """

  try:
    text = src.read()
  except Exception:
    try:
      text = open(src,'r',encoding='latin_1').read()
    except Exception:
       text = src

  if not isinstance(text, str):
    raise Exception("What is this shit you're handing me? [{}]\n".format(src))

  try:
    return _parse_footprint(text)
  except KeyError:
    # OK, that didn't work so well...
    logging.error('Unsupported ECAD tool library: {}'.format(tool))
    raise Exception
  

class Shape:
    def __init__(self, paths: List[List[List[int|float]]]):
        self.paths = paths

    def serialize(self):
        return {
            "paths": self.paths,
        }
    
def extract_footprint(src):
  footprint = parse_footprint(src)
  pads_data = list(map(lambda pad: {"number": pad.number, "type": pad.type[0], "shape": pad.shape[0], 
                               "at": {"x": pad.at.x[0], "y": pad.at.y[0]}, "size": {"width": pad.size.width[0], "height": pad.size.height[0]}, 
                               "drill": pad.drill[0], "layers": list(pad.layers),
                               "removed_unused_layers": pad.removed_unused_layers, "uuid": pad.uuid}, footprint.pads))
  pins_data = list(map(lambda pad: (float(pad["at"]["x"]), float(pad["at"]["y"])), pads_data))
  lines_data = list(map(lambda line: {"start": {"x": line.start.x[0], "y": line.start.y[0]}, 
                                      "end": {"x": line.end.x[0], "y": line.end.y[0]}, 
                                      "stroke": {"width": line.stroke.width[0], "type": line.stroke.type}, 
                                      "layer": line.layer, "uuid": line.uuid}, footprint.lines))
  circles_data = list(map(lambda circle: {"center": {"x": circle.center_pos.x[0], "y": circle.center_pos.y[0]},
                                      "end": {"x": circle.end.x[0], "y": circle.end.y[0]}, 
                                      "stroke": {"width": circle.stroke.width[0], "type": circle.stroke.type}, 
                                      "layer": circle.layer, "uuid": circle.uuid}, footprint.circles))
  paths = list(map(lambda path: {"start": (float(path["start"]["x"]), float(path["start"]["y"])), 
                                 "end": (float(path["end"]["x"]), float(path["end"]["y"])),
                                 "layer": path["layer"]}, lines_data))
  
  for circle in circles_data:
    radius = math.sqrt(pow(float(circle["end"]["x"]) - float(circle["center"]["x"]), 2) + 
                       pow(float(circle["end"]["y"]) - float(circle["center"]["y"]), 2))
    for i in range(1, 25):
      paths.append({"start": (float(radius * math.cos((i % 24) * 2 * math.pi/24)), 
                              float(radius * math.sin((i % 24) * 2 * math.pi/24))),
                    "end": (float(radius * math.cos(((i - 1) % 24) * 2 * math.pi/24)), 
                            float(radius * math.sin(((i - 1) % 24) * 2 * math.pi/24))),
                    "layer": circle["layer"]})

  front_courtyard_paths = list(filter(lambda line: line["layer"] == "F.CrtYd", paths))
  front_silks_paths = list(filter(lambda line: line["layer"] == "F.SilkS", paths))

  fcrtyd_vertices = []
  for path in front_courtyard_paths:
    fcrtyd_vertices.append(path["start"])
    fcrtyd_vertices.append(path["end"])

  x_max = max(fcrtyd_vertices, key=lambda vertex: vertex[0])[0]
  x_min = min(fcrtyd_vertices, key=lambda vertex: vertex[0])[0]
  y_max = max(fcrtyd_vertices, key=lambda vertex: vertex[1])[1]
  y_min = min(fcrtyd_vertices, key=lambda vertex: vertex[1])[1]

  shape_fcrtyd = []
  shape_silks = []

  x_middle = (x_min + x_max) / 2
  y_middle = (y_min + y_max) / 2

  if (x_min < 0 or y_min < 0):
    for path in front_courtyard_paths:
      shape_fcrtyd.append([
        [5.0 * (path["start"][0] - x_middle), 5.0 * (path["start"][1] - y_middle)], 
        [5.0 * (path["end"][0] - x_middle), 5.0 * (path["end"][1] - y_middle)]])
    for path in front_silks_paths:
      shape_silks.append([
        [5.0 * (path["start"][0] - x_middle), 5.0 * (path["start"][1] - y_middle)], 
        [5.0 * (path["end"][0] - x_middle), 5.0 * (path["end"][1] - y_middle)]])
      
  output_fcrtyd = [Shape(shape_fcrtyd)]
  output_silks = [Shape(shape_silks)]
      
  output_cu: List[Shape] = []

  for pad in pads_data:
    shape_path = []
    if pad["shape"] == "rect":
      pad_pos = pad["at"]
      shape_path.append([
        [5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), 5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
        [5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), -5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
      ])
      shape_path.append([
        [5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), -5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
        [-5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), -5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
      ])
      shape_path.append([
        [-5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), -5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
        [-5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), 5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
      ])
      shape_path.append([
        [-5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), 5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
        [5.0 * (float(pad["size"]["width"])/2) + 5.0 * (float(pad_pos["x"]) - x_middle), 5.0 * (float(pad["size"]["height"])/2) + 5.0 * (float(pad_pos["y"]) - y_middle)],
      ])
    if pad["shape"] == "oval" or pad["shape"] == "circle":
      for i in range(1, 25):
        pad_pos = pad["at"]
        shape_path.append([
          [5.0 * ((float(pad["size"]["width"])/2) * math.cos((i % 24) * 2 * math.pi/24) + float(pad_pos["x"]) - x_middle), 
           5.0 * ((float(pad["size"]["height"])/2) * math.sin((i % 24) * 2 * math.pi/24) + float(pad_pos["y"]) - y_middle)],
          [5.0 * ((float(pad["size"]["width"])/2) * math.cos((i % 24) * 2 * math.pi/24) + float(pad_pos["x"]) - x_middle), 
           5.0 * ((float(pad["size"]["height"])/2) * math.sin((i % 24) * 2 * math.pi/24) + float(pad_pos["y"]) - y_middle)],
        ])
    output_cu.append(Shape(shape_path))
      
  pins = list(map(lambda p: (5.0 * (p[0] - x_middle), 5.0 * (p[1] - y_middle)), pins_data))

  return ([output_fcrtyd, output_silks, output_cu], 5.0 * (x_max - x_min), 5.0 * (y_max - y_min), pins)

extract_footprint(".\kicad-footprints\Connector_PinHeader_2.54mm.pretty\PinHeader_2x02_P2.54mm_Vertical.kicad_mod")