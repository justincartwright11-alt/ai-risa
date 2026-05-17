# Button 2 PDF Output Root Configuration — Design (v1)

**Slice:** `button2-pdf-output-root-config-design-v1`
**Date:** 2026-05-17
**Status:** LOCKED — design-only, no implementation changes

---

## Purpose

Design the safe PDF output root configuration for Button 2 before any file write
is implemented. This defines:

- How the output directory is configured (env var only, no hardcoded paths)
- How a `fight_key` becomes a safe output filename
- How path traversal and user-controlled path injection are blocked
- What errors are raised when configuration is absent or invalid

**Output location must be server-controlled. Users may not supply output paths.
No PDF writes are opened in this design slice.**

---

## The Problem Without This

Without a configured output root:
- There is no safe place to write approved PDFs
- Any inline path would be hardcoded (undeployable, fragile)
- A user-supplied path would be a path traversal vulnerability (OWASP A01)

---

## Configuration Source: Environment Variable Only

**Env var name:** `BUTTON2_PDF_OUTPUT_ROOT`

**Rules:**
- The module reads only from this env var — no config file, no hardcoded fallback
- If the var is unset or empty, any call to `resolve_pdf_output_path()` raises
  `OutputRootNotConfiguredError` (a subclass of `ValueError`)
- No default path is substituted — an absent var means the output facility is
  not configured, and a write must not proceed
- The value must be an absolute path. If it is relative, raise
  `OutputRootInvalidError`
- The directory does not need to exist at config-read time, but it must exist
  (or be creatable) before a write is attempted. Creation of the directory is
  the responsibility of the caller (the route), not this module

**Why no hardcoded default:** A default like `/tmp/reports` or
`C:\ai_risa_data\reports` would silently write PDFs to unexpected locations on
any machine without the env var set — including test environments and CI. An
explicit missing-var error makes misconfiguration visible immediately.

---

## fight_key → Safe Filename

The filename for a generated PDF is derived entirely server-side from the
`fight_key`. Users never supply a filename or path component.

**Convention:** `{fight_key}_premium.pdf`

**Validation rules for `fight_key` (locked in prerequisite discovery):**

| Rule | Detail |
|------|--------|
| Non-empty string | Reject empty or whitespace-only values |
| Character allowlist | `[a-zA-Z0-9_-]` only — reject anything else |
| No path separators | Reject `/`, `\`, `:`, `..` |
| No leading/trailing separator | Reject keys starting/ending with `-` or `_` |
| Length limit | Max 200 characters to prevent filesystem issues |
| Basename safety | `os.path.basename(fight_key) == fight_key` (final check) |

**Why allowlist over denylist:** A denylist of dangerous characters is
incomplete. An allowlist `[a-zA-Z0-9_-]` is provably safe for all major
filesystems and cannot be bypassed by encoding tricks.

---

## Path Assembly and Traversal Prevention

Assembly steps (in order):

```
1. get_pdf_output_root()
       → reads BUTTON2_PDF_OUTPUT_ROOT env var
       → validates it is a non-empty absolute path string
       → returns the root str (does not verify existence)

2. _validate_fight_key(fight_key)
       → applies character allowlist + length check
       → raises FightKeyInvalidError on failure

3. filename = fight_key + "_premium.pdf"

4. candidate = os.path.join(root, filename)

5. canonical_root = os.path.realpath(root)
   canonical_candidate = os.path.realpath(candidate)

6. if not canonical_candidate.startswith(canonical_root + os.sep):
       raise PathTraversalError
       (guard: resolved path must be a direct child of the root)

7. return canonical_candidate
```

Step 5–6 is the traversal guard. Even if `fight_key` somehow passed the
allowlist with a `..` component (which it cannot), `os.path.realpath()` would
resolve it and the `startswith` check would catch it. The guard provides
defence-in-depth.

---

## Error Hierarchy

All errors are subclasses of `ValueError` for clean catchability:

```python
class OutputRootNotConfiguredError(ValueError): ...  # env var absent or empty
class OutputRootInvalidError(ValueError): ...        # env var not absolute path
class FightKeyInvalidError(ValueError): ...          # fight_key fails allowlist/length
class PathTraversalError(ValueError): ...            # resolved path escapes root
```

Callers must catch these before proceeding to a file write.

---

## Public API

**Module location:**
```text
operator_dashboard/button2_pdf_output_root_config_v1.py
```

**Exported names:**

```python
OutputRootNotConfiguredError   # raised when BUTTON2_PDF_OUTPUT_ROOT is absent
OutputRootInvalidError         # raised when root is not an absolute path
FightKeyInvalidError           # raised when fight_key fails validation
PathTraversalError             # raised when resolved path escapes root

def get_pdf_output_root() -> str:
    """Read and validate BUTTON2_PDF_OUTPUT_ROOT env var.
    Raises OutputRootNotConfiguredError or OutputRootInvalidError on invalid config.
    Returns the root path string (absolute).
    Does not verify the directory exists."""

def resolve_pdf_output_path(fight_key: str) -> str:
    """Build a safe, absolute output path for a PDF identified by fight_key.
    Raises OutputRootNotConfiguredError, OutputRootInvalidError,
           FightKeyInvalidError, or PathTraversalError.
    Returns the canonical absolute path string."""
```

No other public names. No class definitions beyond the error types.

---

## What This Module Does NOT Do

| Excluded | Reason |
|----------|--------|
| Create the output directory | Caller's responsibility — this module is config-only |
| Write any file | Not in scope — output path resolution only |
| Read or open any file | Not in scope |
| Accept a user-supplied path | Never — path is always server-derived |
| Default to any path when env var is absent | Absent var → explicit error, no default |
| Accept relative env var values | Relative paths → `OutputRootInvalidError` |

---

## Test Coverage Required

| Test | Proof |
|------|-------|
| Env var set → `get_pdf_output_root()` returns value | Core path |
| Env var absent → `OutputRootNotConfiguredError` | Missing config |
| Env var empty string → `OutputRootNotConfiguredError` | Empty config |
| Env var whitespace-only → `OutputRootNotConfiguredError` | Whitespace config |
| Env var relative path → `OutputRootInvalidError` | Relative path rejected |
| Valid fight_key → `resolve_pdf_output_path()` returns path ending in `{fight_key}_premium.pdf` | Filename convention |
| Returned path is under configured root | Root containment |
| Empty fight_key → `FightKeyInvalidError` | Empty key |
| fight_key with `/` → `FightKeyInvalidError` | Separator rejected |
| fight_key with `\` → `FightKeyInvalidError` | Separator rejected |
| fight_key with `..` → `FightKeyInvalidError` | Traversal rejected by allowlist |
| fight_key with `<`, `>`, `*`, `?`, `:`, `"`, `\|` → `FightKeyInvalidError` | Special chars rejected |
| fight_key exceeding 200 chars → `FightKeyInvalidError` | Length limit |
| fight_key with non-ASCII → `FightKeyInvalidError` | Allowlist rejects unicode |
| `resolve_pdf_output_path` when root not configured → `OutputRootNotConfiguredError` | Propagated error |
| Traversal guard: `os.path.realpath` confirms path inside root | Defence-in-depth |

---

## Next Slice

```text
button2-pdf-output-root-config-preview-v1
```

Builds `button2_pdf_output_root_config_v1.py` and its test file per this design.
No changes to `app.py`, the render gate, the composition entry point, or any
other module are made in that slice.
