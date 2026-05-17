"""
Button 2: Customer PDF Typography Token Definitions v1

Purpose:
  Define typography tokens (font sizes, weights, line heights) as constants
  for use across Button 2 PDF composition and visual polish implementation.

Governance:
  - No renderer changes
  - No CSS application (just token definitions)
  - No customer PDF behavior changes
  - Pure data layer (constants only)

Typography Stack:
  - Font family: system sans-serif (defined at render time)
  - Font sizes: 8-20pt scale
  - Weights: 400 (regular), 600 (semibold), 700 (bold)
  - Line heights: 1.2-1.5 range

Tokens Organized By Usage:
  - Display (titles, main headers)
  - Section headers (L1, L2 subsections)
  - Body (paragraph, list items, captions)
  - Small print (sources, metadata, footers)
"""

from dataclasses import dataclass
from typing import Dict, Literal

# =============================================================================
# Typography Token Dataclass
# =============================================================================


@dataclass(frozen=True)
class TypographyToken:
    """
    Immutable typography token definition.

    Attributes:
      name: Token identifier (e.g., "body-primary", "header-l1")
      font_size_pt: Font size in points
      font_weight: CSS font-weight (400, 600, 700)
      line_height: CSS line-height ratio (e.g., 1.5)
      letter_spacing_px: Optional letter-spacing in pixels
      color_hex: Optional color code (e.g., "#000000")
      margin_top_pt: Optional margin-top in points
      margin_bottom_pt: Optional margin-bottom in points
      use_case: Short description of when to apply
    """

    name: str
    font_size_pt: int | float
    font_weight: Literal[400, 600, 700]
    line_height: float
    letter_spacing_px: float = 0.0
    color_hex: str | None = None
    margin_top_pt: int | float = 0
    margin_bottom_pt: int | float = 0
    use_case: str = ""

    def to_css_dict(self) -> Dict[str, str | int | float]:
        """
        Convert token to CSS property dictionary.

        Returns:
          Dict of CSS properties (font-size, font-weight, line-height, etc.)
        """
        css = {
            "font-size": f"{self.font_size_pt}pt",
            "font-weight": self.font_weight,
            "line-height": self.line_height,
        }
        if self.letter_spacing_px != 0:
            css["letter-spacing"] = f"{self.letter_spacing_px}px"
        if self.color_hex:
            css["color"] = self.color_hex
        if self.margin_top_pt > 0:
            css["margin-top"] = f"{self.margin_top_pt}pt"
        if self.margin_bottom_pt > 0:
            css["margin-bottom"] = f"{self.margin_bottom_pt}pt"
        return css

    def to_css_string(self, selector: str = "") -> str:
        """
        Convert token to CSS rule string.

        Args:
          selector: CSS selector (optional, for standalone rule generation)

        Returns:
          CSS rule as string, ready for inline style or stylesheet
        """
        css_dict = self.to_css_dict()
        css_props = "; ".join([f"{k}: {v}" for k, v in css_dict.items()])
        if selector:
            return f"{selector} {{ {css_props}; }}"
        return css_props


# =============================================================================
# Display Tokens (Report Title, Main Headers)
# =============================================================================

TYPOGRAPHY_TOKEN_REPORT_TITLE = TypographyToken(
    name="report-title",
    font_size_pt=20,
    font_weight=700,
    line_height=1.2,
    letter_spacing_px=0.5,
    margin_top_pt=0,
    margin_bottom_pt=8,
    use_case="Report title (fight identification, event name)",
)

TYPOGRAPHY_TOKEN_REPORT_SUBTITLE = TypographyToken(
    name="report-subtitle",
    font_size_pt=14,
    font_weight=600,
    line_height=1.2,
    margin_bottom_pt=4,
    use_case="Report subtitle (date, location, operator info)",
)

# =============================================================================
# Section Header Tokens (L1 Sections)
# =============================================================================

TYPOGRAPHY_TOKEN_SECTION_HEADER_L1 = TypographyToken(
    name="section-header-l1",
    font_size_pt=15,
    font_weight=600,
    line_height=1.2,
    margin_top_pt=12,
    margin_bottom_pt=6,
    use_case="Level 1 section header (Fighter Context, Matchup Signal, Analysis)",
)

