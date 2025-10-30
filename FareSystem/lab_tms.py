from flask import current_app as app, request
from flask import jsonify
import fms
from team import Team
from params import MODE, OperatingMode

@app.route("/Lab/AddTeam/<int:team>", methods=["GET"])
def lab_add_team(team: int):
    if MODE is not OperatingMode.LAB:
        return "Adding teams allowed only in LAB mode", 403
    with fms.mutex:
        if team in fms.teams:
            return f"Team {team} already exists", 409
        fms.teams[team] = Team(team)
    return f"Team {team} added", 200

@app.route("/Lab/RemoveTeam/<int:team>", methods=["GET"])
def lab_remove_team(team: int):
    if MODE is not OperatingMode.LAB:
        return "Removing teams allowed only in LAB mode", 403
    with fms.mutex:
        if team not in fms.teams:
            return f"Team {team} not found", 404
        del fms.teams[team]
    return f"Team {team} removed", 200

@app.route("/Lab/ConfigMatch", methods=["POST"])
def lab_config_match():
    if MODE is not OperatingMode.LAB:
        return "Config allowed only in LAB mode", 403
    data = request.get_json(silent=True) or {}
    try:
        number = int(data.get("number", 0))
        duration = int(data.get("duration", 0))
    except Exception:
        return "Invalid payload", 400
    fms.config_match(number, duration)
    return "OK", 200

@app.route("/Lab/StartMatch", methods=["POST"])
def lab_start_match():
    if MODE is not OperatingMode.LAB:
        return "Start allowed only in LAB mode", 403
    fms.start_match()
    return "OK", 200
