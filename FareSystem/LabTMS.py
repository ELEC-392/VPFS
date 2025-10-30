import fms
from team import Team
from flask import current_app as app, request

IDK = "IDK"

fms.teams.clear()

@app.route("/Lab/AddTeam/<int:team>")
def serve_add_team(team: int):
    with fms.mutex:
        if team in fms.teams:
            return f"Already have team {team}"
        fms.teams[team] = Team(team)
        return f"Added team {team}"

@app.route("/Lab/RemoveTeam/<int:team>")
def serve_remove_team(team: int):
    with fms.mutex:
        if team in fms.teams:
            fms.teams.pop(team)
            return f"Removed team {team}"
        return f"No team {team} to remove"

@app.route("/Lab/ConfigMatch", methods=["post"])
def serve_config_match():
    num = request.json["number"]
    duration = request.json["duration"]
    fms.cancel_match()
    fms.config_match(num, duration)
    return ""

@app.route("/Lab/StartMatch", methods=["post"])
def serve_start_match():
    fms.start_match()
    return ""
