# See RulerRange Column and surrounding

from attrs import define

class Rulers:
    pass

class BaseRuler():
    pass

class SpecialRuler(BaseRuler):
    pass

class Parallel(SpecialRuler):
    pass

class CurveParallel(SpecialRuler):
    pass

class Emit(SpecialRuler):
    pass

class EmitCurve(SpecialRuler):
    pass

class ConcentricCircle(SpecialRuler):
    pass

class Guide(SpecialRuler):
    pass

class Perspective(SpecialRuler):
    pass

class Symmetry(SpecialRuler):
    pass

class VectorRuler(BaseRuler):
    pass