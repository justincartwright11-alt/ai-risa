def norm_str(val):
    if isinstance(val, str):
        val = val.strip()
        if val == "":
            return None
    return val

def norm_dict(d):
    return {k: norm_str(v) for k, v in sorted(d.items())}

def norm_list(lst):
    return [norm_str(x) for x in lst]

def stable_sorted(lst):
    return sorted(lst)
