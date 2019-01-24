import requests
import os
from random import shuffle

from google.cloud import translate
from cs50 import SQL

from flask import Flask, render_template, session, request, redirect, json
from flask_session import Session
from functools import wraps
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///storage.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure username is avilable
        new_user = db.execute("SELECT * FROM user WHERE username = :username", username=request.form.get("username"))
        if len(new_user) > 0:
            return apology("username allready exist")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation")

        # Ensure password and password confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password and password confirmation must match")

        # Register new user
        new_user = db.execute("INSERT INTO user (username, hash, nativelang) VALUES (:username, :hash, :nativelang)",
                              username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")),
                              nativelang=request.form.get("nativelang"))

        # Remember which user has logged in
        session["user_id"] = new_user
        session["nativelang"] = request.form.get("nativelang")

        # Redirect user to main page
        return redirect("/main")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM user WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["nativelang"] = rows[0]["nativelang"]

        # Redirect user to main page
        return redirect("/main")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user
    return redirect("/")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/main")
def main():
    randoms = db.execute("SELECT word FROM dict WHERE rank BETWEEN 1000 AND 5000 AND flag IS NULL ORDER BY RANDOM() LIMIT 5")
    return render_template("main.html", randoms=randoms)


@app.route("/mywords",  methods=["GET", "POST"])
@login_required
def mywords():
    history = db.execute(
        "SELECT userid, word, timestamp FROM memo WHERE userid = :userid ORDER BY timestamp DESC", userid=session["user_id"])
    return render_template("mywords.html", history=history)


@app.route("/play",  methods=["GET", "POST"])
def play():

    if request.method == "POST":
        if 'user_id' in session:
            word = request.form.get("answer")
            memo = db.execute("INSERT INTO memo (userid, word) VALUES (:userid, :word)", userid=session["user_id"], word=word)
            return redirect("/play")
        else:
            return redirect("/play")

    else:
        # get random word
        try:
            rows = db.execute("SELECT * FROM dict WHERE rank BETWEEN 1000 AND 5000 AND flag IS NULL ORDER BY RANDOM() LIMIT 1")
            question = rows[0]["word"]
        except:
            return bug()

        # for debuging
        # question = "bit"

        # oxford API configuration more info: https://developer.oxforddictionaries.com/
        app_id = ''
        app_key = ''
        language = 'en'

        # word_id = question
        try:
            word_id = question
            url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/' + language + '/' + word_id.lower()
            urlFR = 'https://od-api.oxforddictionaries.com:443/api/v1/stats/frequency/word/' + language + '/?corpus=nmc&lemma=' + word_id.lower()
            r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})
        except:
            flag = "NOK (OXFORD API)"
            print(flag + " " + question)
            db.execute("UPDATE dict SET flag = :flag WHERE word = :word", flag=flag, word=question)
            db.execute("INSERT INTO bug (code, question) VALUES (:code, :question)", code=flag, question=question)
            return bug()

        try:
            definition = []
            api = r.json()

            # iterate over json object to get list of definitions
            for i in api["results"]:
                for j in i["lexicalEntries"]:
                    for k in j["entries"]:
                        for v in k["senses"]:
                            definition.append(v["definitions"])
        except:
            flag = "NOK (OXFORD DEF)"
            print(flag + " " + question)
            db.execute("UPDATE dict SET flag = :flag WHERE word = :word", flag=flag, word=question)
            buglog = db.execute("INSERT INTO bug (code, question) VALUES (:code, :question)", code=flag, question=question)
            return bug()

        try:
            # try to get first exaple of use from json object
            samples = r.json()["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]["examples"][0]["text"]
            censoredS = str(samples).replace(question, len(question) * ".")
        except:
            flag = "NOK (JSON -> SAMPLES)"
            print(flag + " " + question)
            buglog = db.execute("INSERT INTO bug (code, question) VALUES (:code, :question)", code=flag, question=question)
            censoredS = "sorry, not this time..."

        # google translator API // please download and copy to static/ folder credentials file.
        # More info: https://cloud.google.com/translate/
        if session.get("user_id") != None:
            # registered user
            try:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "static/google_api.json"
                translate_client = translate.Client()

                target = session["nativelang"]
                text = question

                translation = translate_client.translate(
                    text,
                    source_language='en',
                    target_language=target)
            except:
                flag = "NOK (GOOGLE TRANSLATOR API)"
                print(flag + " " + question)
                buglog = db.execute("INSERT INTO bug (code, question) VALUES (:code, :question)", code=flag, question=question)
                translation = {'translatedText': 'sorry, not this time...'}
        # unregisterd user
        else:
            translation = {'translatedText': 'sorry, not this time...'}

        # make "letters hint"
        letters = []
        for c in question:
            letters += c
        shuffle(letters)

        # render play template
        return render_template("play.html", definition=definition, censoredS=censoredS, question=question, letters=letters, translation=translation['translatedText'])

# bug scenerio template
def bug():
    question = "bug"
    definition = [['A problem that needs fixing']]
    censoredS = "The software ...  led the computer to calculate 2 plus 2 as 5."
    translation = "sorry, not this time..."
    letters = ["u", "g", "b"]

    return render_template("play.html", definition=definition, censoredS=censoredS, question=question, letters=letters, translation=translation)
