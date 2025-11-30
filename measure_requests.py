import argparse
import csv
import time
import requests

BASE_URL = "http://localhost:5000"

GRAPHQL_QUERIES = {
    "A": {
        "query": """
        query ListGames($page: Int!, $limit: Int!) {
          games(page: $page, limit: $limit) {
            id
            name
            genre
          }
        }
        """,
        "variables": {"page": 1, "limit": 20},
    },
    "B": {
        "query": """
        query GameWithReviews($id: Int!) {
          game(id: $id) {
            id
            name
            genre
            reviews {
              id
              rating
              comment
            }
          }
        }
        """,
        "variables": {"id": 1},
    },
    "C": {
        "query": """
        query UserLibrary($id: Int!) {
          user(id: $id) {
            id
            name
            library {
              id
              name
              genre
            }
          }
        }
        """,
        "variables": {"id": 1},
    },
}


def measure_rest_scenario(scenario: str, repetitions: int, writer):
    if scenario == "A":
        url = f"{BASE_URL}/rest/games?page=1&limit=20"
    elif scenario == "B":
        url = f"{BASE_URL}/rest/games/1"
    elif scenario == "C":
        url = f"{BASE_URL}/rest/users/1/library"
    else:
        raise ValueError(f"Cenário REST inválido: {scenario}")
    for rep in range(1, repetitions + 1):
        start = time.perf_counter()
        resp = requests.get(url)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000.0
        size_bytes = len(resp.content)
        writer.writerow(
            {
                "api_type": "rest",
                "scenario": scenario,
                "repetition": rep,
                "response_time_ms": f"{elapsed_ms:.3f}",
                "response_size_bytes": size_bytes,
                "status_code": resp.status_code,
            }
        )


def measure_graphql_scenario(scenario: str, repetitions: int, writer):
    if scenario not in GRAPHQL_QUERIES:
        raise ValueError(f"Cenário GraphQL inválido: {scenario}")
    payload = GRAPHQL_QUERIES[scenario]
    for rep in range(1, repetitions + 1):
        start = time.perf_counter()
        resp = requests.post(f"{BASE_URL}/graphql", json=payload)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000.0
        size_bytes = len(resp.content)
        writer.writerow(
            {
                "api_type": "graphql",
                "scenario": scenario,
                "repetition": rep,
                "response_time_ms": f"{elapsed_ms:.3f}",
                "response_size_bytes": size_bytes,
                "status_code": resp.status_code,
            }
        )


def main():
    parser = argparse.ArgumentParser(
        description="Mede tempo e tamanho de respostas REST vs GraphQL."
    )
    parser.add_argument(
        "--api",
        choices=["rest", "graphql", "both"],
        default="both",
        help="Tipo de API a medir.",
    )
    parser.add_argument(
        "--scenario",
        choices=["A", "B", "C", "all"],
        default="all",
        help="Cenário de consulta.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=30,
        help="Número de repetições por cenário/API.",
    )
    parser.add_argument(
        "--output",
        default="results.csv",
        help="Arquivo CSV de saída.",
    )

    args = parser.parse_args()
    scenarios = ["A", "B", "C"] if args.scenario == "all" else [args.scenario]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "api_type",
            "scenario",
            "repetition",
            "response_time_ms",
            "response_size_bytes",
            "status_code",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for scenario in scenarios:
            if args.api in ("rest", "both"):
                measure_rest_scenario(scenario, args.repetitions, writer)
            if args.api in ("graphql", "both"):
                measure_graphql_scenario(scenario, args.repetitions, writer)


if __name__ == "__main__":
    main()
