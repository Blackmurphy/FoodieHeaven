from flask import Flask, render_template, request
import mysql.connector
import csv
import re
from fuzzywuzzy import fuzz

app = Flask(__name__)

# CONFIGURATION 
CSV_FILE = 'IndianFoodDataset.csv'
HOST = 'localhost'
USER = 'root'
PASSWORD = 'Hmd71hmd'
DATABASE = 'recipe'

def clean_ingredient(text):
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\b(cup|cups|tbsp|tablespoon|tsp|teaspoon|gm|g|kg|ml|ltr|litre|pinch|clove|piece|slices?)\b', '', text)
    text = re.sub(r'[^\w\s,]', '', text)
    return text.lower().strip()

def insert_data_from_csv():
    try:
        conn = mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recipes")
        if cursor.fetchone()[0] > 0:
            return

        with open(CSV_FILE, 'r', encoding='ISO-8859-1') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT INTO recipes (name, ingredients, instructions, cuisine)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        row['Recipe Name'],
                        row['Ingredients'],
                        row['Instructions'],
                        row['Cuisine']
                    ))
                except:
                    continue
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("DB Insert Error:", e)

def fuzzy_match(user_ingredients, recipe_ingredients):
    matched = set()
    for user_ing in user_ingredients:
        for recipe_ing in recipe_ingredients:
            if fuzz.token_set_ratio(user_ing, recipe_ing) >= 80:
                matched.add(recipe_ing)
                break
    return matched

def get_recommendations(user_input):
    user_cleaned = clean_ingredient(user_input)
    user_ingredients = set(i.strip() for i in user_cleaned.split(",") if i.strip())

    conn = mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    cursor.close()
    conn.close()

    recommendations = []
    for recipe in recipes:
        if not recipe['ingredients']:
            continue
        cleaned = clean_ingredient(recipe['ingredients'])
        recipe_ingredients = set(i.strip() for i in cleaned.split(",") if i.strip())
        matched = fuzzy_match(user_ingredients, recipe_ingredients)
        if matched:
            percent = (len(matched) / len(user_ingredients)) * 100
            if percent >= 60:
                missing = recipe_ingredients - matched
                recommendations.append((percent, matched, missing, recipe))

    recommendations.sort(key=lambda x: x[0], reverse=True)
    return recommendations[:5]

@app.route("/", methods=["GET", "POST"])
def index():
    insert_data_from_csv()
    recipes = []
    if request.method == "POST":
        user_input = request.form["ingredients"]
        recipes = get_recommendations(user_input)
    return render_template("index.html", recipes=recipes)

if __name__ == "__main__":
    app.run(debug=True)
