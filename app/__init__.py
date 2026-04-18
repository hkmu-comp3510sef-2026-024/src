from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application import app as app

__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from app.application import app

        return app
    raise AttributeError(name)
