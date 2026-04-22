import json
from pathlib import Path


class SymbolMappingError(Exception):
    """Raised when symbol mapping cannot be loaded."""


class SymbolMapping:
    def __init__(self, mapping_path: str) -> None:
        self._mapping_path = Path(mapping_path)
        self._mapping = self._load()

    def map_symbol(self, symbol_name: str) -> str:
        return self._mapping.get(symbol_name.strip().upper(), symbol_name)

    def _load(self) -> dict[str, str]:
        if not self._mapping_path.exists():
            raise SymbolMappingError(f"Symbol mapping file not found: {self._mapping_path}")
        try:
            raw = json.loads(self._mapping_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SymbolMappingError(
                f"Invalid JSON in symbol mapping file '{self._mapping_path}'."
            ) from exc

        if not isinstance(raw, dict):
            raise SymbolMappingError(
                f"Symbol mapping file '{self._mapping_path}' must contain a JSON object."
            )

        mapping: dict[str, str] = {}
        for source_symbol, target_symbol in raw.items():
            source = str(source_symbol).strip().upper()
            target = str(target_symbol).strip()
            if not source or not target:
                raise SymbolMappingError(
                    "Symbol mapping keys and values must be non-empty strings."
                )
            mapping[source] = target
        return mapping
