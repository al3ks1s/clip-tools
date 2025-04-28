from attrs import define

from clip_tools.constants import TextStyle, TextAlign, TextOutline, TextWrapDirection, TextAttribute
from clip_tools.data_classes import Color, BBox, TextBackground, TextEdge, ReadingSetting

from clip_tools.utils import read_fmt, read_csp_str, read_csp_unicode_le_str
import copy
import io
from attr import field

import logging
logger = logging.getLogger(__name__)

@define
class TextToken():

    start: int = field()
    end: int = field()

    font: str = field()

    color: Color = field(default=Color())

    style: TextStyle = field(default=0)
    scale: float = field(default=0.0)
    align: TextAlign = field(default=0)

    outline: TextOutline = field(default=0)

    aspect_ratio: (float, float) = field(default=(0.0, 0.0))

    character_spacing: float = field(default=0.0)
    condense_text:int = field(default = 0)

    # Line space in csp, relative is "By percentage"
    use_absolute_spacing: bool = field(default=True)
    relative_spacing: float = field(default=0.0)
    absolute_spacing: float = field(default=120.0)

    def str_fmt(self):

        repr_str = "\033[0m"

        if self.style & TextStyle.BOLD:
            repr_str += "\033[1m"
        if self.style & TextStyle.ITALIC:
            repr_str += "\033[3m"
        if self.style & TextStyle.UNDERLINE:
            repr_str += "\033[4m"
        if self.style & TextStyle.STRIKEOUT:
            repr_str += "\033[9m"

        repr_str += f"\033[38;2;{self.color.r};{self.color.g};{self.color.b}m"

        return repr_str

    def __repr__(self):
        return f"{self.__class__.__name__}({self.start}, {self.end})"

    def is_in_range(self, start, end):
        return start < self.end and end > self.start

    def split_token(self, index):

        tok1 = copy.deepcopy(self)
        tok2 = copy.deepcopy(self)

        tok1.end = index
        tok2.start = index

        if tok1.start >= tok1.end:
            tok1 = None

        if tok2.start >= tok2.end:
            tok2 = None

        return tok1, tok2

