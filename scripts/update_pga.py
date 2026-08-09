import json
import urllib.request
from datetime import datetime, timezone

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"

OUTPUT_FILE = "site/pga.json"


def fetch_espn():
    request = urllib.request.Request(
        ESPN_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_current_event(data):
    events = data.get("events", [])

    if not events:
        return None

    # ESPN normally puts the current/recent tournament here.
    # Prefer an event that is currently underway.
    for event in events:
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", {})
        state = status.get("type", {}).get("state")

        if state == "in":
            return event

    # If nothing is currently live, use the first event.
    return events[0]


def get_player_data(competitor):
    athlete = competitor.get("athlete", {})

    name = athlete.get("fullName", "")
    score = competitor.get("score", "")

    # Current round / holes completed
    linescores = competitor.get("linescores", [])

    thru = 0
    current_round = None

    if linescores:
        current_round = linescores[-1]
        round_holes = current_round.get("linescores", [])

        if round_holes:
            thru = len(round_holes)

    # ESPN's "order" is its leaderboard ordering.
    position = competitor.get("order")

    # Convert score to an integer when possible
    score_value = None

    if score:
        try:
            score_value = int(score.replace("+", ""))
        except ValueError:
            score_value = score

    return {
        "name": name,
        "position": position,
        "score": score_value,
        "thru": thru,
    }


def main():
    data = fetch_espn()

    event = get_current_event(data)

    if event is None:
        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "tournament": None,
            "status": "NO_EVENT",
            "players": []
        }

    else:
        competition = event.get("competitions", [{}])[0]

        competitors = competition.get("competitors", [])

        players = [
            get_player_data(player)
            for player in competitors
        ]

        # Keep the leaderboard order ESPN gives us
        players = [
            player for player in players
            if player["name"]
        ]

        status = competition.get("status", {})
        status_type = status.get("type", {})

        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "tournament": event.get("name"),
            "status": status_type.get("description", ""),
            "players": players
        }

    # Make sure the output directory exists
    import os
    os.makedirs("site", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
