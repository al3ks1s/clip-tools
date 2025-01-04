# See RulerRange Column and surrounding

from attrs import define
from clip_tools.clip.ClipData import RulerParallel, RulerCurveParallel, RulerMultiCurve, RulerEmit, RulerCurveEmit, RulerConcentricCircle, RulerGuide, RulerVanishPoint, RulerPerspective, RulerSymmetry
from clip_tools.clip.ClipStudioFile import ClipStudioFile
import logging
from clip_tools.data_classes import Position, VectorPoint
import importlib
import io
from clip_tools.utils import read_fmt, read_csp_unicode_str
from clip_tools.parsers import parse_point_data

logger = logging.getLogger(__name__)

@define
class Rulers():

    layer: None
    manager: None
    rulers: []

    # TODO Emulate list?

    def write_to_db(self):
        pass

    @classmethod
    def init_rulers(cls, layer):

        rulers = []
        manager = None
        
        if layer._data.RulerVectorIndex is not None and layer._data.RulerVectorIndex > 0:
            pass#logger.warning("Vector ruler not implemented")

        if layer._data.SpecialRulerManager is not None and layer._data.SpecialRulerManager > 0:
            
            manager = layer.clip_file.sql_database.get_table("SpecialRulerManager")[layer._data.SpecialRulerManager]
            
            columns = ["FirstParallel",
                        "FirstCurveParallel", 
                        "FirstMultiCurve", 
                        "FirstEmit", 
                        "FirstCurveEmit", 
                        "FirstConcentricCircle", 
                        "FirstGuide",
                        "FirstPerspective", 
                        "FirstSymmetry"]

            for column in columns:
                param = getattr(manager, column)
                
                if param is not None and param > 0:
                    
                    _module = importlib.import_module("clip_tools.api.Ruler")
                    class_name = column.lstrip("First")
                    _class = getattr(_module, class_name)

                    table_name = "Ruler" + class_name

                    rulers_by_layer = layer.clip_file.sql_database.get_referenced_items(table_name, "LayerId", layer._data.MainId)

                    for ruler_data in rulers_by_layer.values():
                        ruler = _class.init(layer, ruler_data)
                        rulers.append(ruler)

        return cls(layer, manager, rulers)

class BaseRuler():
    pass

# Do not instanciate this class
class SpecialRuler(BaseRuler):

    layer: None
    ruler_data: None

    def write_to_db(self):
        pass # Need to update the SpecialRulerManager table

    @classmethod
    def init(cls, layer, ruler_data):
        return cls(layer, ruler_data)

    @classmethod
    def new(cls, layer):
        pass

@define
class Parallel(SpecialRuler):
    layer: None
    ruler_data: RulerParallel

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def rotate(self):
        return self.ruler_data.Rotate

    @rotate.setter
    def rotate(self, new_rotate):
        self.ruler_data.Rotate = new_rotate # Modulo 360

    @property
    def center(self):
        return Position(self.ruler_data.CenterX, self.ruler_data.CenterY)

    @center.setter
    def center(self, new_pos):
        self.ruler_data.CenterX = new_pos.x
        self.ruler_data.CenterY = new_pos.y

@define
class CurveParallel(SpecialRuler):
    layer: None
    ruler_data: RulerCurveParallel

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def curve_kind(self):
        return self.ruler_data.CurveKind

    @curve_kind.setter
    def curve_kind(self, new_kind):
        self.ruler_data.CurveKind = new_kind

    @property
    def point_data(self):
        return parse_point_data(self.ruler_data.PointData)

    @point_data.setter
    def point_data(self, new_points): # TODO Serialize these points
        self.ruler_data.PointData = new_points

