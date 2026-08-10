import json
import os
from datetime import datetime, timezone

import pgatourpy


OUTPUT_FILE = "site/pga.json"


def get_current_tournament():
    schedule = pgatourpy.pga_schedule()

    # First, look for a tournament currently in progress.
    current = schedule[
        schedule["status"].astype(str).str.upper() == "IN_PROGRESS"
    ]

    if not current.empty:
        return current.iloc[0], "IN_PROGRESS"

    # If nothing is currently in progress, find the next upcoming tournament.
    upcoming = schedule[
        schedule["status"].astype(str).str.upper() == "UPCOMING"
    ]

    if not upcoming.empty:
        return upcoming.iloc[0], "UPCOMING"

    return None, "NO_EVENT"


def get_leaderboard(tournament_id):
    return pgatourpy.pga_leaderboard(tournament_id)


def clean_leaderboard(leaderboard):
    players = []

    for _, row in leaderboard.iterrows():

        player = {
            "name": str(row["display_name"]),
            "position": str(row["position"]),
            "score": str(row["total"]),
            "thru": str(row["thru"]),
            "state": str(row["player_state"])
        }

        players.append(player)

    return players


def main():

    print("Getting PGA schedule...")

    tournament, status = get_current_tournament()

    if tournament is None:

        print("No current or upcoming PGA tournament found.")

        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "tournament": None,
            "dates": None,
            "status": "NO_EVENT",
            "players": []
        }

    else:

        tournament_id = tournament["tournament_id"]
        tournament_name = tournament["tournament_name"]
        tournament_dates = tournament["display_date"]

        print(f"Tournament: {tournament_name}")
        print(f"Tournament ID: {tournament_id}")
        print(f"Tournament dates: {tournament_dates}")
        print(f"Status: {status}")

        players = []

        # Only request a leaderboard when the tournament is actually live.
        if status == "IN_PROGRESS":
            print("Getting leaderboard...")

            leaderboard = get_leaderboard(tournament_id)

            players = clean_leaderboard(leaderboard)

        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "tournament": tournament_name,
            "dates": str(tournament_dates),
            "status": status,
            "players": players
        }

    os.makedirs("site", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, separators=(",", ":"))

    print("\nGenerated:")
    print(OUTPUT_FILE)

    print("\nData:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
