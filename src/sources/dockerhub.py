import json
import pathlib
import requests

def decode_hub_data(pool_or_text):
    pool = pool_or_text if isinstance(pool_or_text, list) else json.loads(pool_or_text)

    def at(idx: int):
        return pool[idx if idx >= 0 else len(pool) + idx]

    def key_name_from_idx(idx: int) -> str:
        k = decode_node(at(idx))
        return k if isinstance(k, str) else str(k)

    def decode_value(val):
        if isinstance(val, int):
            return decode_node(at(val))
        if isinstance(val, list):
            return [decode_value(x) for x in val]
        if isinstance(val, dict):
            return { (key_name_from_idx(int(k[1:])) if isinstance(k, str) and k.startswith("_") and k[1:].isdigit() else k)
                     : decode_value(v)
                     for k, v in val.items() }
        return val

    def decode_node(node):
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if isinstance(k, str) and k.startswith("_") and k[1:].isdigit():
                    real_key = key_name_from_idx(int(k[1:]))
                    out[real_key] = decode_value(v)
                else:
                    out[k] = decode_value(v)
            return out
        if isinstance(node, list):
            return [decode_value(x) for x in node]
        return node
    return [decode_node(entry) for entry in pool]

def dockerhub_source():
    response = requests.get("https://hub.docker.com/search.data?sort=updated_at&order=desc")
    if response.status_code == 200:
        decoded_data = decode_hub_data(response.text)
        print(decoded_data)
