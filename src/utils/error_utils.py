import traceback


def as_error(e: object) -> Exception:
    if isinstance(e, Exception):
        return e
    else:
        raise TypeError(f"Unknown object thrown as error: {e}")


def error_string(error: object) -> str:
    if isinstance(error, Exception):
        stack = traceback.format_exc()
        cause = f"\\n[Caused by]: {error_string(error.__cause__)}" if error.__cause__ else ""
        return f"{stack}{cause}"
    else:
        return f"Caught a non-error object: {error}"


def throw_error(msg: str):
    raise Exception(msg)