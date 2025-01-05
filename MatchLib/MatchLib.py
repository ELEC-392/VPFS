####################################################
#             MatchLib V1.0, 2025-01-05            #
# Helper library for watching ELEC390 match status #
####################################################
import json
import time
from urllib import request
from threading import Thread


# Server details will change between lab, home, and competition, so need to be configured by init function
_server = "unset"
_authKey = "unset"
_team = -1
_verbose = False

# Thread
_thread = None

# Poll at 200ms interval normally, but 50ms while waiting for match start
_POLL_INTERVAL_SLOW = 0.2
_POLL_INTERVAL_PREMATCH = 0.05
_poll_interval = _POLL_INTERVAL_SLOW

# Status tracking. Should only be read through accessor methods
_matchData : dict | None = None

# Accessor methods
def is_connected() -> bool:
    """
    Check if there is a good connection to VPFS
    :return: True if connected to VPFS
    """
    return _matchData is not None

def is_match_started() -> bool:
    """
    Check if the match has started
    :return: True if match has started, False if no VPFS connection
    """
    if _matchData is None:
        return False
    return _matchData["matchStart"]


def is_match_finished() -> bool:
    """
    Check if the match has finished
    :return: True if match has started and time is < 0, False if no VPFS connection
    """
    if _matchData is None:
        return False
    return is_match_started() and _matchData["timeRemain"] < 0


def is_in_match():
    """
    Check if your team is in the current/upcoming match
    :return: True if team in match, False if no VPFS connection
    """
    if _matchData is None:
        return False
    return _matchData["inMatch"]


def auth_success():
    """
    Check if your team is successfully authenticating with VPFS
    :return: True if authentication successful, False if no VPFS connection
    """
    if _matchData is None:
        return False
    return _matchData["team"] == _team

# Util Methods
def wait_for_connection():
    """
    Hang the thread until VPFS has connected
    """
    while True:
        if is_connected():
            break
        # No reason to refresh faster than the queries go out
        time.sleep(_poll_interval)

def wait_for_match():
    """
    Hang the thread until a match with your team has started
    """
    global _poll_interval
    while True:
        # Accelerate poll interval while waiting for imminent match start
        if is_in_match():
            _poll_interval = _POLL_INTERVAL_PREMATCH
        if is_in_match() and is_match_started():
            _poll_interval = _POLL_INTERVAL_SLOW
            break
        # No reason to refresh faster than the queries go out
        time.sleep(_poll_interval)


def _update_match_status() -> bool:
    global _matchData
    # Make request to match data
    res = request.urlopen(f"{_server}/match?auth={_authKey}")
    # Verify we got HTTP OK
    if res.status == 200:
        if _matchData is None:
            print("Connected to VFPS")
        # Read data to temp vars
        _matchData = json.loads(res.read())
        return True
    else:
        _matchData = None
        if _verbose:
            print("Match endpoint error")
        return False


def _main():
    while True:
        _update_match_status()

        # Make alot of noise if auth fails
        if _matchData is not None and not auth_success():
            print("Authentication error!")

        time.sleep(_poll_interval)


def init_matchlib(server: str, team: int, auth: str | None=None, verbose:bool=False):
    """
    Initialize the match utils library
    :param server: Server address, with http:// and port
    :param team: Your team number
    :param auth: Your team auth key, if set to None will use team number
    :param verbose: Option for extra debugging output
    """
    global _server, _authKey, _team, _verbose, _thread
    _server = server
    _team = team
    _authKey = auth
    if _authKey is None:
        _authKey = str(team)
    _verbose = verbose

    # Run in a separate thread so main loop can block
    _thread = Thread(target=_main, daemon=True).start()

