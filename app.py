from flask import Flask, jsonify, request
import graphene
import random

app = Flask(__name__)

GENRES = ["RPG", "Shooter", "Action", "Adventure", "Strategy", "Sports"]

GAMES = [
    {
        "id": i,
        "name": f"Game {i}",
        "genre": random.choice(GENRES),
    }
    for i in range(1, 5001)
]

USERS = [
    {
        "id": i,
        "name": f"User {i}",
    }
    for i in range(1, 1001)
]

REVIEWS = []
review_id = 1
for game in GAMES[:500]:
    for _ in range(random.randint(1, 5)):
        REVIEWS.append(
            {
                "id": review_id,
                "game_id": game["id"],
                "user_id": random.randint(1, 1000),
                "rating": random.randint(1, 5),
                "comment": f"Comment {review_id}",
            }
        )
        review_id += 1

USER_GAMES = []
for user in USERS[:500]:
    game_ids = random.sample(range(1, 5001), k=20)
    for gid in game_ids:
        USER_GAMES.append(
            {
                "user_id": user["id"],
                "game_id": gid,
            }
        )


def get_games(page=1, limit=20):
    page = max(page, 1)
    limit = max(limit, 1)
    start = (page - 1) * limit
    end = start + limit
    return GAMES[start:end]


def get_game_with_reviews(game_id: int):
    game = next((g for g in GAMES if g["id"] == game_id), None)
    if not game:
        return None
    game_reviews = [r for r in REVIEWS if r["game_id"] == game_id]
    game_copy = dict(game)
    game_copy["reviews"] = game_reviews
    return game_copy


def get_user_with_library(user_id: int):
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        return None
    game_ids = [ug["game_id"] for ug in USER_GAMES if ug["user_id"] == user_id]
    library_games = [g for g in GAMES if g["id"] in game_ids]
    user_copy = dict(user)
    user_copy["library"] = library_games
    return user_copy


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/rest/games", methods=["GET"])
def rest_games():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({"error": "invalid_params"}), 400
    games = get_games(page, limit)
    return jsonify(games)


@app.route("/rest/games/<int:game_id>", methods=["GET"])
def rest_game_with_reviews(game_id):
    game = get_game_with_reviews(game_id)
    if not game:
        return jsonify({"error": "not_found"}), 404
    return jsonify(game)


@app.route("/rest/users/<int:user_id>/library", methods=["GET"])
def rest_user_library(user_id):
    user = get_user_with_library(user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404
    return jsonify(user)


class ReviewType(graphene.ObjectType):
    id = graphene.Int()
    rating = graphene.Int()
    comment = graphene.String()


class GameType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    genre = graphene.String()
    reviews = graphene.List(ReviewType)

    def resolve_reviews(parent, info):
        game_id = parent["id"]
        return [r for r in REVIEWS if r["game_id"] == game_id]


class UserType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    library = graphene.List(GameType)

    def resolve_library(parent, info):
        user_id = parent["id"]
        game_ids = [ug["game_id"]
                    for ug in USER_GAMES if ug["user_id"] == user_id]
        return [g for g in GAMES if g["id"] in game_ids]


class Query(graphene.ObjectType):
    games = graphene.List(
        GameType,
        page=graphene.Int(required=True),
        limit=graphene.Int(required=True),
    )
    game = graphene.Field(GameType, id=graphene.Int(required=True))
    user = graphene.Field(UserType, id=graphene.Int(required=True))

    def resolve_games(root, info, page, limit):
        return get_games(page, limit)

    def resolve_game(root, info, id):
        return get_game_with_reviews(id)

    def resolve_user(root, info, id):
        return get_user_with_library(id)


schema = graphene.Schema(query=Query)


@app.route("/graphql", methods=["POST"])
def graphql_endpoint():
    data = request.get_json() or {}
    query = data.get("query")
    variables = data.get("variables")
    result = schema.execute(query, variable_values=variables)
    response = {}
    if result.errors:
        response["errors"] = [str(e) for e in result.errors]
    if result.data is not None:
        response["data"] = result.data
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
