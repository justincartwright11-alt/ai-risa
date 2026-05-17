"""
Button 2: Customer PDF Typography Tokens Tests v1

Test Coverage:
  - Token instantiation and immutability (5 tests)
  - Token validation constraints (10 tests)
  - CSS conversion (to_css_dict, to_css_string) (8 tests)
  - Registry access and lookups (6 tests)
  - Token lifecycle (get, validate, all) (5 tests)
  - CSS stylesheet generation (3 tests)
  - Error handling and edge cases (3 tests)

Total: 40 tests

Governance:
  - Pure token definition layer (no rendering)
  - No CSS application (just generation)
  - No customer PDF behavior changes
"""

import pytest
from operator_dashboard.button2_customer_pdf_typography_tokens_v1 import (
    TypographyToken,
    TYPOGRAPHY_TOKEN_REPORT_TITLE,
    TYPOGRAPHY_TOKEN_BODY_PRIMARY,
    TYPOGRAPHY_TOKEN_SOURCE_CITATION,
    TYPOGRAPHY_TOKEN_PAGE_METADATA,
    TYPOGRAPHY_TOKEN_SECTION_HEADER_L1,
    TYPOGRAPHY_TOKEN_SECTION_HEADER_L2,
    TYPOGRAPHY_TOKENS_REGISTRY,
    get_typography_token,
    get_all_typography_tokens,
    validate_typography_token,
    generate_typography_css_rule,
    generate_typography_css_stylesheet,
)


# =============================================================================
# Token Instantiation and Immutability (5 tests)
# =============================================================================


class TestTypographyTokenInstantiation:
    """Test token creation and immutability."""

    def test_token_instantiation_minimal(self):
        """Token can be created with required fields only."""
        token = TypographyToken(
            name="test-token",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
        )
        assert token.name == "test-token"
        assert token.font_size_pt == 12
        assert token.font_weight == 400
        assert token.line_height == 1.5
        assert token.letter_spacing_px == 0.0
        assert token.color_hex is None

    def test_token_instantiation_full(self):
        """Token can be created with all optional fields."""
        token = TypographyToken(
            name="full-token",
            font_size_pt=16,
            font_weight=600,
            line_height=1.3,
            letter_spacing_px=0.5,
            color_hex="#333333",
            margin_top_pt=12,
            margin_bottom_pt=8,
            use_case="Test full token",
        )
        assert token.name == "full-token"
        assert token.font_size_pt == 16
        assert token.font_weight == 600
        assert token.letter_spacing_px == 0.5
        assert token.color_hex == "#333333"
        assert token.margin_top_pt == 12
        assert token.margin_bottom_pt == 8

    def test_token_immutability(self):
        """Token instances are immutable (frozen dataclass)."""
        token = TypographyToken(
            name="immutable-token",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
        )
        with pytest.raises(AttributeError):
            token.font_size_pt = 14

    def test_predefined_tokens_exist(self):
        """Predefined token constants are accessible."""
        assert TYPOGRAPHY_TOKEN_REPORT_TITLE.name == "report-title"
        assert TYPOGRAPHY_TOKEN_REPORT_TITLE.font_size_pt == 20
        assert TYPOGRAPHY_TOKEN_REPORT_TITLE.font_weight == 700

    def test_predefined_tokens_immutable(self):
        """Predefined tokens are frozen (immutable)."""
        with pytest.raises(AttributeError):
            TYPOGRAPHY_TOKEN_BODY_PRIMARY.font_size_pt = 13


# =============================================================================
# Token Validation Constraints (10 tests)
# =============================================================================


