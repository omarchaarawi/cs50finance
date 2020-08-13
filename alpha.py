# alpha.py is used to develop initial code, it then gets further developed in beta.py
# alpha.p and beta.py are dynamic while final.py is static
from cs50 import SQL
import helpers
from helpers import lookup, get_portfolio, in_stocks, usd
#export API_KEY=pk_efaab746a5ac4e0fb5f295683c01e5c0


db = SQL("sqlite:///finance.db")

"""Retrieves the portfolio of a user and saves it in a dictionary"""
user = db.execute("Select username FROM users")

print(user)