import streamlit as st
import pandas as pd
import re

# Load dataset
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("IndianFoodDataset.csv", encoding='ISO-8859-1')
        df.dropna(subset=['Ingredients', 'Recipe Name', 'Instructions'], inplace=True)
        return df
    except FileNotFoundError:
        st.error("❌ CSV file not found. Make sure 'IndianFoodDataset.csv' is uploaded.")
        return pd.DataFrame()

# Clean ingredients
def clean_ingredients(text):
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\b(cup|cups|tbsp|tablespoon|tsp|teaspoon|gm|g|kg|ml|ltr|litre|pinch|clove|piece|slices?)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[^\w\s,]', '', text)
    return [i.strip().lower() for i in text.split(",") if i.strip()]

# Matching
def match_ingredients(user_ings, recipe_ings):
    matched = set()
    for u in user_ings:
        for r in recipe_ings:
            if u in r or r in u:
                matched.add(r)
                break
    return matched

# Recommender
def recommend_recipes(user_input, df):
    user_ings = clean_ingredients(user_input)
    if not user_ings:
        return []

    recommendations = []
    for _, row in df.iterrows():
        recipe_ings = clean_ingredients(row['Ingredients'])
        matched = match_ingredients(user_ings, recipe_ings)
        if matched:
            percent = (len(matched) / len(user_ings)) * 100
            if percent >= 60:
                missing = set(recipe_ings) - matched
                recommendations.append((percent, matched, missing, row))

    recommendations.sort(key=lambda x: x[0], reverse=True)
    return recommendations[:5]

# Streamlit UI
st.set_page_config(page_title="Smart Recipe Recommender", layout="wide")
st.title("🍽️ Smart Recipe Recommender System")

df = load_data()

with st.form("ingredients_form"):
    user_input = st.text_area("Enter available ingredients (comma-separated):", height=100)
    submitted = st.form_submit_button("🔍 Recommend Recipes")

if submitted:
    if df.empty:
        st.stop()

    if not user_input.strip():
        st.warning("Please enter some ingredients.")
    else:
        results = recommend_recipes(user_input, df)
        if not results:
            st.info("No recipes found with at least 60% match.")
        else:
            st.markdown("### 🧾 Recommended Recipes")
            for percent, matched, missing, recipe in results:
                st.markdown(f"#### 🥘 {recipe['Recipe Name']} — `{percent:.1f}% Match`")
                st.write(f"**✔️ Matched Ingredients**: {', '.join(matched)}")
                if missing:
                    st.write(f"**❗Missing Ingredients**: {', '.join(missing)}")
                with st.expander("📖 Instructions"):
                    st.write(recipe["Instructions"])
