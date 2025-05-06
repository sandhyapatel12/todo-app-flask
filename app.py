#----------------------------------------BACKEND----------------------------------------

# Import the Flask class from the flask module
from flask import Flask, render_template, request, redirect, flash, url_for
from datetime import datetime
import os
from database import db  # Import the database instance
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt


# Create a Flask application instance
app = Flask(__name__)
app.secret_key = "12345"  # Required for flash messages(after create todo display message)


# Set the absolute path for the database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'todo.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize (db is an instance of the SQLAlchemy class  which define in database.py)
db.init_app(app)  # initialize database
bcrypt = Bcrypt(app)  # Initialize Bcrypt with the Flask app(Bcrypt is used to securely hash passwords before storing them in the database.)
login_manager = LoginManager(app)  # Initialize LoginManager with the Flask app(sets up Flask-Login, which manages user sessions (login/logout))
login_manager.login_view = "login"  # Set the login view for the login manager

# --------------------------- DATABASE MODELS ---------------------------

# User model(for authentication)
# Define the User model(create table in database using SQLAlchemy because  here we used SQLite database )
#UserMixin: Adds extra login-related functionalities automatically.
class User(UserMixin, db.Model): #User is a databse table name for users
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) 

# Todo Model (For Tasks)
# Define the Todo model(create table in database using SQLAlchemy because  here we used SQLite database )
class Todo(db.Model):  # Todo is database table name (for tasks)
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(
        db.String(200), nullable=False
    )  # define title type, length and not null
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #  Links each todo to a specific user


    # It tells Python how to display the object when you print it.   (if we not using this then it will show object like --> <Todo object at 0x7f8a3c2b5e50>)
    def __repr__(self):
        return f"{self.sno}-{self.title}"
    

# load user function
# @login_manager is an instance of the LoginManager class (which define in above initilazaition section)
@login_manager.user_loader  #user_loader is a special function used by Flask-Login to load a user from the database based on their user ID.
def load_user(user_id):
    # Convert user_id to an integer (because database IDs are stored as numbers)
    # Fetch the user from the database using their ID
    return User.query.get(int(user_id))  # If found, return the user object; otherwise, return None

# --------------------------- USER REGISTRATION (Optional) ---------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]

        #generate_password_hash is a function from Flask-Bcrypt that converts a password into a secure, encrypted format.
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")  #.decode("utf-8") converts the hash into a readable string format.

        # Check if the username already exists in the database
        if User.query.filter_by(username = username).first():  #.first() is used to fetch the first matching user from the database
            flash("username already exist", "warning")
            return redirect(url_for("register"))
        
        # If the username is unique, create a new user object
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successfully ! please login", "success")
        return redirect(url_for("login"))
    
    # If the request is GET (user is visiting the page), show the registration form
    return render_template("register.html")  

# --------------------------- LOGIN USER ---------------------------

#login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Search for the user in the database by username(find that user is exits or not)
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password): #The password stored in the database is hashed (encrypted), so we cannot compare it directly with the entered password.
            login_user(user) #is a Flask-Login function that logs in a user and starts their session.
            flash("login successfull", "success")
            return redirect("/")  # redirect to home page
        
        else:
            flash("invalid username or password", "warning")

    return render_template("login.html")   

# --------------------------- LOGOUT USER ---------------------------

#logout route
@app.route("/logout")
@login_required #@login_required is a Flask-Login decorator that restricts access to certain routes and ensures that only logged-in users can access them
def logout():
    logout_user() #logout_user() is a Flask-Login function that logs out the currently logged-in user and clears their session.
    flash("you have been logged out", "info")
    return redirect(url_for("login"))



# ----------------------------------------------------CREATE ----------------------------------------------------
#create a route for the home page and allow both GET and POST requests
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":      #Checks if the user submitted a form (POST request).
        title = request.form["title"]  # get title from form
        desc = request.form["desc"] # get desc from form

        # Create a new todo and associate it with the logged-in user
        todo = Todo(title=title, desc=desc, user_id=current_user.id) # creates a new object of the Todo class (which represents a task in the database).
        
        db.session.add(todo)  # add new todo to the database
        db.session.commit() #used to save the changes made to the database permanently.

        if title and desc:  # check if title and desc is not empty
            flash("Task added successfully!", "success")  # flash message
            return redirect("/")  # redirect to home page

    allTodo = Todo.query.all()  #fetch all todo from database
    return render_template(
        "index.html", allTodo=allTodo
    )  # send all todos to the index.html file and index.html file will display all todos


# ----------------------------------------------------READ----------------------------------------------------
@app.route("/view")
@login_required
def view():
    allTodo = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template("view.html", allTodo=allTodo)  # send all todos to the view.html file and view.html file will display all todos


# ----------------------------------------------------UPDATE----------------------------------------------------
@app.route("/update/<int:sno>", methods=["GET", "POST"])  #<int:sno>  for specific id
@login_required
def update(sno):

    todo = Todo.query.filter_by(sno=sno, user_id=current_user.id).first()

    # Prevent unauthorized users from updating others' todos
    if not todo:
        flash("you are not authorized to update this task!", "warning")
        return redirect("/")

    if request.method == "POST":
        todo.title = request.form["title"] # update title
        todo.desc = request.form["desc"] # update desc
        db.session.commit()
        flash("Task updated successfully...", "success")
        return redirect("/")

    return render_template("update.html", todo=todo)   #Fetches the task to be updated from the database.


# ----------------------------------------------------DELETE----------------------------------------------------
@app.route("/delete/<int:sno>")
@login_required
def delete(sno):

    todo = Todo.query.filter_by(sno=sno, user_id=current_user.id).first()

    # Prevent unauthorized users from deleting others' todos
    if not todo:
        flash("you are not authorized to delete this task!", "warning")
        return redirect("/")

    db.session.delete(todo)  # delete todo from database
    db.session.commit()
    flash("Task deleted successfully!", "success")
    return redirect("/view")

# --------------------------- RUN THE FLASK APP ---------------------------

# Run the Flask app only if this script is executed directly means run app.py file
if __name__ == "__main__":
    with app.app_context():  # Ensure Flask is in the application context
        db.create_all()  # Create database tables
        print("Database created successfully!")  # Confirmation message

    # use locally
    # Starts the development server, and 'debug=True' allows automatic reloading on changes.when we delopy our app then we set debug=False  so that it will not show error on browser to user
    # app.run(debug=True)  
    
    #----------------------
    
    # use in production
    if os.environ.get("FLASK_ENV") == "development":
        app.run(debug=True)
