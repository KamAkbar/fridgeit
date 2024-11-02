from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flash messages
DB_PATH = "food_expiration.db"

# Database setup function
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        expiration_date TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Home page - list all items
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, expiration_date FROM food_items")
    items = cursor.fetchall()
    conn.close()
    
    # Check for items expiring within 3 days and add notifications
    notifications = []
    today = datetime.today()
    for item_id, name, exp_date in items:
        days_left = (datetime.strptime(exp_date, "%Y-%m-%d") - today).days
        if 0 <= days_left <= 3:
            notifications.append(f"{name} expires in {days_left} day(s).")
    
    return render_template('index.html', items=items, notifications=notifications)

# Route to add new food items
@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    expiration_date = request.form['expiration_date']
    
    try:
        # Validate date format
        datetime.strptime(expiration_date, "%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO food_items (name, expiration_date) VALUES (?, ?)", (name, expiration_date))
        conn.commit()
        conn.close()
        flash(f"{name} added with expiration date {expiration_date}.", "success")
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
    
    return redirect(url_for('index'))

# Route to delete an item by ID
@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item removed successfully.", "success")
    return redirect(url_for('index'))

# Make API requests
API_KEY = "769c0353b2ba49558879cd467d54f0a2"  

@app.route('/suggest_recipes')
def suggest_recipes():
    # Fetch items from the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM food_items")
    items = cursor.fetchall()
    conn.close()

    # Collect ingredients and format them for the API request
    ingredients = ",".join([item[0] for item in items])

    # Fetch recipes from Spoonacular API
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&number=5&apiKey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        recipes = response.json()
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching recipes: {e}", "danger")
        recipes = []

    return render_template('recipes.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe_info(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=true&apiKey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        recipe_details = response.json()
        return render_template('recipe_info.html', recipe=recipe_details)
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching recipe details: {e}", "danger")
        return redirect(url_for('index'))  # Redirect to index on error


if __name__ == '__main__':
    setup_database()
    app.run(host="0.0.0.0", port=9000, debug=True)
