import shutil
from svg import *

terminal_size = shutil.get_terminal_size()
terminal_x = terminal_size[0]
MAPS = {
    "111": 0,
    "110": 1,
    "101": 1,
    "100": 0,
    "011": 1,
    "010": 1,
    "001": 1,
    "000": 0,
}
def generate_rule110(generations=terminal_size[1],  calculate_rows=False):
    chars_per_row = generations+2 if calculate_rows else terminal_x
    grid = [[0]*(chars_per_row-1)+ [1]]
    for i in range(1, generations):
        new_gen = [0]
        previous_gen = grid[i-1] 
        for j in range(1,chars_per_row-1):
            first = previous_gen[j-1]
            second = previous_gen[j]
            third = previous_gen[j+1]

            key = f"{first}{second}{third}"
            new_gen.append(MAPS[key])

        new_gen.append(MAPS[f"{previous_gen[chars_per_row-2]}{previous_gen[chars_per_row-1]}{previous_gen[0]}"])
        grid.append(new_gen)
    return grid

def print_grid(generations):
    for g in generations:
        s = ""
        for num in g:
            if num == 1:
                s += "*"
            else:
                s += " "
        print(s)

def export_grid_to_svg(grid):
    x = len(grid[0]) * 20
    y = len(grid) * 50
    star_length = y / 450

    svg = SVG(x,y)
    cursor_x = 10
    cursor_y = 10
    instructions = [(M, cursor_x, cursor_y)]
    long_stretch = (0,0)
    on_a_long_stretch = False
    for row in grid:
        for col in row:
            if col == 0:
                on_a_long_stretch = True
                # instructions.append((M, cursor_x, cursor_y))
                long_stretch = (cursor_x, cursor_y)
            elif col == 1:
                if on_a_long_stretch:
                    instructions.append((M, long_stretch[0],long_stretch[1]))
                    on_a_long_stretch = False
                # do a little circle thing around this point
                instructions.extend([(M, cursor_x-star_length/2, cursor_y-star_length/2), (L, cursor_x - star_length/2, cursor_y+star_length/2), (L, cursor_x+star_length/2, cursor_y + star_length/2), (L, cursor_x+star_length/2, cursor_y-star_length/2), (L, cursor_x-star_length/2, cursor_y-star_length/2)])
            cursor_x += 5
        instructions.append((M, 10, cursor_y))
        cursor_x = 10
        cursor_y += 10
    svg.path(instructions)

    return svg
