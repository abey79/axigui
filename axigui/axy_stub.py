# noinspection PyMethodMayBeStatic
class Axy:
    def __init__(self):
        print("STUB: __init__()")

    def __del__(self):
        print("STUB: __del__()")

    def set_option(self, option, value):
        print(f"STUB: set_option({option}, {value})")

    def walk_x(self, x: float):
        print(f"STUB: walk_x({x})")

    def walk_y(self, y: float):
        print(f"STUB: walk_y({y})")

    def plot_svg(self, svg: str):
        print(f"STUB: plot_svg()")

    def shutdown(self):
        print(f"STUB: shutdown()")

    def pen_up(self):
        print(f"STUB: pen_up()")

    def pen_down(self):
        print(f"STUB: pen_down()")
