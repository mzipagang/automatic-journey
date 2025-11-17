from jwt import encode


def encode_dict_as_jwt(data: dict, secret: str = "", algorithm: str = "HS256") -> str:
    return encode(data, secret, algorithm=algorithm)
