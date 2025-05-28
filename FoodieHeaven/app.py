import streamlit as st
import mysql.connector
import csv
import re
from fuzzywuzzy import fuzz

# ---------- CONFIGURATION ----------
CSV_FILE = 'IndianFoodDataset.csv'
HOST = 'localhost'
USER = 'root'
PASSWORD = 'Hmd71hmd'
DATABASE = 'recipe'
# -----------------------------------

def clean_ingredient(text):
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\b(cup|cups|tbsp|tablespoon|tsp|teaspoon|gm|g|kg|ml|ltr|litre|pinch|clove|piece|slices?)\b', '', text)
    text = re.sub(r'[^\w\s,]', '', text)
    return text.lower().strip()

def insert_data_from_csv():
    try:
        conn = mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS recipes ("
                       "id INT AUTO_INCREMENT PRIMARY KEY, "
                       "name TEXT, ingredients TEXT, instructions TEXT, cuisine TEXT)")
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
        st.error(f"Database Insert Error: {e}")

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

# ---------------- STREAMLIT UI ----------------

st.set_page_config(page_title="Smart Recipe Recommender", layout="wide")
st.title("🍛 Smart Recipe Recommender System")

insert_data_from_csv()

with st.form("ingredient_form"):
    ingredients_input = st.text_area("Enter your available ingredients (comma-separated):", height=100)
    submitted = st.form_submit_button("Recommend Recipes")

if submitted:
    if not ingredients_input.strip():
        st.warning("Please enter at least one ingredient.")
    else:
        st.markdown("### 🔍 Recommended Recipes")
        results = get_recommendations(ingredients_input)
        if not results:
            st.info("No recipes found with at least 60% match. Try adding more or different ingredients.")
        else:
            for percent, matched, missing, recipe in results:
                st.markdown(f"#### 🥘 {recipe['name']} — `{percent:.1f}%` match")
                st.write(f"**✔️ Matched Ingredients**: {', '.join(matched)}")
                if missing:
                    st.write(f"**❗Missing Ingredients**: {', '.join(missing)}")
                with st.expander("📖 Instructions"):
                    st.write(recipe["instructions"])
