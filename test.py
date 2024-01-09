from svg import *
from helpers import *
def test_svg():
    svg = SVG(100, 100)
    svg.circle(10,10,2)
    instructions = [
        (M, 10, 10),
        (L, 15, 15),
        (L, 10, 20),
        (L, 15, 25),
        (L, 10, 30)
    ]
    svg.path(instructions)
    svg.circle(10,30,2)
    svg.save("funny.svg")


def main():
    # test_svg()
    create_n_zigzag(16, "", "").save("paths/funny.svg")


if __name__ == "__main__":
    main()
