import json
import requests
import logging
logger = logging.getLogger("sly-eye")

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
    return decode_node(pool[0])

def dockerhub_source():
    url_parameters = [
        "sort=updated_at",  # most recently updated
        "order=desc",
        "_routes=root,routes/_layout.search",
        "type=image",  # only interested in images not extensions, plugins, etc.
        "page_size=100"  # max page size
    ]

    url = f"https://hub.docker.com/search.data?{'&'.join(url_parameters)}"

    logger.debug(f"Sending GET request to {url}")
    response = requests.get(url)

    if response.status_code == 200:
        decoded_data = decode_hub_data(response.text)
        return decoded_data
    
    return None
