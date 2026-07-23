from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CatalogBundle:
    log_sources: dict[str, Any]
    detection_dependencies: dict[str, Any]
    investigation_questions: dict[str, Any]
    measurements: dict[str, Any]
    source_volumes: dict[str, Any]
    pricing: dict[str, Any]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def package_data_root() -> Path:
    return Path(__file__).resolve().parent / "data"


def load_catalog_bundle(root: Path | None = None) -> CatalogBundle:
    base = root if root is not None else package_data_root()
    return CatalogBundle(
        log_sources=load_restricted_yaml(base / "catalog" / "log_sources.yaml"),
        detection_dependencies=load_restricted_yaml(
            base / "catalog" / "detection_dependencies.yaml"
        ),
        investigation_questions=load_restricted_yaml(
            base / "catalog" / "investigation_questions.yaml"
        ),
        measurements=load_restricted_yaml(
            base / "measurements" / "detfuzz_lab_measurements.yaml"
        ),
        source_volumes=load_restricted_yaml(
            base / "measurements" / "source_volumes_lab_sample.yaml"
        ),
        pricing=load_restricted_yaml(
            base / "pricing" / "microsoft_sentinel_eastus_2026-07-23.yaml"
        ),
    )


def load_restricted_yaml(path: Path) -> dict[str, Any]:
    """Parse the small YAML subset used by SignalBudget catalogs."""
    result: dict[str, Any] = {}
    current_list_name: str | None = None
    current_item: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and stripped.endswith(":"):
            current_list_name = stripped[:-1]
            result[current_list_name] = []
            current_item = None
            continue

        if indent == 0:
            key, value = _split_key_value(stripped)
            result[key] = _parse_scalar(value)
            current_list_name = None
            current_item = None
            continue

        if indent == 2 and stripped.startswith("- "):
            if current_list_name is None:
                raise ValueError(f"list item outside list in {path}: {raw_line}")
            current_item = {}
            result[current_list_name].append(current_item)
            remainder = stripped[2:]
            if remainder:
                key, value = _split_key_value(remainder)
                current_item[key] = _parse_scalar(value)
            continue

        if indent == 4 and current_item is not None:
            key, value = _split_key_value(stripped)
            current_item[key] = _parse_scalar(value)
            continue

        raise ValueError(f"unsupported YAML shape in {path}: {raw_line}")

    return result


def _strip_comment(line: str) -> str:
    in_quote = False
    quote_char = ""
    for index, character in enumerate(line):
        if character in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = character
            elif quote_char == character:
                in_quote = False
        if character == "#" and not in_quote:
            return line[:index]
    return line


def _split_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"expected key/value pair: {text}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> Any:
    if value == "":
        return None
    if value == "null":
        return None
    if value in {"true", "false"}:
        return value == "true"
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in _split_inline_list_items(inner)]
    if (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _split_inline_list_items(value: str) -> list[str]:
    items: list[str] = []
    in_quote = False
    quote_char = ""
    start = 0

    for index, character in enumerate(value):
        if character in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = character
            elif quote_char == character:
                in_quote = False
            continue

        if character == "," and not in_quote:
            item = value[start:index].strip()
            if not item:
                raise ValueError(f"empty item in inline list: [{value}]")
            items.append(item)
            start = index + 1

    if in_quote:
        raise ValueError(f"unterminated quote in inline list: [{value}]")

    item = value[start:].strip()
    if not item:
        raise ValueError(f"empty item in inline list: [{value}]")
    items.append(item)
    return items