@define
class MultiCurve(SpecialRuler):
    layer: None
    ruler_data: RulerMultiCurve

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def curve_kind(self):
        return self.ruler_data.CurveKind

    @curve_kind.setter
    def curve_kind(self, new_kind):
        self.ruler_data.CurveKind = new_kind

    @property
    def angle(self):
        return self.ruler_data.OffsetAngle

    @angle.setter
    def angle(self, new_angle):
        self.ruler_data.OffsetAngle = new_angle    

    @property
    def center(self):
        return Position(self.ruler_data.CenterX, self.ruler_data.CenterY)

    @center.setter
    def center(self, new_pos):
        self.ruler_data.CenterX = new_pos.x
        self.ruler_data.CenterY = new_pos.y

    @property
    def point_data(self): 
        return parse_point_data(self.ruler_data.PointData)

    @point_data.setter
    def point_data(self, new_points): # TODO Serialize these points
        self.ruler_data.PointData = new_points

@define
class Emit(SpecialRuler):
    layer: None
    ruler_data: RulerEmit

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def center(self):
        return Position(self.ruler_data.CenterX, self.ruler_data.CenterY)

    @center.setter
    def center(self, new_pos):
        self.ruler_data.CenterX = new_pos.x
        self.ruler_data.CenterY = new_pos.y

@define
class CurveEmit(SpecialRuler):
    layer: None
    ruler_data: RulerCurveEmit

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def point_data(self):
        return parse_point_data(self.ruler_data.PointData)

    @point_data.setter
    def point_data(self, new_points): # TODO Serialize these points
        self.ruler_data.PointData = new_points

@define
class ConcentricCircle(SpecialRuler):
    layer: None
    ruler_data: RulerConcentricCircle

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def rotate(self):
        return self.ruler_data.Rotate

    @rotate.setter
    def rotate(self, new_rotate):
        self.ruler_data.Rotate = new_rotate

    @property
    def radius(self):
        return Position(self.ruler_data.RadiusX, self.ruler_data.RadiusY)

    @radius.setter
    def radius(self, new_radius):
        self.ruler_data.RadiusX = new_radius.x
        self.ruler_data.RadiusY = new_radius.y

    @property
    def center(self):
        return Position(self.ruler_data.CenterX, self.ruler_data.CenterY)

    @center.setter
    def center(self, new_pos):
        self.ruler_data.CenterX = new_pos.x
        self.ruler_data.CenterY = new_pos.y

@define
class Guide(SpecialRuler):
    layer: None
    ruler_data: RulerGuide

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def horizontal(self):
        return bool(self.ruler_data.IsHorz)

    @horizontal.setter
    def horizontal(self, is_horizontal):
        self.ruler_data.IsHorz = bool(is_horizontal) # Modulo 360

    @property
    def center(self):
        return Position(self.ruler_data.CenterX, self.ruler_data.CenterY)

    @center.setter
    def center(self, new_pos):
        self.ruler_data.CenterX = new_pos.x
        self.ruler_data.CenterY = new_pos.y


