from __future__ import annotations

import logging
import re
from typing import Iterable, List, Tuple

log = logging.getLogger("voice_by_sumanonline.dictionary")

_Pattern = Tuple[re.Pattern, str]

def compile_dictionary(pairs: Iterable[Tuple[str, str]]) -> List[_Pattern]:
    out: List[_Pattern] = []
    for find, replace in pairs:
        if not find:
            continue
        try:
            pattern = re.compile(r"\b" + re.escape(find) + r"\b", re.IGNORECASE)
        except re.error as e:
            log.warning("Skipping invalid dictionary entry %r: %s", find, e)
            continue
        out.append((pattern, replace))
    return out

def apply_dictionary(text: str, compiled: List[_Pattern]) -> str:
    for pattern, replacement in compiled:
        text = pattern.sub(replacement, text)
    return text
