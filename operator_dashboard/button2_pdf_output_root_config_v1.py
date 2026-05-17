"""
Button 2 PDF Output Root Configuration (v1)
--------------------------------------------
Provides the safe, server-controlled output path facility for Button 2 PDFs.

Public API
----------
OutputRootNotConfiguredError  – env var absent or empty
OutputRootInvalidError        – env var present but not an absolute path
FightKeyInvalidError          – fight_key fails character/length validation
PathTraversalError            – resolved path escapes configured root

get_pdf_output_root()         – read + validate BUTTON2_PDF_OUTPUT_ROOT
resolve_pdf_output_path(key)  – build safe absolute PDF output path

Governance
----------
- Output location is server-controlled (env var only).
- Users never supply a path or filename component.
- No file I/O is performed here; path resolution only.
- No default is substituted when the env var is absent.
"""

import os
import re

# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class OutputRootNotConfiguredError(ValueError):
    """BUTTON2_PDF_OUTPUT_ROOT env var is absent or empty."""


class OutputRootInvalidError(ValueError):
    """BUTTON2_PDF_OUTPUT_ROOT is set but is not an absolute path."""


class FightKeyInvalidError(ValueError):
    """fight_key fails the character allowlist or length constraint."""


class PathTraversalError(ValueError):
    """Resolved output path escapes the configured output root."""


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_ENV_VAR = "BUTTON2_PDF_OUTPUT_ROOT"

# Allowlist: lowercase and uppercase letters, digits, hyphen, underscore.
# No path separators, dots, colons, spaces, or unicode.
_FIGHT_KEY_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_FIGHT_KEY_MAX_LEN = 200


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_fight_key(fight_key: str) -> None:
    """Raise FightKeyInvalidError if fight_key does not pass all safety checks."""
    if not isinstance(fight_key, str) or not fight_key.strip():
        raise FightKeyInvalidError(
            "fight_key must be a non-empty string"
        )
    if len(fight_key) > _FIGHT_KEY_MAX_LEN:
        raise FightKeyInvalidError(
            f"fight_key exceeds maximum length of {_FIGHT_KEY_MAX_LEN} characters"
        )
    if not _FIGHT_KEY_RE.match(fight_key):
        raise FightKeyInvalidError(
            "fight_key contains characters outside the allowed set [a-zA-Z0-9_-]"
        )
    # Basename safety: ensure fight_key alone cannot introduce a path component.
    if os.path.basename(fight_key) != fight_key:
        raise FightKeyInvalidError(
            "fight_key failed basename safety check"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_pdf_output_root() -> str:
    """Read and validate the BUTTON2_PDF_OUTPUT_ROOT environment variable.

    Returns the configured root path string (absolute).
    Does NOT verify that the directory exists.

    Raises
    ------
    OutputRootNotConfiguredError  – env var is absent or empty/whitespace
    OutputRootInvalidError        – env var is set but is not an absolute path
    """
    raw = os.environ.get(_ENV_VAR, "")
    if not raw or not raw.strip():
        raise OutputRootNotConfiguredError(
            f"{_ENV_VAR} is not configured. "
            "Set this environment variable to the absolute path of the PDF output directory."
        )
    root = raw.strip()
    if not os.path.isabs(root):
        raise OutputRootInvalidError(
            f"{_ENV_VAR} must be an absolute path; got: {root!r}"
        )
    return root


def resolve_pdf_output_path(fight_key: str) -> str:
    """Build a safe, absolute output path for a PDF identified by fight_key.

    The output filename is always server-derived: ``{fight_key}_premium.pdf``.
    The output directory is always from ``get_pdf_output_root()``.
    Users never supply a path or filename component.

    Parameters
    ----------
    fight_key : str
        Lowercase slug identifying the fight (e.g. ``bahram_rajabzadeh_vs_donovan_wisse``).
        Must match ``[a-zA-Z0-9_-]+`` and be ≤ 200 characters.

    Returns
    -------
    str
        Canonical absolute path to the output PDF file.

    Raises
    ------
    OutputRootNotConfiguredError  – BUTTON2_PDF_OUTPUT_ROOT absent or empty
    OutputRootInvalidError        – BUTTON2_PDF_OUTPUT_ROOT is not absolute
    FightKeyInvalidError          – fight_key fails character/length validation
    PathTraversalError            – resolved path escapes the configured root
    """
    root = get_pdf_output_root()  # raises if not configured or invalid

    _validate_fight_key(fight_key)  # raises if fight_key is unsafe

    filename = fight_key + "_premium.pdf"
    candidate = os.path.join(root, filename)

    # Traversal guard: resolve symlinks and relative components, then confirm
    # the candidate is a direct child of the root.
    canonical_root = os.path.realpath(root)
    canonical_candidate = os.path.realpath(candidate)

    # The candidate must start with root + separator to be a direct child.
    if not canonical_candidate.startswith(canonical_root + os.sep):
        raise PathTraversalError(
            f"Resolved output path escapes configured root: {canonical_candidate!r}"
        )

    return canonical_candidate
