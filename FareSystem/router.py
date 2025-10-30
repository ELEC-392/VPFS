"""
HTTP and WebSocket API for VPFS.

- Exposes REST endpoints for status, teams, fares, and position queries.
- Accepts real-time position updates via Socket.IO.
- Uses a shared match state in `fms` guarded by `fms.mutex`.
- Authenticates teams based on operating mode via `auth.authenticate`.
"""

import time

from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from jsonschema.exceptions import ValidationError

from utils import Point
import fms
from jsonschema import validate
from threading import Thread
from auth import authenticate
from params import MODE, OperatingMode

# Create Flask app and Socket.IO wrapper
app = Flask(__name__)
sock = SocketIO(app)

# Optionally initialize lab-specific modules
app.app_context().push()
if MODE == OperatingMode.LAB:
    # Lab-only support code (import side effects, config, etc.)
    import lab_tms
    lab_tms.IDK = ""

@app.route("/")
def serve_root():
    """Health check endpoint."""
    return "VPFS is alive!\n"

@app.route("/match")
def serve_status():
    """
    Returns match/server status for the authenticated team.
    Query params:
      - auth: team code or team number depending on mode
    """
    auth_code = request.args.get("auth")  # None if missing
    team = authenticate(auth_code, MODE) if auth_code else -1

    # Update last poll time if team exists
    if team in fms.teams:
        fms.teams[team].lastStatus = time.time()

    # Return snapshot of match state (with lock)
    with fms.mutex:
        return jsonify({
            "mode": MODE.value,
            "match": fms.matchNum,
            "matchStart": fms.matchRunning,
            "timeRemain": fms.matchEndTime - time.time(),
            "inMatch": team in fms.teams,
            "team": team,
        })

@app.route("/dashboard/teams")
def serve_teams():
    """
    Returns a list of teams with money, rep, current fare, and last update times.
    Intended for dashboard/monitoring use.
    """
    data = []
    with fms.mutex:
        for team in fms.teams.values():
            data.append({
                "number": team.number,
                "money": team.money,
                "rep": team.karma,
                "currentFare": team.currentFare,
                "position": {
                    "x": team.pos.x,
                    "y": team.pos.y
                },
                "lastPosUpdate": team.lastPosUpdate,
                "lastStatus": team.lastStatus
            })
    return jsonify(data)

def serve_fares(extended: bool, include_expired: bool):
    """
    Helper to serialize fares.
    - extended: include internal fields for dashboard or current-fare views.
    - include_expired: include fares that are no longer active.
    """
    data = []
    with fms.mutex:
        for idx, fare in enumerate(fms.fares):
            if fare.isActive or include_expired:
                data.append(fare.to_json_dict(idx, extended))
        return jsonify(data)

@app.route("/dashboard/fares")
def serve_fares_dashboard():
    """Dashboard-oriented fare list (extended info, includes expired)."""
    return serve_fares(True, True)

@app.route("/fares")
def serve_fares_normal():
    """
    Client-visible fare list.
    Query params:
      - all=true|false to include expired fares.
    """
    return serve_fares(
        False,
        request.args.get("all", default=False, type=lambda st: st.lower() == "true"),
    )

@app.route("/fares/claim/<int:idx>")
def claim_fare(idx: int):
    """
    Claims a fare for the authenticated team.
    - Path: idx is the fare index.
    - Query: auth carries code/team depending on mode.
    """
    team = authenticate(request.args.get("auth", default=""), MODE)
    with fms.mutex:
        success = False
        message = ""
        if team == -1:
            message = "Authentication failed"
        elif team in fms.teams.keys():
            if idx < len(fms.fares):
                err = fms.fares[idx].claim_fare(idx, fms.teams[team])
                if err is None:
                    success = True
                else:
                    message = err
            else:
                # NOTE: likely intended to use idx, not id (built-in). Left unchanged.
                message = f"Could not find fare with ID {id}"
        else:
            message = f"Team {team} not in this match"

        return jsonify({
            "success": success,
            "message": message
        })

@app.route("/fares/current/<int:team>")
def current_fare(team: int):
    """
    Returns the currently assigned fare (with extended info) for a team number.
    """
    with fms.mutex:
        fare_dict = None
        message = ""
        if team in fms.teams.keys():
            fare_idx = fms.teams[team].currentFare
            if fare_idx is None:
                message = f"Team {team} does not have an active fare."
            else:
                fare = fms.fares[fare_idx]
                fare_dict = fare.to_json_dict(fare_idx, True)
        else:
            message = f"Team {team} not in this match."

        return jsonify({
            "fare": fare_dict,
            "message": message
        })

@app.route("/whereami/<int:team>")
def whereami_get(team: int):
    """
    Gets the last known position for a team number.
    Returns x/y coordinates and the last update timestamp.
    """
    point = None
    last_update: int = 0
    message = ""
    if team in fms.teams.keys():
        team = fms.teams[team]
        point = {
            "x": team.pos.x,
            "y": team.pos.y
        }
        last_update = team.lastPosUpdate
    else:
        message = f"Team {team} not in this match"

    return jsonify({
        "position": point,
        "last_update": last_update,
        "message": message
    })

# Socket.IO endpoints

@sock.on("connect")
def sock_connect(auth):
    """Logs when a Socket.IO client connects."""
    print("Connected")

@sock.on("disconnect")
def sock_disconnect():
    """Logs when a Socket.IO client disconnects."""
    print("Disconnected")

# JSON schema for batched position updates: [{team:int, x:float, y:float}, ...]
whereami_update_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "team": {"type": "number"},
            "x": {"type": "number"},
            "y": {"type": "number"},
        },
        "required": ["team", "x", "y"],
    },
}

@sock.on("whereami_update")
def whereami_update(json):
    """
    Receives batched position updates over Socket.IO.
    Payload: list of {team, x, y} objects. Validated by JSON Schema.
    """
    # Log sending address (consider whitelisting in production)
    print(f"Recv whereami update from {request.remote_addr}")

    try:
        validate(json, schema=whereami_update_schema)
        for entry in json:
            team = entry['team']
            x = entry['x']
            y = entry['y']
            if team in fms.teams.keys():
                fms.teams[team].update_position(Point(x, y))
            else:
                print(f"Team not in match {team}")
    except ValidationError as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    # Start background periodic task that advances match/fare state
    Thread(target=fms.periodic, daemon=True).start()
    # Start HTTP + Socket.IO server; bind to all interfaces
    sock.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)
