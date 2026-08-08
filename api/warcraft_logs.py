import os

import requests
from dotenv import load_dotenv


load_dotenv()


class WarcraftLogsAPI:
    TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
    API_URL = "https://www.warcraftlogs.com/api/v2/client"

    def __init__(self):
        self.client_id = os.getenv(
            "WARCRAFT_LOGS_CLIENT_ID"
        )

        self.client_secret = os.getenv(
            "WARCRAFT_LOGS_CLIENT_SECRET"
        )

        self.access_token = None

    def authenticate(self):
        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "Warcraft Logs API credentials are missing."
            )

        response = requests.post(
            self.TOKEN_URL,
            auth=(
                self.client_id,
                self.client_secret
            ),
            data={
                "grant_type": "client_credentials"
            },
            timeout=15,
        )

        response.raise_for_status()

        self.access_token = response.json()[
            "access_token"
        ]

        return self.access_token

    def query(self, query, variables=None):
        if not self.access_token:
            self.authenticate()

        response = requests.post(
            self.API_URL,
            headers={
                "Authorization":
                    f"Bearer {self.access_token}",
                "Content-Type":
                    "application/json",
            },
            json={
                "query": query,
                "variables": variables or {},
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            raise RuntimeError(
                data["errors"]
            )

        return data["data"]

    def get_fight_players(
        self,
        report_code,
        fight_id
    ):
        query = """
        query GetFightPlayers(
            $code: String,
            $fightIDs: [Int]
        ) {
            reportData {
                report(code: $code) {
                    fights(
                        fightIDs: $fightIDs
                    ) {
                        id
                        name
                        friendlyPlayers
                        friendlySpecs
                        friendlyItemLevels
                    }

                    masterData {
                        actors {
                            id
                            name
                            type
                        }
                    }
                }
            }
        }
        """

        return self.query(
            query,
            {
                "code": report_code,
                "fightIDs": [fight_id],
            }
        )

    def get_player_events_page(
        self,
        report_code,
        fight_id,
        player_id,
        start_time=None,
        end_time=None,
    ):
        query = """
        query GetPlayerEvents(
            $code: String,
            $fightIDs: [Int],
            $sourceID: Int,
            $limit: Int,
            $startTime: Float,
            $endTime: Float
        ) {
            reportData {
                report(code: $code) {
                    events(
                        fightIDs: $fightIDs
                        sourceID: $sourceID
                        limit: $limit
                        startTime: $startTime
                        endTime: $endTime
                        useAbilityIDs: true
                        useActorIDs: true
                    ) {
                        data
                        nextPageTimestamp
                    }
                }
            }
        }
        """

        variables = {
            "code": report_code,
            "fightIDs": [fight_id],
            "sourceID": player_id,
            "limit": 10000,
        }

        if start_time is not None:
            variables["startTime"] = start_time

        if end_time is not None:
            variables["endTime"] = end_time

        return self.query(
            query,
            variables
        )

    def get_all_player_events(
        self,
        report_code,
        fight_id,
        player_id,
    ):
        print("Fetching fight timestamps...")

        fight_query = """
        query GetFightTimestamps(
            $code: String,
            $fightIDs: [Int]
        ) {
            reportData {
                report(code: $code) {
                    fights(
                        fightIDs: $fightIDs
                    ) {
                        id
                        name
                        startTime
                        endTime
                    }
                }
            }
        }
        """

        fight_result = self.query(
            fight_query,
            {
                "code": report_code,
                "fightIDs": [fight_id],
            }
        )

        report = (
            fight_result
            ["reportData"]
            ["report"]
        )

        if report is None:
            raise RuntimeError(
                "Report not found."
            )

        fights = report["fights"]

        if not fights:
            raise RuntimeError(
                f"Fight {fight_id} not found."
            )

        fight = fights[0]

        fight_start = fight["startTime"]
        fight_end = fight["endTime"]

        print(
            f"Fight start: {fight_start}"
        )

        print(
            f"Fight end:   {fight_end}"
        )

        print(
            f"Fight range: "
            f"{fight_end - fight_start} ms"
        )

        print()
        print(
            "Fetching ALL player events..."
        )

        all_events = []

        next_timestamp = fight_start
        page_number = 1

        while True:
            print(
                f"Fetching event page "
                f"{page_number}..."
            )

            result = self.get_player_events_page(
                report_code,
                fight_id,
                player_id,
                start_time=next_timestamp,
                end_time=fight_end,
            )

            events = (
                result["reportData"]
                ["report"]
                ["events"]
            )

            page_events = events["data"]

            print(
                f"  Received "
                f"{len(page_events)} events "
                f"(total: "
                f"{len(all_events) + len(page_events)})"
            )

            all_events.extend(
                page_events
            )

            next_page_timestamp = (
                events["nextPageTimestamp"]
            )

            if not next_page_timestamp:
                break

            if (
                next_page_timestamp
                <= next_timestamp
            ):
                print(
                    "WARNING: Pagination timestamp "
                    "did not advance."
                )
                break

            if (
                next_page_timestamp
                >= fight_end
            ):
                break

            next_timestamp = (
                next_page_timestamp
            )

            page_number += 1

        # Remove accidental duplicates caused by
        # overlapping pagination boundaries.
        unique_events = {}

        for event in all_events:
            key = (
                event.get("timestamp"),
                event.get("type"),
                event.get("sourceID"),
                event.get("targetID"),
                event.get("abilityGameID"),
                event.get("fight"),
                event.get("targetInstance"),
            )

            unique_events[key] = event

        all_events = list(
            unique_events.values()
        )

        all_events.sort(
            key=lambda event:
            event.get("timestamp", 0)
        )

        print()
        print(
            f"Unique events received: "
            f"{len(all_events)}"
        )

        if all_events:
            print(
                f"First event timestamp: "
                f"{all_events[0].get('timestamp')}"
            )

            print(
                f"Last event timestamp: "
                f"{all_events[-1].get('timestamp')}"
            )

        return all_events