"""Authentication helpers for VPFS.

Resolves a team number from a provided code based on operating mode:
- match: validate the code against an internal mapping (_authCodes).
- lab/home: interpret the input as a team number string.
Returns -1 on failure.
"""

_authCodes: dict[str : int] = {
    "asdf" : 7
}

def authenticate(code: str, mode: str) -> int:
    """
    Get the team corresponding to a given authentication code
    :param code: Provided authentication code
    :param mode: Server operating mode
    :returns: Corresponding team number, or -1 if not found
    """

    # For match mode, check against auth code dict
    if mode == "match":
        if code in _authCodes:
            return _authCodes[code]
        else:
            return -1
    # For home and lab modes don't need auth codes
    else:
        try:
            return int(code)
        except ValueError as e:
            print(f"Expected team number, not code {code}")
            return -1
