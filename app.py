# Import the Flask class from the flask module
from flask import Flask, render_template, request, redirect
from datetime import datetime
import os
from database import db  # Import the database instance


# Create a Flask application instance
app = Flask(__name__)

# Set the absolute path for the database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'todo.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the Flask app
db.init_app(app)


# Define the Todo model(create table in database using SQLAlchemy because  here we used SQLite database )
class Todo(db.Model):  # Todo is db table name
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(
        db.String(200), nullable=False
    )  # define title type, length and not null
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # It tells Python how to display the object when you print it.   (if we not using this then it will show object like --> <Todo object at 0x7f8a3c2b5e50>)
    def __repr__(self):
        return f"{self.sno}-{self.title}"


# ----------------------------------------------------CREATE ----------------------------------------------------
#create a route for the home page and allow both GET and POST requests
@app.route("/", methods=["GET", "POST"])
def demo():
    if request.method == "POST":      #Checks if the user submitted a form (POST request).
        title = request.form["title"]  # get title from form
        desc = request.form["desc"] # get desc from form
        todo = Todo(title=title, desc=desc) # creates a new object of the Todo class (which represents a task in the database).
        db.session.add(todo)  # add new todo to the database
        db.session.commit() #used to save the changes made to the database permanently.

    allTodo = Todo.query.all()  #fetch all todo from database
    return render_template(
        "index.html", allTodo=allTodo
    )  # send all todos to the index.html file and index.html file will display all todos


# ----------------------------------------------------READ----------------------------------------------------
@app.route("/show")
def show():
    allTodo = Todo.query.all()
    print(allTodo)
    return "this is product page"  # This function runs when someone visits 'http://127.0.0.1:5000/products'


# ----------------------------------------------------UPDATE----------------------------------------------------
@app.route("/update/<int:sno>", methods=["GET", "POST"])  #<int:sno>  for specific id
def update(sno):
    if request.method == "POST":
        title = request.form["title"] # get title from form
        desc = request.form["desc"] # get desc from form
        todo = Todo.query.filter_by(sno=sno).first() # get todo by sno  from database  
        todo.title = title  # update title
        todo.desc = desc # update desc
        db.session.add(todo) # add updated todo to the database
        db.session.commit()
        return redirect("/")

    todo = Todo.query.filter_by(sno=sno).first()
    return render_template("update.html", todo=todo)   #Fetches the task to be updated from the database.


# ----------------------------------------------------DELETE----------------------------------------------------
@app.route("/delete/<int:sno>")
def delete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    db.session.delete(todo)  # delete todo from database
    db.session.commit()
    return redirect("/")


# Run the Flask app only if this script is executed directly means run app.py file
if __name__ == "__main__":
    with app.app_context():  # Ensure Flask is in the application context
        db.create_all()  # Create database tables
        # exit()
        print("Database created successfully!")  # Confirmation message

    # Starts the development server, and 'debug=True' allows automatic reloading on changes.when we delopy our app then we set debug=False  so that it will not show error on browser to user
    app.run(debug=True)  