TYPOGRAPHY_TOKEN_SECTION_HEADER_L1_LARGE = TypographyToken(
    name="section-header-l1-large",
    font_size_pt=16,
    font_weight=600,
    line_height=1.2,
    margin_top_pt=12,
    margin_bottom_pt=6,
    use_case="Large L1 header for prominent sections",
)

TYPOGRAPHY_TOKEN_SECTION_HEADER_L1_SMALL = TypographyToken(
    name="section-header-l1-small",
    font_size_pt=14,
    font_weight=600,
    line_height=1.2,
    margin_top_pt=12,
    margin_bottom_pt=6,
    use_case="Small L1 header for compact sections",
)

# =============================================================================
# Subsection Header Tokens (L2 Sections)
# =============================================================================

TYPOGRAPHY_TOKEN_SECTION_HEADER_L2 = TypographyToken(
    name="section-header-l2",
    font_size_pt=13,
    font_weight=600,
    line_height=1.2,
    margin_top_pt=8,
    margin_bottom_pt=4,
    use_case="Level 2 subsection header (Record Summary, Style Notes, Injury Notes)",
)

TYPOGRAPHY_TOKEN_SECTION_HEADER_L2_LARGE = TypographyToken(
    name="section-header-l2-large",
    font_size_pt=14,
    font_weight=600,
    line_height=1.2,
    margin_top_pt=8,
    margin_bottom_pt=4,
    use_case="Large L2 header for emphasized subsections",
)

TYPOGRAPHY_TOKEN_SECTION_HEADER_L2_SMALL = TypographyToken(
    name="section-header-l2-small",
    font_size_pt=12,
    font_weight=600,
    line_height=1.2,
    margin_top_pt=6,
    margin_bottom_pt=3,
    use_case="Small L2 header for compact subsections",
)

# =============================================================================
# Body Text Tokens (Paragraphs, List Items)
# =============================================================================

TYPOGRAPHY_TOKEN_BODY_PRIMARY = TypographyToken(
    name="body-primary",
    font_size_pt=12,
    font_weight=400,
    line_height=1.5,
    margin_bottom_pt=8,
    use_case="Main paragraph text (operator signal, context, analysis)",
)

TYPOGRAPHY_TOKEN_BODY_SECONDARY = TypographyToken(
    name="body-secondary",
    font_size_pt=11,
    font_weight=400,
    line_height=1.5,
    margin_bottom_pt=8,
    use_case="Secondary paragraph text (detailed notes, background)",
)

TYPOGRAPHY_TOKEN_BODY_COMPACT = TypographyToken(
    name="body-compact",
    font_size_pt=11,
    font_weight=400,
    line_height=1.4,
    margin_bottom_pt=4,
    use_case="Compact body text (list items, brief explanations)",
)

TYPOGRAPHY_TOKEN_LIST_ITEM = TypographyToken(
    name="list-item",
    font_size_pt=12,
    font_weight=400,
    line_height=1.4,
    margin_top_pt=2,
    margin_bottom_pt=4,
    use_case="Bullet or numbered list item",
)

# =============================================================================
# Caption and Small Print Tokens
# =============================================================================

TYPOGRAPHY_TOKEN_CAPTION_PRIMARY = TypographyToken(
    name="caption-primary",
    font_size_pt=10,
    font_weight=600,
    line_height=1.3,
    color_hex="#666666",
    margin_bottom_pt=8,
    use_case="Figure or chart caption (descriptive, not functional)",
)

TYPOGRAPHY_TOKEN_CAPTION_SECONDARY = TypographyToken(
    name="caption-secondary",
    font_size_pt=9,
    font_weight=400,
    line_height=1.3,
    color_hex="#777777",
    margin_bottom_pt=4,
    use_case="Secondary caption (metadata, date, source hint)",
)

TYPOGRAPHY_TOKEN_SOURCE_CITATION = TypographyToken(
    name="source-citation",
    font_size_pt=9,
    font_weight=400,
    line_height=1.3,
    color_hex="#777777",
    use_case="Inline source URL or citation (monospace in render)",
)

