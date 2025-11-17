from unittest.mock import MagicMock


def auto_mock(mock_json: dict, mock: MagicMock) -> MagicMock:
    for key, value in mock_json.items():
        if isinstance(value, dict):
            sub_mock = MagicMock()
            mock.__setattr__(key, auto_mock(value, sub_mock))
        elif isinstance(value, list):
            sub_list = [auto_mock(item, MagicMock()) for item in value]
            mock.__setattr__(key, sub_list)
        else:
            mock.__setattr__(key, value)

    return mock