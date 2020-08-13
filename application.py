#export API_KEY=pk_efaab746a5ac4e0fb5f295683c01e5c0


import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, get_portfolio, in_stocks

# Configure database
db = SQL("sqlite:///finance.db")

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

#INDEX ######################################################################

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    total_portfolio = get_portfolio(session['user_id'])
    value = db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash']
    amnt_in_stocks = in_stocks(total_portfolio)

    return render_template("index.html", total_portfolio = total_portfolio, assets = usd(value + amnt_in_stocks), cash = usd(value))

#BUY  ######################################################################

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        userId = session['user_id']
        symbol = request.form.get("symbol").upper()
        if lookup(symbol) == None:
            return apology("symbol not exist", 400)
        shares = int(request.form.get("shares"))
        stats = lookup(symbol)
        rows = db.execute(f"SELECT * FROM users WHERE id = '{userId}'")
        cost = shares * stats['price']

        if (rows[0]['cash'] - cost) < 0:
            return apology("you cannot afford this", 400)
        elif shares <= 0:
            return apology("You can't purchase 0 shares!", 400)
        db.execute(f"INSERT INTO 'transactions' ('userId','purchaseId','symbol','price','shares','stock') VALUES ('{userId}',NULL,'{symbol}','{stats['price']}','{shares}','{stats['name']}')")

        total_portfolio = get_portfolio(session['user_id'])
        assets = db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash']
        new_balance = db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash'] - cost
        db.execute(f"UPDATE 'users' SET ('cash') = ('{ new_balance }') WHERE id = '{ userId }'")

        value = (db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash'])
        total_portfolio = get_portfolio(session['user_id'])
        amnt_in_stocks = in_stocks(total_portfolio)

        return render_template("index.html", confirm = 'Purchase Successful!', total_portfolio = total_portfolio, assets = usd(value + amnt_in_stocks), cash = usd(value))

    return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():

    username = request.args.get("username")

    taken_usernames = db.execute("SELECT username FROM users")

    if not len(str(username)) > 0:
        return jsonify(False)
    for taken_username in taken_usernames:
        if username == taken_username["username"]:
            return jsonify(False)

    return jsonify(True)


# HISTORY ################### ################## #################### ################# ###################

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user = session['user_id']
    history = db.execute(f"SELECT *  FROM transactions WHERE userId = '{user}'")
    return render_template("history.html", history = history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        stats = lookup(request.form.get("symbol"))
        if stats == None:
            return apology("No such symbol", 400)
        else:
            share = f"A share of {stats['name']} ({stats['symbol']}) is worth {stats['price']} "
        return render_template("quoted.html", share=usd(share))
    return render_template("quote.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        """Register user"""
        username = request.form.get("username")
        password = request.form.get("password")

        """Checks that the register used a unique user name, an appropriate password, and that the passwords match"""
        if len(username) <= 0:
            return apology("too short", 400)
        for user in db.execute("SELECT username FROM 'users'"):
            if user['username'] == username:
                return apology("username taken, please select another username", 400)

        if password != request.form.get("confirmation"):
            return apology("passwords did not match", 400)
        elif len(password) < 6:
            return apology("password must be at least 6 characters", 400)
        elif password == "password" or password == username:
            return apology("password cannot be your username or 'password'", 400)

        db.execute(f"INSERT INTO 'users' ('id','username','hash') VALUES (NULL,'{username}', '{generate_password_hash(password)}')")
        login()
        confirm = "You registered!"
        value = db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash']

        return render_template("index.html", confirm = confirm, assets = usd(value))
    return render_template("register.html")


# SELL ################# ################# ################# ################# ################# #################

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    total_portfolio = get_portfolio(session['user_id'])
    if request.method == "POST":
        userId = session["user_id"]
        symbol = request.form.get("symbol")
        shares = float(request.form.get("shares"))
        if shares > total_portfolio[symbol]['shares']:
            return apology("You are trying to sell more shares than you have!")
        elif shares <= 0:
            return apology("You can't sell 0 shares!", 400)
        else:
            stats = lookup("FIW"); price = stats['price']; name = stats['name']
            sale = shares * price
            db.execute(f"INSERT INTO 'transactions' ('userId','purchaseId','symbol','price','shares','stock') VALUES ('{ userId }',NULL,'{ symbol }','{ price }','{(-1) * shares }','{ name }')")
            new_balance = db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash'] + sale
            db.execute(f"UPDATE 'users' SET ('cash') = ('{ new_balance }') WHERE id = '{ userId }'")

            value = (db.execute(f"SELECT cash FROM users WHERE id = '{session['user_id']}'")[0]['cash'])
            total_portfolio = get_portfolio(session['user_id'])
            amnt_in_stocks = in_stocks(total_portfolio)
            return render_template("index.html", confirm = "Sold!", total_portfolio = total_portfolio, assets = usd(value + amnt_in_stocks), cash = usd(value))
    return render_template("sell.html", total_portfolio = total_portfolio)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

