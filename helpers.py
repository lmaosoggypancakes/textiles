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
        svg.circle(cursor_x, 10, 2, "none")
    else: 
        svg.circle(cursor_x, 20, 2, "none")
    return svg

def total_energy(connections):
    s = 0
    for c in connections:
        s += c.spring_energy()
    return s



def render_graph(nodes, connections, stretchification, zig):
    max_x = max(map(lambda x: x.x, nodes))
    max_y = max(map(lambda y: y.y, nodes))
    min_x = min(map(lambda x: x.x, nodes))
    min_y = min(map(lambda y: y.y, nodes))
    max_length = max(map(lambda c: c.get_length(), connections))
    
    # -> how do we normalize coordinates to respect proportions without having an absurd size?
    svg = SVG(max_x-min_x + 100, max_y-min_y + 50)
    for node in nodes:
        node.x = max_x-node.x+20
        node.y = max_y - node.y + 20
        svg.circle(node.x,node.y,4,fill='none')
    for connection in connections:
        svg.create_n_zigzag((connection.one.x, connection.one.y), (connection.two.x, connection.two.y), stretchification,zig_size=zig, svg=svg)
    
    return svg
