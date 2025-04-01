import attr
from attr import field

from enum import IntEnum, IntFlag

@attr.define
class ClipData():

    PW_ID: int = None

    # For API defined objects
    @classmethod
    def new(cls, db, **kwarg):

        PW_ID = db.get_free_pw_id(cls.__name__)

        obj = None

        if "MainId" in dir(cls):
            MainId = db.get_free_main_id(cls.__name__)
            obj = cls(PW_ID, MainId, **kwarg)
        else:
            obj = cls(PW_ID, **kwarg)

        obj.write_to_db(db)
        return obj

    def write_to_db(self, db):

        data_types = {
            int: "INTEGER",
            float: "FLOAT",
            str: "TEXT",
            bytes: "BYTES"
        }

        class_name = self.__class__.__name__

        if class_name not in db.table_scheme:
            db.create_table(class_name)

        table_scheme = db.table_scheme[class_name]

        new_columns = [
            f"{attribute} {data_types[type(getattr(self, attribute))]}"
            for attribute in self.__slots__
            if getattr(self, attribute) is not None and attribute not in table_scheme
        ]

        if len(new_columns) != 0:
            db.alter_table(class_name, new_columns)
            table_scheme = db.table_scheme[class_name]

        data_to_add = {attribute:attr.asdict(self)[attribute] for attribute in table_scheme}

        ids = [x[0] for x in db._execute_query(f"Select _PW_ID from {class_name}")]

        if self.PW_ID not in ids:
            self.PW_ID = db.insert_new_entry(class_name, data_to_add)
        else:
            db.edit_entry(class_name, data_to_add)


@attr.define
class Offscreen(ClipData):
    # Class with 4 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    Attribute: bytes = None
    BlockData: bytes = None


@attr.define
class VOffscreen(ClipData):
    # Class with 35 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    VOffscreenWidth: int = None
    VOffscreenHeight: int = None
    VOffscreenHorizontalBlockCount: int = None
    VOffscreenVerticalBlockCount: int = None
    VOffscreenBlockBinarySize: int = None
    VOffscreenBlockBinary: bytes = None
    BlockDataChannelOrder: int = None
    BlockDataChannelBytes: int = None
    BlockDataChannelImageCount: int = None
    BlockDataPixelBytes: int = None
    BlockDataOffsetImageBlockBytes: int = None
    BlockDataOffsetImagePixelBytes: int = None
    BlockDataOffsetImageRowBytes: int = None
    BlockDataOffsetAlphaPixelBytes: int = None
    BlockDataOffsetAlphaRowBytes: int = None
    BlockDataOffsetImageBlock: int = None
    BlockDataHorizontalBlockWide: int = None
    BlockDataVerticalBlockWide: int = None
    BlockDataHorizontalBlockShift: int = None
    BlockDataVerticalBlockShift: int = None
    InitColorDataDoInitialize: int = None
    InitColorDataAlphaValue: int = None
    InitColorDataImageValueCount: int = None
    InitColorDataImageValue00: int = None
    InitColorDataImageValue01: int = None
    InitColorDataImageValue02: int = None
    InitColorDataImageValue03: int = None
    InitColorDataImageValue04: int = None
    InitColorDataImageValue05: int = None
    InitColorDataImageValue06: int = None
    InitColorDataImageValue07: int = None
    InitColorDataImageValue08: int = None
    InitColorDataImageValue09: int = None


