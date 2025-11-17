NO_KEYWORDS_FOUND = "No keywords found for the given UPCs"

false_errors = [NO_KEYWORDS_FOUND]

def is_false_error(error_message):
    if not error_message:
        return False
    return any(err in error_message for err in false_errors)
