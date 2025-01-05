import time

from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from jsonschema.exceptions import ValidationError

from Utils import Point
import FMS
from jsonschema import validate
from threading import Thread
from Auth import authenticate

app = Flask(__name__)
sock = SocketIO(app)

operatingMode = "lab"

app.app_context().push()
if operatingMode == "lab":
    import LabTMS
    LabTMS.IDK = ""

@app.route("/")
def serve_root():
    return "VPFS is alive\n"

@app.route("/match")
def serve_status():
    team = authenticate(request.args.get("auth", default=""), operatingMode)
    with FMS.mutex:
        return jsonify({
            "mode": operatingMode,
            "match": FMS.matchNum,
            "matchStart": FMS.matchRunning,
            "timeRemain": FMS.matchEndTime - time.time(),
            "inMatch": team in FMS.teams,
            "team": team,
        })

@app.route("/dashboard/teams")
def serve_teams():
    data = []
    with FMS.mutex:
        # Create list of teams with desired information
        for team in FMS.teams.values():
            data.append({
                "number": team.number,
                "money": team.money,
                "karma": team.karma,
                "currentFare": team.currentFare,
                "position": {
                    "x": team.pos.x,
                    "y": team.pos.y
                },
                "lastPosUpdate": team.lastPosUpdate
            })
    return jsonify(data)

def serve_fares(extended: bool, include_expired: bool):
    data = []
    with FMS.mutex:
        # Create copied list of data with desired information
        for idx, fare in enumerate(FMS.fares):
            if fare.isActive or include_expired:
                data.append(fare.to_json_dict(idx, extended))
        return jsonify(data)

@app.route("/dashboard/fares")
def serve_fares_dashboard():
    return serve_fares(True, True)

@app.route("/fares")
def serve_fares_normal():
    return serve_fares(False, request.args.get("all", default=False, type=lambda st: st.lower() == "true"))

@app.route("/fares/claim/<int:idx>")
def claim_fare(idx: int):
    team = authenticate(request.args.get("auth", default=""), operatingMode)
    with FMS.mutex:
        success = False
        message = ""
        if team == -1:
            message = "Authentication failed"
        elif team in FMS.teams.keys():
            if idx < len(FMS.fares):
                err = FMS.fares[idx].claim_fare(idx, FMS.teams[team])
                if err is None:
                    success = True
                else:
                    message = err
            else:
                message = f"Could not find fare with ID {id}"
        else:
            message = f"Team {team} not in this match"

        return jsonify({
            "success": success,
            "message": message
        })

@app.route("/fares/current/<int:team>")
def current_fare(team: int):
    with FMS.mutex:
        fare_dict = None
        message = ""
        if team in FMS.teams.keys():
            fare_idx = FMS.teams[team].currentFare
            if fare_idx is None:
                message = f"Team {team} does not have an active fare"
            else:
                fare = FMS.fares[fare_idx]
                fare_dict = fare.to_json_dict(fare_idx, True)
        else:
            message = f"Team {team} not in this match"

        return jsonify({
            "fare": fare_dict,
            "message": message
        })

@app.route("/whereami/<int:team>")
def whereami_get(team: int):
    point = None
    last_update : int = 0
    message = ""
    if team in FMS.teams.keys():
        team = FMS.teams[team]
        point = {
            "x": team.pos.x,
            "y": team.pos.y
        },
        last_update = team.lastPosUpdate
    else:
        message = f"Team {team} not in this match"

    return jsonify({
        "position": point,
        "last_update": last_update,
        "message": message
    })

# Socket endpoints
@sock.on("connect")
def sock_connect(auth):
    print("Connected")

@sock.on("disconnect")
def sock_disconnect():
    print("Disconnected")

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
    # Data should be JSON payload with [{team:int, x:float, y:float}]
    # Log sending address, should be whitelisted in production
    print(f"Recv whereami update from {request.remote_addr}")
    # Validate payload
    try:
        validate(json, schema=whereami_update_schema)
        for entry in json:
            team = entry['team']
            x = entry['x']
            y = entry['y']
            if team in FMS.teams.keys():
                FMS.teams[team].update_position(Point(x, y))
            else:
                print(f"Team not in match {team}")
    except ValidationError as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    Thread(target=FMS.periodic, daemon=True).start()
    sock.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)