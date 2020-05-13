from pyaxidraw import axidraw


class Axy:
    def __init__(self):
        self.ad = axidraw.AxiDraw()
        self.ad.plot_setup()
        self.ad.options.auto_rotate = False

    def __del__(self):
        self.shutdown()

    def set_option(self, option, value):
        setattr(self.ad.options, option, value)

    def walk_x(self, x: float):
        if x == 0:
            return
        self.ad.options.mode = "manual"
        self.ad.options.manual_cmd = "walk_x"
        self.ad.options.walk_dist = x
        self.ad.plot_run()

    def walk_y(self, y: float):
        if y == 0:
            return
        self.ad.options.mode = "manual"
        self.ad.options.manual_cmd = "walk_y"
        self.ad.options.walk_dist = y
        self.ad.plot_run()

    def plot_svg(self, svg: str):
        self.ad.plot_setup(svg)
        self.ad.options.mode = "plot"
        self.ad.plot_run()

    def shutdown(self):
        self.ad.options.mode = "manual"
        self.ad.options.manual_cmd = "disable_xy"
        self.ad.plot_run()

    def pen_up(self):
        self.ad.options.mode = "manual"
        self.ad.options.manual_cmd = "raise_pen"
        self.ad.plot_run()

    def pen_down(self):
        self.ad.options.mode = "manual"
        self.ad.options.manual_cmd = "lower_pen"
        self.ad.plot_run()