TYPOGRAPHY_TOKEN_PAGE_METADATA = TypographyToken(
    name="page-metadata",
    font_size_pt=9,
    font_weight=400,
    line_height=1.2,
    color_hex="#999999",
    use_case="Page footer metadata (page number, operator, timestamp)",
)

TYPOGRAPHY_TOKEN_APPROVAL_TIMESTAMP = TypographyToken(
    name="approval-timestamp",
    font_size_pt=8,
    font_weight=400,
    line_height=1.2,
    color_hex="#999999",
    use_case="Operator approval timestamp (small, muted)",
)

# =============================================================================
# Accent and Highlighted Tokens
# =============================================================================

TYPOGRAPHY_TOKEN_EMPHASIS_BOLD = TypographyToken(
    name="emphasis-bold",
    font_size_pt=12,
    font_weight=700,
    line_height=1.5,
    use_case="Emphasized text within body (rare use, bold inline only)",
)

TYPOGRAPHY_TOKEN_CONFIDENCE_BOUND = TypographyToken(
    name="confidence-bound",
    font_size_pt=11,
    font_weight=600,
    line_height=1.4,
    color_hex="#2c5282",
    margin_top_pt=4,
    margin_bottom_pt=4,
    use_case="Confidence bound or certainty level indicator",
)

TYPOGRAPHY_TOKEN_WARNING_TEXT = TypographyToken(
    name="warning-text",
    font_size_pt=11,
    font_weight=600,
    line_height=1.4,
    color_hex="#c53030",
    use_case="Warning or alert text (injury factor, uncertainty)",
)

# =============================================================================
# Chart and Data Visualization Tokens
# =============================================================================

TYPOGRAPHY_TOKEN_CHART_LABEL = TypographyToken(
    name="chart-label",
    font_size_pt=10,
    font_weight=400,
    line_height=1.3,
    use_case="Chart axis label, legend label, data point label",
)

TYPOGRAPHY_TOKEN_CHART_TITLE = TypographyToken(
    name="chart-title",
    font_size_pt=12,
    font_weight=600,
    line_height=1.2,
    margin_bottom_pt=6,
    use_case="Chart or table title",
)

TYPOGRAPHY_TOKEN_CHART_ANNOTATION = TypographyToken(
    name="chart-annotation",
    font_size_pt=9,
    font_weight=400,
    line_height=1.2,
    color_hex="#666666",
    use_case="Chart annotation, callout, note on data",
)

# =============================================================================
# Typography Token Registry (Central Reference)
# =============================================================================

TYPOGRAPHY_TOKENS_REGISTRY: Dict[str, TypographyToken] = {
    # Display
    "report-title": TYPOGRAPHY_TOKEN_REPORT_TITLE,
    "report-subtitle": TYPOGRAPHY_TOKEN_REPORT_SUBTITLE,
    # L1 Headers
    "section-header-l1": TYPOGRAPHY_TOKEN_SECTION_HEADER_L1,
    "section-header-l1-large": TYPOGRAPHY_TOKEN_SECTION_HEADER_L1_LARGE,
    "section-header-l1-small": TYPOGRAPHY_TOKEN_SECTION_HEADER_L1_SMALL,
    # L2 Headers
    "section-header-l2": TYPOGRAPHY_TOKEN_SECTION_HEADER_L2,
    "section-header-l2-large": TYPOGRAPHY_TOKEN_SECTION_HEADER_L2_LARGE,
    "section-header-l2-small": TYPOGRAPHY_TOKEN_SECTION_HEADER_L2_SMALL,
    # Body
    "body-primary": TYPOGRAPHY_TOKEN_BODY_PRIMARY,
    "body-secondary": TYPOGRAPHY_TOKEN_BODY_SECONDARY,
    "body-compact": TYPOGRAPHY_TOKEN_BODY_COMPACT,
    "list-item": TYPOGRAPHY_TOKEN_LIST_ITEM,
    # Captions & Small Print
    "caption-primary": TYPOGRAPHY_TOKEN_CAPTION_PRIMARY,
    "caption-secondary": TYPOGRAPHY_TOKEN_CAPTION_SECONDARY,
    "source-citation": TYPOGRAPHY_TOKEN_SOURCE_CITATION,
    "page-metadata": TYPOGRAPHY_TOKEN_PAGE_METADATA,
    "approval-timestamp": TYPOGRAPHY_TOKEN_APPROVAL_TIMESTAMP,
    # Accent
    "emphasis-bold": TYPOGRAPHY_TOKEN_EMPHASIS_BOLD,
    "confidence-bound": TYPOGRAPHY_TOKEN_CONFIDENCE_BOUND,
    "warning-text": TYPOGRAPHY_TOKEN_WARNING_TEXT,
    # Chart
    "chart-label": TYPOGRAPHY_TOKEN_CHART_LABEL,
    "chart-title": TYPOGRAPHY_TOKEN_CHART_TITLE,
    "chart-annotation": TYPOGRAPHY_TOKEN_CHART_ANNOTATION,
}


