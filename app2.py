from flask import Flask, render_template, request, jsonify, session
import random

app2 = Flask(__name__)
app2.secret_key = "craps_secret_key"

MIN_BET = 3
MAX_BET = 20
STARTING_BANKROLL = 100

# Global leaderboard (shared across all players)
leaderboard = {}

def init_game():
    session["bankroll"] = STARTING_BANKROLL
    session["point"] = None
    session["bet"] = 0
    session["in_round"] = False
    session["name"] = None
    session["odds_bet"] = 0

def roll_dice():
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1, die2

def update_leaderboard(name, bankroll):
    if name:
        leaderboard[name] = bankroll

@app2.route("/")
def index():
    if "bankroll" not in session:
        init_game()
    return render_template("index2.html")

@app2.route("/set_name", methods=["POST"])
def set_name():
    name = request.json.get("name")
    session["name"] = name
    update_leaderboard(name, session["bankroll"])
    return jsonify({"success": True})

@app2.route("/leaderboard")
def get_leaderboard():
    sorted_board = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_board[:10])  # top 10

@app2.route("/state")
def state():
    return jsonify({
        "bankroll": session.get("bankroll", STARTING_BANKROLL),
        "point": session.get("point"),
        "in_round": session.get("in_round"),
        "name": session.get("name")
    })

@app2.route("/bet", methods=["POST"])
def bet():
    amount = request.json.get("amount")

    if amount < MIN_BET or amount > MAX_BET:
        return jsonify({"error": f"Bet must be between ${MIN_BET} and ${MAX_BET}"}), 400

    if amount > session["bankroll"]:
        return jsonify({"error": "Not enough bankroll"}), 400

    session["bet"] = amount
    session["bankroll"] -= amount

    update_leaderboard(session["name"], session["bankroll"])
    return jsonify({"success": True})

@app2.route("/roll", methods=["POST"])
def roll():
    die1, die2 = roll_dice()
    roll = die1 + die2

    if not session["in_round"]:
        if roll in [7, 11]:
            # base win
            session["bankroll"] += session["bet"] * 2

            # odds payout
            point = session["point"]
            odds = session["odds_bet"]

            if odds > 0:
                if point in [4, 10]:
                    session["bankroll"] += odds * 3
                elif point in [5, 9]:
                    session["bankroll"] += odds * 2.5
                elif point in [6, 8]:
                    session["bankroll"] += odds * 2.2

            session["odds_bet"] = 0
            result = "win"
        else:
            session["point"] = roll
            session["in_round"] = True
            result = f"Point: {roll}"
    else:
        if roll == 7:
            session["in_round"] = False
            result = "lose"
            session["odds_bet"] = 0
        elif roll == session["point"]:
            # base win
            session["bankroll"] += session["bet"] * 2

            # odds payout
            point = session["point"]
            odds = session["odds_bet"]

            if odds > 0:
                if point in [4, 10]:
                    session["bankroll"] += odds * 3
                elif point in [5, 9]:
                    session["bankroll"] += odds * 2.5
                elif point in [6, 8]:
                    session["bankroll"] += odds * 2.2

            session["odds_bet"] = 0
            session["in_round"] = False
            result = "win"
        else:
            result = "roll again"

    update_leaderboard(session["name"], session["bankroll"])

    return jsonify({
        "roll": roll,
        "dice": [die1, die2],   # 👈 THIS LINE IS REQUIRED
        "result": result,
        "bankroll": session["bankroll"],
        "point": session["point"],
        "in_round": session["in_round"]
    })

@app2.route("/reset", methods=["POST"])
def reset():
    name = session.get("name")
    init_game()
    session["name"] = name  # keep same player name
    update_leaderboard(name, session["bankroll"])
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)

@app2.route("/odds", methods=["POST"])
def place_odds():
    amount = request.json.get("amount")

    if not session["in_round"]:
        return jsonify({"error": "No point set yet"}), 400

    if amount > session["bankroll"]:
        return jsonify({"error": "Not enough bankroll"}), 400

    session["odds_bet"] = amount
    session["bankroll"] -= amount

    return jsonify({
        "bankroll": session["bankroll"],
        "odds_bet": session["odds_bet"]
    })