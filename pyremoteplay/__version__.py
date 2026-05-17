"""Version for pyremoteplay.

Single source of truth is `pyproject.toml`; this module mirrors the values for
runtime introspection. Update both together when bumping versions.
"""
VERSION = "0.7.7"
MIN_PY_VERSION = "3.11"

if __name__ == "__main__":
    print(VERSION)
