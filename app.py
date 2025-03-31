from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "basketball.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    """
    Home page: Display a list of all players, and link to game stats.
    """
    conn = get_db_connection()
    players = conn.execute("SELECT * FROM players").fetchall()
    conn.close()

    return render_template("index.html", players=players)

@app.route("/add_player", methods=["GET", "POST"])
def add_player():
    """
    Add a new player with team name and player name.
    """
    if request.method == "POST":
        team_name = request.form.get("team_name")
        player_name = request.form.get("player_name")

        if not team_name or not player_name:
            return "Missing team or player name!", 400

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO players (team_name, player_name) VALUES (?, ?)",
            (team_name, player_name),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add_player.html")

@app.route("/player/<int:player_id>")
def view_player(player_id):
    """
    View all game stats for a specific player.
    """
    conn = get_db_connection()
    player = conn.execute(
        "SELECT * FROM players WHERE id = ?", (player_id,)
    ).fetchone()

    if not player:
        conn.close()
        return "Player not found!", 404

    games = conn.execute(
        "SELECT * FROM game_stats WHERE player_id = ? ORDER BY game_date ASC",
        (player_id,),
    ).fetchall()
    conn.close()

    return render_template("player_stats.html", player=player, games=games)

@app.route("/add_game/<int:player_id>", methods=["GET", "POST"])
def add_game(player_id):
    """
    Add a new game record for a specific player.
    """
    conn = get_db_connection()
    player = conn.execute(
        "SELECT * FROM players WHERE id = ?", (player_id,)
    ).fetchone()
    conn.close()

    if not player:
        return "Player not found!", 404

    if request.method == "POST":
        game_date = request.form.get("game_date")
        points = request.form.get("points", 0, type=int)
        assists = request.form.get("assists", 0, type=int)
        rebounds = request.form.get("rebounds", 0, type=int)
        steals = request.form.get("steals", 0, type=int)
        blocks = request.form.get("blocks", 0, type=int)
        turnovers = request.form.get("turnovers", 0, type=int)

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO game_stats
                (player_id, game_date, points, assists, rebounds, steals, blocks, turnovers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (player_id, game_date, points, assists, rebounds, steals, blocks, turnovers),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("view_player", player_id=player_id))

    return render_template("add_game.html", player=player)

@app.route("/edit_game/<int:game_id>", methods=["GET", "POST"])
def edit_game(game_id):
    """
    Edit (update) an existing game stat record.
    """
    conn = get_db_connection()
    game = conn.execute(
        "SELECT * FROM game_stats WHERE id = ?", (game_id,)
    ).fetchone()

    if not game:
        conn.close()
        return "Game record not found!", 404

    if request.method == "POST":
        game_date = request.form.get("game_date")
        points = request.form.get("points", 0, type=int)
        assists = request.form.get("assists", 0, type=int)
        rebounds = request.form.get("rebounds", 0, type=int)
        steals = request.form.get("steals", 0, type=int)
        blocks = request.form.get("blocks", 0, type=int)
        turnovers = request.form.get("turnovers", 0, type=int)

        conn.execute(
            """
            UPDATE game_stats
            SET game_date = ?,
                points = ?,
                assists = ?,
                rebounds = ?,
                steals = ?,
                blocks = ?,
                turnovers = ?
            WHERE id = ?
            """,
            (game_date, points, assists, rebounds, steals, blocks, turnovers, game_id),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("view_player", player_id=game["player_id"]))

    conn.close()
    return render_template("edit_game.html", game=game)

@app.route("/delete_game/<int:game_id>", methods=["POST"])
def delete_game(game_id):
    """
    Delete a game record by ID.
    """
    conn = get_db_connection()
    game = conn.execute(
        "SELECT * FROM game_stats WHERE id = ?", (game_id,)
    ).fetchone()

    if not game:
        conn.close()
        return "Game record not found!", 404

    player_id = game["player_id"]

    conn.execute("DELETE FROM game_stats WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("view_player", player_id=player_id))

@app.route("/averages")
def averages():
    """
    Display each player's average for points, assists, rebounds, steals, blocks, turnovers.
    This requires joining players with game_stats and using AVG.
    """
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            p.id,
            p.team_name,
            p.player_name,
            AVG(gs.points)   AS avg_points,
            AVG(gs.assists)  AS avg_assists,
            AVG(gs.rebounds) AS avg_rebounds,
            AVG(gs.steals)   AS avg_steals,
            AVG(gs.blocks)   AS avg_blocks,
            AVG(gs.turnovers)AS avg_turnovers
        FROM players p
        JOIN game_stats gs ON p.id = gs.player_id
        GROUP BY p.id
        """
    ).fetchall()
    conn.close()

    return render_template("averages.html", players=rows)

if __name__ == "__main__":
    app.run(debug=True)


@app.route("/delete_player/<int:player_id>", methods=["POST"])
def delete_player(player_id):
    conn = get_db_connection()
    # (Optional) Manually delete stats if you don't use ON DELETE CASCADE:
    conn.execute("DELETE FROM game_stats WHERE player_id = ?", (player_id,))

    # Now delete the player
    conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))