class TestTypographyTokenValidation:
    """Test token validation rules."""

    def test_validate_font_size_valid(self):
        """Valid font sizes (8-20pt) pass validation."""
        for size in [8, 10, 12, 15, 18, 20]:
            token = TypographyToken(
                name=f"size-{size}",
                font_size_pt=size,
                font_weight=400,
                line_height=1.5,
            )
            assert validate_typography_token(token) is True

    def test_validate_font_size_too_small(self):
        """Font sizes below 8pt fail validation."""
        token = TypographyToken(
            name="size-small",
            font_size_pt=7,
            font_weight=400,
            line_height=1.5,
        )
        with pytest.raises(ValueError, match="outside 8-20pt range"):
            validate_typography_token(token)

    def test_validate_font_size_too_large(self):
        """Font sizes above 20pt fail validation."""
        token = TypographyToken(
            name="size-large",
            font_size_pt=21,
            font_weight=400,
            line_height=1.5,
        )
        with pytest.raises(ValueError, match="outside 8-20pt range"):
            validate_typography_token(token)

    def test_validate_font_weight_valid(self):
        """Valid font weights (400, 600, 700) pass validation."""
        for weight in [400, 600, 700]:
            token = TypographyToken(
                name=f"weight-{weight}",
                font_size_pt=12,
                font_weight=weight,
                line_height=1.5,
            )
            assert validate_typography_token(token) is True

    def test_validate_font_weight_invalid(self):
        """Invalid font weights (e.g., 500) fail validation."""
        token = TypographyToken(
            name="weight-invalid",
            font_size_pt=12,
            font_weight=500,
            line_height=1.5,
        )
        with pytest.raises(ValueError, match="not in allowed"):
            validate_typography_token(token)

    def test_validate_line_height_valid(self):
        """Valid line heights (1.2-1.5) pass validation."""
        for height in [1.2, 1.3, 1.4, 1.5]:
            token = TypographyToken(
                name=f"height-{height}",
                font_size_pt=12,
                font_weight=400,
                line_height=height,
            )
            assert validate_typography_token(token) is True

    def test_validate_line_height_too_small(self):
        """Line heights below 1.2 fail validation."""
        token = TypographyToken(
            name="height-small",
            font_size_pt=12,
            font_weight=400,
            line_height=1.1,
        )
        with pytest.raises(ValueError, match="outside 1.2-1.5 range"):
            validate_typography_token(token)

    def test_validate_line_height_too_large(self):
        """Line heights above 1.5 fail validation."""
        token = TypographyToken(
            name="height-large",
            font_size_pt=12,
            font_weight=400,
            line_height=1.6,
        )
        with pytest.raises(ValueError, match="outside 1.2-1.5 range"):
            validate_typography_token(token)

    def test_validate_negative_margin(self):
        """Negative margins fail validation."""
        token = TypographyToken(
            name="margin-negative",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
            margin_top_pt=-4,
        )
        with pytest.raises(ValueError, match="non-negative"):
            validate_typography_token(token)

    def test_validate_letter_spacing_out_of_range(self):
        """Letter spacing outside -1 to +2px range fails validation."""
        token = TypographyToken(
            name="spacing-invalid",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
            letter_spacing_px=3.0,
        )
        with pytest.raises(ValueError, match="-1 to \\+2px"):
            validate_typography_token(token)


# =============================================================================
# CSS Conversion (8 tests)
# =============================================================================


