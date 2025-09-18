import json
import pathlib
from typing import Any, Union, List, Dict


# https://hub.docker.com/search.data?sort=updated_at&order=desc

def decode_hub_data(pool_or_text: Union[str, List[Any]]) -> List[Any]:
    pool: List[Any] = pool_or_text if isinstance(pool_or_text, list) else json.loads(pool_or_text)

    def at(idx: int) -> Any:
        # Negative indexes count from the end (adjust if your blob uses relative backrefs)
        return pool[idx if idx >= 0 else len(pool) + idx]

    def key_name_from_idx(idx: int) -> str:
        k = decode_node(at(idx))  # key name is in the pool; decode as a node (no extra deref on ints)
        return k if isinstance(k, str) else str(k)

    def decode_value(val: Any) -> Any:
        """Decode a value that appears *inside* an object/array.
        Integers here are POINTERS -> ONE deref, then decode_node."""
        if isinstance(val, int):
            return decode_node(at(val))  # one hop
        if isinstance(val, list):
            return [decode_value(x) for x in val]
        if isinstance(val, dict):
            return { (key_name_from_idx(int(k[1:])) if isinstance(k, str) and k.startswith("_") and k[1:].isdigit() else k)
                     : decode_value(v)
                     for k, v in val.items() }
        return val  # primitive literal

    def decode_node(node: Any) -> Any:
        """Decode something we already fetched from the pool.
        Integers here are *literals* (no deref)."""
        if isinstance(node, dict):
            out: Dict[str, Any] = {}
            for k, v in node.items():
                if isinstance(k, str) and k.startswith("_") and k[1:].isdigit():
                    real_key = key_name_from_idx(int(k[1:]))
                    out[real_key] = decode_value(v)
                else:
                    out[k] = decode_value(v)
            return out
        if isinstance(node, list):
            return [decode_value(x) for x in node]
        # primitives (including int) are literals at node level
        return node

    # materialize entire pool so you can index into decoded objects by position later
    return [decode_node(entry) for entry in pool]


p = pathlib.Path("hub_search_data.json")
blob = p.read_text(encoding="utf-8")
decoded = decode_hub_data(json.loads(blob))
print(decoded)
