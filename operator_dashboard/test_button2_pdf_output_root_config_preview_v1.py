"""
Tests: Button 2 PDF Output Root Configuration (v1)

Coverage map
------------
TestGetPdfOutputRoot          (7 tests)  – env var read + validation
TestResolvePdfOutputPath      (14 tests) – filename convention, root containment,
                                           fight_key allowlist, error propagation
TestFightKeyValidation        (11 tests) – _validate_fight_key edge cases via
                                           resolve_pdf_output_path
TestPathTraversalGuard        (3 tests)  – realpath traversal defence-in-depth
"""

import os
import pytest
from unittest.mock import patch

from operator_dashboard.button2_pdf_output_root_config_v1 import (
    OutputRootNotConfiguredError,
    OutputRootInvalidError,
    FightKeyInvalidError,
    PathTraversalError,
    get_pdf_output_root,
    resolve_pdf_output_path,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _with_root(tmp_path, fight_key):
    """Call resolve_pdf_output_path with tmp_path as the configured root."""
    with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(tmp_path)}):
        return resolve_pdf_output_path(fight_key)


# ---------------------------------------------------------------------------
# TestGetPdfOutputRoot
# ---------------------------------------------------------------------------

class TestGetPdfOutputRoot:
    def test_returns_root_when_set(self, tmp_path):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(tmp_path)}):
            result = get_pdf_output_root()
        assert result == str(tmp_path)

    def test_strips_surrounding_whitespace(self, tmp_path):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": f"  {tmp_path}  "}):
            result = get_pdf_output_root()
        assert result == str(tmp_path)

    def test_raises_when_env_var_absent(self):
        env = {k: v for k, v in os.environ.items() if k != "BUTTON2_PDF_OUTPUT_ROOT"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(OutputRootNotConfiguredError):
                get_pdf_output_root()

    def test_raises_when_env_var_empty_string(self):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": ""}):
            with pytest.raises(OutputRootNotConfiguredError):
                get_pdf_output_root()

    def test_raises_when_env_var_whitespace_only(self):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": "   "}):
            with pytest.raises(OutputRootNotConfiguredError):
                get_pdf_output_root()

    def test_raises_when_relative_path(self):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": "relative/path"}):
            with pytest.raises(OutputRootInvalidError):
                get_pdf_output_root()

    def test_raises_when_relative_path_with_dotdot(self):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": "../some/path"}):
            with pytest.raises(OutputRootInvalidError):
                get_pdf_output_root()


# ---------------------------------------------------------------------------
# TestResolvePdfOutputPath
# ---------------------------------------------------------------------------

class TestResolvePdfOutputPath:
    def test_returns_absolute_path(self, tmp_path):
        result = _with_root(tmp_path, "fighter_a_vs_fighter_b")
        assert os.path.isabs(result)

    def test_filename_ends_with_premium_pdf(self, tmp_path):
        result = _with_root(tmp_path, "fighter_a_vs_fighter_b")
        assert result.endswith("fighter_a_vs_fighter_b_premium.pdf")

    def test_path_is_under_configured_root(self, tmp_path):
        result = _with_root(tmp_path, "fighter_a_vs_fighter_b")
        assert result.startswith(str(tmp_path))

    def test_valid_key_lowercase_letters_only(self, tmp_path):
        result = _with_root(tmp_path, "alpha")
        assert "alpha_premium.pdf" in result

    def test_valid_key_with_underscores(self, tmp_path):
        result = _with_root(tmp_path, "bahram_rajabzadeh_vs_donovan_wisse")
        assert "bahram_rajabzadeh_vs_donovan_wisse_premium.pdf" in result

    def test_valid_key_with_hyphens(self, tmp_path):
        result = _with_root(tmp_path, "jiri-vs-ankalaev")
        assert "jiri-vs-ankalaev_premium.pdf" in result

    def test_valid_key_with_digits(self, tmp_path):
        result = _with_root(tmp_path, "ufc300_main_event")
        assert "ufc300_main_event_premium.pdf" in result

    def test_valid_key_max_length(self, tmp_path):
        key = "a" * 200
        result = _with_root(tmp_path, key)
        assert result.endswith(key + "_premium.pdf")

    def test_raises_not_configured_when_env_absent(self):
        env = {k: v for k, v in os.environ.items() if k != "BUTTON2_PDF_OUTPUT_ROOT"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(OutputRootNotConfiguredError):
                resolve_pdf_output_path("any_key")

    def test_raises_invalid_root_when_relative(self):
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": "relative/path"}):
            with pytest.raises(OutputRootInvalidError):
                resolve_pdf_output_path("any_key")

    def test_raises_fight_key_invalid_empty(self, tmp_path):
        with pytest.raises(FightKeyInvalidError):
            _with_root(tmp_path, "")

    def test_raises_fight_key_invalid_whitespace(self, tmp_path):
        with pytest.raises(FightKeyInvalidError):
            _with_root(tmp_path, "   ")

    def test_raises_fight_key_invalid_over_max_length(self, tmp_path):
        with pytest.raises(FightKeyInvalidError):
            _with_root(tmp_path, "a" * 201)

    def test_raises_fight_key_invalid_forward_slash(self, tmp_path):
        with pytest.raises(FightKeyInvalidError):
            _with_root(tmp_path, "fighter/evil")


# ---------------------------------------------------------------------------
# TestFightKeyValidation  (via resolve_pdf_output_path)
# ---------------------------------------------------------------------------

class TestFightKeyValidation:
    """fight_key character allowlist covers all dangerous injection points."""

    def _raises(self, tmp_path, key):
        with pytest.raises(FightKeyInvalidError):
            _with_root(tmp_path, key)

    def test_backslash_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter\\evil")

    def test_colon_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter:evil")

    def test_dotdot_rejected(self, tmp_path):
        self._raises(tmp_path, "../evil")

    def test_single_dot_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter.evil")

    def test_space_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter a vs b")

    def test_angle_bracket_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter<b>")

    def test_asterisk_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter*")

    def test_question_mark_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter?")

    def test_pipe_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter|evil")

    def test_non_ascii_unicode_rejected(self, tmp_path):
        self._raises(tmp_path, "jiří_vs_ankalaev")

    def test_null_byte_rejected(self, tmp_path):
        self._raises(tmp_path, "fighter\x00evil")


# ---------------------------------------------------------------------------
# TestPathTraversalGuard
# ---------------------------------------------------------------------------

class TestPathTraversalGuard:
    """Defence-in-depth: realpath traversal check catches any future bypass."""

    def test_normal_path_passes_guard(self, tmp_path):
        """A normal fight_key that passes allowlist also passes the traversal guard."""
        result = _with_root(tmp_path, "normal_fight_key")
        # Confirm it is inside root after realpath resolution
        canonical_root = os.path.realpath(str(tmp_path))
        canonical_result = os.path.realpath(result)
        assert canonical_result.startswith(canonical_root + os.sep)

    def test_traversal_guard_blocks_symlink_escape(self, tmp_path):
        """If somehow a fight_key produced a path outside root via symlink,
        the realpath guard catches it.

        We simulate this by patching os.path.realpath so the candidate resolves
        outside the root while the allowlist-checked key is valid.
        """
        import operator_dashboard.button2_pdf_output_root_config_v1 as mod

        root_str = str(tmp_path)
        original_realpath = os.path.realpath

        def fake_realpath(p):
            if p != root_str and "normal" in p:
                return "/evil/escape/normal_fight_key_premium.pdf"
            return original_realpath(p)

        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": root_str}):
            with patch.object(mod.os.path, "realpath", side_effect=fake_realpath):
                with pytest.raises(PathTraversalError):
                    resolve_pdf_output_path("normal_fight_key")

    def test_basename_safety_via_allowlist(self, tmp_path):
        """fight_key with path separator chars already fails allowlist before
        reaching the traversal guard — double protection."""
        with pytest.raises(FightKeyInvalidError):
            _with_root(tmp_path, "../../etc/passwd")
