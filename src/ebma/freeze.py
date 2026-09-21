from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ebma import V_VERSION
from ebma.atoms import Audience


def freeze(audience: Audience, theta: dict[str, Any], dest_root: Path) -> Path:
    dest = dest_root / audience.arm / audience.audience_id
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "ast.json").write_text(json.dumps(audience.to_ast(), indent=2), encoding="utf-8")
    (dest / "theta.json").write_text(json.dumps(theta, indent=2), encoding="utf-8")
    (dest / "V_version.txt").write_text(V_VERSION + "\n", encoding="utf-8")
    return dest
