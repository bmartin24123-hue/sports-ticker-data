import json
import os
from datetime import datetime, timezone

import pgatourpy


OUTPUT_FILE = "site/pga.json"


def get_current_tournament():
    schedule = pgatourpy.pga_schedule()

    current = schedule[
        schedule["status"].str.upper() == "IN_PROGRESS"
    ]

    if current.empty:
        return None

    return current.iloc[0]


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

    tournament = get_current_tournament()

    if tournament is None:

        print("No PGA tournament is currently in progress.")

        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "tournament": None,
            "status": "NO_EVENT",
            "players": []
        }

    else:

        tournament_id = tournament["tournament_id"]
        tournament_name = tournament["tournament_name"]

        print(f"Current tournament: {tournament_name}")
        print(f"Tournament ID: {tournament_id}")

        print("Getting leaderboard...")

        leaderboard = get_leaderboard(tournament_id)

        players = clean_leaderboard(leaderboard)

        output = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "tournament": tournament_name,
            "status": "IN_PROGRESS",
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