@define
class Perspective(SpecialRuler):
    layer: None
    ruler_data: RulerPerspective
    vanish_points: []

    @classmethod
    def init(cls, layer, ruler_data):

        vanish_points = []

        all_vanish_points = layer.clip_file.sql_database.get_table("RulerVanishPoint")
        vanish_points.append(VanishPoint(layer, all_vanish_points[ruler_data.FirstVanishIndex]))

        current_point = vanish_points[0]

        while current_point.ruler_data.NextIndex != 0:
            current_point = VanishPoint(layer, all_vanish_points[ruler_data.FirstVanishIndex])
            vanish_points.append(current_point)

        return cls(layer, ruler_data, vanish_points)

    @property
    def flag(self):
        return self.ruler_data.Flag

    @flag.setter
    def flag(self, new_flag):
        self.ruler_data.Flag = new_flag

    @property
    def grid_flag(self):
        return self.ruler_data.GridFlag

    @grid_flag.setter
    def grid_flag(self, new_flag):
        self.ruler_data.GridFlag = new_flag

    @property
    def grid_size(self):
        return self.ruler_data.GridSize

    @grid_size.setter
    def grid_size(self, new_size):
        self.ruler_data.GridSize = new_size

    @property
    def camera_near(self):
        return self.ruler_data.CameraNear

    @camera_near.setter
    def camera_near(self, new_camera_near):
        self.ruler_data.CameraNear = new_camera_near

    @property
    def eye_level_handle(self):
        return Position(self.ruler_data.EyeLevelHandleX, self.ruler_data.EyeLevelHandleY)

    @eye_level_handle.setter
    def eye_level_handle(self, new_handle):
        self.ruler_data.EyeLevelHandleX = new_handle.x
        self.ruler_data.EyeLevelHandleY = new_handle.y

    @property
    def move_handle(self):
        return Position(self.ruler_data.MoveHandleX, self.ruler_data.MoveHandleY)

    @move_handle.setter
    def move_handle(self, new_handle):
        self.ruler_data.MoveHandleX = new_handle.x
        self.ruler_data.MoveHandleY = new_handle.y

    @property
    def grid_origin(self):
        return Position(self.ruler_data.GridOriginX, self.ruler_data.GridOriginY)

    @grid_origin.setter
    def grid_origin(self, new_origin):
        self.ruler_data.GridOriginX = new_origin.x
        self.ruler_data.GridOriginY = new_origin.y


@define
class Symmetry(SpecialRuler):
    layer: None
    ruler_data: RulerSymmetry

    @property
    def snap(self):
        return bool(self.ruler_data.Snap)

    @snap.setter
    def snap(self, new_snap):
        self.ruler_data.Snap = bool(new_snap)

    @property
    def line_number(self):
        return self.ruler_data.LineNumber

    @line_number.setter
    def line_number(self, new_count):
        self.ruler_data.LineNumber = new_count

    @property
    def line_symmetry(self):
        return bool(self.ruler_data.LineSymmetry)

    @line_symmetry.setter
    def line_symmetry(self, new_sym):
        self.ruler_data.LineSymmetry = new_sym

    @property
    def rotate(self):
        return self.ruler_data.Rotate

    @rotate.setter
    def rotate(self, new_rotate):
        self.ruler_data.Rotate = new_rotate

    @property
    def center(self):
        return Position(self.ruler_data.CenterX, self.ruler_data.CenterY)

    @center.setter
    def center(self, new_pos):
        self.ruler_data.CenterX = new_pos.x
        self.ruler_data.CenterY = new_pos.y

@define
class VanishPoint():
    layer: None
    ruler_data: RulerVanishPoint

    @property
    def flag(self):
        return self.ruler_data.Flag

    @flag.setter
    def flag(self, new_flag):
        self.ruler_data.Flag = new_flag

    @property
    def position(self):
        return Position(self.ruler_data.VanishPointX, self.ruler_data.VanishPointY)

    @position.setter
    def position(self, new_pos):
        self.ruler_data.VanishPointX = new_pos.x
        self.ruler_data.VanishPointY = new_pos.y

    @property
    def angle(self):
        return self.ruler_data.ParallelAngle

    @angle.setter
    def angle(self, new_angle):
        self.ruler_data.ParallelAngle = new_angle

    @property
    def guide_number(self):
        return self.ruler_data.GuideNumber

    @guide_number.setter
    def guide_number(self, new_guide):
        self.ruler_data.GuideNumber = new_guide

    @property
    def guide_size(self):
        return self.ruler_data.GuideDataSize

    @guide_size.setter
    def guide_size(self, new_size):
        self.ruler_data.GuideDataSize = new_size

    @property
    def guide(self):
        return self.ruler_data.Guide

    @guide.setter
    def guide(self, new_guide):
        self.ruler_data.Guide = new_guide


class VectorRuler(BaseRuler):

    def __init__(self, layer, ruler_vector):
        self.layer = layer
        logger.warning("Vector parsing not implemented")
