"""Preserved schema support and observed-parent routing; no predictive model."""
import numpy as np

def _options(schema, name):
    item = schema["items"][name]
    return list(item["values"]) + ([schema["gated_value"]] if item.get("gate") else [])

def _route(frame, schema, names, train, query, outputs):
    # Hard routing requires an observed GIVEN parent and reliable current TRAIN.
    contexts = [
        name for name, item in schema["items"].items()
        if item["class"] == "GIVEN"
        and ("country" in name.lower() or name.lower() in ("wave", "round"))
    ]
    keys = list(zip(*(frame[c].to_numpy() for c in contexts))) if contexts else [()] * len(frame)
    mapping, codes = {}, []
    for key in keys:
        if key not in mapping:
            mapping[key] = len(mapping)
        codes.append(mapping[key])
    codes = np.asarray(codes, dtype=np.int64)
    for t, name in enumerate(names):
        gate = schema["items"][name].get("gate")
        if not gate or gate["parent"] not in frame.columns:
            continue
        parent = gate["parent"]
        if schema["items"][parent]["class"] != "GIVEN":
            continue
        eligible = frame[parent].isin(gate["observed_if"]).to_numpy()
        known = frame[parent].isin(_options(schema, parent)).to_numpy()
        off = train[known[train] & ~eligible[train]]
        support = np.bincount(codes[off], minlength=len(mapping))
        contradictions = np.bincount(
            codes[off],
            weights=(frame[name].to_numpy()[off] != schema["gated_value"]),
            minlength=len(mapping),
        )
        reliable = (support >= 10) & (contradictions == 0)
        use = known[query] & ~eligible[query] & reliable[codes[query]]
        outputs[t][use] = 0
        outputs[t][use, -1] = 1