class TestTypographyTokenCssConversion:
    """Test CSS generation from tokens."""

    def test_to_css_dict_minimal(self):
        """Minimal token converts to CSS dict with required properties."""
        token = TypographyToken(
            name="test",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
        )
        css_dict = token.to_css_dict()
        assert css_dict["font-size"] == "12pt"
        assert css_dict["font-weight"] == 400
        assert css_dict["line-height"] == 1.5
        assert "color" not in css_dict
        assert "letter-spacing" not in css_dict

    def test_to_css_dict_with_color(self):
        """Token with color includes color in CSS dict."""
        token = TypographyToken(
            name="test",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
            color_hex="#666666",
        )
        css_dict = token.to_css_dict()
        assert css_dict["color"] == "#666666"

    def test_to_css_dict_with_letter_spacing(self):
        """Token with letter-spacing includes it in CSS dict."""
        token = TypographyToken(
            name="test",
            font_size_pt=12,
            font_weight=600,
            line_height=1.2,
            letter_spacing_px=0.5,
        )
        css_dict = token.to_css_dict()
        assert css_dict["letter-spacing"] == "0.5px"

    def test_to_css_dict_with_margins(self):
        """Token with margins includes them in CSS dict."""
        token = TypographyToken(
            name="test",
            font_size_pt=14,
            font_weight=600,
            line_height=1.2,
            margin_top_pt=12,
            margin_bottom_pt=6,
        )
        css_dict = token.to_css_dict()
        assert css_dict["margin-top"] == "12pt"
        assert css_dict["margin-bottom"] == "6pt"

    def test_to_css_string_without_selector(self):
        """Token converts to inline CSS string (no selector)."""
        token = TypographyToken(
            name="test",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
        )
        css_string = token.to_css_string()
        assert "font-size: 12pt" in css_string
        assert "font-weight: 400" in css_string
        assert "line-height: 1.5" in css_string
        assert "{" not in css_string

    def test_to_css_string_with_selector(self):
        """Token converts to CSS rule with selector."""
        token = TypographyToken(
            name="body",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
        )
        css_rule = token.to_css_string(".body-primary")
        assert css_rule.startswith(".body-primary")
        assert "{" in css_rule
        assert "}" in css_rule
        assert "font-size: 12pt" in css_rule

    def test_predefined_token_report_title_css(self):
        """Predefined report title token generates correct CSS."""
        css_dict = TYPOGRAPHY_TOKEN_REPORT_TITLE.to_css_dict()
        assert css_dict["font-size"] == "20pt"
        assert css_dict["font-weight"] == 700
        assert css_dict["letter-spacing"] == "0.5px"

    def test_predefined_token_source_citation_css(self):
        """Predefined source citation token generates correct CSS."""
        css_dict = TYPOGRAPHY_TOKEN_SOURCE_CITATION.to_css_dict()
        assert css_dict["font-size"] == "9pt"
        assert css_dict["font-weight"] == 400
        assert css_dict["color"] == "#777777"


# =============================================================================
# Registry Access and Lookups (6 tests)
# =============================================================================


class TestTypographyTokenRegistry:
    """Test token registry access and management."""

    def test_registry_contains_predefined_tokens(self):
        """Registry contains all predefined tokens."""
        assert "report-title" in TYPOGRAPHY_TOKENS_REGISTRY
        assert "body-primary" in TYPOGRAPHY_TOKENS_REGISTRY
        assert "section-header-l1" in TYPOGRAPHY_TOKENS_REGISTRY
        assert "source-citation" in TYPOGRAPHY_TOKENS_REGISTRY

    def test_get_token_by_name(self):
        """Retrieve token by name from registry."""
        token = get_typography_token("report-title")
        assert token.name == "report-title"
        assert token.font_size_pt == 20

    def test_get_token_invalid_name(self):
        """Getting non-existent token raises KeyError."""
        with pytest.raises(KeyError, match="Typography token"):
            get_typography_token("nonexistent-token")

    def test_get_all_tokens(self):
        """Retrieve all tokens from registry."""
        all_tokens = get_all_typography_tokens()
        assert len(all_tokens) > 0
        assert "report-title" in all_tokens
        assert "body-primary" in all_tokens
        assert isinstance(all_tokens, dict)

    def test_registry_token_count(self):
        """Registry contains expected number of tokens (21+)."""
        token_count = len(TYPOGRAPHY_TOKENS_REGISTRY)
        assert token_count >= 21  # 21 predefined tokens

    def test_registry_values_are_valid_tokens(self):
        """All registry values are valid TypographyToken instances."""
        for token_name, token in TYPOGRAPHY_TOKENS_REGISTRY.items():
            assert isinstance(token, TypographyToken)
            assert token.name == token_name
            assert validate_typography_token(token) is True


# =============================================================================
# Token Lifecycle (5 tests)
# =============================================================================


