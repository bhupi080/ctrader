from pathlib import Path

import yaml


class SignalAccountMapError(Exception):
    """Raised when signal-account mapping cannot be loaded or resolved."""


class SignalAccountMap:
    def __init__(self, mapping_path: str) -> None:
        self._mapping_path = Path(mapping_path)
        self._mapping = self._load()

    def resolve_account_id(self, signal_type: str) -> int:
        normalized = signal_type.strip().upper()
        if not normalized:
            raise SignalAccountMapError("signal_type cannot be empty.")
        account_id = self._mapping.get(normalized)
        if account_id is None:
            raise SignalAccountMapError(f"Unknown signal_type '{signal_type}'.")
        return account_id

    def _load(self) -> dict[str, int]:
        if not self._mapping_path.exists():
            raise SignalAccountMapError(
                f"Signal mapping file not found: {self._mapping_path}"
            )
        try:
            raw = yaml.safe_load(self._mapping_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise SignalAccountMapError(
                f"Invalid YAML in signal mapping file '{self._mapping_path}'."
            ) from exc

        if not isinstance(raw, dict) or not raw:
            raise SignalAccountMapError(
                f"Signal mapping file '{self._mapping_path}' must contain a non-empty mapping."
            )

        mapping: dict[str, int] = {}
        for signal_type, account_id in raw.items():
            key = str(signal_type).strip().upper()
            if not key:
                raise SignalAccountMapError("Signal mapping contains an empty signal_type key.")
            try:
                value = int(account_id)
            except (TypeError, ValueError) as exc:
                raise SignalAccountMapError(
                    f"Signal '{signal_type}' must map to an integer account_id."
                ) from exc
            if value <= 0:
                raise SignalAccountMapError(
                    f"Signal '{signal_type}' must map to a positive account_id."
                )
            mapping[key] = value

        return mapping
