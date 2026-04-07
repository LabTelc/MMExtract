from vispy.visuals.colorbar import ColorBarVisual, _CoreColorBarVisual
from vispy.visuals import TextVisual, CompoundVisual, _BorderVisual
from vispy.color import get_colormap
from vispy.scene.visuals import create_visual_node

import numpy as np


class TickedColorBarVisual(ColorBarVisual):
    def __init__(self, cmap, orientation, size,
                 pos=(0, 0),
                 label="",
                 label_color='black',
                 clim=(0.0, 1.0),
                 border_width=1.0,
                 border_color="black",
                 ticks_number=5,
                 ):

        _CoreColorBarVisual._check_orientation(orientation)
        self._cmap = get_colormap(cmap)
        self._clim = clim
        self._pos = pos
        self._size = size
        self._orientation = orientation
        self._ticks_number = ticks_number

        if not isinstance(label, TextVisual):
            label = TextVisual(label, color=label_color)
        self._label = label

        ticks = np.linspace(self._clim[0], self._clim[1], self._ticks_number)
        self._ticks = []
        for tick in ticks:
            self._ticks.append(TextVisual(str(tick), color=label_color, font_size=12))

        if orientation in ["top", "bottom"]:
            (width, height) = size
        elif orientation in ["left", "right"]:
            (height, width) = size
        else:
            raise ValueError("Invalid orientation")

        self._halfdim = (width * 0.5, height * 0.5)

        self._colorbar = _CoreColorBarVisual(pos, self._halfdim,
                                             cmap, orientation)

        self._border = _BorderVisual(pos, self._halfdim,
                                     border_width, border_color)

        CompoundVisual.__init__(self, [self._colorbar,
                                       self._border,
                                       *self._ticks,
                                       self._label,
                                       ])
        self._update()

    def _update(self):
        """Rebuilds the shaders, and repositions the objects that are used internally by the ColorBarVisual"""
        self._colorbar.halfdim = self._halfdim
        self._border.halfdim = self._halfdim
        minor = self.size[0] if self.size[0] < self.size[1] else self.size[1]
        font_size = int(2 / 19 * minor + 168 / 19)

        ticks = [a for a in np.linspace(self._clim[0], self._clim[1], self._ticks_number)]
        for i, tick in enumerate(ticks):
            self._ticks[i].text = f"{tick:.5g}"
            self._ticks[i].font_size = font_size

        self._update_positions()

        self._colorbar._update()
        self._border._update()

    def _update_positions(self):
        """Updates the positions of the colorbars and labels"""
        self._colorbar.pos = self._pos
        self._border.pos = self._pos

        if self._orientation == "right" or self._orientation == "left":
            self._label.rotation = -90

        label_anchors = TickedColorBar._get_label_anchors(
            center=self._pos,
            halfdim=self._halfdim,
            orientation=self._orientation,
            transforms=self.label.transforms
        )
        self._label.anchors = label_anchors

        ticks_anchors = TickedColorBar._get_ticks_anchors(
            center=self._pos,
            halfdim=self._halfdim,
            orientation=self._orientation,
            transforms=self.label.transforms
        )

        # All ticks share the same anchor
        for tick in self._ticks:
            tick.anchors = ticks_anchors

        (label_pos, ticks_pos_border) = TickedColorBar._calc_positions(
            center=self._pos,
            halfdim=self._halfdim,
            border_width=self.border_width,
            orientation=self._orientation,
            transforms=self.transforms
        )

        self._label.pos = label_pos

        p0 = ticks_pos_border[0]  # start (min)
        p1 = ticks_pos_border[1]  # end (max)

        num_ticks = len(self._ticks)

        # Linear interpolation for each tick
        for i, tick in enumerate(self._ticks):
            t = i / (num_ticks - 1) if num_ticks > 1 else 0
            tick.pos = p0 * (1 - t) + p1 * t

    @staticmethod
    def _calc_positions(center, halfdim, border_width,
                        orientation, transforms):
        """
        Calculate the text centeritions given the ColorBar
        parameters.

        Note
        ----
        This is static because in principle, this
        function does not need access to the state of the ColorBar
        at all. It's a computation function that computes coordinate
        transforms

        Parameters
        ----------
        center: tuple (x, y)
            Center of the ColorBar
        halfdim: tuple (halfw, halfh)
            Half of the dimensions measured from the center
        border_width: float
            Width of the border of the ColorBar
        orientation: "top" | "bottom" | "left" | "right"
            Position of the label with respect to the ColorBar
        transforms: TransformSystem
            the transforms of the ColorBar
        """
        (x, y) = center
        (halfw, halfh) = halfdim

        visual_to_doc = transforms.get_transform('visual', 'document')
        doc_to_visual = transforms.get_transform('document', 'visual')

        # doc_widths = visual_to_doc.map(np.array([halfw, halfh, 0, 0],
        #                                         dtype=np.float32))

        doc_x = visual_to_doc.map(np.array([halfw, 0, 0, 0], dtype=np.float32))
        doc_y = visual_to_doc.map(np.array([0, halfh, 0, 0], dtype=np.float32))

        if doc_x[0] < 0:
            doc_x *= -1

        if doc_y[1] < 0:
            doc_y *= -1

        # doc_halfw = np.abs(doc_widths[0])
        # doc_halfh = np.abs(doc_widths[1])

        if orientation == "top":
            doc_perp_vector = -doc_y
        elif orientation == "bottom":
            doc_perp_vector = doc_y
        elif orientation == "left":
            doc_perp_vector = -doc_x
        if orientation == "right":
            doc_perp_vector = doc_x

        perp_len = np.linalg.norm(doc_perp_vector)
        doc_perp_vector /= perp_len
        perp_len += border_width
        perp_len += 5  # pixels
        perp_len *= ColorBarVisual.text_padding_factor
        doc_perp_vector *= perp_len

        doc_center = visual_to_doc.map(np.array([x, y, 0, 0],
                                                dtype=np.float32))
        doc_label_pos = doc_center + doc_perp_vector
        visual_label_pos = doc_to_visual.map(doc_label_pos)[:3]

        if orientation == "top":
            doc_ticks_pos = [doc_label_pos - doc_x - doc_y / 2,
                             doc_label_pos + doc_x - doc_y / 2]
        elif orientation == "bottom":
            doc_ticks_pos = [doc_label_pos - doc_x + doc_y / 2,
                             doc_label_pos + doc_x + doc_y / 2]
        elif orientation == "left":
            doc_ticks_pos = [doc_label_pos + doc_y - doc_x / 2,
                             doc_label_pos - doc_y - doc_x / 2]
        elif orientation == "right":
            doc_ticks_pos = [doc_label_pos + doc_y + doc_x / 2,
                             doc_label_pos - doc_y + doc_x / 2]
        else:
            raise ValueError(f"Invalid orientation: {orientation}")

        visual_ticks_pos = []
        visual_ticks_pos.append(doc_to_visual.map(doc_ticks_pos[0])[:3])
        visual_ticks_pos.append(doc_to_visual.map(doc_ticks_pos[1])[:3])

        return visual_label_pos, visual_ticks_pos


TickedColorBar = create_visual_node(TickedColorBarVisual)
