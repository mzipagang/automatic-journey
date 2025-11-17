def deep_merge(d1, d2):
    result = d1.copy()
    for key in d2:
        if key in result and isinstance(result[key], dict) and isinstance(d2[key], dict):
            result[key] = deep_merge(result[key], d2[key])
        else:
            result[key] = d2[key]
    return result