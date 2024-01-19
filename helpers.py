from svg import *
from graphs import *
X = 244
def create_n_zigzag(n, one="", two="", horizontal = True) -> SVG:
    if n <= 0: return 
    step_size=X // n
    if n >= 50: raise Exception("n too large")
    svg = SVG(X+10, X+10)
    if one != "":
        svg.text(5,5, one)
    instructions = [
        (M, 3, 10),
    ]
    cursor_x = 10
    for i in range(n+1):
        if i == 0: continue
        if i % 2 == 1:
            instructions.append((L, cursor_x+step_size, 20))
        else:
            instructions.append((L, cursor_x+step_size, 10))
        cursor_x += step_size
    # instructions.extend(instructions[::-1])
    svg.path(instructions)
    if two != "":
        svg.text(X, 30, two)
    svg.circle(3,10,2)
    if n % 2 == 0:
        svg.circle(cursor_x, 10, 2)
    else: 
        svg.circle(cursor_x, 20, 2)
    return svg

def total_energy(connections):
    s = 0
    for c in connections:
        s += c.spring_energy()
    return s

def create_n_zigzag_better(n, one,two, svg=None):
    """
    Given a diagonal from (x1,y1) <> (x2,y2), create an n-zigzag according to those diagonals.
    ref: https://www.desmos.com/calculator/b8tq1khfwd
    """
    (x1, y1) = one
    (x2, y2) = two

    dx = x2 - x1
    dy = y2 - y1

    step_x = dx/n
    step_y = dy/n
    
    points = []
    magnitude_of_zig = abs((dx + dy) / 32)
    for i in range(1,n):
        x = (x1) + (i * step_x) + (magnitude_of_zig * ((-1) ** (i+1)))
        y = (y1) + (i * step_y) + (magnitude_of_zig * ((-1) ** (i)))
        points.append((x,y))
    if not svg:
        m = max([x1,x2,y1,y2])
        svg = SVG(m+200,m+200)
    
    svg.circle(x1,y1,3)
    svg.circle(x2,y2,3)
    instructions = [(M, x1,y1)]
    for (x,y) in points:
        instructions.append((L, x,y))

    instructions.append((L, x2,y2))
    svg.path(instructions)
    return svg

def render_graph(nodes, connections):
    pass
