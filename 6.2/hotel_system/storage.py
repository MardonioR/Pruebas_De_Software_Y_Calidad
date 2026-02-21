"""
storage.py
---
JSON persistence utilities with invalid-data tolerance.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class JsonStore:
    """A simple JSON file store for a list of objects."""

    path: Path

    def load_list(
        self,
        *,
        item_loader: Callable[[Dict[str, Any]], T],
        item_name: str,
    ) -> List[T]:
        """
        Load a list of items from JSON.

        Invalid file contents or invalid items are reported to console and
        skipped; execution continues (Req 5).
        """
        if not self.path.exists():
            return []

        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: Cannot read {self.path}: {exc}")
            return []

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"ERROR: Invalid JSON in {self.path}: {exc}")
            return []

        if not isinstance(data, list):
            print(f"ERROR: Expected a JSON list in {self.path}, got {type(data)}")
            return []

        items: List[T] = []
        for idx, entry in enumerate(data):
            if not isinstance(entry, dict):
                print(
                    f"ERROR: Invalid {item_name} at index {idx} in {self.path}: "
                    f"expected object, got {type(entry)}"
                )
                continue
            try:
                items.append(item_loader(entry))
            except (KeyError, TypeError, ValueError) as exc:
                print(
                    f"ERROR: Invalid {item_name} at index {idx} in {self.path}: {exc}"
                )
        return items

    def save_list(self, items: Iterable[Any]) -> None:
        """Save a list of items to JSON (pretty printed)."""
        payload = []
        for item in items:
            if hasattr(item, "to_dict"):
                payload.append(item.to_dict())
            else:
                payload.append(item)

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"ERROR: Cannot write {self.path}: {exc}")


def index_by_id(
    items: Iterable[T],
    *,
    get_id: Callable[[T], str],
) -> Dict[str, T]:
    """Build an id->object index."""
    result: Dict[str, T] = {}
    for item in items:
        result[get_id(item)] = item
    return result


def safe_get(mapping: Dict[str, T], key: str) -> Optional[T]:
    """Return mapping[key] or None."""
    return mapping.get(key)