@define
class Text():

    _text: str

    tokens: [TextToken]

    font: str
    font_size: float
    style: TextStyle
    color: Color

    align: TextAlign

    horizontal_in_vertical: int # TateChuYoko

    bbox: BBox

    wrap_frame: bool
    wrap_direction: TextWrapDirection

    half_width_punctuation: bool

    background: TextBackground
    edge: TextEdge

    identifier: int
    additional_fonts: []

    angle: float

    skew_angles: (float, float)

    box_size: [] # Maybe useless
    quad_verts: []

    reading_setting: ReadingSetting

    def __repr__(self):

        repr_str = ""
        for token in self.tokens:
            repr_str += token.str_fmt()
            repr_str += self._text[token.start:token.end]

        repr_str += "\033[0m"

        return repr_str

    def _remove_nones(self):
        self.tokens = [tok for tok in self.tokens if tok is not None]

    def _merge_adjacent_tokens(self):

        for i in range(len(self.tokens) - 1)[::-1]:

            t1 = self.tokens[i]
            t2 = self.tokens[i + 1]

            if (
                t1.font == t2.font and
                t1.color == t2.color and
                t1.style == t2.style and
                t1.align == t2.align and
                t1.outline == t2.outline and
                t1.aspect_ratio == t2.aspect_ratio and
                t1.use_absolute_spacing == t2.use_absolute_spacing and
                t1.relative_spacing == t2.relative_spacing and
                t1.absolute_spacing == t2.absolute_spacing
            ):
                t1.end = t2.end
                del self.tokens[i+1]

    def _tokenize(self, start, end):

        if start == end:
            return

        if start > end:
            raise ValueError("The start cannot be after the end")

        if start < 0:
            raise ValueError("Start cannot be negative")

        if end > self.tokens[-1].end:
            raise ValueError("End out of bound")

        relevant_tokens = [tok for tok in self.tokens if tok.is_in_range(start, end)]

        if len(relevant_tokens) == 0:
            return None

        if len(relevant_tokens) == 1:

            token_index = self.tokens.index(relevant_tokens[0])

            token_1, temp_token_2 = relevant_tokens[0].split_token(start)
            token_2, token_3 = temp_token_2.split_token(end)

            del self.tokens[token_index]

            self.tokens.insert(token_index, token_3)
            self.tokens.insert(token_index, token_2)
            self.tokens.insert(token_index, token_1)

            self._remove_nones()

            return [token_2]

        s_token_index = self.tokens.index(relevant_tokens[0])
        s_tok_1, s_tok_2 = relevant_tokens[0].split_token(start)

        e_token_index = self.tokens.index(relevant_tokens[-1])
        e_tok_1, e_tok_2 = relevant_tokens[-1].split_token(end)

        del self.tokens[e_token_index]
        self.tokens.insert(e_token_index, e_tok_2)
        self.tokens.insert(e_token_index, e_tok_1)

        del self.tokens[s_token_index]
        self.tokens.insert(s_token_index, s_tok_2)
        self.tokens.insert(s_token_index, s_tok_1)

        self._remove_nones()

        final_tokens = [s_tok_2]
        final_tokens.extend(relevant_tokens[1:-1])
        final_tokens.append(e_tok_1)

        return final_tokens

    def set_font(self, start, end, font: str):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.font = font

        self._merge_adjacent_tokens()

    def set_color(self, start, end, color: Color):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.color = color

        self._merge_adjacent_tokens()

    def set_style(self, start, end, text_style: TextStyle):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.style = text_style

        self._merge_adjacent_tokens()

    def apply_style(self, start, end, text_style: TextStyle):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.style = token.style | text_style

        self._merge_adjacent_tokens()

    def set_align(self, start, end, align: TextAlign):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.align = align

        self._merge_adjacent_tokens()

    def set_scale(self, start, end, scale: float):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.scale = scale

        self._merge_adjacent_tokens()

    def reset_scale(self, start, end):

        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.scale = 0.0

        self._merge_adjacent_tokens()

    def set_outline(self, start, end, outline):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.outline = outline

        self._merge_adjacent_tokens()

    def set_aspect_ratio(self, start, end, aspect_ratio):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.aspect_ratio = aspect_ratio

        self._merge_adjacent_tokens()

    def set_use_absolute_spacing(self, start, end, use_absolute):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.use_absolute_spacing = use_absolute

        self._merge_adjacent_tokens()

    def set_character_spacing(self, start, end, spacing):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.character_spacing = spacing

        self._merge_adjacent_tokens()

    def set_condense_text(self, start, end, condense):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.condense_text = condense

        self._merge_adjacent_tokens()

    def set_absolute_spacing(self, start, end, spacing):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.absolute_spacing = spacing

        self._merge_adjacent_tokens()

    def set_relative_spacing(self, start, end, spacing):
        tokens_to_affect = self._tokenize(start, end)

        if tokens_to_affect is None or len(tokens_to_affect) == 0:
            return

        for token in tokens_to_affect:
            token.relative_spacing = spacing

        self._merge_adjacent_tokens()

    def write(self, io_stream):
        pass

    @classmethod
    def new(cls, text, font = "Tahoma"):
        text_obj = cls(
            text = text,
            tokens = [TextToken(
                start = 0,
                end = len(text),
                font = font,
                color = Color(),
                style = TextStyle.NONE,
                scale = 0.0, # Text scale, 0 means no change from base font size
                align = TextAlign.CENTER,
                outline = TextOutline.NONE,
                aspect_ratio = (100.0, 100.0),
                use_absolute_spacing = True,
                relative_spacing = 0.0,
                absolute_spacing = 120.0
            )],
            font = font,
            font_size = 10.0,
            style = TextStyle.NONE,
            color = Color(),
            align = TextAlign.CENTER,
            horizontal_in_vertical = 2, # TateChuYoko
            bbox = BBox(0, 0, 0, 0), # Placeholder
            wrap_frame = False,
            wrap_direction = TextWrapDirection.TOP,
            half_width_punctuation = True,
            background = TextBackground(False, Color(), 100),
            edge = TextEdge(False, 5, Color()),
            identifier = 1000, # Placeholder
            angle = 180.0,
            skew_angles = [90.0, 90.0],
            additional_fonts = [font],
            box_size = [0, 0],
            quad_verts = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            reading_setting = ReadingSetting(0, 0, 0, 0, 0, '')
        )

        return text_obj

    @classmethod
    def read(cls, text, text_attributes_raw):

        text_obj = Text.new(text)

        text_attributes = io.BytesIO(text_attributes_raw)

        while text_attributes.tell() < len(text_attributes_raw):
            param_id = read_fmt("<i", text_attributes)
            param_size = read_fmt("<i", text_attributes)

            if param_size == 0:
                continue

            if param_id == TextAttribute.RUNS:
                num_runs = read_fmt("<i", text_attributes)

                for _ in range(num_runs):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    entry_size = read_fmt("<i", text_attributes)

                    style_flag = read_fmt("<b", text_attributes)
                    default_style_flag = read_fmt("<b", text_attributes)

                    color = Color.read(text_attributes, "<H")

                    font_scale = read_fmt("<d", text_attributes)

                    font = read_csp_unicode_le_str("<h", text_attributes)

                    text_obj.apply_style(start, start + length, TextStyle(style_flag))
                    text_obj.set_color(start, start + length, color)
                    text_obj.set_scale(start, start + length, font_scale)
                    text_obj.set_font(start, start + length, font)

            elif param_id == TextAttribute.ALIGN:

                num_aligns = read_fmt("<i", text_attributes)

                for _ in range(num_aligns):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)
                    align = read_fmt("h", text_attributes)
                    text_obj.set_align(start, start + length, align)

            elif param_id == TextAttribute.UNDERLINE:
                num_underlines = read_fmt("<i", text_attributes)

                for _ in range(num_underlines):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)
                    underline = bool(read_fmt("<h", text_attributes))

                    if underline:
                        text_obj.apply_style(start, start + length, TextStyle.UNDERLINE)

            elif param_id == TextAttribute.STRIKE:

                num_strikes = read_fmt("<i", text_attributes)

                for _ in range(num_strikes):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)
                    strike = bool(read_fmt("h", text_attributes))

                    if strike:
                        text_obj.apply_style(start, start + length, TextStyle.STRIKEOUT)

            elif param_id == TextAttribute.ASPECT_RATIO:
                num_ratio = read_fmt("<i", text_attributes)

                for _ in range(num_ratio):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)

                    text_obj.set_aspect_ratio(start, start + length, (read_fmt("<d", text_attributes), read_fmt("<d", text_attributes)))

            elif param_id == TextAttribute.CONDENSE_TEXT:
                num_param = read_fmt("<i", text_attributes)

                for _ in range(num_param):
                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)

                    text_obj.set_character_spacing(start, start + length, read_fmt("<d", text_attributes))

            elif param_id == TextAttribute.CHARACTER_SPACING:
                num_param = read_fmt("<i", text_attributes)

                for _ in range(num_param):
                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)

                    text_obj.set_character_spacing(start, start + length, read_fmt("<d", text_attributes))

            elif param_id == TextAttribute.FONT:
                text_obj.font = text_attributes.read(param_size)

            elif param_id == TextAttribute.FONT_SIZE:
                text_obj.font_size = read_fmt("<i", text_attributes) / 100

            elif param_id == TextAttribute.GLOBAL_COLOR:
                text_obj.color = Color.read(text_attributes, "<I")

            elif param_id == TextAttribute.BBOX:
                text_obj.bbox = BBox.read(text_attributes, "<I")

            elif param_id == TextAttribute.FONTS:
                num_fonts = read_fmt("<h", text_attributes)

                for _ in range(num_fonts):

                    disp_name = read_csp_str("<h", text_attributes)
                    font_name = read_csp_str("<h", text_attributes)

                    text_obj.additional_fonts.append([disp_name, font_name])

                angle = read_fmt("<i", text_attributes)

            elif param_id == TextAttribute.BOX_SIZE:
                text_obj.box_size = [read_fmt("<i", text_attributes), read_fmt("<i", text_attributes)]

            elif param_id == TextAttribute.QUAD_VERTS:
                text_obj.quad_verts = [read_fmt("<i", text_attributes) / 100 for _ in range(8)]

            elif param_id == TextAttribute.OUTLINE:

                num_outlines = read_fmt("<i", text_attributes)

                for _ in range(num_outlines):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<I", text_attributes)

                    data_size = read_fmt("<i", text_attributes)

                    text_obj.set_outline(start, start + length, TextOutline(read_fmt("<h", text_attributes)))

            elif param_id == TextAttribute.GLOBAL_STYLE:
                style_flag = TextStyle(read_fmt("<i", text_attributes))
                text_obj.style = style_flag

            elif param_id == TextAttribute.SKEW_ANGLE_1:
                skew_angle = read_fmt("<i", text_attributes) / 10
                text_obj.skew_angles[0] = skew_angle

            elif param_id == TextAttribute.SKEW_ANGLE_2:
                skew_angle = read_fmt("<i", text_attributes) / 10
                text_obj.skew_angles[1] = skew_angle

            elif param_id == TextAttribute.GLOBAL_JUSTIFY:
                text_obj.align  = TextAlign(read_fmt("<i", text_attributes))

            elif param_id == TextAttribute.ABSOLUTE_SPACING:
                # This is not spacing, something else but its also correlated to spacing?
                spacing = read_fmt("<i", text_attributes)
                #print(spacing)

            elif param_id == TextAttribute.READING_SETTING:
                text_obj.reading_setting = ReadingSetting.read(text_attributes)

            elif param_id == TextAttribute.BACKGROUND:
                text_obj.background = TextBackground.read(text_attributes)

            elif param_id == TextAttribute.EDGE:
                text_obj.edge = TextEdge.read(text_attributes)

            elif param_id == TextAttribute.ANTI_ALIASING:
                # Anti aliasing on/off ? Has 1 for on, 2 for off
                value = read_fmt("<i", text_attributes)

            elif param_id == TextAttribute.WRAP_FRAME:
                text_obj.wrap_frame = bool(read_fmt("<i", text_attributes))

            elif param_id == TextAttribute.WRAP_DIRECTION:
                text_obj.wrap_direction = TextWrapDirection(read_fmt("<i", text_attributes))

            elif param_id == TextAttribute.HALF_WIDTH_PUNCT:
                text_obj.half_width_punctuation = bool(read_fmt("<i", text_attributes))

            elif param_id == TextAttribute.ROTATION_ANGLE:
                text_obj.angle = read_fmt("<i", text_attributes) / 10

            elif param_id == TextAttribute.HORZ_IN_VERT:
                # TateChuYoko (Horizontal In Vertical) Never managed to make it work on my csp so idk what it does
                text_obj.horizontal_in_vertical = read_fmt("<i", text_attributes)

            elif param_id == TextAttribute.TEXT_ID:
                text_obj.identifier = read_fmt("<i", text_attributes)

            elif param_id == TextAttribute.LINE_SPACING:

                num_spacings = read_fmt("<i", text_attributes)

                for _ in range(num_spacings):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)
                    absolute_spacing_enabled = read_fmt("<h", text_attributes)
                    # 1 is absolute, 0 is relative

                    relative_spacing = read_fmt("<d", text_attributes)
                    absolute_spacing = read_fmt("<d", text_attributes)

                    text_obj.set_absolute_spacing(start, start + length, bool(absolute_spacing_enabled))
                    text_obj.set_relative_spacing(start, start + length, relative_spacing)
                    text_obj.set_absolute_spacing(start, start + length, absolute_spacing)

            elif param_id == 39:
                # Info doesn't seem valuable, need to see if it can be safely removed
                # Tuple usually defining the text length, either on the first or second index
                unk_pair = (read_fmt("<i", text_attributes), read_fmt("<i", text_attributes))
                #print(unk_pair)
            elif param_id == 44:
                # No idea, consistently 8333, ignore if no valuable info
                value = read_fmt("<i", text_attributes)
                assert value == 8333
                #print(decompositor(value))
            elif param_id == 43:
                # Consistently 50, Ignore in newly made layers if useless
                value = read_fmt("<i", text_attributes)
                assert value == 50
                #print(value)
            elif param_id == 45:
                # Consistently 0
                value = read_fmt("<i", text_attributes)
                assert value == 0
            elif param_id == 46:
                # 0
                value = read_fmt("<i", text_attributes)
                #print(param_id, value)
            elif param_id == 49:
                # 100
                value = read_fmt("<i", text_attributes)
                assert value == 1000
                #print(param_id, value)
            elif param_id == 51:
                # 0
                value = read_fmt("<i", text_attributes)
                assert value == 0
                #print(param_id, value)
            elif param_id == 61:
                # 0
                value = read_fmt("<i", text_attributes)
                assert value == 0
                #print(param_id, value)
            elif param_id == 62:
                # 0
                value = read_fmt("<i", text_attributes)
                assert value == 0
                #print(param_id, value)
            elif param_id == 17:
                # Mixed font data?
                
                params = []
                num_params = read_fmt("<i", text_attributes)

                for _ in range(num_params):

                    start = read_fmt("<I", text_attributes)
                    length = read_fmt("<i", text_attributes)

                    data_size = read_fmt("<i", text_attributes)

                    # 4 ints? 2 floats? anything else?
                    unk1 = read_fmt("<i", text_attributes)
                    unk2 = read_fmt("<i", text_attributes)
                    unk3 = read_fmt("<i", text_attributes)
                    unk4 = read_fmt("<i", text_attributes)

                    stri = read_csp_unicode_le_str("<h", text_attributes)

                    params.append((start, length, unk1, unk2, unk3, unk4, stri))

                #print(params)

            else:

                value = text_attributes.read(param_size)
                logger.debug(f"Unknown text param: {param_id} {param_size} {value}")

        return text_obj
