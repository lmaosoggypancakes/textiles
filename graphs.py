import math
from svg import *
from springs import *
from embroidery import *
import copy
from helpers import create_r_zigzag

PROPULSION_FIELD_RADIUS = 20
TIME = 50 # optimization iterations
class Frontier:
    def __init__(self, start) -> None:
        self.frontier = [start]
    def pop(self):
        return self.frontier.pop()
    def push(self, node):
        if not isinstance(node, Node): raise Exception("wtf")
        self.frontier.append(node)
    def empty(self):
        return len(self.frontier) == 0;

class Node:
    def __init__(self, node, parent) -> None:
        self.node = node
        self.parent = parent

class Obstacle:
    def __init__(self, x, y, fixed=False) -> None:
        self.x = x
        self.y = y
        self.fixed = fixed
    
def neighbors_for_node(node, obs, explored):
    (x,y) = node
    potential_neighbors = [
        (x-1,y-1), (x-1,y),(x-1,y+1),
        (x,y-1), (x,y+1),
        (x+1,y-1), (x+1,y), (x+1,y+1)
    ]
    neighbors = []
    for (xp, yp) in potential_neighbors:
        flag = False
        for o in obs:
            x0 = o.x
            y0 = o.y
            if point_in_circle(xp,yp, x0,y0, PROPULSION_FIELD_RADIUS):
                flag = True
        if (not flag) and ((xp,yp) not in explored): neighbors.append((xp,yp)) # YIPPEEEEE
    return neighbors

def heuristic(point, goal):
    # manhattan distance
    (xi, yi) = point
    (xf, yf) = goal
    dx = abs(xf - xi)
    dy = abs(yf - yi)
    # return math.sqrt(dx**2 + dy**2)
    return dy + dx

def best_node(points, goal):
    return min(points, key=lambda node: heuristic(node, goal))

def gbfs(one, two, obstacles):
    (x1,y1) = one
    (x2,y2) = two
    for o in obstacles:
        x = o.x
        y = o.y
        if point_in_circle(x1,y1,x,y,PROPULSION_FIELD_RADIUS) or point_in_circle(x2,y2,x,y,PROPULSION_FIELD_RADIUS):
            raise Exception("impossible")
    # greedy best-first search
    frontier = Frontier(Node(one, None))
    explored = set()
    while not frontier.empty():
        node = frontier.pop()
        explored.add(node.node)
                    
        if node.node == two:
            return backtrack(node)
        # add e new nodes onto the frontier
        children = neighbors_for_node(node.node, obstacles, explored)
        children_sorted = list(sorted(children, key=lambda x: heuristic(x, two), reverse=True))
        for child in children_sorted:
                frontier.push(Node(child, node))

def render(one,two,path,obstacles, filename="output.svg"):
    """
    requires that the max coordinate of anything is (400,400)
    """
    svg = SVG(400,400)
    svg.circle(one[0], one[1], 10, "blue")
    svg.circle(two[0], two[1], 10, "blue")
    for o in obstacles:
        if o.fixed:
            svg.circle(o.x, o.y, PROPULSION_FIELD_RADIUS, "red")
        else: 
            svg.circle(o.x, o.y, PROPULSION_FIELD_RADIUS, "green")
    
    if isinstance(path[0], Node):
        inst = [(M, path[0].node[0], path[0].node[1])]
        for node in path:
            inst.append((L, node.node[0], node.node[1]))
    else: 
        inst = [(M, path[0][0], path[0][1])]
        for node in path:
            inst.append((L, node[0], node[1]))
    svg.path(inst)
    svg.save(filename)

def backtrack(node):
    path = [node]
    while node.parent is not None:
        node = node.parent
        path.append(node)
    return list(reversed(path))

def discretize(path):
    """
    given a path as a list of points, return 
    """
    new_path = []
    (xi, yi) = path[0].node
    (xf, yf) = path[-1].node
    dist = int(math.sqrt((xf-xi)**2 + (yf-yi)**2))

    new_step = int(len(path) / math.sqrt(dist))
    i = 0
    while i < len(path):
        new_path.append(path[i])
        i += new_step
    new_path.append(path[-1])
    return new_path

