import os
import datetime
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Set up the database connection
db = SQL("sqlite:///your_database.db")

# Define the rooms list globally so it's accessible in all routes
rooms = [
    {"id": 1, "name": "Cabot LL10", "description": "Group Study Room -- Lower Level", "image": "https://library.harvard.edu/sites/default/files/spacefinder/rooms/2018-04/LL10%20Cabot%20Inside%20view.jpg"},
    {"id": 2, "name": "Cabot L212", "description": "Group Study Room -- Second Floor.", "image": "https://library.harvard.edu/sites/default/files/spacefinder/rooms/2018-04/Cabot%20L205%20-%20Inside%20View.jpg"},
    {"id": 3, "name": "Cabot L107", "description": "Video Conference Room -- Main Level.", "image": "https://library.harvard.edu/sites/default/files/spacefinder/rooms/2018-03/Cabot-L107-VideoConference-01.jpg"},
    {"id": 4, "name": "Cabot L214", "description": "Group Study Room -- Second Floor", "image": "https://library.harvard.edu/sites/default/files/spacefinder/rooms/2018-04/Cabot%20L214%20-%20Inside%20View%201.jpg"},
    {"id": 5, "name": "Cabot LL06", "description": "Group Study Room -- Lower Level", "image": "https://library.harvard.edu/sites/default/files/spacefinder/rooms/2018-04/L006%20inside.jpg"},
    {"id": 6, "name": "Cabot L210", "description": "Group Study Room -- Second Floor", "image": "https://library.harvard.edu/sites/default/files/spacefinder/rooms/2018-04/Cabot%20L210%20-%20Outside%20View.jpg"},
]

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Handle GET requests
    if request.method == "GET":
        return render_template("register.html")
    else:
        # handle POST requests
        username = request.form.get("username")
        if not username:
            return apology("Need to provide a username!!")

        password = request.form.get("password")
        if not password:
            return apology("Need to provide a password!!")

        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("Need to provide a confirmation!!")

        if password != confirmation:
            return apology("Your password and confirmation don't match")

        hashed_password = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                       username=username, hash=hashed_password)
        except ValueError:
            return apology("That username already exists I fear")
        return redirect("/")

@app.route("/music")
def music():
    return render_template("music.html")

@app.route("/roombook")
def roombook():
    return render_template("roombook.html", rooms=rooms)

@app.route('/reserve')
def reserve():
    room_id = request.args.get('room_id', type=int)
    room = next((room for room in rooms if room["id"] == room_id), None)
    if room is None:
        return "Room not found", 404

    # Get current date and time for comparison
    current_time = datetime.datetime.now()

    return render_template('reserve.html', room=room, current_time=current_time)

@app.route("/book", methods=["POST"])
def book():
    room_id = request.form.get("room_id")
    booking_date = request.form.get("booking_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    # Convert booking date and times to datetime objects
    booking_datetime = datetime.datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M")
    current_datetime = datetime.datetime.now()

    # Check if the booking time is in the future
    if booking_datetime < current_datetime:
        flash("Booking time must be in the future.", "danger")
        return redirect("/")

    # Proceed with booking logic
    try:
        # Insert the booking into the database
        db.execute("""
            INSERT INTO bookings (user_id, room_id, booking_date, start_time, end_time)
            VALUES (:user_id, :room_id, :booking_date, :start_time, :end_time)
        """, user_id=session["user_id"], room_id=room_id, booking_date=booking_date, start_time=start_time, end_time=end_time)

        flash("Room booked successfully!", "success")
    except Exception as e:
        flash("An error occurred while booking. Please try again.", "danger")

    return redirect("/")

@app.route("/history")
def history():
    """Show user's booking history"""
    if not session.get("user_id"):
        return redirect("/login")

    bookings = db.execute("""
        SELECT b.booking_date, b.start_time, b.end_time, r.name
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, session["user_id"])

    return render_template("history.html", bookings=bookings)

def check_room_availability(room_id, start_time, end_time):
    # Query to check if any reservation overlaps with the requested time slot
    overlapping_reservations = db.execute("""
        SELECT 1
        FROM bookings
        WHERE room_id = :room_id
        AND (
            (start_time < :end_time AND end_time > :start_time)
        )
    """, room_id=room_id, start_time=start_time, end_time=end_time)

    # If there are overlapping reservations, the room is not available
    return len(overlapping_reservations) == 0

@app.route("/filter", methods=["GET", "POST"])
def filter_rooms():
    # Retrieve the filter parameters from the form or query string
    filter_date = request.form.get("filter_date") or request.args.get("filter_date")
    filter_start_time = request.form.get("filter_start_time") or request.args.get("filter_start_time")
    filter_end_time = request.form.get("filter_end_time") or request.args.get("filter_end_time")

    if not filter_date or not filter_start_time or not filter_end_time:
        flash("Please provide a date and time range to filter.", "danger")
        return redirect("/roombook")

    available_rooms = []
    for room in rooms:
        if check_room_availability(room['id'], filter_start_time, filter_end_time):
            available_rooms.append(room)

    return render_template("roombook.html", available_rooms=available_rooms)


if __name__ == "__main__":
    app.run(debug=True)