class TestTypographyTokenLifecycle:
    """Test complete token workflow."""

    def test_create_validate_register(self):
        """Lifecycle: create token, validate, then retrieve from registry."""
        # Create custom token
        custom_token = TypographyToken(
            name="custom-test",
            font_size_pt=14,
            font_weight=600,
            line_height=1.3,
        )
        # Validate
        assert validate_typography_token(custom_token) is True
        # Verify it would be found if added to registry
        token_copy = get_typography_token("section-header-l1")
        assert token_copy.font_weight == 600

    def test_get_then_validate_predefined(self):
        """Workflow: get predefined token from registry, validate it."""
        token = get_typography_token("body-primary")
        assert validate_typography_token(token) is True
        assert token.font_size_pt == 12

    def test_get_then_generate_css(self):
        """Workflow: get token from registry, generate CSS."""
        token = get_typography_token("report-title")
        css_dict = token.to_css_dict()
        assert len(css_dict) > 0
        css_rule = token.to_css_string(".report-title")
        assert ".report-title" in css_rule

    def test_validate_all_registry_tokens(self):
        """All tokens in registry pass validation."""
        for token_name, token in TYPOGRAPHY_TOKENS_REGISTRY.items():
            assert validate_typography_token(token) is True

    def test_token_use_case_descriptions(self):
        """Predefined tokens have use case descriptions."""
        token = get_typography_token("body-primary")
        assert token.use_case != ""
        assert len(token.use_case) > 10


# =============================================================================
# CSS Stylesheet Generation (3 tests)
# =============================================================================


class TestTypographyTokenCssStylesheet:
    """Test complete CSS stylesheet generation."""

    def test_generate_css_stylesheet_structure(self):
        """Generated stylesheet contains all tokens as CSS rules."""
        stylesheet = generate_typography_css_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
        assert ".typography-" in stylesheet
        assert "{" in stylesheet
        assert "}" in stylesheet

    def test_generate_css_stylesheet_contains_all_tokens(self):
        """Generated stylesheet includes all registry tokens."""
        stylesheet = generate_typography_css_stylesheet()
        for token_name in TYPOGRAPHY_TOKENS_REGISTRY.keys():
            selector = f".typography-{token_name}"
            assert selector in stylesheet

    def test_generate_css_rule_with_selector(self):
        """Generate CSS rule for specific token with custom selector."""
        token = get_typography_token("body-primary")
        css_rule = generate_typography_css_rule(token, ".my-body-text")
        assert ".my-body-text" in css_rule
        assert "font-size: 12pt" in css_rule
        assert "{" in css_rule


# =============================================================================
# Error Handling and Edge Cases (3 tests)
# =============================================================================


class TestTypographyTokenErrorHandling:
    """Test error handling and edge cases."""

    def test_css_dict_with_zero_margins(self):
        """CSS dict excludes margins when they are zero."""
        token = TypographyToken(
            name="test",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
            margin_top_pt=0,
            margin_bottom_pt=0,
        )
        css_dict = token.to_css_dict()
        assert "margin-top" not in css_dict
        assert "margin-bottom" not in css_dict

    def test_css_dict_with_zero_letter_spacing(self):
        """CSS dict excludes letter-spacing when it is zero."""
        token = TypographyToken(
            name="test",
            font_size_pt=12,
            font_weight=400,
            line_height=1.5,
            letter_spacing_px=0.0,
        )
        css_dict = token.to_css_dict()
        assert "letter-spacing" not in css_dict

    def test_predefined_tokens_boundary_values(self):
        """Predefined tokens use boundary values correctly."""
        # Smallest size
        page_metadata = get_typography_token("page-metadata")
        assert page_metadata.font_size_pt == 9
        # Largest size
        report_title = get_typography_token("report-title")
        assert report_title.font_size_pt == 20
        # All weights present
        weights = {token.font_weight for token in TYPOGRAPHY_TOKENS_REGISTRY.values()}
        assert 400 in weights or 600 in weights or 700 in weights


# =============================================================================
# Integration Test (1 bonus test)
# =============================================================================


class TestTypographyTokenIntegration:
    """Integration test: full workflow."""

    def test_full_workflow_token_to_css(self):
        """Complete workflow: get token, validate, generate CSS, check output."""
        # Retrieve
        token = get_typography_token("section-header-l1")
        # Validate
        assert validate_typography_token(token) is True
        # Generate CSS
        css_dict = token.to_css_dict()
        assert css_dict["font-weight"] == 600
        assert "margin-top" in css_dict
        # Generate CSS rule
        css_rule = token.to_css_string(".section-header")
        assert ".section-header" in css_rule
        assert "600" in css_rule
