"""
Serializers and deserializers for different data types in TauseStack storage module.
Includes support for text, JSON, binary and DataFrame (pandas).
"""
import json
from typing import Any

try:
    import pandas as pd
except ImportError:
    pd = None

# Text

def serialize_text(data: str) -> bytes:
    """Serialize text to bytes using UTF-8 encoding."""
    return data.encode("utf-8")

def deserialize_text(data: bytes) -> str:
    """Deserialize bytes to text using UTF-8 encoding."""
    return data.decode("utf-8")

# JSON

def serialize_json(obj: Any) -> bytes:
    """Serialize any JSON-serializable object to bytes."""
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")

def deserialize_json(data: bytes) -> Any:
    """Deserialize bytes to a JSON object."""
    return json.loads(data.decode("utf-8"))

# Binary (passthrough)

def serialize_bytes(data: bytes) -> bytes:
    """Serialize bytes (passthrough)."""
    return data

def deserialize_bytes(data: bytes) -> bytes:
    """Deserialize bytes (passthrough)."""
    return data

# DataFrame (pandas, CSV)

def serialize_dataframe(df: "pd.DataFrame") -> bytes:
    """Serialize pandas DataFrame to CSV bytes."""
    if pd is None:
        raise ImportError("pandas is not installed")
    return df.to_csv(index=False).encode("utf-8")

def deserialize_dataframe(data: bytes) -> "pd.DataFrame":
    """Deserialize CSV bytes to pandas DataFrame."""
    if pd is None:
        raise ImportError("pandas is not installed")
    from io import StringIO
    return pd.read_csv(StringIO(data.decode("utf-8"))) 