# =============================================================================
# Helper Functions
# =============================================================================


def get_typography_token(token_name: str) -> TypographyToken:
    """
    Retrieve typography token by name.

    Args:
      token_name: Token identifier (e.g., "body-primary")

    Returns:
      TypographyToken instance

    Raises:
      KeyError: If token_name not found in registry
    """
    if token_name not in TYPOGRAPHY_TOKENS_REGISTRY:
        raise KeyError(
            f"Typography token '{token_name}' not found. Available tokens: "
            f"{', '.join(sorted(TYPOGRAPHY_TOKENS_REGISTRY.keys()))}"
        )
    return TYPOGRAPHY_TOKENS_REGISTRY[token_name]


def get_all_typography_tokens() -> Dict[str, TypographyToken]:
    """
    Retrieve all typography tokens in registry.

    Returns:
      Dict of all tokens, keyed by name
    """
    return dict(TYPOGRAPHY_TOKENS_REGISTRY)


def validate_typography_token(token: TypographyToken) -> bool:
    """
    Validate typography token definition.

    Args:
      token: TypographyToken to validate

    Returns:
      True if valid, raises ValueError otherwise

    Raises:
      ValueError: If token violates constraints
    """
    # Font size constraint: 8-20pt
    if not (8 <= token.font_size_pt <= 20):
        raise ValueError(f"Font size {token.font_size_pt}pt outside 8-20pt range")

    # Font weight constraint: 400, 600, or 700
    if token.font_weight not in (400, 600, 700):
        raise ValueError(
            f"Font weight {token.font_weight} not in allowed (400, 600, 700)"
        )

    # Line height constraint: 1.2-1.5
    if not (1.2 <= token.line_height <= 1.5):
        raise ValueError(f"Line height {token.line_height} outside 1.2-1.5 range")

    # Margin constraint: non-negative
    if token.margin_top_pt < 0 or token.margin_bottom_pt < 0:
        raise ValueError("Margins must be non-negative")

    # Letter spacing constraint: -1 to +2 px
    if not (-1 <= token.letter_spacing_px <= 2):
        raise ValueError(
            f"Letter spacing {token.letter_spacing_px}px outside -1 to +2px range"
        )

    return True


# =============================================================================
# CSS Generation Functions
# =============================================================================


def generate_typography_css_rule(token: TypographyToken, selector: str) -> str:
    """
    Generate CSS rule for typography token.

    Args:
      token: TypographyToken to convert
      selector: CSS selector (e.g., ".report-title", "h1")

    Returns:
      CSS rule as string
    """
    return token.to_css_string(selector)


def generate_typography_css_stylesheet() -> str:
    """
    Generate complete CSS stylesheet for all typography tokens.

    Returns:
      CSS stylesheet as string (ready for inline <style> tag)
    """
    css_lines = []
    for token_name, token in sorted(TYPOGRAPHY_TOKENS_REGISTRY.items()):
        # Generate selector from token name (.report-title, .body-primary, etc.)
        selector = f".typography-{token_name}"
        css_rule = generate_typography_css_rule(token, selector)
        css_lines.append(css_rule)
    return "\n".join(css_lines)
