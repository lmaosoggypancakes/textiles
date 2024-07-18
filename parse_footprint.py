import logging
from pyparsing import *

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
  number = ZeroOrMore(White()).suppress() + Combine(Optional(plusorminus) + decimal + Optional(Literal('.') + decimal)) + ZeroOrMore(White())

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
  at = _paren_clause('at', Group(number('x') + number('y') + Optional(number('z'))))
  uuid = _paren_clause('uuid', anystring('uuid'))
  size = _paren_clause('size', Group(number('width') + number('height')))
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
  start = _paren_clause('start', Group(number('x') + number('y')))
  end = _paren_clause('end', Group(number('x') + number('y')))
  width = _paren_clause('width', number('width'))
  type = _paren_clause('type', inum('type'))
  stroke = _paren_clause('stroke', width & type)
  drill = _paren_clause('drill', number('size'))
  remove_unused_layers = _paren_clause('remove_unused_layers', keyword('bool'))
  xyz = _paren_clause('xyz', Group(number('x') + number('y') + Optional(number('z'))))

  # Shapes
  fp_line = _paren_clause('fp_line', start & end & stroke & layer & uuid)
  fp_text = _paren_clause('fp_text', Group(keyword('author') + qstring('text') + (at & layer & uuid & effects)))
  shape = fp_line | fp_text
  shapes = ZeroOrMore(shape)('shapes')

  # Pad
  pad = _paren_clause('pad', Group(qstring('number') + keyword('type') + keyword('shape') + (at & size & drill & layers & remove_unused_layers & uuid)))
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
    shapes & 
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

print(parse_footprint("PinHeader_1x02_P2.54mm_Vertical.kicad_mod"))