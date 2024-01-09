from svg import *
X = 244
def create_n_zigzag(n, one, two, horizontal = True) -> SVG:
    if n <= 0: return 
    step_size=X // n
    print(f"{n=}")
    if n >= 50: raise Exception("n too large")
    svg = SVG(X+10, X+10)
    svg.text(5,5, one)
    instructions = [
        (M, 3, 10),
    ]
    cursor_x = 10
    for i in range(n+1):
        print(cursor_x)
        if i == 0: continue
        if i % 2 == 1:
            instructions.append((L, cursor_x+step_size, 20))
        else:
            instructions.append((L, cursor_x+step_size, 10))
        cursor_x += step_size
    svg.path(instructions)
    svg.text(X, 30, two)
    svg.circle(3,10,2)
    if n % 2 == 0:
        svg.circle(cursor_x, 10, 2)
    else: 
        svg.circle(cursor_x, 20, 2)
    return svg