def zigzagify(path, r, n):
    new_path = []
    for i in range(1,len(path)):
        one = path[i-1].node
        two = path[i].node
        new_path.extend(create_r_zigzag(one, two, r, n))
    return new_path
    
def point_in_circle(x, y, h, k, r):
    # Calculate the distance between (x, y) and (h, k)
    d = math.sqrt((x - h)**2 + (y - k)**2)
    # Compare d to r
    return d <= r

def passes_through(one, two, obstacles):
    (x1, y1) = one
    (x2, y2) = two
    dx = (x2-x1)/100
    dy = (y2-y1)/100
    for i, (h,k) in enumerate(obstacles):
        x = x1 + i*dx
        y = y1 + i*dy
        if point_in_circle(x,y,h,k,10):
            return False
    return True

def optimize(path: List[Node], obstacles,time=TIME):
    """
    given a path of sequences, optimize it by trying to reduce sharp turns/attempt to make it smooth
    """ 
    new_obstacles = copy.deepcopy(obstacles)
    physical_nodes: List[PhysicalNode] = []
    physical_connections: List[PhysicalConnection] = []
    # initialize nodes and connections
    for (i, node) in enumerate(path):
        (x,y) = node.node
        physical_nodes.append(PhysicalNode(x,y,i))

    # if n nodes, n-1 connections
    for i in range(1, len(physical_nodes)):
        one = physical_nodes[i-1]
        two = physical_nodes[i]
        dist = int(math.sqrt((two.x - one.x)**2 + (two.y - one.y)**2))
        physical_connections.append(PhysicalConnection(one,two, i, dist-10))
    
    best_energy = path_energy(physical_connections)
    best_nodes = physical_nodes
    best_connections = physical_connections
    for _ in range(time):
        # after i seconds
        for (i, node) in enumerate(physical_nodes):
            if i == 0:
                continue
            if i == len(physical_nodes)-1:
                continue
            local_connections: List[PhysicalConnection] = [physical_connections[i-1], physical_connections[i]]
            local_forces = list(map(lambda c: c.spring_force_vector(node), local_connections))
            (x_new, y_new) = node.next_state_peek(local_forces)
            flag = False
            for obj in new_obstacles:
                x = obj.x
                y = obj.y
                if point_in_circle(x_new, y_new,x,y,PROPULSION_FIELD_RADIUS):
                    flag = True
                if point_in_circle(x_new, y_new, x,y, PROPULSION_FIELD_RADIUS) and not obj.fixed:
                    # get it tf out
                    dx = obj.x-node.x # if positive, obj is to the right; push it that wa
                    dy = obj.y - node.y # if postiive, obj is below
                    obj.x += 5 if dx > 0 else -5
                    obj.y += 5 if dy > 0 else -5
            if not flag:
                node.x = x_new
                node.y = y_new
        energy = path_energy(physical_connections)
        # print(energy)
        if energy < best_energy:
            best_energy = energy
            best_nodes = []
            for node in physical_nodes:
                best_nodes.append(PhysicalNode(node.x, node.y, node.ref))
    new_path = []
    for node in best_nodes:
        new_path.append((node.x, node.y))
    print(best_energy)
    return (new_path, new_obstacles)
def path_energy(connections: List[PhysicalConnection]):
    e = 0
    for c in connections:
        e += c.spring_energy()
    return e
if __name__ == "__main__":
    # test out some cases
    one = (10, 10)
    two = (200, 200)
    ob = [Obstacle(70, 200), Obstacle(80,60), Obstacle(125, 120)]
    path = gbfs(one, two, ob)
    discretized = discretize(path)
    (optimized_decent, decent_obstacles) = optimize(discretized, ob, 50)
    (optimized_bad, bad_obstacles) = optimize(discretized, ob, 2000)
    # zigzagified = zigzagify(discretized, 1.3, 2)
    # if not is_safe_path(zigzagified):
        # print("WARNING: path is NOT safe to embroider: some jumps are too small")
    render(one, two, path, ob, "paths/search/base.svg")
    render(one, two, discretized, ob, "paths/search/discrete.svg")
    render(one, two, optimized_decent, decent_obstacles, "paths/search/optimized_decent.svg")
    render(one, two, optimized_bad, bad_obstacles,"paths/search/optimized_bad.svg")