@attr.define
class MipmapInfo(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    ThisScale: float = None
    Offscreen: int = None
    NextIndex: int = None


@attr.define
class Mipmap(ClipData):
    # Class with 4 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    MipmapCount: int = None
    BaseMipmapInfo: int = None


@attr.define
class LayerThumbnail(ClipData):
    # Class with 42 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    ThumbnailSmallerNeedRefresh: int = None
    ThumbnailSmallNeedRefresh: int = None
    ThumbnailMiddleNeedRefresh: int = None
    ThumbnailLargeNeedRefresh: int = None
    ThumbnailLargerNeedRefresh: int = None
    ThumbnailMiddle2xNeedRefresh: int = None
    ThumbnailLarger2xNeedRefresh: int = None
    ThumbnailSmallerNeedRefresh1: int = None
    ThumbnailSmallNeedRefresh1: int = None
    ThumbnailMiddleNeedRefresh1: int = None
    ThumbnailLargeNeedRefresh1: int = None
    ThumbnailLargerNeedRefresh1: int = None
    ThumbnailMiddle2xNeedRefresh1: int = None
    ThumbnailLarger2xNeedRefresh1: int = None
    ThumbnailDrewMode: int = None
    ThumbnailFixMode: int = None
    ThumbnailCanvasWidth: int = None
    ThumbnailCanvasHeight: int = None
    ThumbnailUseDrawColor: int = None
    ThumbnailMainColorRed: int = None
    ThumbnailMainColorGreen: int = None
    ThumbnailMainColorBlue: int = None
    ThumbnailSubColorRed: int = None
    ThumbnailSubColorGreen: int = None
    ThumbnailSubColorBlue: int = None
    ThumbnailColorTypeIndex: int = None
    ThumbnailColorTypeBlack: int = None
    ThumbnailColorTypeWhite: int = None
    ThumbnailPrewviewColorTypeIndex: int = None
    ThumbnailPrewviewColorTypeBlack: int = None
    ThumbnailPrewviewColorTypeWhite: int = None
    ThumbnailPrewviewColorTypeOpacity: int = None
    ThumbnailPrewviewColorTypeImage: int = None
    ThumbnailPrewviewColorTypeAlpha: int = None
    ThumbnailPrewviewColorTypeMask: int = None
    ThumbnailPrewviewMaskBinarize: int = None
    ThumbnailPrewviewMaskThreshold: int = None
    ThumbnailDrewUseCanvasAspect0: int = None
    ThumbnailDrewUseCanvasAspect1: int = None
    ThumbnailOffscreen: int = None


@attr.define
class Layer(ClipData):
    # Class with 185 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerName: str = None
    LayerType: int = None
    LayerLock: int = None
    LayerClip: int = None
    LayerMasking: int = None
    LayerOffsetX: int = None
    LayerOffsetY: int = None
    LayerRenderOffscrOffsetX: int = None
    LayerRenderOffscrOffsetY: int = None
    LayerMaskOffsetX: int = None
    LayerMaskOffsetY: int = None
    LayerMaskOffscrOffsetX: int = None
    LayerMaskOffscrOffsetY: int = None
    LayerOpacity: int = None
    LayerComposite: int = None
    LayerUsePaletteColor: int = None
    LayerNoticeablePaletteColor: int = None
    LayerPaletteRed: int = None
    LayerPaletteGreen: int = None
    LayerPaletteBlue: int = None
    LayerFolder: int = None
    LayerVisibility: int = None
    LayerSelect: int = None
    LayerUuid: str = None
    LayerNextIndex: int = None
    LayerFirstChildIndex: int = None
    LayerRenderMipmap: int = None
    LayerLayerMaskMipmap: int = None
    LayerRenderThumbnail: int = None
    LayerLayerMaskThumbnail: int = None
    DrawColorMainRed: int = None
    DrawColorMainGreen: int = None
    DrawColorMainBlue: int = None
    DrawColorSubRed: int = None
    DrawColorSubGreen: int = None
    DrawColorSubBlue: int = None
    DrawColorEnable: int = None
    ReferLayer: int = None
    DraftLayer: int = None
    MaterialContentType: int = None
    LayerColorTypeIndex: int = None
    LayerColorTypeBlackChecked: int = None
    LayerColorTypeWhiteChecked: int = None
    PreviewColorTypeIndex: int = None
    PreviewColorTypeBlackChecked: int = None
    PreviewColorTypeWhiteChecked: int = None
    PreviewColorTypeColorToAlpha: int = None
    PreviewColorTypeApplyOpacity: int = None
    PreviewColorTypeApplyOpacityNewRender: int = None
    PreviewColorTypeThresholdImage: int = None
    PreviewColorTypeThresholdAlpha: int = None
    UsePreviewColorType: int = None
    PreviewMaskBinarize: int = None
    PreviewMaskThreshold: int = None
    UsePreviewMaskColorType: int = None
    EffectRangeType: int = None
    DrawToRenderOffscreenType: int = None
    DrawToMaskOffscreenType: int = None
    OutputAttribute: int = None
    SpecialRenderType: int = None
    DrawToRenderMipmapType: int = None
    DrawToMaskMipmapType: int = None
    EffectLayerRenderType: int = None
    EffectRenderType: int = None
    EffectReferAreaType: int = None
    EffectSetUpdateRectType: int = None
    EffectOffscreenFixType: int = None
    EffectOffscreenMoveType: int = None
    LayerEffectAttached: int = None
    MoveOffsetAndExpandType: int = None
    FixOffsetAndExpandType: int = None
    RenderBoundForLayerMoveType: int = None
    MaskBoundForLayerMoveType: int = None
    SetRenderThumbnailInfoType: int = None
    SetMaskThumbnailInfoType: int = None
    DrawRenderThumbnailType: int = None
    ShowImageAreaColorRed: int = None
    ShowImageAreaColorGreen: int = None
    ShowImageAreaColorBlue: int = None
    BankItemUuid: str = None
    FirstLayerObject: int = None
    EnableSelectLayerObject: int = None
    CurrentLayerObjectUUID: str = None
    TextLayerType: int = None
    TextLayerString: bytes = None
    TextLayerAttributes: bytes = None
    TextLayerStringArray: bytes = None
    TextLayerAttributesArray: bytes = None
    TextLayerAddAttributesV01: bytes = None
    TextLayerAttributesVersion: int = None
    TextLayerVersion: int = None
    VectorNormalType: int = None
    VectorNormalStrokeIndex: int = None
    VectorNormalFillIndex: int = None
    VectorNormalBalloonIndex: int = None
    VectorNormalStroke: bytes = None
    VectorNormalFill: bytes = None
    VectorNormalBalloon: bytes = None
    MixSubColorForEveryPlot: int = None
    ResizableImageInfo: bytes = None
    ResizableOriginalMipmap: int = None
    ResizableLockFlag: int = None
    ResizableBlackIndex: int = None
    LinkLayerUUID: str = None
    LinkLayerItemUUID: str = None
    LinkLayerLastUpdate: int = None
    LinkLayerTime: float = None
    LinkLayerTimeForTimeLine: float = None
    LinkLayerTimeLine: str = None
    LinkLayerLastModifiedCount: int = None
    LinkLayerInfo: bytes = None
    LinkLayerStatus: int = None
    LinkLayerRenderSettings: bytes = None
    ComicFrameLineMipmap: int = None
    ComicFrameColorTypeIndex: int = None
    ComicFrameColorTypeBlackChecked: int = None
    ComicFrameColorTypeWhiteChecked: int = None
    ComicFramePreviewColorTypeIndex: int = None
    ComicFramePreviewColorTypeBlackChecked: int = None
    ComicFramePreviewColorTypeWhiteChecked: int = None
    ComicFramePreviewColorTypeColorToAlpha: int = None
    ComicFramePreviewColorTypeApplyOpacity: int = None
    ComicFramePreviewColorTypeThresholdImage: int = None
    ComicFramePreviewColorTypeThresholdAlpha: int = None
    ComicFramePreviewColorTypeThresholdMask: int = None
    ComicFrameUsePreviewColorType: int = None
    Manager3D: int = None
    Manager3DOd: int = None
    Flag3DOdRelease: int = None
    HasNewDessindoll: int = None
    HasPrimitive: int = None
    Has1_0_6: int = None
    Has1_0_7: int = None
    RulerVectorIndex: int = None
    SpecialRulerManager: int = None
    RulerRange: int = None
    GuideMove: int = None
    FilterLayerInfo: bytes = None
    FilterLayerV132: int = None
    GradationFillInfo: bytes = None
    MonochromeFillInfo: bytes = None
    LayerEffectInfo: bytes = None
    CropFrame: bytes = None
    ComicStoryInfoType: int = None
    ComicStoryInfoForRightPage: int = None
    StreamLineIndex: int = None
    AudioLayer: int = None
    VoiceSpeakParam: int = None
    WebCooperationLayerEditable: int = None
    LightTableReferCell: int = None
    AnimationFolder: int = None
    AnimationCelCurrentUuid: str = None
    AnimationCaptionAttribute: bytes = None
    AnimationCaptionUseAttributeType: int = None
    TimeLineOriginalMipmap: int = None
    TimeLineOriginalMaskMipmap: int = None
    TimeLineLayerKeyFrameEnabled: int = None
    TimeLineTransformedByAction: int = None
    TimeLineRenderOriginalLeft: int = None
    TimeLineRenderOriginalTop: int = None
    TimeLineRenderOriginalRight: int = None
    TimeLineRenderOriginalBottom: int = None
    TimeLineMaskOriginalLeft: int = None
    TimeLineMaskOriginalTop: int = None
    TimeLineMaskOriginalRight: int = None
    TimeLineMaskOriginalBottom: int = None
    TimeLineRenderOriginalOffsetX: int = None
    TimeLineRenderOriginalOffsetY: int = None
    TimeLineMaskOriginalOffsetX: int = None
    TimeLineMaskOriginalOffsetY: int = None
    TimeLineRenderExtentLeft: int = None
    TimeLineRenderExtentTop: int = None
    TimeLineRenderExtentRight: int = None
    TimeLineRenderExtentBottom: int = None
    TimeLineMaskExtentLeft: int = None
    TimeLineMaskExtentTop: int = None
    TimeLineMaskExtentRight: int = None
    TimeLineMaskExtentBottom: int = None
    TimeLineOriginalLayerOpacity: int = None
    TimeLineRenderFixAspectRatio: int = None
    TimeLineMaskFixAspectRatio: int = None
    Camera2DResizableImageInfo: bytes = None
    Camera2DOriginalFrameCenterX: float = None
    Camera2DOriginalFrameCenterY: float = None
    Camera2DApplyTransform: int = None
    LightTableInfo: bytes = None
    DrawUpperMipmapForMonochromeIndex: int = None
    DrawUpperMipmapForMonochromeUse: int = None
    DrawUpperMipmapForLineIndex: int = None
    DrawUpperMipmapForLineFlag: int = None
    DrawUpperMipmapForEdgeIndex: int = None
    DrawUpperMipmapForEdgeFlag: int = None
    DrawUpperMipmapForToneIndex: int = None
    DrawUpperMipmapForToneFlag: int = None
    FilterLayerColorMixingInfo: bytes = None
    GradationFillColorMixingInfo: bytes = None


@attr.define
class LayerObject(ClipData):
    # Class with 20 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    ObjectUuid: str = None
    BankItemUuid: str = None
    ObjectName: str = None
    ObjectLock: int = None
    ObjectVisibility: int = None
    ObjectSelect: int = None
    ObjectPickmask: int = None
    ObjectNext: int = None
    Camera: int = None
    CameraNode3D: int = None
    Character: int = None
    Dessindoll: bytes = None
    Room: int = None
    SmallObject: int = None
    Primitive3D: bytes = None
    Light: int = None
    Folder: int = None
    IsAudio: int = None


@attr.define
class CameraInfo(ClipData):
    # Class with 40 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    CameraPositionX: float = None
    CameraPositionY: float = None
    CameraPositionZ: float = None
    CameraTargetX: float = None
    CameraTargetY: float = None
    CameraTargetZ: float = None
    CameraUpX: float = None
    CameraUpY: float = None
    CameraUpZ: float = None
    CameraTwist: float = None
    CameraZoomWithDolly: int = None
    FrustumLeft: float = None
    FrustumRight: float = None
    FrustumTop: float = None
    FrustumBottom: float = None
    FrustumNear: float = None
    FrustumFar: float = None
    FrustumOrtho: int = None
    FrustumTempLeft: float = None
    FrustumTempRight: float = None
    FrustumTempTop: float = None
    FrustumTempBottom: float = None
    FrustumTempNear: float = None
    FrustumTempFar: float = None
    FrustumTempOrtho: int = None
    ViewportXmin: int = None
    ViewportYmin: int = None
    ViewportWidth: int = None
    ViewportHeight: int = None
    LayerOpticalAxisPtX: float = None
    LayerOpticalAxisPtY: float = None
    CameraUuidMain: str = None
    CameraUuidSub0: str = None
    CameraUuidSub1: str = None
    CameraUuidSub2: str = None
    CameraUuidSub3: str = None
    CameraUuidSub4: str = None


@attr.define
class CameraNodeInfo(ClipData):
    # Class with 4 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    CameraNodeUUID: str = None


@attr.define
class CharacterInfo(ClipData):
    # Class with 4 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    CharacterUUID: str = None


@attr.define
class DessinDollInfo(ClipData):
    # Class with 4 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    DessindollUUID: str = None


@attr.define
class RoomInfo(ClipData):
    # Class with 4 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    RoomObjectUUID: str = None


@attr.define
class SmallObjectInfo(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    SmallObjectUUID: str = None
    SmallObjectTreeNodeGUIOpenClose: bytes = None


@attr.define
class PrimitiveInfo(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    PrimitiveUUID: str = None
    DiffuseTextureExternalFilePath: bytes = None


@attr.define
class LightInfo(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    LightIndex: int = None
    LightUuid: str = None
    LightType: int = None


@attr.define
class FolderInfo(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    LayerObjectId: int = None
    FolderObjectUUID: str = None
    FolderChildCount: int = None
    FolderGUIOpened: int = None


@attr.define
class VectorObjectList(ClipData):
    # Class with 3 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    VectorData: bytes = None # External chunk


@attr.define
class Manager3D(ClipData):
    # Class with 46 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    CameraPositionX: float = None
    CameraPositionY: float = None
    CameraPositionZ: float = None
    CameraTargetX: float = None
    CameraTargetY: float = None
    CameraTargetZ: float = None
    CameraUpX: float = None
    CameraUpY: float = None
    CameraUpZ: float = None
    FrustumLeft: float = None
    FrustumRight: float = None
    FrustumTop: float = None
    FrustumBottom: float = None
    FrustumNear: float = None
    FrustumFar: float = None
    FrustumTempLeft: float = None
    FrustumTempRight: float = None
    FrustumTempTop: float = None
    FrustumTempBottom: float = None
    FrustumTempNear: float = None
    FrustumTempFar: float = None
    ViewportWidth: int = None
    ViewportHeight: int = None
    CanvasRectLeft: float = None
    CanvasRectTop: float = None
    CanvasRectRight: float = None
    CanvasRectBottom: float = None
    CameraPers: float = None
    CameraRoll: float = None
    IsDispGrid: int = None
    IsLighting: int = None
    IsUseManipulator: int = None
    IsAngleLimit: int = None
    IsDrawShadow: int = None
    ModelInfoCount: int = None
    ModelInfoFirstIndex: int = None
    LayerFrustumAxisPtX: float = None
    LayerFrustumAxisPtY: float = None
    CameraPersFloat: float = None
    CameraRollFloat: float = None
    Light0VectorX: float = None
    Light0VectorY: float = None
    Light0VectorZ: float = None
    Light0VectorW: float = None


@attr.define
class ModelInfo3D(ClipData):
    # Class with 48 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    ModelNo: int = None
    ModelType: int = None
    ModelRootNodeTranslation: bytes = None
    ModelSkeletonRootNodeTranslation: bytes = None
    ModelNodeRotation: bytes = None
    ModelNodeInfo: bytes = None
    BBox: bytes = None
    Scale: int = None
    OffsetScale: float = None
    OutlineWidth: float = None
    OutlineColorR: int = None
    OutlineColorG: int = None
    OutlineColorB: int = None
    OutlineColorA: int = None
    PartsHair: int = None
    PartsFace: int = None
    PartsBody: int = None
    PartsAc: bytes = None
    PartsAngle: int = None
    PartsMaterial: int = None
    PartsLayout: int = None
    PartsMovable: bytes = None
    LastVisibleType: int = None
    ModelSkirtClothNodeInfo: bytes = None
    DessindollShapeInfo: bytes = None
    DessindollBoneInfo: bytes = None
    ScaleFloat: float = None
    SkirtGravity: float = None
    SkirtSpryness: float = None
    SkirtBendSpring: float = None
    FacialCategory: int = None
    FacialDetailEyes: int = None
    FacialDetailMouth: int = None
    ModelDocVer: int = None
    GroundToeAutoPosition: int = None
    GroundHeight: float = None
    PartsTransform: int = None
    ForcedTextureOff: int = None
    ModelNameForGUI: str = None
    IsModelVisible: int = None
    IsModelEditLocked: int = None
    NextIndex: int = None
    ModelNodeInfoCount: int = None
    ModelNodeInfoFirstIndex: int = None
    ModelNnbNodeInfoCount: int = None
    ModelNnbNodeInfoFirstIndex: int = None


@attr.define
class ModelNodeInfo3D(ClipData):
    # Class with 16 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NodeName: str = None
    NodeRotationR: float = None
    NodeRotationVX: float = None
    NodeRotationVY: float = None
    NodeRotationVZ: float = None
    NodeTranslationX: float = None
    NodeTranslationY: float = None
    NodeTranslationZ: float = None
    NodeScaleX: float = None
    NodeScaleY: float = None
    NodeScaleZ: float = None
    NodeTreeGUIOpened: int = None
    NodeTreeGUIVisible: int = None
    NextIndex: int = None


@attr.define
class Manager3DOd(ClipData):
    # Class with 21 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    CanvasRectLeft: float = None
    CanvasRectTop: float = None
    CanvasRectRight: float = None
    CanvasRectBottom: float = None
    LayerFrustumAxisPtX: float = None
    LayerFrustumAxisPtY: float = None
    CameraNearFarAutoSet: int = None
    SceneData: bytes = None
    MultiViewTargetPosition: bytes = None
    MultiViewZoom: float = None
    MultiViewPresetCameraFrustum: bytes = None
    MultiViewPresetCameraOrthographic: int = None
    MultiViewPresetCameraTwist: float = None
    MultiViewPresetCameraPosition: bytes = None
    MultiViewPresetCameraRotate: bytes = None
    MultiViewPresetCameraDistance: float = None
    MultiViewPresetCameraUpGuide: bytes = None
    MultiViewNearClipEnable: bytes = None
    MultiViewNearClipPosition: bytes = None


@attr.define
class RulerParallel(ClipData):
    # Class with 7 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    Rotate: float = None
    CenterX: float = None
    CenterY: float = None


@attr.define
class RulerCurveParallel(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    CurveKind: int = None
    PointData: bytes = None


@attr.define
class RulerMultiCurve(ClipData):
    # Class with 9 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    CurveKind: int = None
    OffsetAngle: float = None
    CenterX: float = None
    CenterY: float = None
    PointData: bytes = None


@attr.define
class RulerEmit(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    CenterX: float = None
    CenterY: float = None


@attr.define
class RulerCurveEmit(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    PointData: bytes = None
    CurveKind: int = None


@attr.define
class RulerConcentricCircle(ClipData):
    # Class with 9 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    RadiusX: float = None
    RadiusY: float = None
    Rotate: float = None
    CenterX: float = None
    CenterY: float = None


@attr.define
class RulerGuide(ClipData):
    # Class with 7 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    IsHorz: int = None
    CenterX: float = None
    CenterY: float = None


@attr.define
class RulerVanishPoint(ClipData):
    # Class with 10 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Flag: int = None
    VanishPointX: float = None
    VanishPointY: float = None
    ParallelAngle: float = None
    GuideNumber: int = None
    GuideDataSize: int = None
    Guide: bytes = None


@attr.define
class RulerPerspective(ClipData):
    # Class with 15 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    FirstVanishIndex: int = None
    Flag: int = None
    PerspectiveType: int = None
    EyeLevelHandleX: float = None
    EyeLevelHandleY: float = None
    MoveHandleX: float = None
    MoveHandleY: float = None
    GridOriginX: float = None
    GridOriginY: float = None
    GridFlag: int = None
    GridSize: float = None
    CameraNear: float = None


@attr.define
class RulerSymmetry(ClipData):
    # Class with 9 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    NextIndex: int = None
    Snap: int = None
    LineNumber: int = None
    LineSymmetry: int = None
    Rotate: float = None
    CenterX: float = None
    CenterY: float = None


@attr.define
class SpecialRulerManager(ClipData):
    # Class with 11 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    FirstParallel: int = None
    FirstCurveParallel: int = None
    FirstMultiCurve: int = None
    FirstEmit: int = None
    FirstCurveEmit: int = None
    FirstConcentricCircle: int = None
    FirstGuide: int = None
    FirstPerspective: int = None
    FirstSymmetry: int = None


@attr.define
class StreamLine(ClipData):
    # Class with 46 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    Kind: int = None
    ShapeCurve: bytes = None
    BaseCurve: bytes = None
    BrushStyleIndex: int = None
    OffsetAngle: float = None
    RandomSeed: int = None
    MaxLineNumber: int = None
    LineLength: float = None
    UseLineLengthDisturb: int = None
    LineLengthDisturb: float = None
    BrushSize: float = None
    UseBrushSizeDisturb: int = None
    BrushSizeDisturb: float = None
    UseIntervalAngle: int = None
    IntervalAngle: float = None
    IntervalDistance: float = None
    UseIntervalDisturb: int = None
    IntervalDisturb: float = None
    BasePointType: int = None
    UseStartGapDisturb: int = None
    StartGapDisturb: float = None
    UseGroup: int = None
    GroupSize: int = None
    UseGroupDisturb: int = None
    GroupDisturb: float = None
    GroupGap: int = None
    UseJag: int = None
    JagNumber: int = None
    JagLength: float = None
    MainRed: int = None
    MainGreen: int = None
    MainBlue: int = None
    SubRed: int = None
    SubGreen: int = None
    SubBlue: int = None
    UseFill: int = None
    FillOpacity: float = None
    InOutType: int = None
    UseIn: int = None
    InLength: float = None
    InRatio: float = None
    UseOut: int = None
    OutLength: float = None
    OutRatio: float = None


@attr.define
class SpeechSynthesis(ClipData):
    # Class with 25 attributes
    MainId: int = None 
    CanvasId: int = None
    LayerId: int = None
    BankId: int = None
    ItemId: int = None
    SpeakParamLibName: str = None
    SpeakParamCharaName: str = None
    SpeakParamOjtSpeed: float = None
    SpeakParamOjtPitch: float = None
    SpeakParamOjtIntonation: float = None
    SpeakParamOjtVolume: float = None
    SpeakParamOjt0: float = None
    SpeakParamOjt1: float = None
    SpeakParamOjt2: float = None
    SpeakParamOjtType: int = None
    SpeakParamAitSpeed: float = None
    SpeakParamAitPitch: float = None
    SpeakParamAitIntonation: float = None
    SpeakParamMttSpeed: int = None
    SpeakParamMttPitch: int = None
    SpeakParamMttIntonation: int = None
    SpeakParamMttPriority: int = None
    SpeakParamCcsSpeed: int = None
    SpeakParamCcsPitch: int = None
    SpeakParamCcsIntonation: int = None
    SpeakParamCcsEmotion: str = None


@attr.define
class Canvas(ClipData):
    # Class with 132 attributes
    MainId: int = None 
    CanvasUnit: int = None
    CanvasWidth: float = None
    CanvasHeight: float = None
    CanvasResolution: float = None
    CanvasChannelBytes: int = None
    CanvasDefaultChannelOrder: int = None
    CanvasDefaultColorTypeIndex: int = None
    CanvasDefaultColorBlackChecked: int = None
    CanvasDefaultColorWhiteChecked: int = None
    CanvasDefaultToneLine: int = None
    CanvasRootFolder: int = None
    CanvasCurrentLayer: int = None
    CanvasSrcProfileName: str = None
    CanvasSrcProfile: bytes = None
    CanvasDstProfileName: str = None
    CanvasDstProfile: bytes = None
    CanvasRenderingIntent: int = None
    CanvasUseLibraryType: int = None
    CanvasDoSimulateColor: int = None
    CanvasSimulateSrcProfileName: str = None
    CanvasSimulateSrcProfile: bytes = None
    CanvasSimulateDstProfileName: str = None
    CanvasSimulateDstProfile: bytes = None
    CanvasSimulateRenderingIntent: int = None
    CanvasSimulateUseLibraryType: int = None
    CanvasUseColorAdjustment: int = None
    CanvasColorAdjustmentToneCurve: int = None
    CanvasColorAdjustmentLevel: int = None
    CanvasProgressStep: int = None
    CanvasDoublePage: int = None
    CanvasRenderMipmapForceSaved: int = None
    CanvasWorkTime: int = None
    ShowGrid: int = None
    GridDitch: float = None
    GridDitchUnit: int = None
    GridDivide: int = None
    GridOriginType: int = None
    GridOriginX: float = None
    GridOriginXUnit: int = None
    GridOriginY: float = None
    GridOriginYUnit: int = None
    ShowToneArea: int = None
    ShowToneAreaWithImage: int = None
    BankItemUuid: str = None
    BrushStyleManager: int = None
    BrushStyleReadProtect070: int = None
    Canvas3DModelDataLoaderIndex: int = None
    RulerRotateCenterX: float = None
    RulerRotateCenterY: float = None
    CropFrameOptionFlag: int = None
    CropFrameUnitKind: int = None
    CropFrameWidth: float = None
    CropFrameHeight: float = None
    CropFrameDitch: float = None
    CropFrameInnerWidth: float = None
    CropFrameInnerHeight: float = None
    CropFrameInnerOffsetX: float = None
    CropFrameInnerOffsetY: float = None
    CropFrameMergeDitch: float = None
    CropFrameShow: int = None
    CropFrameCropOffsetX: int = None
    CropFrameCropOffsetY: int = None
    CropFrameSafeMarginLeft: int = None
    CropFrameSafeMarginTop: int = None
    CropFrameSafeMarginRight: int = None
    CropFrameSafeMarginBottom: int = None
    CropFrameInnerOffsetBasePosition: int = None
    CropFrameDesignationType: int = None
    ComicStoryLayerCreated: int = None
    ComicNombreLayerCreated: int = None
    ComicStoryRightLayerCreated: int = None
    ComicNombreRightLayerCreated: int = None
    ComicStoryStoryName: str = None
    ComicStoryUseStoryIndex: int = None
    ComicStoryStoryIndex: int = None
    ComicStorySubTitle: str = None
    ComicStoryStoryPosition: int = None
    ComicStoryAuthorName: str = None
    ComicStoryAuthorPosition: int = None
    ComicStoryUsePageNumber: int = None
    ComicStoryPageNumberStart: int = None
    ComicStoryPageNumberPosition: int = None
    ComicStoryNombreStart: int = None
    ComicStoryNombreFont: str = None
    ComicStoryNombreFontSize: float = None
    ComicStoryNombreFontPostScriptName: str = None
    ComicStoryUseShownNombre: int = None
    ComicStoryNombrePosition: int = None
    ComicStoryNombrePrefix: str = None
    ComicStoryNombreSuffix: str = None
    ComicStoryUseHiddenNombre: int = None
    ComicStoryNombreColor: int = None
    ComicStoryNombreUseEdge: int = None
    ComicStoryNombreEdgeWidth: float = None
    ComicStoryNombreEdgeUnit: int = None
    ComicStoryXPageNombreOffset: float = None
    ComicStoryXPageNombreOffsetUnit: int = None
    ComicStoryYPageNombreOffset: float = None
    ComicStoryYPageNombreOffsetUnit: int = None
    ComicBindPosition: int = None
    ComicPageIndex: int = None
    ComicIsLeftPage: int = None
    ComicStoryBackupNombreFont: str = None
    ComicStoryBackupNombreFontSize: float = None
    ComicStoryBackupNombrePosition: int = None
    ComicStoryBackupNombreColor: int = None
    ComicStoryBackupNombreUseEdge: int = None
    ComicStoryBackupNombreEdgeWidth: float = None
    ComicStoryBackupNombreEdgeUnit: int = None
    ComicStoryNeedRefresh: int = None
    ComicHasComicCover: int = None
    ComicHasDoubleCover: int = None
    OnionSkinStatus: int = None
    OnionSkinSettingRegisted: int = None
    OnionSkinPrevDisplayCount: int = None
    OnionSkinNextDisplayCount: int = None
    OnionSkinUseOpacity: int = None
    OnionSkinStartOpacity: int = None
    OnionSkinStepOpaciy: int = None
    OnionSkinUseColor: int = None
    OnionSkinHalfColor: int = None
    OnionSkinFrontColorRed: int = None
    OnionSkinFrontColorGreen: int = None
    OnionSkinFrontColorBlue: int = None
    OnionSkinBehindColorRed: int = None
    OnionSkinBehindColorGreen: int = None
    OnionSkinBehindColorBlue: int = None
    TimeLineFrameDisplay: int = None
    TimeLineEditMode: int = None
    TimeLineUseNameFormat: int = None
    TimeLineNameFormat: int = None
    TimeLineResizeQuality: int = None
    LightTableRotateCenterX: float = None
    LightTableRotateCenterY: float = None
    LightTableEnable: int = None
    LightTableFixTarget: int = None
    LightTableEnableWhenSave: int = None
    LightTableReferCommonOpacity: int = None
    TimeLapseManagerIndex: int = None


@attr.define
class BrushEffectorGraphData(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    ControlNumber: int = None
    ControlDataSize: int = None
    ControlPoints: bytes = None


@attr.define
class BrushPatternImage(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    Uuid: bytes = None
    Name: str = None
    Mipmap: int = None


@attr.define
class BrushPatternStyle(ClipData):
    # Class with 7 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    ImageNumber: int = None
    ImageIndex: bytes = None
    OrderType: int = None
    Reverse: int = None
    Reverse2: int = None


@attr.define
class BrushFixedSpray(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    PlotNumber: int = None
    PlotDataSize: int = None
    PlotPoints: bytes = None


@attr.define
class BrushStyle(ClipData):
    # Class with 65 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    DualStyleIndex: int = None
    StyleFlag: int = None
    PenRadius: float = None
    SizeEffector: bytes = None
    OpacityEffector: bytes = None
    FlowBase: float = None
    FlowEffector: bytes = None
    AntiAlias: int = None
    Hardness: float = None
    IntervalBase: float = None
    IntervalEffector: bytes = None
    AutoIntervalType: int = None
    ThicknessBase: float = None
    ThicknessEffector: bytes = None
    RotationBase: float = None
    RotationInSprayBase: float = None
    RotationEffector: int = None
    RotationRandom: float = None
    RotationEffectorInSpray: int = None
    RotationRandomInSpray: float = None
    PatternStyle: int = None
    CompositeMode: int = None
    DualCompositeMode: int = None
    TexturePattern: int = None
    TextureFlag: int = None
    TextureComposite: int = None
    TextureScale: float = None
    TextureRotate: float = None
    TextureOffsetX: float = None
    TextureOffsetY: float = None
    TextureBrightness: float = None
    TextureContrast: float = None
    TextureDensityBase: float = None
    TextureDensityEffector: bytes = None
    UseWaterColor: int = None
    WaterColorType: int = None
    MixColorBase: float = None
    MixColorEffector: bytes = None
    MixAlphaBase: float = None
    MixAlphaEffector: bytes = None
    ColorExtension: float = None
    BlurBase: float = None
    BlurEffector: bytes = None
    SubColorBase: float = None
    SubColorEffector: bytes = None
    HueChangeBase: float = None
    HueChangeEffector: bytes = None
    SaturationChangeBase: float = None
    SaturationChangeEffector: bytes = None
    ValueChangeBase: float = None
    ValueChangeEffector: bytes = None
    ChangeDrawColorTarget: int = None
    SprayFlag: int = None
    SpraySizeBase: float = None
    SpraySizeEffector: bytes = None
    SprayDensityBase: float = None
    SprayDensityEffector: bytes = None
    SprayBias: float = None
    FixedSpray: int = None
    WaterEdgeFlag: int = None
    WaterEdgeRadius: float = None
    WaterEdgeAlphaPower: float = None
    WaterEdgeValuePower: float = None
    WaterEdgeBlur: float = None
    BrushColorMixingMode: int = None
    BrushLMSLinearity: int = None


@attr.define
class FillStyle(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    StyleFlag: int = None
    AntiAlias: int = None
    CompositeMode: int = None
    TextureDensity: int = None


@attr.define
class BrushStyleManager(ClipData):
    # Class with 8 attributes
    MainId: int = None 
    CanvasId: int = None
    FirstGraphData: int = None
    FirstPatternImage: int = None
    FirstPattern: int = None
    FirstPatternStyle: int = None
    FirstFixedSpray: int = None
    FirstBrushStyle: int = None
    FirstFillStyle: int = None


@attr.define
class ModelData3D(ClipData):
    # Class with 2 attributes
    MainId: int = None 
    CanvasId: int = None
    Layer3DModelData: bytes = None


@attr.define
class TimeLapseBlob(ClipData):
    # Class with 7 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    BlobOffset: int = None
    BlobSize: int = None
    BlobSizeCompressed: int = None
    BlobType: int = None
    BlobData: bytes = None


@attr.define
class TimeLapseRecord(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    NextIndex: int = None
    EncoderName: str = None
    EncoderSequence: int = None
    BlobFirstIndex: int = None


@attr.define
class TimeLapseManager(ClipData):
    # Class with 2 attributes
    MainId: int = None 
    CanvasId: int = None
    RecordFirstIndex: int = None


@attr.define
class CanvasPreview(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    CanvasId: int = None
    ImageType: int = None
    ImageWidth: bytes = None
    ImageHeight: int = None
    ImageData: bytes = None


@attr.define
class CanvasNode(ClipData):
    # Class with 23 attributes
    MainId: int = None 
    Name: str = None
    NextIndex: int = None
    FirstChildIndex: int = None
    SelectedIndex: int = None
    CanvasIndex: int = None
    CanvasThumbnail: int = None
    PageFlag: int = None
    Memo: str = None
    BookBindMemo: str = None
    BookBindWarning: int = None
    BookBindWarningDef: int = None
    LinkPath: str = None
    LinkWriteYear: int = None
    LinkWriteMonth: int = None
    LinkWriteDay: int = None
    LinkWriteHour: int = None
    LinkWriteMinute: int = None
    LinkWriteSecond: int = None
    LinkIsFolder: int = None
    LinkUnit: int = None
    LinkWidth: float = None
    LinkHeight: float = None
    LinkResolution: float = None


@attr.define
class CanvasItem(ClipData):
    # Class with 20 attributes
    MainId: int = None 
    BankId: int = None
    ItemNextItemMainIndex: int = None
    ItemBinaryMainIndex: int = None
    ItemUuid: str = None
    ItemType: str = None
    ItemCaption: str = None
    ItemThumbnail: bytes = None
    ItemDataHoldMethod: str = None
    ItemRegistedDirect: int = None
    ItemFileExtension: str = None
    ItemExternalFilePath: bytes = None
    ItemExternalFilePathType: int = None
    ItemImportYear: int = None
    ItemImportMonth: int = None
    ItemImportDay: int = None
    ItemImportHour: int = None
    ItemImportMinute: int = None
    ItemImportSecond: int = None
    ItemImportIndex: int = None
    kLabelItem3DDataID: str = None


@attr.define
class CanvasItemBinary(ClipData):
    # Class with 3 attributes
    MainId: int = None 
    BankId: int = None
    ItemId: int = None
    ItemBinaryData: bytes = None


@attr.define
class Canvas3DModelLoader(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    BankId: int = None
    ModelData: bytes = None
    ModelUuid: str = None
    ModelType: int = None
    NextIndex: int = None


@attr.define
class Canvas3DModelBank(ClipData):
    # Class with 3 attributes
    MainId: int = None 
    BankId: int = None
    BankData: bytes = None
    FirstLoaderIndex: int = None


@attr.define
class CanvasItemBank(ClipData):
    # Class with 2 attributes
    MainId: int = None 
    BankRootItemMainIndex: int = None
    ModelBankMainIndex: int = None


@attr.define
class Track(ClipData):
    # Class with 18 attributes
    MainId: int = None 
    BankId: int = None
    ItemId: int = None
    TrackNextIndex: int = None
    TrackActionMixer: bytes = None
    TrackActionMixerSize: int = None
    TrackActionMixer2: bytes = None
    TrackActionMixer2Size: int = None
    TrackValueMap: bytes = None
    TrackUuid: bytes = None
    LayerUuidWithTrack: bytes = None
    TrackLayerObjectUuid: bytes = None
    TrackKind: int = None
    TrackOpen: int = None
    TrackOptionFlag: int = None
    TrackContentOpen: int = None
    ActionMixerPlayType: int = None
    TrackLabelFirstIndex: int = None
    PoseCorrectionObject: bytes = None


@attr.define
class TimeLineLabel(ClipData):
    # Class with 8 attributes
    MainId: int = None 
    BankId: int = None
    ItemId: int = None
    TrackId: int = None
    LabelNextIndex: int = None
    LabelName: str = None
    LabelFrame: float = None
    LabelType: int = None
    LabelLength: float = None


@attr.define
class TimeLine(ClipData):
    # Class with 14 attributes
    MainId: int = None 
    BankId: int = None
    NextTimeLine: int = None
    NextScenario: int = None
    FirstTrack: int = None
    LabelFirstIndex: int = None
    TimeLineUuid: bytes = None
    TimeLineName: str = None
    SceneIndexForName: int = None
    CutIndexForName: int = None
    FrameRate: float = None
    StartFrame: float = None
    EndFrame: float = None
    CurrentFrame: float = None
    GuidelineFrameRate: int = None


@attr.define
class SituationCast(ClipData):
    # Class with 10 attributes
    MainId: int = None 
    CanvasId: int = None
    BankId: int = None
    ItemId: int = None
    NextIndex: int = None
    Character: str = None
    Face: str = None
    Hair: str = None
    Body: str = None
    Accessory: str = None
    SpeakParam: int = None


@attr.define
class SituationSet(ClipData):
    # Class with 6 attributes
    MainId: int = None 
    CanvasId: int = None
    BankId: int = None
    ItemId: int = None
    Room: str = None
    Situation: str = None
    FirstCast: int = None


@attr.define
class Scenario(ClipData):
    # Class with 32 attributes
    MainId: int = None 
    BankId: int = None
    NextTimeLine: int = None
    NextScenario: int = None
    Situation: int = None
    ScenarioUuid: bytes = None
    ScenarioName: str = None
    Sentence: str = None
    PhysicsLayerGroundHeight: float = None
    PhysicsLayerSetting: int = None
    PhysicsLayerOnlySkirt: int = None
    PhysicsLayerObjectSkirtGravity: float = None
    PhysicsLayerObjectSkirtSpryness: float = None
    PhysicsLayerObjectSkirtBendSpring: float = None
    PhysicsLayerObjectToeAutoPosition: int = None
    RenderingOutlineEnable: int = None
    RenderingOutlineWidth: float = None
    RenderingOutlineColorR: int = None
    RenderingOutlineColorG: int = None
    RenderingOutlineColorB: int = None
    RenderingOutlineColorA: int = None
    RenderingBackfaceCullingEnable: int = None
    RenderingLightRecieved: int = None
    RenderingCameraFrustumNear: float = None
    RenderingCameraFrustumFar: float = None
    RenderingCameraFrustumNearFarAutoSet: int = None
    RenderingLighting: int = None
    RenderingDrawTexture: int = None
    RenderingShadowEnable: int = None
    RenderingAlphaTestEnabl: int = None
    RenderingAlphaTestValue: float = None
    RenderingShadingKind: int = None
    RenderingTextureFilterKind: int = None


@attr.define
class AnimationCutBank(ClipData):
    # Class with 5 attributes
    MainId: int = None 
    FirstTimeLine: int = None
    FirstScenario: int = None
    CurrentIndex: int = None
    Enable: int = None
    FlagScenarioV155: int = None


@attr.define
class Project(ClipData):
    # Class with 89 attributes
    ProjectCanvas: int = None
    ProjectItemBank: int = None
    ProjectCutBank: int = None
    ProjectLayerCompManager: int = None
    ProjectName: str = None
    ProjectInternalVersion: str = None
    ProjectProgressStep: int = None
    ProjectRootCanvasNode: int = None
    ComicStoryStoryName: str = None
    ComicStoryUseStoryIndex: int = None
    ComicStoryStoryIndex: int = None
    ComicStorySubTitle: str = None
    ComicStoryStoryPosition: int = None
    ComicStoryAuthorName: str = None
    ComicStoryAuthorPosition: int = None
    ComicStoryUsePageNumber: int = None
    ComicStoryPageNumberStart: int = None
    ComicStoryPageNumberPosition: int = None
    ComicStoryNombreStart: int = None
    ComicStoryNombreFont: str = None
    ComicStoryNombreFontSize: float = None
    ComicStoryNombreFontPostScriptName: str = None
    ComicStoryUseShownNombre: int = None
    ComicStoryNombrePosition: int = None
    ComicStoryNombrePrefix: str = None
    ComicStoryNombreSuffix: str = None
    ComicStoryUseHiddenNombre: int = None
    ComicStoryNombreColor: int = None
    ComicStoryNombreUseEdge: int = None
    ComicStoryNombreEdgeWidth: float = None
    ComicStoryNombreEdgeUnit: int = None
    ComicStoryXPageNombreOffset: float = None
    ComicStoryXPageNombreOffsetUnit: int = None
    ComicStoryYPageNombreOffset: float = None
    ComicStoryYPageNombreOffsetUnit: int = None
    DefaultPageUnit: int = None
    DefaultPageWidth: float = None
    DefaultPageHeight: float = None
    DefaultPageResolution: float = None
    DefaultPageChannelBytes: int = None
    DefaultPageChannelOrder: int = None
    DefaultPageColorType: int = None
    DefaultPageBlackChecked: int = None
    DefaultPageWhiteChecked: int = None
    DefaultPageToneLine: int = None
    DefaultPageUsePaper: int = None
    DefaultPagePaperRed: int = None
    DefaultPagePaperGreen: int = None
    DefaultPagePaperBlue: int = None
    DefaultPageUseCropFrame: int = None
    DefaultPageCropOptionFlag: int = None
    DefaultPageCropWidth: float = None
    DefaultPageCropHeight: float = None
    DefaultPageCropDitch: float = None
    DefaultPageCropOffsetX: float = None
    DefaultPageCropOffsetY: float = None
    DefaultPageCropInnerWidth: float = None
    DefaultPageCropInnerHeight: float = None
    DefaultPageCropInnerOffsetX: float = None
    DefaultPageCropInnerOffsetY: float = None
    DefaultPageCropMergeDitch: float = None
    DefaultPageSafeMarginLeft: float = None
    DefaultPageSafeMarginRight: float = None
    DefaultPageSafeMarginTop: float = None
    DefaultPageSafeMarginBottom: float = None
    DefaultPageUseTemplate: int = None
    DefaultPageTemplatePath: str = None
    DefaultPageTemplatePath2: str = None
    DefaultPageTemplateName: str = None
    DefaultPageIsUserTemplate: int = None
    DefaultPageDoublePage: int = None
    DefaultPagePresetID: str = None
    DefaultPageCheckBookBinding: int = None
    DefaultPageRecordTimeLapse: int = None
    DefaultPageTemplateUUID: str = None
    DefaultPageCelUseTemplate: int = None
    DefaultPageCelTemplatePath: str = None
    DefaultPageCelTemplatePath2: str = None
    DefaultPageCelTemplateName: str = None
    DefaultPageCelIsUserTemplate: int = None
    DefaultCoverResolution: float = None
    DefaultCoverChannelBytes: int = None
    DefaultCoverUsePaper: int = None
    DefaultCoverPaperRed: int = None
    DefaultCoverPaperGreen: int = None
    DefaultCoverPaperBlue: int = None
    DefaultPageUseDefaultCoverInfo: int = None
    DefaultCoverUseTemplate: int = None
    DefaultCoverTemplatePath: str = None
    DefaultCoverTemplatePath2: str = None
    DefaultCoverTemplateName: str = None
    DefaultPageCelTemplateUUID: str = None
    DefaultCoverIsUserTemplate: int = None
    DefaultCoverTemplateUUID: str = None
    DefaultPageSettingType: str = None
    WebCooperationUploadUrl: str = None
    WebCooperationUploadToken: str = None

@attr.define
class LayerCompManager(ClipData):
    MainId: int = None
    FirstLayerCompIndex: int = None
    LastStateLayerCompIndex: int = None
    AppliedLayerCompIndex: int = None

@attr.define
class LayerComp(ClipData):
    MainId: int = None
    BankId: int = None
    CompNextIndex: int = None
    CompName: str = None
    CompUuid: str = None
    CompLayerInfo: bytes = None
