from attrs import define

from clip_tools.utils import read_fmt
from clip_tools.constants import VectorFlag, VectorPointFlag
from clip_tools.data_classes import BBox, Color, Position
import io

@define
class VectorPoint():
    position: Position
    bbox: BBox

    point_flag: VectorPointFlag

    scale:  float
    scale2: float
    scale3: float

    width: float
    opacity: float

    bezier_points: [Position]

    def write(self, io_stream):
        pass

    @classmethod
    def read(cls, io_stream, vector_flag):
        pos = Position.read(io_stream)
        point_bbox = BBox.read(">i", io_stream)

        point_vector_flag = VectorPointFlag(read_fmt(">i", io_stream))

        point_scale = read_fmt(">f", io_stream)
        point_scale_2 = read_fmt(">f", io_stream)
        point_scale_3 = read_fmt(">f", io_stream)

        unk1 = read_fmt(">f", io_stream)
        unk2 = read_fmt(">f", io_stream) # Dispersion? seems to define a statistical looking curve

        point_width = read_fmt(">f", io_stream)
        point_opacity = read_fmt(">f", io_stream)

        # Some corner values for frames, angles? Doesn't seem to have effect
        unk1 = read_fmt(">f", io_stream)
        unk2 = read_fmt(">f", io_stream)
        unk3 = read_fmt(">f", io_stream)
        #print(unk1, unk2, unk3)

        # Unknown non zero parameter
        unk1 = read_fmt(">f", io_stream)
        unk2 = read_fmt(">f", io_stream)
        #print(unk1, unk2)

        # Only zeros
        unk = read_fmt(">i", io_stream)
        #print(unk)

        bezier_points = []

        if vector_flag & VectorFlag.CURVE_QUADRATIC_BEZIER:
            
            bezier_points.append(Position.read(io_stream))

        if vector_flag & VectorFlag.CURVE_CUBIC_BEZIER:

            bezier_points.append(Position.read(io_stream))
            bezier_points.append(Position.read(io_stream))

        return cls(
            pos,
            point_bbox,
            point_vector_flag,
            point_scale,
            point_scale_2,
            point_scale_3,
            point_width,
            point_opacity,
            bezier_points
        )

    @classmethod
    def new(cls, position, flag):
        return cls(
            position,
            BBox(position.x - 10, position.y - 10, position.x + 10, position.y + 10),
            flag
        )

@define
class Vector():

    point_count: int
    vector_flag: VectorFlag
    vector_bbox: BBox

    main_color: Color
    sub_color: Color

    opacity: float

    brush_id: int
    brush_radius: float

    fill_style_id: int

    points: [VectorPoint]

    def write(self, io_stream):
        pass

    @classmethod
    def read(cls, io_stream):

        # Header, holds section size info
        header_size = read_fmt(">i", io_stream) # Full Header section size
        sign2 = read_fmt(">i", io_stream) # Point section size without the point size (16 bytes)
        point_size = read_fmt(">i", io_stream) # Seems to be a single point section size
        sign4 = read_fmt(">i", io_stream) # Default point section size?

        # To identify new values
        assert sign2 == 72, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        assert sign4 == 88, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        num_points = read_fmt(">i", io_stream)

        vector_flag = VectorFlag(read_fmt(">i", io_stream))
        vector_bbox = BBox.read(">i", io_stream)

        main_color = Color.read(io_stream)
        sub_color = Color.read(io_stream)

        global_opacity = read_fmt(">d", io_stream)

        brush_id = read_fmt(">i", io_stream)
        brush_radius = 0
        frame_fill_id = 0

        if vector_flag & VectorFlag.NORMAL:
            brush_radius = read_fmt(">d", io_stream)
            last_value_unk = read_fmt(">i", io_stream)

        if vector_flag & VectorFlag.FRAME:

            frame_brush_id = read_fmt(">i", io_stream)
            frame_fill_id = read_fmt(">i", io_stream)

            brush_radius = read_fmt(">d", io_stream)
            last_value_unk = read_fmt(">i", io_stream)

            brush_id = frame_brush_id

        points = []

        for _ in range(num_points):
            points.append(VectorPoint.read(io_stream, vector_flag))

        return cls(
            num_points,
            vector_flag,
            vector_bbox,
            main_color,
            sub_color,
            global_opacity,
            brush_id,
            brush_radius,
            frame_fill_id,
            points
        )

    @classmethod
    def new(cls):
        pass


@define
class VectorList():

    vector_list: [Vector]

    @classmethod
    def read(cls, io_stream):

        vector_data = io.BytesIO(io_stream)

        data_end = vector_data.seek(0, 2)
        vector_data.seek(0, 0)

        while vector_data.tell() < data_end - 16:
            self.lines.append(Vector.read(vector_data))