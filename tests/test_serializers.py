import pytest
import json

from tausestack.sdk.storage import serializers

@pytest.mark.parametrize("text", ["hola mundo", "áéíóú üñ ç", "", "123"])
def test_serialize_deserialize_text(text):
    data = serializers.serialize_text(text)
    assert isinstance(data, bytes)
    result = serializers.deserialize_text(data)
    assert result == text

@pytest.mark.parametrize("obj", [
    {"a": 1, "b": [1,2,3]},
    [1,2,3],
    "texto",
    123,
    None
])
def test_serialize_deserialize_json(obj):
    data = serializers.serialize_json(obj)
    assert isinstance(data, bytes)
    result = serializers.deserialize_json(data)
    assert result == obj

@pytest.mark.parametrize("b", [b"hola", b"", b"\x00\x01\x02"])
def test_serialize_deserialize_bytes(b):
    data = serializers.serialize_bytes(b)
    assert data == b
    result = serializers.deserialize_bytes(data)
    assert result == b

@pytest.mark.skipif(serializers.pd is None, reason="pandas no instalado")
def test_serialize_deserialize_dataframe():
    import pandas as pd
    df = pd.DataFrame({"a": [1,2], "b": ["x", "y"]})
    data = serializers.serialize_dataframe(df)
    assert isinstance(data, bytes)
    df2 = serializers.deserialize_dataframe(data)
    pd.testing.assert_frame_equal(df, df2)
