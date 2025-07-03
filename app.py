import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import random, time, sys, atexit, csv
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from pymongo import MongoClient
import uuid
import threading
import re 
import requests 
from datetime import datetime, timedelta 
import traceback 
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import os


# Connect to MongoDB for data analysis (used by PricePredictor)
collection_analysis = None 
db_analysis = None
client_analysis = None
try:
    client_analysis = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client_analysis.server_info()  
    db_analysis = client_analysis["flight_database"]
    collection_analysis = db_analysis["flights"]
    print("MongoDB (analysis client) connected successfully.")
except Exception as e_analysis_client:
    print(f"Warning: MongoDB (analysis client) connection failed: {str(e_analysis_client)}")

# --- GLOBAL DATA ---
AIRPORT_DATA = {
    "CDG": {"name": "Paris Charles de Gaulle", "country": "France", "code": "CDG", "image_url": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1420&q=80"},
    "NRT": {"name": "Tokyo Narita", "country": "Japan", "code": "NRT", "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1494&q=80"},
    "JFK": {"name": "New York JFK", "country": "USA", "code": "JFK", "image_url": "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "DPS": {"name": "Bali Denpasar", "country": "Indonesia", "code": "DPS", "image_url": "https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "LHR": {"name": "London Heathrow", "country": "UK", "code": "LHR", "image_url": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "CMN": {"name": "Casablanca Mohammed V", "country": "Morocco", "code": "CMN", "image_url": "https://images.unsplash.com/photo-1588467856439-aefe9d873f42?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "RAK": {"name": "Marrakech Menara", "country": "Morocco", "code": "RAK", "image_url": "https://aeroport-marrakech.com/wp-content/uploads/2018/12/25.jpg"},
    "AGA": {"name": "Agadir Al Massira", "country": "Morocco", "code": "AGA", "image_url": "https://images.unsplash.com/photo-1607038517029-755180749515?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "BCN": {"name": "Barcelona El Prat", "country": "Spain", "code": "BCN", "image_url": "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1374&q=80"},
    "IST": {"name": "Istanbul Airport", "country": "Turkey", "code": "IST", "image_url": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "DXB": {"name": "Dubai International", "country": "UAE", "code": "DXB", "image_url": "https://images.unsplash.com/photo-1512453979791-6ea1e8782737?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "AMS": {"name": "Amsterdam Schiphol", "country": "Netherlands", "code": "AMS", "image_url": "https://images.unsplash.com/photo-1579036421379-add40fdefef9?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "ORY": {"name": "Paris Orly", "country": "France", "code": "ORY", "image_url": "https://media.istockphoto.com/id/2152340722/fr/photo/paris-orly-ory-airport-terminal-4-sud-in-france.jpg?s=612x612&w=0&k=20&c=pNdS0esIz8anPMJD_NBszOQ92-g0LzZmY79MarPuKiE="},
    "BVA": {"name": "Paris Beauvais", "country": "France", "code": "BVA", "image_url": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "VIL": {"name": "Vilnius Airport", "country": "Lithuania", "code": "VIL", "image_url": "https://static.routesonline.com/images/cached/newsarticle-299664159-scaled-620x0.jpg"},
    "LIS": {"name": "Lisbon Airport", "country": "Portugal", "code": "LIS", "image_url": "https://images.unsplash.com/photo-1555694489-4063APa4el2D?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "FCO": {"name": "Rome Fiumicino", "country": "Italy", "code": "FCO", "image_url": "https://images.unsplash.com/photo-1529260830199-42c24126f198?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "ROM": {"name": "Rome Fiumicino", "country": "Italy", "code": "FCO", "image_url": "https://images.unsplash.com/photo-1529260830199-42c24126f198?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80"},
    "DEFAULT_DEST_IMG": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1474&q=80"
}

AIRLINE_LOGOS = {
    "Royal Air Maroc": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Logo_Royal_Air_Maroc.svg/2560px-Logo_Royal_Air_Maroc.svg.png",
    "Vueling": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Logo_Vueling.svg/2560px-Logo_Vueling.svg.png",
    "Ryanair": "data:image/png;base64,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",
    "Transavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Transavia_logo.svg/2560px-Transavia_logo.svg.png",
    "Jetairfly": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Jetairfly_Logo.svg/1200px-Jetairfly_Logo.svg.png",
    "EasyJet": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/EasyJet_logo.svg/2560px-EasyJet_logo.svg.png",
    "easyJet": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/EasyJet_logo.svg/2560px-EasyJet_logo.svg.png",
    "TUI fly Belgium": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Netherlands": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Nordic": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI Airways": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly UK": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Germany": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Denmark": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Finland": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Poland": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Austria": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Switzerland": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Belgium": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Netherlands": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Nordic": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI Airways": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly UK": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Germany": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "TUI fly Denmark": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/TUI_Fly_Belgium_logo.svg/2560px-TUI_Fly_Belgium_logo.svg.png",
    "Air Arabia Maroc": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Air_Arabia_Logo.svg/1200px-Air_Arabia_Logo.svg.png",
    "Air Europa": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Air_Europa_Logo_%282015%29.svg/2560px-Air_Europa_Logo_%282015%29.svg.png",
    "British Airways": "https://upload.wikimedia.org/wikipedia/sco/thumb/4/42/British_Airways_Logo.svg/2560px-British_Airways_Logo.svg.png",
    "Iberia": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Logo_iberia_2013.png/1200px-Logo_iberia_2013.png",
    "Air France": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Air_France_Logo.svg/2560px-Air_France_Logo.svg.png",
    "Wizz Air": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Wizz_Air_logo.svg/2560px-Wizz_Air_logo.svg.png",
    "Emirates": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Emirates_logo.svg/2560px-Emirates_logo.svg.png",
    "Qatar Airways": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Qatar_Airways_Logo.svg/2560px-Qatar_Airways_Logo.svg.png",
    "Singapore Airlines": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Singapore_Airlines_logo_vertical.svg/1200px-Singapore_Airlines_logo_vertical.svg.png",
    "Delta Airlines": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/DELTA_AIR_LINES_LOGO.svg/2560px-DELTA_AIR_LINES_LOGO.svg.png",
    "DEFAULT": "/static/images/airlines/default_airline.png" 
}

class PricePredictor:
    def __init__(self):
        self._route_cache = {}  # Cache for {"FROM_TO_TAG": {"model": model_obj, "features": [feature_list]}}
        self.MIN_PLAUSIBLE_INTERNATIONAL_PRICE = 700  # MAD
        self.MAX_PLAUSIBLE_INTERNATIONAL_PRICE = 25000 # MAD
        
        os.makedirs("models", exist_ok=True)

    def _get_price_float_internal(self, price_str_or_num):
        if isinstance(price_str_or_num, (int, float)): 
            return float(price_str_or_num) if price_str_or_num >=0 else None

        if not price_str_or_num or price_str_or_num == "N/A" or "N/A" in str(price_str_or_num).upper():
            return None
        price_str_processed = str(price_str_or_num)
        cleaned_price = re.sub(r'(MAD|EUR|USD|\$|€|£)', '', price_str_processed, flags=re.IGNORECASE)
        cleaned_price = cleaned_price.replace(u'\xa0', '').replace(u'\u202f', '').replace(u'\u2009', '')
        cleaned_price = cleaned_price.replace(',', '').replace(' ', '').strip()
        try:
            price_match = re.search(r'(\d+\.?\d*)', cleaned_price)
            if price_match:
                price = float(price_match.group(1))
                return price if price >= 0 else None
            return None
        except ValueError:
            return None

    def train(self, flight_data_list):
        """
        Train a separate price-prediction model for every distinct (from, to) route
        found in `flight_data_list`. Each model is saved to models/<FROM>_<TO>_model.pkl
        along with its feature list.
        """
        try:
            if not flight_data_list:
                print("PricePredictor.train: No flight data provided.")
                return False

            routes_data_for_df = {} # Key: (from_code, to_code), Value: list of dicts for DataFrame

            for flight in flight_data_list:
                from_code = str(flight.get("from", "")).upper()
                to_code = str(flight.get("to", "")).upper()
                price = self._get_price_float_internal(flight.get("price") or flight.get("economy_price"))

                if not from_code or not to_code or price is None:
                    continue

                airline = str(flight.get("airline", "Unknown")).split(",")[0].strip()
                stops_str = str(flight.get("stops", "0")).lower()
                stops = 0
                if stops_str not in {"direct", "0", "0 stop", ""}:
                    match_num_stops = re.search(r'(\d+)', stops_str)
                    stops = int(match_num_stops.group(1)) if match_num_stops else 1

                days_to_departure = 30 # Default
                departure_date_str = flight.get("departure_date")
                if departure_date_str:
                    try:
                        dt_depart = datetime.strptime(departure_date_str, "%Y-%m-%d")
                        days_to_departure = max(0, (dt_depart - datetime.now()).days)
                    except (ValueError, TypeError): pass

                processed_row = {
                    "airline": airline,
                    "stops": stops,
                    "days_to_departure": days_to_departure,
                    "price": price # Target variable
                }

                route_key = (from_code, to_code)
                if route_key not in routes_data_for_df:
                    routes_data_for_df[route_key] = []
                routes_data_for_df[route_key].append(processed_row)

            if not routes_data_for_df:
                print("PricePredictor.train: No valid routes to train after processing input data.")
                return False

            trained_model_count = 0
            for route_key, route_rows_list in routes_data_for_df.items():
                orig, dest = route_key

                if len(route_rows_list) < 10: # Min samples for a somewhat useful model
                    print(f"Skipping route {orig}->{dest}: Insufficient data ({len(route_rows_list)} samples). Need at least 10.")
                    continue

                print(f"\nTraining model for route: {orig} -> {dest} with {len(route_rows_list)} samples.")
                df_route = pd.DataFrame(route_rows_list)

                X_route = df_route.drop(columns=["price"])
                y_route = df_route["price"]

                # One-Hot Encode 'airline' specifically for this route's data
                X_route_encoded = pd.get_dummies(X_route, columns=['airline'], prefix='airline', dummy_na=False)
                route_feature_columns = list(X_route_encoded.columns)

                if X_route_encoded.empty or not route_feature_columns:
                    print(f"Skipping route {orig}->{dest}: No features after encoding or empty dataset.")
                    continue

                # Split data
                if len(X_route_encoded) < 20: 
                    X_train, X_test, y_train, y_test = X_route_encoded, X_route_encoded, y_route, y_route
                else:
                    X_train, X_test, y_train, y_test = train_test_split(X_route_encoded, y_route, test_size=0.2, random_state=42)

                model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)

                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test) if len(X_test) > 0 else train_score 
                print(f"Route {orig}->{dest}: Train R2: {train_score:.3f}, Test R2: {test_score:.3f}")

                route_tag = f"{orig}_{dest}"
                model_path = os.path.join("models", f"{route_tag}_model.pkl")
                features_path = os.path.join("models", f"{route_tag}_features.pkl")

                joblib.dump(model, model_path)
                joblib.dump(route_feature_columns, features_path)
                print(f"Saved model to {model_path} and features to {features_path}")

                self._route_cache[route_tag] = {"model": model, "features": route_feature_columns}
                trained_model_count += 1

            if trained_model_count > 0:
                print(f"Training complete. {trained_model_count} route-specific models were trained/updated.")
                return True
            else:
                print("Training executed, but no new models were trained (e.g., due to insufficient data for all routes).")
                return False

        except Exception as e:
            print(f"Error during PricePredictor training: {e}")
            traceback.print_exc()
            return False

    def predict_price(self, prediction_data):
        """
        `prediction_data` dict: {'from':'CDG', 'to':'JFK', 'airline':'Air France', 'stops':0, 'departure_date':'YYYY-MM-DD'}
        """
        try:
            from_code = str(prediction_data.get("from", "")).upper()
            to_code = str(prediction_data.get("to", "")).upper()

            if not from_code or not to_code:
                print(f"PricePredictor.predict_price: 'from' ({from_code}) or 'to' ({to_code}) code missing or empty.")
                return None

            route_tag = f"{from_code}_{to_code}"
            print(f"PricePredictor.predict_price: Attempting prediction for route_tag: {route_tag}")


            if route_tag not in self._route_cache:
                model_path = os.path.join("models", f"{route_tag}_model.pkl")
                features_path = os.path.join("models", f"{route_tag}_features.pkl")
                if os.path.exists(model_path) and os.path.exists(features_path):
                    print(f"PricePredictor.predict_price: Loading model for route {route_tag} from disk.")
                    model = joblib.load(model_path)
                    features = joblib.load(features_path)
                    self._route_cache[route_tag] = {"model": model, "features": features}
                else:
                    print(f"PricePredictor.predict_price: No trained model found on disk for route {route_tag} (model: {model_path}, features: {features_path}).")
                    return None

            route_model_info = self._route_cache[route_tag]
            model = route_model_info["model"]
            route_feature_columns = route_model_info["features"]

            airline = str(prediction_data.get("airline", "Unknown")).split(",")[0].strip()
            stops_str = str(prediction_data.get("stops", "0")).lower()
            stops = 0
            if stops_str not in {"direct", "0", "0 stop", ""}:
                match_num_stops = re.search(r'(\d+)', stops_str)
                stops = int(match_num_stops.group(1)) if match_num_stops else 1

            days_to_departure = prediction_data.get("days_to_departure")
            if days_to_departure is None:
                departure_date_str = prediction_data.get("departure_date")
                if departure_date_str:
                    try:
                        dt_depart = datetime.strptime(departure_date_str, "%Y-%m-%d")
                        days_to_departure = max(0, (dt_depart - datetime.now()).days)
                    except (ValueError, TypeError): days_to_departure = 30
                else: days_to_departure = 30

            input_data_for_df = {feature_name: 0 for feature_name in route_feature_columns}

            if 'stops' in input_data_for_df: input_data_for_df['stops'] = stops
            if 'days_to_departure' in input_data_for_df: input_data_for_df['days_to_departure'] = days_to_departure

            airline_column_name_in_model = f"airline_{airline}"
            if airline_column_name_in_model in input_data_for_df:
                input_data_for_df[airline_column_name_in_model] = 1
            else:
                print(f"PricePredictor.predict_price: Airline '{airline}' (column '{airline_column_name_in_model}') not found in model features for route {route_tag}. Using model without this airline specific feature.")


            df_predict = pd.DataFrame([input_data_for_df])[route_feature_columns]
            print(f"PricePredictor.predict_price: Input DataFrame for prediction ({route_tag}):\n{df_predict.head()}")


            predicted_price = model.predict(df_predict)[0]
            print(f"PricePredictor.predict_price: Raw model prediction for {route_tag}: {predicted_price}")


            is_international = False
            if from_code in AIRPORT_DATA and to_code in AIRPORT_DATA:
                is_international = AIRPORT_DATA[from_code]["country"] != AIRPORT_DATA[to_code]["country"]
            
            if is_international:
                if not (self.MIN_PLAUSIBLE_INTERNATIONAL_PRICE <= predicted_price <= self.MAX_PLAUSIBLE_INTERNATIONAL_PRICE):
                    print(f"PricePredictor.predict_price: Predicted price {predicted_price} for international route {route_tag} is outside plausible range ({self.MIN_PLAUSIBLE_INTERNATIONAL_PRICE}-{self.MAX_PLAUSIBLE_INTERNATIONAL_PRICE}). Returning None.")
                    return None
            
            print(f"PricePredictor.predict_price: Final predicted price for {route_tag}: {round(predicted_price, 2)}")
            return round(predicted_price, 2)

        except Exception as e:
            print(f"Error in PricePredictor.predict_price for route {prediction_data.get('from','?')}-{prediction_data.get('to','?')}: {e}")
            traceback.print_exc()
            return None

    def predict_price_trend(self, prediction_data_base, offsets=(7, 15, 30)):
        global collection_analysis 
        try:
            from_code = str(prediction_data_base.get("from", "")).upper()
            to_code = str(prediction_data_base.get("to", "")).upper()

            if not from_code or not to_code:
                print("PricePredictor.predict_price_trend: 'from' or 'to' missing.")
                return None
            print(f"PricePredictor.predict_price_trend: Generating trend for {from_code}->{to_code}")


            historic_prices_list = []
            if collection_analysis is not None: 
                pipeline = [
                    {"$match": {
                        "status": "completed", "has_error": {"$ne": True},
                        "from": from_code,
                        "to": to_code
                    }},
                    {"$unwind": "$flights"},
                    {"$match": {
                        "flights.from": from_code,
                        "flights.to": to_code,
                        "$or": [
                            {"flights.price": {"$exists": True, "$ne": None, "$ne": "N/A"}},
                            {"flights.economy_price": {"$exists": True, "$ne": None, "$ne": "N/A"}}
                        ]
                    }},
                    {"$project": {
                        "_id": 0,
                        "price_val": "$flights.price",
                        "eco_price_val": "$flights.economy_price"
                    }}
                ]

                results = collection_analysis.aggregate(pipeline)
                for res in results:
                    price = self._get_price_float_internal(res.get("price_val"))
                    if price is None:
                        price = self._get_price_float_internal(res.get("eco_price_val"))
                    if price is not None:
                        historic_prices_list.append(price)
                print(f"PricePredictor.predict_price_trend: Found {len(historic_prices_list)} historical prices for {from_code}->{to_code}.")

            avg_hist_price = sum(historic_prices_list) / len(historic_prices_list) if historic_prices_list else None
            min_hist_price = min(historic_prices_list) if historic_prices_list else None
            max_hist_price = max(historic_prices_list) if historic_prices_list else None

            today = datetime.now()
            future_price_predictions = {}
            trend_prices_for_heuristic = []

            base_airline = prediction_data_base.get('airline', 'Unknown')
            base_stops = prediction_data_base.get('stops', 0)

            for days_offset in offsets:
                target_date_obj = today + timedelta(days=days_offset)
                target_date_str = target_date_obj.strftime("%Y-%m-%d")

                current_prediction_input = {
                    **prediction_data_base,
                    'departure_date': target_date_str,
                    'airline': base_airline,
                    'stops': base_stops
                }

                predicted_p = self.predict_price(current_prediction_input)
                print(f"PricePredictor.predict_price_trend: Prediction for {target_date_str} ({from_code}->{to_code}): {predicted_p}")
                if predicted_p is not None:
                    future_price_predictions[target_date_str] = predicted_p
                    trend_prices_for_heuristic.append(predicted_p)
            
            trend = "stable"
            if len(trend_prices_for_heuristic) >= 2:
                first_pred, last_pred = trend_prices_for_heuristic[0], trend_prices_for_heuristic[-1]
                if last_pred > first_pred * 1.05: trend = "rising"
                elif last_pred < first_pred * 0.95: trend = "falling"
            
            trend_result = {
                "avg_price": round(avg_hist_price,2) if avg_hist_price is not None else None,
                "min_price": round(min_hist_price,2) if min_hist_price is not None else None,
                "max_price": round(max_hist_price,2) if max_hist_price is not None else None,
                "future_prices": future_price_predictions,
                "trend": trend
            }
            print(f"PricePredictor.predict_price_trend: Trend data for {from_code}->{to_code}: {trend_result}")
            return trend_result
        except Exception as e:
            print(f"Error in PricePredictor.predict_price_trend for {from_code}->{to_code}: {e}")
            traceback.print_exc()
            return None


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'flight_insight_secret_key'
chrome_init_lock = threading.Lock()

# Initialize price predictor (global instance)
price_predictor = PricePredictor()

# Selectors for TravelWings
SEL = {
    "flight_results_container": "div.round-trip[data-ng-if='flight.pageLoader==false']",
    "main_flight_card": "div[data-tag='tw.flight.result.card']",
    "card_airline_name": "p[data-tag='tw.flight.result.card.trip.airlineName']",
    "card_dep_time": "p[data-tag='tw.flight.result.card.trip.originTime']",
    "card_arr_time": "p[data-tag='tw.flight.result.card.trip.destinationTime']",
    "card_dep_airport_code": "p[data-tag='tw.flight.result.card.trip.originAirport']",
    "card_arr_airport_code": "p[data-tag='tw.flight.result.card.trip.destinationAirport']",
    "card_duration": "span[data-tag='tw.flight.result.card.trip.travelTime']",
    "card_stops": "span[data-tag='tw.flight.result.card.trip.travelStop']",
    "card_price_value": "span[data-tag='tw.flight.result.card.price'].price-value",
    "card_price_currency": "span[data-tag='tw.flight.result.card.currency']",
    "card_refundable_status": "span[data-tag='tw.flight.result.card.refundable']",
    "card_layover_time": "p[data-tag='tw.flight.result.card.trip.travelStop.layoverTime']",
    "card_layover_airport": "span[data-tag='tw.flight.result.card.trip.travelStop.airportCode']",
    "card_select_button": "button[data-tag='tw.flight.result.card.select']"
}

# Connect to MongoDB (main connection for Flask app)
mongodb_connected = False
flights_collection = None
db = None
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['flight_database']
    flights_collection = db['flights']
    mongodb_connected = True
    print("MongoDB connected successfully.")
except Exception as e:
    print(f"Warning: MongoDB connection failed: {str(e)}")



def pause_script(a=0.8, b=1.6):
    time.sleep(random.uniform(a, b))

def set_journey_type(driver, wait, journey_type):
    try:
        journey_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[aria-label*="fc-booking-journey-type-aria-label"]')
        ))
        journey_btn.click()
        pause_script(1, 1.5)
        option_xpath = '//li[.//span[contains(@class, "css-0") and text()="Aller simple"]]'
        if journey_type != "Aller simple":
            option_xpath = f'//li[.//span[contains(@class, "css-0") and text()="{journey_type}"]]'

        option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, option_xpath)
        ))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", option)
        pause_script(0.2, 0.5)
        option.click()
        pause_script(1, 1.5)
    except Exception as e:
        print(f"Error setting journey type: {str(e)}")
        raise

def fill_airport(driver, wait, aria_label, code):
    field = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, f'input[aria-label="{aria_label}"]')))
    field.clear()
    field.send_keys(code)
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[role="option"]'))).click()
    pause_script()

def navigate_to_month(driver, wait, target_date):
    max_attempts = 12
    attempts = 0
    if len(target_date.split('-')[0]) != 4 :
        print(f"Warning: Unusual target_date format in navigate_to_month: {target_date}")

    while not driver.find_elements(By.CSS_SELECTOR, f'[data-att="day-{target_date}"]'):
        try:
            next_month_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-att="next-month"]')))
            driver.execute_script("arguments[0].click();", next_month_btn)
            pause_script(0.5, 1)
        except Exception as e:
            print(f"Error navigating to month (clicking next): {str(e)}")
            try:
                driver.execute_script("""
                    var nextBtn = document.querySelector('[data-att="next-month"]');
                    if(nextBtn) nextBtn.click();
                """)
                pause_script(0.5, 1)
            except Exception as e_js:
                print(f"JS click for next_month_btn also failed: {e_js}")
                break
        attempts += 1
        if attempts >= max_attempts:
            print(f"Maximum month navigation attempts ({max_attempts}) reached for date {target_date}. Date element not found.")
            break


def select_single_date(driver, wait, target_date_yyyy_mm_dd):
    try:
        date_picker_toggler = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-att="start-date-toggler"]')
        ))
        try:
            is_picker_open = False
            try:
                if driver.find_element(By.CSS_SELECTOR, '[data-att^="day-"]').is_displayed():
                    is_picker_open = True
            except:
                pass

            if not is_picker_open:
                date_picker_toggler.click()
                pause_script(0.5, 1)
        except Exception as e_click_toggler:
             print(f"Error clicking date_picker_toggler (or picker already open): {e_click_toggler}")
             if not is_picker_open:
                driver.execute_script("arguments[0].click();", date_picker_toggler)
                pause_script(0.5, 1)

        navigate_to_month(driver, wait, target_date_yyyy_mm_dd)

        date_element = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f'[data-att="day-{target_date_yyyy_mm_dd}"]')
        ))
        try:
            date_element.click()
        except:
            driver.execute_script("arguments[0].click();", date_element)
        pause_script(0.5, 1)

        try:
            done_button_candidates = driver.find_elements(By.CSS_SELECTOR, '[data-att="done"]')
            if done_button_candidates and done_button_candidates[0].is_displayed() and done_button_candidates[0].is_enabled():
                done_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '[data-att="done"]')
                ))
                done_button.click()
                pause_script(0.5, 1)
            else:
                print("Date picker 'Done' button not found/visible/enabled, or not required.")
        except TimeoutException:
            print("Date picker 'Done' button not found or not clickable (short timeout), assuming date selected.")
        except Exception as e_done:
            print(f"Error clicking 'Done' button: {e_done}, trying JS click.")
            try:
                done_button_js = driver.find_element(By.CSS_SELECTOR, '[data-att="done"]')
                if done_button_js.is_displayed() and done_button_js.is_enabled():
                    driver.execute_script("arguments[0].click();", done_button_js)
                    pause_script(0.5, 1)
            except Exception as e_js_done:
                 print(f"JS click for 'Done' button also failed or button not suitable: {e_js_done}")
    except Exception as e:
        print(f"Error selecting date {target_date_yyyy_mm_dd}: {str(e)}")
        raise

# Helper function record_scraper_completion
def record_scraper_completion(search_id, scraper_name_base, flight_data_list, error_message=None):
    if not mongodb_connected or flights_collection is None: # Corrected check
        print(f"MongoDB not connected. Cannot record completion for {scraper_name_base}.")
        return

    scraper_final_name = scraper_name_base
    current_timestamp = time.time()
    update_payload = {
        "$inc": {"scrapers_done": 1},
        "$push": {}
    }
    if flight_data_list:
        processed_flights_for_db = []
        for flight in flight_data_list:
            flight.setdefault('source', scraper_name_base)
            raw_price = flight.get('price') or flight.get('economy_price')
            if raw_price is None or str(raw_price).strip() == "" or "N/A" in str(raw_price):
                flight['price'] = "N/A"
            else:
                flight['price'] = str(raw_price)
            processed_flights_for_db.append(flight)

        if processed_flights_for_db:
             update_payload["$push"]["flights"] = {"$each": processed_flights_for_db}


    if error_message:
        scraper_final_name = f"{scraper_name_base}_failed"
        update_payload.setdefault("$set", {})["has_error"] = True
        update_payload["$push"]["error_details"] = {
            "scraper": scraper_name_base,
            "message": str(error_message),
            "timestamp": current_timestamp
        }

    update_payload["$push"]["scrapers_completed_log"] = {
        "name": scraper_final_name,
        "timestamp": current_timestamp,
        "had_error": bool(error_message),
        "flights_found": len(flight_data_list) if flight_data_list else 0
    }

    flights_collection.update_one({"search_id": search_id}, update_payload)

    search_doc = flights_collection.find_one({"search_id": search_id})
    if not search_doc:
        print(f"Search document {search_id} not found after update by {scraper_name_base}.")
        return

    scrapers_done_count = search_doc.get("scrapers_done", 0)
    scrapers_total_count = search_doc.get("scrapers_total", 3)
    has_error_flag = search_doc.get("has_error", False)
    current_db_status = search_doc.get("status")
    new_status = current_db_status

    if scrapers_done_count >= scrapers_total_count:
        if has_error_flag and any(err_detail.get("scraper") for err_detail in search_doc.get("error_details",[])):
            new_status = "failed"
        else:
            new_status = "completed"
    else:
        if has_error_flag and current_db_status != "failed":
             new_status = "in_progress_with_errors"
        elif not has_error_flag:
             new_status = "in_progress"

    if new_status != current_db_status:
        flights_collection.update_one(
            {"search_id": search_id},
            {"$set": {"status": new_status}}
        )
        print(f"Search {search_id}: Status changed from '{current_db_status}' to '{new_status}' by {scraper_name_base}.")


# Royal Air Maroc Scraper Specific Functions
def scrape_flights(driver, main_from_code, main_to_code): 
    flights = []
    try:
        show_more_wait = WebDriverWait(driver, 7)
        attempt_count = 0
        max_attempts = 3

        while attempt_count < max_attempts:
            try:
                more_btn = show_more_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.show-more-flights-button')))
                if more_btn.is_displayed() and more_btn.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", more_btn)
                    pause_script(0.3,0.6)
                    driver.execute_script("arguments[0].click();", more_btn)
                    print("RAM: Clicked 'Show more flights'.")
                    pause_script(2, 3.5)
                    attempt_count +=1
                else:
                    print("RAM: 'Show more flights' button not displayed or enabled.")
                    break
            except TimeoutException:
                print("RAM: 'Show more flights' button not found or not clickable in time, assuming all flights loaded.")
                break
            except Exception as e_more:
                print(f"RAM: Error clicking 'Show more flights': {e_more}, proceeding.")
                break
    except Exception as e_outer_more:
        print(f"RAM: Outer error in 'Show more flights' logic: {e_outer_more}")

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    flight_cards = soup.select('div.bound-element')
    print(f"RAM: Found {len(flight_cards)} flight cards after 'show more' attempts.")

    for card_index, card in enumerate(flight_cards):
        try:
            departure_time_el = card.select_one('time#departureTime')
            arrival_time_el = card.select_one('time#arrivalTime')
            departure_airport_el = card.select_one('abbr#departureLocation')
            arrival_airport_el = card.select_one('abbr#arrivalLocation')
            duration_el = card.select_one('span.total-duration')
            stops_element = card.select_one('span.number-of-stops')
            economy_price_el = card.select_one('div.eco-cabin span.price-amount')
            business_price_el = card.select_one('div.business-cabin span.price-amount')

            if not all([departure_time_el, arrival_time_el, duration_el]):
                print(f"RAM: Skipping card {card_index+1} due to missing core flight details (time/duration).")
                continue

            if not economy_price_el and not business_price_el:
                print(f"RAM: Skipping card {card_index+1} as no price (economy or business) found.")
                continue

            departure_time = departure_time_el.get_text(strip=True)
            arrival_time = arrival_time_el.get_text(strip=True)
            departure_airport = departure_airport_el.get_text(strip=True) if departure_airport_el else main_from_code
            arrival_airport = arrival_airport_el.get_text(strip=True) if arrival_airport_el else main_to_code
            duration = duration_el.get_text(strip=True)
            stops = stops_element.get_text(strip=True) if stops_element else 'Direct'

            economy_price_text = "N/A"
            if economy_price_el:
                economy_price_text = economy_price_el.get_text(strip=True).replace(u'\xa0', '').replace('MAD', '').strip()
                economy_price_formatted = f"MAD {economy_price_text}"
            else:
                economy_price_formatted = "N/A"

            business_price_text = "N/A"
            if business_price_el:
                business_price_text = business_price_el.get_text(strip=True).replace(u'\xa0', '').replace('MAD', '').strip()
                business_price_formatted = f"MAD {business_price_text}"
            else:
                business_price_formatted = "N/A"

            main_price_formatted = economy_price_formatted
            if main_price_formatted == "N/A":
                main_price_formatted = business_price_formatted

            if main_price_formatted == "N/A":
                 print(f"RAM: Skipping card {card_index+1} because main_price_formatted is N/A after checking eco/biz.")
                 continue

            booking_link = 'https://www.royalairmaroc.com/fr_ma/'

            flights.append({
                'airline': 'Royal Air Maroc',
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'from': departure_airport.upper(),
                'to': arrival_airport.upper(),
                'duration': duration,
                'stops': stops,
                'price': main_price_formatted,
                'economy_price': economy_price_formatted,
                'business_price': business_price_formatted,
                'booking_link': booking_link,
                'source': 'Royal Air Maroc'
            })
        except Exception as e:
            print(f"Error scraping one RAM flight card (index {card_index}): {str(e)}")
            continue
    return flights

def search_flights(search_id, from_code, to_code, departure_date_yyyy_mm_dd): # RAM search
    if not mongodb_connected:
        print("MongoDB not connected, RAM search cannot proceed.")
        record_scraper_completion(search_id, "royalairmaroc", [], "MongoDB not connected at start")
        return

    driver = None
    try:
        print(f"RAM ({search_id}): Attempting to acquire lock for Chrome initialization.")
        with chrome_init_lock:
            print(f"RAM ({search_id}): Lock acquired. Initializing Chrome.")
            opts = uc.ChromeOptions()
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument('--disable-blink-features=AutomationControlled')
            opts.page_load_strategy = 'eager'
            # Make browser visible for RAM
            driver = uc.Chrome(options=opts, headless=False, version_main=136)
            print(f"RAM ({search_id}): Chrome initialized (PageLoadStrategy: {opts.page_load_strategy}, Headless: False).")

        wait = WebDriverWait(driver, 40)

        print(f"RAM ({search_id}): Navigating to Royal Air Maroc site.")
        driver.get("https://www.royalairmaroc.com/fr_ma/")

        try:
            print(f"RAM ({search_id}): Waiting for key page elements (cookie banner or form fields)...")
            WebDriverWait(driver, 45).until(
                EC.any_of(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label*="fc-booking-journey-type-aria-label"]')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="fc-booking-origin-aria-label"]'))
                )
            )
            print(f"RAM ({search_id}): Key element found. Page seems interactive.")
        except TimeoutException:
            print(f"RAM ({search_id}): Timed out waiting for key element after driver.get(). Page might not have loaded correctly.")
            if driver: driver.save_screenshot(f"error_ram_key_element_timeout_{search_id}.png")
            raise

        pause_script(0.5,1)

        try:
            accept_cookies_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_cookies_btn.click()
            print(f"RAM ({search_id}): Cookies accepted.")
            pause_script(0.5, 1)
        except Exception as e_cookie:
            print(f"RAM ({search_id}): Cookies button not found or not clickable: {e_cookie}")

        set_journey_type(driver, wait, "Aller simple")
        fill_airport(driver, wait, "fc-booking-origin-aria-label", from_code)
        fill_airport(driver, wait, "fc-booking-destination-aria-label", to_code)
        select_single_date(driver, wait, departure_date_yyyy_mm_dd)

        search_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-att="search"]')
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
        pause_script(0.2,0.5)
        search_button.click()
        print(f"RAM ({search_id}): Search initiated for {from_code} to {to_code} on {departure_date_yyyy_mm_dd}.")

        flight_data = []
        try:
            print(f"RAM ({search_id}): Waiting for flight result cards ('div.bound-element') to appear...")
            WebDriverWait(driver, 75).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.bound-element'))
            )
            print(f"RAM ({search_id}): At least one flight card ('div.bound-element') found. Results page seems loaded.")
            pause_script(3, 5)
            flight_data = scrape_flights(driver, from_code, to_code)
        except TimeoutException as e_results:
            print(f"RAM ({search_id}): Timed out waiting for flight cards ('div.bound-element'). {e_results}")
            if driver: driver.save_screenshot(f"error_ram_no_flight_cards_timeout_{search_id}.png")

            no_flights_msg_found = False
            try:
                no_flights_msg_xpath = "//*[contains(text(), 'Aucun vol disponible') or contains(text(), 'No flights available') or contains(text(), 'pas de vols disponibles') or contains(text(), 'No direct flights') or contains(text(), 'No results found') or contains(text(), 'Aucun résultat') or contains(@class, 'no-flights') or contains(@class, 'no-results') or contains(@class, 'msg-no-flight')]"
                no_flights_elements = driver.find_elements(By.XPATH, no_flights_msg_xpath)
                if any(el.is_displayed() for el in no_flights_elements):
                    no_flights_msg_found = True
                    print(f"RAM ({search_id}): Explicit 'no flights found' message detected on the page.")
            except Exception as find_ex:
                print(f"RAM ({search_id}): Error trying to find 'no flights' message: {find_ex}")

            if not no_flights_msg_found:
                print(f"RAM ({search_id}): No flight cards found and no explicit 'no flights' message detected.")

        print(f"RAM ({search_id}): Scraped {len(flight_data)} flights.")
        record_scraper_completion(search_id, "royalairmaroc", flight_data)

    except Exception as e:
        error_message = f"Error in Royal Air Maroc search_flights ({search_id}): {type(e).__name__} - {str(e)}"
        print(error_message)
        if driver:
            try:
                if not ('e_results' in locals() and isinstance(e, TimeoutException)):
                     driver.save_screenshot(f"error_ram_main_exception_{search_id}.png")
                     print(f"RAM ({search_id}): Screenshot saved: error_ram_main_exception_{search_id}.png")
            except Exception as se:
                print(f"RAM ({search_id}): Failed to save screenshot: {se}")
        record_scraper_completion(search_id, "royalairmaroc", [], error_message)
    finally:
        if driver:
            
            if not driver.options.headless: 
                print(f"RAM ({search_id}): Search complete. Browser will close in 5 seconds.")
                time.sleep(5)
            driver.quit()
        print(f"Royal Air Maroc search ended for {search_id}")


# Aviasales Scraper Specific Functions
def aviasales_pause(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))

def scrape_aviasales(driver, wait, search_id, from_code_param, to_code_param):
    flights = []
    try:
        print(f"Aviasales ({search_id}): Waiting for flight cards list to load ('div[data-test-id=\"search-results-items-list\"]')...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test-id="search-results-items-list"]')))
        print(f"Aviasales ({search_id}): Flight cards list container detected. Giving time for content rendering...")

        aviasales_pause(7, 10)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        flight_cards = soup.select('div[data-test-id="ticket-preview"]')
        print(f"Aviasales ({search_id}): Found {len(flight_cards)} potential flight cards ('div[data-test-id=\"ticket-preview\"]').")

        eur_to_mad_rate = 10.8
        usd_to_mad_rate = 10.0

        for card_index, card in enumerate(flight_cards):
            try:
                airline_logo_elements = card.select('div.s__iLii9nj713he1PD8WMQ9 img[alt]')
                airline_names = [logo_el['alt'] for logo_el in airline_logo_elements if logo_el.has_attr('alt') and logo_el['alt']]

                airline_text_el = card.select_one('div.s__zd5b4BW9AJ6975mGH405[data-test-id="text"], span[data-test-id="airline-name"]')
                if airline_text_el:
                    text_airline = airline_text_el.get_text(strip=True)
                    if text_airline and text_airline not in airline_names:
                        airline_names.insert(0, text_airline)

                if not airline_names:
                    fallback_airline_el = card.select_one('div[data-test-id="text"][style*="color: rgb"]')
                    if fallback_airline_el: airline_names.append(fallback_airline_el.get_text(strip=True))

                airline = ', '.join(list(dict.fromkeys(filter(None, airline_names)))) if airline_names else 'N/A'

                origin_endpoint = card.select_one('div[data-test-id="origin-endpoint"]')
                destination_endpoint = card.select_one('div[data-test-id="destination-endpoint"]')

                departure_time_el = origin_endpoint.select_one('span.s__o7ypaUnV4J9QEiFgKJq3[data-test-id="text"]') if origin_endpoint else None
                arrival_time_el = destination_endpoint.select_one('span.s__o7ypaUnV4J9QEiFgKJq3[data-test-id="text"]') if destination_endpoint else None

                dep_airport_code_el = origin_endpoint.select_one('span.s__iPfYoBmp1qVHqkPI5MCQ[data-test-id="text"]') if origin_endpoint else None
                arr_airport_code_el = destination_endpoint.select_one('span.s__iPfYoBmp1qVHqkPI5MCQ[data-test-id="text"]') if destination_endpoint else None

                from_airport_code = dep_airport_code_el.get_text(strip=True) if dep_airport_code_el else from_code_param
                to_airport_code = arr_airport_code_el.get_text(strip=True) if arr_airport_code_el else to_code_param


                duration_el = card.select_one('div[data-test-id="ticket-segment-route"] span.s__iPfYoBmp1qVHqkPI5MCQ[data-test-id="text"]')
                price_el = card.select_one('div.s__mvNEtCM6SuXfR8Kopm7T[data-test-id="text"], span[data-test-id="price"]')


                if not all([airline != 'N/A', departure_time_el, arrival_time_el, price_el]):
                    print(f"Aviasales ({search_id}): Skipping card {card_index+1} due to missing core elements (airline, times, or price).")
                    continue

                departure_time = departure_time_el.get_text(strip=True)
                arrival_time = arrival_time_el.get_text(strip=True)
                duration_text_raw = duration_el.get_text(strip=True) if duration_el else 'N/A'
                duration = duration_text_raw.replace('Travel time:', '').replace('\u200a', '').replace('\u202f', '').strip()

                stops = "Direct"
                layover_details_list = []
                layover_airport_els = card.select('div[data-test-id="ticket-segment-route"] div.s__rlTYRhcn2gWyUix5hTE1 span[data-test-id="text"]')
                if layover_airport_els:
                    num_stops = 0
                    for layover_el in layover_airport_els:
                        layover_text = layover_el.get_text(strip=True)
                        if layover_text and layover_text.upper() not in [from_airport_code.upper(), to_airport_code.upper()]:
                            layover_details_list.append(layover_text)
                            num_stops += 1
                    if num_stops > 0:
                        stops = f"{num_stops} stop{'s' if num_stops > 1 else ''}"

                price_text_raw = price_el.get_text(strip=True)
                price_currency_symbol = None
                if '€' in price_text_raw: price_currency_symbol = 'EUR'
                elif '$' in price_text_raw: price_currency_symbol = 'USD'

                price_text_cleaned = price_text_raw.replace('$', '').replace('€', '').replace('£', '') \
                                    .replace(',', '').replace(u'\u00a0', '').replace(u'\u2009', '') \
                                    .replace(u'\u202f', '').strip()

                price_mad_formatted = "N/A"
                try:
                    price_original_currency_float = float(price_text_cleaned)
                    price_mad_float = price_original_currency_float

                    if price_currency_symbol == 'EUR':
                        price_mad_float = price_original_currency_float * eur_to_mad_rate
                    elif price_currency_symbol == 'USD':
                        price_mad_float = price_original_currency_float * usd_to_mad_rate

                    price_mad_formatted = f"MAD {price_mad_float:.2f}"
                except ValueError:
                    print(f"Aviasales ({search_id}): Could not parse price '{price_text_raw}' (cleaned: '{price_text_cleaned}') to float.")
                    price_mad_formatted = f"MAD N/A (raw: {price_text_raw})"

                booking_link = driver.current_url

                flight_info = {
                    'airline': airline,
                    'departure_time': departure_time,
                    'arrival_time': arrival_time,
                    'from': from_airport_code.upper(),
                    'to': to_airport_code.upper(),
                    'duration': duration,
                    'stops': stops,
                    'price': price_mad_formatted,
                    'refundable': "Info N/A",
                    'booking_link': booking_link,
                    'source': 'Aviasales'
                }
                if layover_details_list:
                    unique_layovers = list(dict.fromkeys(layover_details_list))
                    flight_info['layover'] = f"Layover at {', '.join(unique_layovers)}"

                flights.append(flight_info)
            except Exception as e_card:
                print(f"Aviasales ({search_id}): Error scraping one flight card (index {card_index+1}): {type(e_card).__name__} - {str(e_card)}")
                continue

        print(f"Aviasales ({search_id}): Successfully scraped {len(flights)} flight offers.")
        return flights

    except TimeoutException:
        print(f"Aviasales ({search_id}): Timeout waiting for flight cards list after initial detection.")
        return []
    except Exception as e_scrape_main:
        print(f"Aviasales ({search_id}): Major error in scrape_aviasales function: {type(e_scrape_main).__name__} - {str(e_scrape_main)}")
        return []


def search_aviasales(search_id, from_code, to_code, departure_date_str_yyyy_mm_dd):
    if not mongodb_connected:
        print(f"MongoDB not connected, Aviasales search ({search_id}) cannot proceed.")
        record_scraper_completion(search_id, "aviasales", [], "MongoDB not connected at start")
        return

    driver = None
    try:
        print(f"Aviasales ({search_id}): Attempting to acquire lock for Chrome initialization.")
        with chrome_init_lock:
            print(f"Aviasales ({search_id}): Lock acquired. Initializing Chrome.")
            opts = uc.ChromeOptions()
            # opts.add_argument('--headless=new') # Make browser visible for Aviasales 
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument('--disable-blink-features=AutomationControlled')
            # Make browser visible for Aviasales
            driver = uc.Chrome(options=opts, headless=False, version_main=136)
            print(f"Aviasales ({search_id}): Chrome initialized (Headless: False).")

        wait = WebDriverWait(driver, 45)

        try:
            date_parts = departure_date_str_yyyy_mm_dd.split('-')
            day = date_parts[2]
            month = date_parts[1]
            date_ddmm = f"{day}{month}"
        except (IndexError, ValueError) as e_date:
            error_msg = f"Invalid departure date format for Aviasales: '{departure_date_str_yyyy_mm_dd}'. Expected YYYY-MM-DD. Error: {e_date}"
            print(error_msg)
            record_scraper_completion(search_id, "aviasales", [], error_msg)
            return

        passengers_block = "1"
        marker = "573812.Zz8dbab13b019740cd85fb734-573812" 
        url = (
            "https://www.aviasales.com/search/"
            f"{from_code}{date_ddmm}{to_code}{passengers_block}"
            f"?currency=eur&language=en&marker={marker}&with_request=true"
        )

        print(f"Aviasales ({search_id}): Navigating to URL: {url}")
        driver.get(url)
        print(f"Aviasales ({search_id}): driver.get() completed.")

        flight_data = []
        try:
            print(f"Aviasales ({search_id}): Waiting for page to indicate load (results, no-results, or error)...")
            WebDriverWait(driver, 90).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test-id="search-results-items-list"]')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.prediction-advice__text')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.error__title')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.empty-message')),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'No flights found') or contains(text(), 'Unfortunately, there are no flights')]"))
                )
            )
            print(f"Aviasales ({search_id}): Page load indicator found.")
            aviasales_pause(2,4)

            no_flights_found = False
            no_flights_selectors = [
                "//*[contains(@class, 'empty-message') and contains(normalize-space(), 'No flights found')]",
                "//*[contains(@class, 'stub__title')]", 
                "//*[contains(@class, 'prediction-advice__text') and (contains(.,'no flights') or contains(.,'Unfortunately'))]",
                "//div[@data-test-id='search-results-title' and contains(normalize-space(),'no flights')]",
                "//div[@class='error__title']" 
            ]
            for selector in no_flights_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if any(el.is_displayed() for el in elements):
                        print(f"Aviasales ({search_id}): Explicit 'no flights' or error message detected via selector '{selector}'.")
                        no_flights_found = True
                        break
                except:
                    pass 

            if not no_flights_found:
                print(f"Aviasales ({search_id}): No explicit 'no flights/error' message. Attempting to scrape flight data...")
                flight_data = scrape_aviasales(driver, wait, search_id, from_code, to_code)
            else:
                 print(f"Aviasales ({search_id}): Skipping scrape_aviasales due to 'no flights' or error message pre-detection.")

        except TimeoutException:
            print(f"Aviasales ({search_id}): Timed out waiting for results, 'no flights' message, or error. Page might be stuck or very slow.")
            if driver: driver.save_screenshot(f"error_aviasales_results_timeout_{search_id}.png")
            raise 

        print(f"Aviasales ({search_id}): Scraped {len(flight_data)} flights.")
        record_scraper_completion(search_id, "aviasales", flight_data)

    except Exception as e:
        error_msg = f"Error in Aviasales search_flights ({search_id}): {type(e).__name__} - {str(e)}"
        print(error_msg)
        traceback.print_exc() 
        if driver:
            try:
                driver.save_screenshot(f"error_aviasales_main_exception_{search_id}.png")
                print(f"Aviasales ({search_id}): Screenshot saved: error_aviasales_main_exception_{search_id}.png")
            except Exception as se:
                print(f"Aviasales ({search_id}): Failed to save screenshot during main error: {se}")
        record_scraper_completion(search_id, "aviasales", [], error_msg)
    finally:
        if driver:
            
            if not driver.options.headless: 
                print(f"Aviasales ({search_id}): Search complete. Browser will close in 5 seconds.")
                time.sleep(5)
            driver.quit()
        print(f"Aviasales search ended for {search_id}")


# TravelWings Scraper Specific Functions
def scrape_travelwings(driver, wait, main_from_code, main_to_code):
    flights = []
    try:
        print("TravelWings: Waiting for flight results container...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEL['flight_results_container'])))
        print("TravelWings: Flight results container found. Giving time for results to populate...")
        pause_script(5, 8) # Wait for JS to render results

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        flight_cards = soup.select(SEL['main_flight_card'])
        print(f"TravelWings: Found {len(flight_cards)} flight cards based on selector '{SEL['main_flight_card']}'.")

        if not flight_cards:
            # Double-check for "no flights" message if container is present but no cards
            try:
                no_flights_msg_xpath = "//*[contains(text(), 'Sorry, no flights found') or contains(@class, 'no-flight-found') or contains(text(), 'No flights available for your selection') or contains(@class,'flight-not-found-msg')]"
                no_flights_elements_tw = driver.find_elements(By.XPATH, no_flights_msg_xpath)
                if any(el.is_displayed() for el in no_flights_elements_tw):
                    print("TravelWings: Explicit 'no flights found' message detected on page (after container presence).")
                    return []
            except Exception as e_nf_check:
                print(f"TravelWings: Error checking for 'no flights' message: {e_nf_check}")


        for card_index, card in enumerate(flight_cards):
            try:
                airline_el = card.select_one(SEL['card_airline_name'])
                dep_time_el = card.select_one(SEL['card_dep_time'])
                arr_time_el = card.select_one(SEL['card_arr_time'])
                dep_airport_el = card.select_one(SEL['card_dep_airport_code'])
                arr_airport_el = card.select_one(SEL['card_arr_airport_code'])
                duration_el = card.select_one(SEL['card_duration'])
                stops_el = card.select_one(SEL['card_stops'])
                price_currency_el = card.select_one(SEL['card_price_currency'])
                price_value_el = card.select_one(SEL['card_price_value'])
                refundable_status_el = card.select_one(SEL['card_refundable_status'])

                flight_info = {'source': 'TravelWings'}

                def get_text_safe(element, default_val="N/A"):
                    return element.get_text(strip=True) if element else default_val

                flight_info['airline'] = get_text_safe(airline_el)
                flight_info['departure_time'] = get_text_safe(dep_time_el)
                flight_info['arrival_time'] = get_text_safe(arr_time_el)
                flight_info['from'] = get_text_safe(dep_airport_el, main_from_code).upper()
                flight_info['to'] = get_text_safe(arr_airport_el, main_to_code).upper()
                flight_info['duration'] = get_text_safe(duration_el)
                flight_info['stops'] = get_text_safe(stops_el)

                price_currency = get_text_safe(price_currency_el).upper()
                price_value_raw = get_text_safe(price_value_el)
                price_value = price_value_raw.replace(',', '') 

                if price_currency != "N/A" and price_value != "N/A":
                    flight_info['price'] = f"{price_currency} {price_value}"
                else:
                    flight_info['price'] = "N/A"

                flight_info['refundable'] = get_text_safe(refundable_status_el, 'Info N/A')

                # Check if essential fields are missing before appending
                essential_fields = [flight_info['airline'], flight_info['departure_time'], flight_info['arrival_time'], flight_info['price']]
                if any(v == "N/A" for v in essential_fields):
                    print(f"TravelWings: Skipping card {card_index+1} due to missing essential N/A data. Details: Airline='{flight_info['airline']}', DepTime='{flight_info['departure_time']}', ArrTime='{flight_info['arrival_time']}', Price='{flight_info['price']}'")
                    continue

                if flight_info['stops'] not in ['Direct', 'N/A', '0 Stop', '0 Stops']: 
                    layover_time_el = card.select_one(SEL['card_layover_time'])
                    layover_airport_el = card.select_one(SEL['card_layover_airport'])
                    layover_time_str = get_text_safe(layover_time_el)
                    layover_airport_str = get_text_safe(layover_airport_el)
                    if layover_time_str != "N/A" and layover_airport_str != "N/A":
                        flight_info['layover'] = f"{layover_time_str} at {layover_airport_str}"
                    else:
                         flight_info['layover'] = 'Layover Info N/A' 

                flight_info['booking_link'] = driver.current_url 

                flights.append(flight_info)
            except Exception as e_card:
                print(f"Error processing one TravelWings flight card (card index {card_index}): {str(e_card)}")
                continue
    except TimeoutException:
        print("TravelWings: Timed out waiting for flight results container. Page might be empty or stuck.")
        # Check for "no flights" message again, as the container might have appeared briefly
        try:
            no_flights_msg_xpath = "//*[contains(text(), 'Sorry, no flights found') or contains(@class, 'no-flight-found') or contains(@class, 'flight-not-found-msg')]"
            no_flights_elements_tw = driver.find_elements(By.XPATH, no_flights_msg_xpath)
            if any(el.is_displayed() for el in no_flights_elements_tw):
                print("TravelWings: Explicit 'no flights found' message detected after container timeout.")
                return [] 
        except Exception:
            pass 
        raise 
    except Exception as e_main_scrape:
        print(f"TravelWings: Main scraping function failed: {str(e_main_scrape)}")
        raise 
    return flights


def search_travelwings_flights(search_id, from_code, to_code, date_str_yyyy_mm_dd):
    if not mongodb_connected:
        print(f"MongoDB not connected, TravelWings search ({search_id}) cannot proceed.")
        record_scraper_completion(search_id, "travelwings", [], "MongoDB not connected at start")
        return

    try:
        dt_obj = datetime.strptime(date_str_yyyy_mm_dd, '%Y-%m-%d')
        formatted_date_for_url = dt_obj.strftime('%d-%m-%Y')
    except ValueError:
        msg = f"Invalid date format for TravelWings URL: '{date_str_yyyy_mm_dd}'. Expected YYYY-MM-DD."
        print(msg)
        record_scraper_completion(search_id, "travelwings", [], msg)
        return

    driver = None
    try:
        print(f"TravelWings ({search_id}): Attempting to acquire lock for Chrome initialization.")
        with chrome_init_lock:
            print(f"TravelWings ({search_id}): Lock acquired. Initializing Chrome.")
            opts = uc.ChromeOptions()
            # opts.add_argument('--headless=new') # Make browser visible for TravelWings - REMOVED/COMMENTED
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument('--disable-blink-features=AutomationControlled')
            # Make browser visible for TravelWings
            driver = uc.Chrome(options=opts, headless=False, version_main=136)
            print(f"TravelWings ({search_id}): Chrome initialized (Headless: False).")

        wait = WebDriverWait(driver, 75) 

        url = f"https://www.travelwings.com/ma/en/flight-search/oneway/{from_code}-{to_code}/{formatted_date_for_url}/Economy/1"
        print(f"TravelWings ({search_id}): Navigating to URL: {url}")
        driver.get(url)

        # It's good to wait for some indication the page has loaded or results are there/not there
        print(f"TravelWings ({search_id}): Waiting for page to stabilize after initial load...")
        try:
            WebDriverWait(driver, 45).until( 
                EC.any_of(
                     EC.presence_of_element_located((By.CSS_SELECTOR, SEL['flight_results_container'])),
                    
                     EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Sorry, no flights found') or contains(@class, 'no-flight-found') or contains(text(), 'No flights available for your selection') or contains(@class,'flight-not-found-msg')]"))
                )
            )
            print(f"TravelWings ({search_id}): Page stabilized or known state detected.")
        except TimeoutException:
            print(f"TravelWings ({search_id}): Page did not stabilize to a known state (results or no-results) in time. Proceeding with scrape attempt anyway.")
            


        flight_data = scrape_travelwings(driver, wait, from_code, to_code)
        print(f"TravelWings ({search_id}): Scraped {len(flight_data)} flights.")
        record_scraper_completion(search_id, "travelwings", flight_data)

    except Exception as e:
        error_msg = f"Error in TravelWings search ({search_id}): {type(e).__name__} - {str(e)}"
        print(error_msg)
        traceback.print_exc() 
        if driver:
            try:
                driver.save_screenshot(f"error_tw_main_exception_{search_id}.png")
                print(f"TravelWings ({search_id}): Screenshot saved: error_tw_main_exception_{search_id}.png")
            except Exception as se:
                print(f"TravelWings ({search_id}): Failed to save screenshot during main error: {se}")
        record_scraper_completion(search_id, "travelwings", [], error_msg)
    finally:
        if driver:
            # Add a small delay before quitting if running non-headless
            if not driver.options.headless: 
                print(f"TravelWings ({search_id}): Search complete. Browser will close in 5 seconds.")
                time.sleep(5)
            driver.quit()
        print(f"TravelWings search ended for {search_id}")

# Price Parsing Helper for Sorting 
def get_price_float(price_str_or_num):
    if isinstance(price_str_or_num, (int, float)):
        return float('inf') if price_str_or_num < 0 else float(price_str_or_num)

    if not price_str_or_num or price_str_or_num == "N/A" or "N/A" in str(price_str_or_num).upper():
        return float('inf')

    price_str_processed = str(price_str_or_num)
    cleaned_price = re.sub(r'(MAD|EUR|USD|\$|€|£)', '', price_str_processed, flags=re.IGNORECASE)
    cleaned_price = cleaned_price.replace(u'\xa0', '').replace(u'\u202f', '').replace(u'\u2009', '')
    cleaned_price = cleaned_price.replace(',', '').replace(' ', '').strip()

    try:
        price_match = re.search(r'(\d+\.?\d*)', cleaned_price)
        if price_match:
            price = float(price_match.group(1))
            return price if price >= 0 else float('inf')
        return float('inf')
    except ValueError:
        return float('inf')
    except Exception:
        return float('inf')


# Initialize the price prediction model (load existing or train new ones)
def initialize_model():
    global price_predictor
    global mongodb_connected, flights_collection 

    print("Initializing price prediction models...")
    price_predictor._route_cache = {} 

    loaded_from_disk_count = 0
    try:
        os.makedirs("models", exist_ok=True) # Ensure 'models' directory exists

        # Try loading existing models from disk
        for fname in os.listdir("models"):
            if fname.endswith("_model.pkl"):
                route_tag = fname[:-10] 
                model_path = os.path.join("models", fname)
                features_path = os.path.join("models", f"{route_tag}_features.pkl")

                if os.path.exists(features_path):
                    try:
                        model = joblib.load(model_path)
                        features = joblib.load(features_path)
                        price_predictor._route_cache[route_tag] = {"model": model, "features": features}
                        loaded_from_disk_count += 1
                    except Exception as load_err:
                        print(f"Error loading model for {route_tag} from disk: {load_err}")
                else:
                    print(f"Warning: Model file {fname} found, but corresponding features file {route_tag}_features.pkl missing. Skipping.")

        if loaded_from_disk_count > 0:
            print(f"Successfully loaded {loaded_from_disk_count} route-specific models from disk.")

        # If no models loaded and DB connected, try initial training
        if loaded_from_disk_count == 0 and mongodb_connected and flights_collection is not None:
            print("No pre-trained models found on disk. Attempting to train initial models from MongoDB data...")

            initial_training_data = []
            # Fetch recent, successful searches with flight data
            cursor = flights_collection.find(
                {"status": "completed", "has_error": {"$ne": True}, "flights": {"$exists": True, "$ne": []}},
                {"_id": 0, "from": 1, "to": 1, "departure_date": 1, "flights": 1} 
            ).sort("created_at", -1).limit(1000) 

            for search_doc in cursor:
                departure_date_for_search = search_doc.get('departure_date')
                for flight in search_doc.get('flights', []):
                    
                    if 'departure_date' not in flight and departure_date_for_search:
                        flight['departure_date'] = departure_date_for_search
                    initial_training_data.append(flight)

            if initial_training_data:
                print(f"Fetched {len(initial_training_data)} flight records from MongoDB for initial training.")
                training_success = price_predictor.train(initial_training_data)
                if training_success:
                    print("Initial model training from DB completed successfully.")
                else:
                    print("Initial model training from DB reported issues or trained no models.")
            else:
                print("No suitable data found in MongoDB for initial model training.")

        elif loaded_from_disk_count == 0 and (not mongodb_connected or flights_collection is None):
            print("No pre-trained models found, and MongoDB is not available. Price predictor will be inactive until models are trained.")

    except Exception as e:
        print(f"Critical error during model initialization: {e}")
        traceback.print_exc()



def get_country_from_airport_code(airport_code):
    data = AIRPORT_DATA.get(str(airport_code).upper())
    if data:
        return data.get("country")
    return None

def get_representative_image_for_country(country_name):
    for code, data in AIRPORT_DATA.items():
        if data.get("country") == country_name and data.get("image_url"):
            return data["image_url"]
    return AIRPORT_DATA["DEFAULT_DEST_IMG"]

def get_representative_airport_for_country(country_name):
    # Prioritize known hubs for the country, then any airport
    priority_hubs = {
        "Morocco": ["CMN", "RAK", "AGA"],
        "France": ["CDG", "ORY"],
        "Spain": ["BCN", "MAD"], 
        "UK": ["LHR"],
        "USA": ["JFK"],
        "Japan": ["NRT"],
        "Turkey": ["IST"]
        
    }
    if country_name in priority_hubs:
        for hub_code in priority_hubs[country_name]:
            if hub_code in AIRPORT_DATA: 
                return hub_code

    # Fallback to any airport in that country
    for code, data in AIRPORT_DATA.items():
        if data.get("country") == country_name:
            return code
    return None 


def get_monthly_popular_destinations_predictions(num_months_to_predict=3, top_n_countries=3):
    if not mongodb_connected or flights_collection is None: # Corrected check
        print("Monthly Popularity: MongoDB not connected.")
        return {}

    monthly_searches_by_country = {}
    # Look at data from the last 2 years for relevance
    two_years_ago_timestamp = (datetime.now() - timedelta(days=365 * 2)).timestamp()

    cursor = flights_collection.find(
        {
            "status": "completed",
            "has_error": {"$ne": True},
            "departure_date": {"$exists": True, "$ne": None, "$ne": ""}, 
            "to": {"$exists": True, "$ne": None, "$ne": ""}, 
            "created_at": {"$gte": two_years_ago_timestamp} 
        },
        {"_id": 0, "to": 1, "departure_date": 1} 
    )

    for search_doc in cursor:
        try:
            dest_airport_code = str(search_doc.get("to", "")).upper()
            departure_date_str = search_doc.get("departure_date")

            if not dest_airport_code or not departure_date_str:
                continue 

            country = get_country_from_airport_code(dest_airport_code)
            if not country: 
                continue

            # Parse departure_date to get month and year
            dep_date_obj = datetime.strptime(departure_date_str, "%Y-%m-%d")
            month_year_key = (dep_date_obj.year, dep_date_obj.month) 

            if month_year_key not in monthly_searches_by_country:
                monthly_searches_by_country[month_year_key] = {}

            monthly_searches_by_country[month_year_key][country] = \
                monthly_searches_by_country[month_year_key].get(country, 0) + 1

        except ValueError: 
            # print(f"Monthly Popularity: Skipping doc due to date parse error: {departure_date_str}")
            continue
        except Exception as e_doc_proc: 
            # print(f"Monthly Popularity: Error processing doc: {e_doc_proc}")
            continue


    predictions_for_template = {}
    today = datetime.now()
    default_origin_for_price_est = "CMN" 

    for i in range(num_months_to_predict): 
        current_year = today.year
        current_month = today.month

        # Calculate target month and year for prediction
        target_month_num_raw = current_month + i
        year_offset = (target_month_num_raw - 1) // 12
        target_predict_year = current_year + year_offset
        target_predict_month = (target_month_num_raw - 1) % 12 + 1

        target_month_date_obj = datetime(target_predict_year, target_predict_month, 1)
        month_name_display = target_month_date_obj.strftime("%B %Y") 

        # Unique key for the dictionary for display
        if i == 0: display_key_for_dict = f"This Month ({month_name_display})"
        elif i == 1: display_key_for_dict = f"Next Month ({month_name_display})"
        else: display_key_for_dict = month_name_display


        # Aggregate historical search counts for this specific calendar month across different years
        aggregated_country_counts_for_target_calendar_month = {}
        for (hist_year, hist_month), country_data in monthly_searches_by_country.items():
            if hist_month == target_predict_month: 
                for country, count in country_data.items():
                    aggregated_country_counts_for_target_calendar_month[country] = \
                        aggregated_country_counts_for_target_calendar_month.get(country, 0) + count

        if not aggregated_country_counts_for_target_calendar_month:
            predictions_for_template[display_key_for_dict] = [] 
            continue

        # Sort countries by aggregated search count for this calendar month
        sorted_popular_countries = sorted(
            aggregated_country_counts_for_target_calendar_month.items(),
            key=lambda item: item[1], # Sort by count
            reverse=True
        )

        top_destinations_for_month_list = []
        
        search_departure_day = 15 

        for country_name, search_count in sorted_popular_countries[:top_n_countries]:
            rep_airport = get_representative_airport_for_country(country_name)
            # Create departure date for price estimation 
            price_est_date_obj = datetime(target_predict_year, target_predict_month, search_departure_day)
            price_est_date_str = price_est_date_obj.strftime("%Y-%m-%d")

            estimated_price_val = None
            if rep_airport: 
                prediction_input = {
                    'from': default_origin_for_price_est, 'to': rep_airport,
                    'departure_date': price_est_date_str, 'airline': 'Unknown', 'stops': 0
                }
                estimated_price_val = price_predictor.predict_price(prediction_input)

            
            search_link_departure_date_str = price_est_date_str

            top_destinations_for_month_list.append({
                "country": country_name,
                "image_url": get_representative_image_for_country(country_name),
                "representative_airport_code": rep_airport, 
                "reason": f"High interest in {target_month_date_obj.strftime('%B')} (based on {search_count} past searches).",
                "estimated_price_display": f"MAD {estimated_price_val:.0f} (est.)" if estimated_price_val is not None else "Price N/A",
                "search_params": { 
                    "from_code": default_origin_for_price_est,
                    "to_code": rep_airport if rep_airport else "", 
                    "departure_date": search_link_departure_date_str
                }
            })
        predictions_for_template[display_key_for_dict] = top_destinations_for_month_list
    return predictions_for_template


# Flask Routes
@app.route('/')
def index():
    recent_cheapest_flights = []
    recommendations = []
    popular_destinations_data = [] 
    popular_route_predictions_list = [] 
    predicted_monthly_popular_countries = {} 

    try:
        
        predicted_monthly_popular_countries = get_monthly_popular_destinations_predictions(num_months_to_predict=3, top_n_countries=3)
    except Exception as e_monthly_pred:
        print(f"Error generating monthly popular destinations: {e_monthly_pred}")
        traceback.print_exc()


    
    static_popular_codes = ["CDG", "NRT", "JFK", "DPS", "LHR", "RAK", "VIL", "LIS", "ROM"]
    for code in static_popular_codes:
        airport_info = AIRPORT_DATA.get(code)
        if code == "ROM" and "FCO" in AIRPORT_DATA: 
            airport_info = AIRPORT_DATA["FCO"]
        if airport_info:
            popular_destinations_data.append(airport_info)
        if len(popular_destinations_data) >= 6: 
            break
    if not popular_destinations_data: 
         popular_destinations_data = [
            {"code": "CDG", "name": "Paris", "image_url": AIRPORT_DATA.get("CDG", {}).get("image_url", AIRPORT_DATA["DEFAULT_DEST_IMG"])},
            {"code": "NRT", "name": "Tokyo", "image_url": AIRPORT_DATA.get("NRT", {}).get("image_url", AIRPORT_DATA["DEFAULT_DEST_IMG"])},
            
         ]


    if mongodb_connected and flights_collection is not None:
        try:
            
            recent_searches_cursor = flights_collection.find(
                {"status": "completed", "has_error": {"$ne": True}, "flights": {"$exists": True, "$ne": []}},
                {"_id": 0, "from": 1, "to": 1, "departure_date": 1, "flights": 1, "created_at":1}
            ).sort("created_at", -1).limit(5) 

            for search_item in recent_searches_cursor:
                if search_item.get("flights"):
                    sorted_flights_in_search = sorted(
                        search_item["flights"],
                        key=lambda f: get_price_float(f.get("price") or f.get("economy_price"))
                    )
                    if sorted_flights_in_search and len(recent_cheapest_flights) < 3: 
                        cheapest_flight = sorted_flights_in_search[0]
                        airline_name_for_logo = str(cheapest_flight.get("airline", "")).split(',')[0].strip()
                        price_display = cheapest_flight.get("price") 
                        if not isinstance(price_display, str) and price_display is not None: price_display = str(price_display)
                        elif price_display is None: price_display = "N/A"

                        recent_cheapest_flights.append({
                            "from_location": search_item.get("from"), "to_location": search_item.get("to"),
                            "departure_date": search_item.get("departure_date"), "airline": cheapest_flight.get("airline"),
                            "price": price_display, "departure_time": cheapest_flight.get("departure_time"),
                            "arrival_time": cheapest_flight.get("arrival_time"), "duration": cheapest_flight.get("duration"),
                            "stops": cheapest_flight.get("stops", "N/A"), "booking_link": cheapest_flight.get("booking_link", "#"),
                            "logo_url": AIRLINE_LOGOS.get(airline_name_for_logo, AIRLINE_LOGOS["DEFAULT"])
                        })

            
            pipeline_popular_routes = [
                {"$match": {"status": "completed", "has_error": {"$ne": True}, "from": {"$exists": True, "$ne": None, "$ne": ""}, "to": {"$exists": True, "$ne": None, "$ne": ""}}},
                {"$group": {"_id": {"from": "$from", "to": "$to"}, "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}, {"$limit": 10} 
            ]
            db_popular_routes = list(flights_collection.aggregate(pipeline_popular_routes))

            processed_routes_for_rec_pred = set() 
            days_future_predict = 30 
            predict_date_obj = datetime.now() + timedelta(days=days_future_predict)
            predict_date_str = predict_date_obj.strftime('%Y-%m-%d')

            for route_info in db_popular_routes:
                if len(recommendations) >= 3 and len(popular_route_predictions_list) >=3 : break # Got enough

                route_id_obj = route_info.get("_id")
                if not isinstance(route_id_obj, dict): continue

                from_code = route_id_obj.get("from")
                to_code = route_id_obj.get("to")

                if not from_code or not to_code or (from_code, to_code) in processed_routes_for_rec_pred:
                    continue

                
                prediction_input = {'from': from_code, 'to': to_code, 'departure_date': predict_date_str, 'airline': 'Unknown', 'stops': 0}
                predicted_price_val = price_predictor.predict_price(prediction_input)
                trend_data = price_predictor.predict_price_trend(prediction_input)

                if len(recommendations) < 3 and predicted_price_val is not None :
                    dest_details = AIRPORT_DATA.get(to_code, {})
                    dest_name = dest_details.get("name", f"Destination {to_code}")
                    dest_image = dest_details.get("image_url", AIRPORT_DATA["DEFAULT_DEST_IMG"])
                    origin_name = AIRPORT_DATA.get(from_code, {}).get("name", from_code)
                    # Price range for display
                    price_disp = f"MAD {predicted_price_val * 0.9:.0f} - {predicted_price_val * 1.1:.0f}"

                    recommendations.append({
                        "destination_code": to_code, "destination_name": dest_name, "destination_image_url": dest_image,
                        "origin_display": origin_name, "price_estimate_display": price_disp,
                        "trend": trend_data.get('trend', 'stable') if trend_data else 'stable',
                        "reason": "Popular route with good forecast",
                        "localized_predict_url": url_for('localized_prediction', destination_code=to_code)
                    })

                if len(popular_route_predictions_list) < 3 and predicted_price_val is not None:
                    popular_route_predictions_list.append({
                        "from": from_code, "to": to_code,
                        "from_display": AIRPORT_DATA.get(from_code, {}).get("name", from_code),
                        "to_display": AIRPORT_DATA.get(to_code, {}).get("name", to_code),
                        "predicted_price": f"MAD {predicted_price_val:.2f}", 
                        "trend": trend_data.get('trend', 'stable') if trend_data else 'stable',
                    })
                processed_routes_for_rec_pred.add((from_code, to_code))

            
            if len(recommendations) < 3:
                fallback_insp_dest_codes = {"CMN_CDG": ("CMN", "CDG"), "RAK_BCN": ("RAK", "BCN"), "AGA_ORY":("AGA", "ORY")}
                for key, (orig, dest) in fallback_insp_dest_codes.items():
                    if len(recommendations) >= 3: break
                    if (orig, dest) in processed_routes_for_rec_pred: continue 
                    fb_pred_input = {'from': orig, 'to': dest, 'departure_date': predict_date_str, 'airline': 'Unknown', 'stops': 0}
                    fb_price = price_predictor.predict_price(fb_pred_input)
                    if fb_price is not None:
                        recommendations.append({
                            "destination_code": dest, "destination_name": AIRPORT_DATA.get(dest, {}).get("name", dest),
                            "destination_image_url": AIRPORT_DATA.get(dest, {}).get("image_url", AIRPORT_DATA["DEFAULT_DEST_IMG"]),
                            "origin_display": AIRPORT_DATA.get(orig, {}).get("name", orig),
                            "price_estimate_display": f"MAD {fb_price * 0.9:.0f} - {fb_price * 1.1:.0f}", 
                            "trend": "check_details", 
                            "reason": "Consider this trip!",
                            "localized_predict_url": url_for('localized_prediction', destination_code=dest)
                        })
                        processed_routes_for_rec_pred.add((orig,dest))

            if len(popular_route_predictions_list) < 3:
                fallback_pred_routes = {"CMN_IST": ("CMN", "IST"), "AGA_LHR": ("AGA", "LHR")}
                for key, (orig, dest) in fallback_pred_routes.items():
                    if len(popular_route_predictions_list) >= 3: break
                    if (orig, dest) in processed_routes_for_rec_pred: continue
                    fb_pred_input_rt = {'from': orig, 'to': dest, 'departure_date': predict_date_str, 'airline': 'Unknown', 'stops': 0}
                    fb_price_rt = price_predictor.predict_price(fb_pred_input_rt)
                    if fb_price_rt is not None:
                         popular_route_predictions_list.append({
                            "from": orig, "to": dest,
                            "from_display": AIRPORT_DATA.get(orig, {}).get("name", orig),
                            "to_display": AIRPORT_DATA.get(dest, {}).get("name", dest),
                            "predicted_price": f"MAD {fb_price_rt:.2f}",
                            "trend": "check_details",
                        })


        except Exception as e:
            print(f"Error fetching data for index page AI sections: {e}")
            traceback.print_exc()

    return render_template('index.html',
                           recent_cheapest_flights=recent_cheapest_flights,
                           popular_destinations_data=popular_destinations_data, 
                           recommendations=recommendations, 
                           popular_route_predictions=popular_route_predictions_list, 
                           predicted_monthly_popular_countries=predicted_monthly_popular_countries, 
                           datetime=datetime, timedelta=timedelta, AIRPORT_DATA=AIRPORT_DATA)


@app.route('/search', methods=['POST'])
def search():
    if not mongodb_connected or flights_collection is None:
        return render_template('error.html', error="Database connection error. Cannot initiate search.")

    from_location = request.form.get('from_code', '').upper()
    to_location = request.form.get('to_code', '').upper()
    departure_date_str = request.form.get('departure_date', '')

    if not all([from_location, to_location, departure_date_str]):
        return render_template('error.html', error="Missing search parameters (from, to, or date).")
    try:
        datetime.strptime(departure_date_str, '%Y-%m-%d') 
    except ValueError:
        return render_template('error.html', error="Invalid departure date format. Please use YYYY-MM-DD.")

    search_id = str(uuid.uuid4())
    search_document = {
        "search_id": search_id,
        "from": from_location,
        "to": to_location,
        "departure_date": departure_date_str,
        "status": "pending",
        "flights": [],
        "scrapers_completed_log": [],
        "error_details": [],
        "has_error": False,
        "scrapers_total": 3,
        "scrapers_done": 0,
        "created_at": time.time()
    }
    flights_collection.insert_one(search_document)
    print(f"New search created with ID: {search_id} for {from_location} to {to_location} on {departure_date_str}")

   
    threading.Thread(target=search_flights, args=(search_id, from_location, to_location, departure_date_str)).start()
    threading.Thread(target=search_travelwings_flights, args=(search_id, from_location, to_location, departure_date_str)).start()
    threading.Thread(target=search_aviasales, args=(search_id, from_location, to_location, departure_date_str)).start()

    session['search_id'] = search_id 
    return redirect(url_for('waiting'))

@app.route('/waiting')
def waiting():
    search_id = session.get('search_id')
    if not search_id:
        return redirect(url_for('index')) 

    search_details = None
    if mongodb_connected and flights_collection is not None:
        search_doc = flights_collection.find_one({"search_id": search_id}, {"from": 1, "to": 1, "departure_date": 1})
        if search_doc:
            search_details = {
                "from": search_doc.get("from"),
                "to": search_doc.get("to"),
                "date": search_doc.get("departure_date")
            }
    return render_template('waiting.html', search_id=search_id, search_details=search_details)


@app.route('/check_status/<search_id>')
def check_status(search_id):
    if not mongodb_connected or flights_collection is None:
        return jsonify({"status": "error", "message": "Database not connected"}), 500

    search = flights_collection.find_one({"search_id": search_id})
    if not search:
        return jsonify({"status": "not_found", "message": "Search ID not found in database."}), 404

    scrapers_done = search.get("scrapers_done", 0)
    scrapers_total = search.get("scrapers_total", 3) 
    progress_percentage = int((scrapers_done / scrapers_total) * 100) if scrapers_total > 0 else 0

    response = {
        "status": search.get("status", "unknown"),
        "progress": progress_percentage,
        "scrapers_done": scrapers_done,
        "scrapers_total": scrapers_total,
        "search_details": {
            "from": search.get("from"),
            "to": search.get("to"),
            "date": search.get("departure_date")
        },
        "completed_log": search.get("scrapers_completed_log", []) 
    }

    current_status = search.get("status")
    
    if current_status == "completed" or \
       (current_status == "failed" and scrapers_done >= scrapers_total) or \
       (current_status == "in_progress_with_errors" and scrapers_done >= scrapers_total) :
        response["redirect"] = url_for('results', search_id=search_id)


    
    if current_status == "failed" or current_status == "in_progress_with_errors":
        errors = search.get("error_details", [])
        if errors:
            error_messages = [f"{e.get('scraper', 'Unknown scraper')}: {e.get('message', 'No details')}" for e in errors]
            response["error_message"] = "; ".join(error_messages)
        elif current_status == "failed": 
            response["error_message"] = "Search failed with no specific error details."

    return jsonify(response)


@app.route('/results/<search_id>')
def results(search_id):
    if not mongodb_connected or flights_collection is None:
        return render_template('error.html', error="Database connection error. Cannot fetch results.")

    search_data = flights_collection.find_one({"search_id": search_id})
    if not search_data:
        return render_template('error.html', error=f"Search ID {search_id} not found.")

    current_status = search_data.get("status")
    scrapers_done = search_data.get("scrapers_done", 0)
    scrapers_total = search_data.get("scrapers_total", 3)

    
    if current_status not in ["completed", "failed"] and \
       not (current_status == "in_progress_with_errors" and scrapers_done >= scrapers_total):
        if scrapers_done < scrapers_total : # Still actively in progress
            return redirect(url_for('waiting', search_id=search_id))
        

    all_flights = search_data.get("flights", [])
    
    sorted_flights = sorted(all_flights, key=lambda flight: get_price_float(flight.get('price')))

    # AI Insights
    ai_insights = {
        'predicted_price': None,
        'price_trend_data': None,
        'recommendation': None
    }
    if search_data.get("from") and search_data.get("to") and search_data.get("departure_date"):
        predict_input_results = {
            'from': search_data.get("from"),
            'to': search_data.get("to"),
            'departure_date': search_data.get("departure_date"),
            'airline': 'Unknown', 
            'stops': 0 
        }
        predicted_current_search_price = price_predictor.predict_price(predict_input_results)
        if predicted_current_search_price is not None:
            ai_insights['predicted_price'] = f"MAD {predicted_current_search_price:.2f}"
            
            if sorted_flights:
                best_found_price_float = get_price_float(sorted_flights[0].get('price'))
                if best_found_price_float != float('inf'): 
                    if best_found_price_float < predicted_current_search_price * 0.95: 
                        ai_insights['recommendation'] = "Good deal! Found prices are lower than AI estimates."
                    elif best_found_price_float > predicted_current_search_price * 1.05: 
                        ai_insights['recommendation'] = "Prices are a bit high. Consider checking other dates if flexible."
                    else:
                        ai_insights['recommendation'] = "Prices match AI estimates. Book if it fits your budget."

        trend_data_for_results = price_predictor.predict_price_trend(predict_input_results)
        if trend_data_for_results:
            ai_insights['price_trend_data'] = trend_data_for_results

    return render_template('search.html',
                          flights=sorted_flights,
                          from_location=search_data.get("from"),
                          to_location=search_data.get("to"),
                          departure_date=search_data.get("departure_date"),
                          search_status=search_data.get("status"),
                          error_details=search_data.get("error_details", []),
                          search_id=search_id,
                          completed_log=search_data.get('scrapers_completed_log', []),
                          airline_logos=AIRLINE_LOGOS,
                          ai_insights=ai_insights)


@app.route('/api/price-history')
def price_history():
    if not mongodb_connected or flights_collection is None:
        return jsonify({"error": "MongoDB not connected"}), 500

    pipeline = [
        {"$match": {"status": "completed", "has_error": {"$ne": True}, "flights": {"$exists": True, "$ne": []}}},
        {"$sort": {"created_at": -1}}, 
        {"$limit": 10}, 
        {"$unwind": "$flights"}, 
        {"$limit": 50} 
    ]
    raw_flights_from_db = list(flights_collection.aggregate(pipeline))

    processed_flights = []
    for item in raw_flights_from_db:
        flight_detail = item.get('flights')
        if flight_detail: 
            flight_detail['numeric_price'] = get_price_float(flight_detail.get('price') or flight_detail.get('economy_price'))
            airline_name_for_logo_api = str(flight_detail.get("airline", "")).split(',')[0].strip()
            flight_detail['logo'] = AIRLINE_LOGOS.get(airline_name_for_logo_api, AIRLINE_LOGOS["DEFAULT"])
            # Add from/to from the parent search document if not in flight_detail 
            flight_detail['departureAirport'] = flight_detail.get('from', item.get('from'))
            flight_detail['arrivalAirport'] = flight_detail.get('to', item.get('to'))
            
            price_disp_api = flight_detail.get("price")
            if not isinstance(price_disp_api, str) and price_disp_api is not None: flight_detail['price'] = str(price_disp_api)
            elif price_disp_api is None: flight_detail['price'] = "N/A"

            processed_flights.append(flight_detail)

   
    final_sorted_flights = sorted([f for f in processed_flights if f['numeric_price'] != float('inf')], key=lambda x: x['numeric_price'])
    return jsonify(final_sorted_flights[:8])


@app.route('/api/predict-price', methods=['POST'])
def api_predict_price_route():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ['from', 'to', 'departure_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field for prediction: {field}"}), 400

    prediction_input_dict = {
        'airline': data.get('airline', 'Unknown'),
        'from': data['from'],
        'to': data['to'],
        'stops': data.get('stops', 0), 
        'departure_date': data['departure_date']
    }

    predicted_price_val = price_predictor.predict_price(prediction_input_dict)

    if predicted_price_val is None:
        return jsonify({"error": "Could not generate price prediction. Model may not be trained for this route, or data is insufficient/out of scope."}), 500

    price_trend_data = price_predictor.predict_price_trend(prediction_input_dict)

    return jsonify({
        "predicted_price": f"MAD {predicted_price_val:.2f}",
        "price_trend": price_trend_data, 
        "confidence": "medium" 
    })


@app.route('/api/train-model', methods=['POST'])
def train_model_route():
    if not mongodb_connected or flights_collection is None:
        return jsonify({"error": "MongoDB not connected, cannot fetch data for training."}), 500
    try:
        all_flights_for_training = []
        
        cursor = flights_collection.find(
            {"status": "completed", "has_error": {"$ne": True}, "flights": {"$exists": True, "$ne": []}},
            {"_id":0, "from":1, "to":1, "departure_date":1, "flights":1} 
        )
        for search_doc in cursor:
            departure_date_for_search = search_doc.get('departure_date')
            for flight in search_doc.get('flights', []):
                if 'departure_date' not in flight and departure_date_for_search:
                    flight['departure_date'] = departure_date_for_search
                all_flights_for_training.append(flight)

        if not all_flights_for_training:
            return jsonify({"message": "No flight data available in DB for training. Model not retrained."}), 200

        print(f"Attempting to re-train all route models with {len(all_flights_for_training)} flight records from DB...")
        success = price_predictor.train(all_flights_for_training)

        if success:
            return jsonify({"message": f"Models re-trained successfully using {len(all_flights_for_training)} flight records."})
        else:
            
            return jsonify({"error": "Model training process completed, but may have had issues or trained no new models. Check server logs."}), 500
    except Exception as e:
        print(f"Error during API model training: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Training error: {str(e)}"}), 500


@app.route('/localized_prediction/<destination_code>')
def localized_prediction(destination_code):
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    print(f"Localized prediction: User IP (raw): {user_ip}")

    # Handle local development IPs by fetching public IP
    if user_ip == '127.0.0.1' or user_ip.startswith('192.168.') or user_ip.startswith('10.'):
        try:
            print("Localized prediction: Detected local IP, attempting to fetch public IP...")
            public_ip_res = requests.get('https://api.ipify.org?format=json', timeout=2)
            public_ip_res.raise_for_status()
            user_ip = public_ip_res.json()['ip']
            print(f"Localized prediction: Fetched public IP for local dev: {user_ip}")
        except requests.RequestException as e_ipify:
            print(f"Localized prediction: Could not fetch public IP from ipify: {e_ipify}. Using fallback Moroccan IP.")
            user_ip = '102.52.109.0' 

    # Defaults
    user_currency = 'MAD'
    user_country_code = 'MA' 
    user_city = 'your region'
    from_origin_code_for_prediction = "CMN" 

    try:
        print(f"Localized prediction: Requesting geolocation for IP: {user_ip}")
        
        geo_url = f"http://ip-api.com/json/{user_ip}?fields=status,message,countryCode,city,currency"
        geo_response = requests.get(geo_url, timeout=3)
        geo_response.raise_for_status() 
        geo_data = geo_response.json()
        print(f"Localized prediction: IP-API Data for {user_ip}: {geo_data}")

        if geo_data.get('status') == 'success':
            user_currency = geo_data.get('currency') or 'MAD' 
            user_country_code_api = geo_data.get('countryCode') 
            temp_user_city = geo_data.get('city') 

            if user_country_code_api: 
                user_country_code = user_country_code_api 
                user_city = temp_user_city or 'your region' 

                
                if user_country_code == "MA": 
                    if temp_user_city:
                        city_lower = temp_user_city.lower()
                        if "agadir" in city_lower:
                            from_origin_code_for_prediction = "AGA"
                        elif "marrakech" in city_lower or "marrakesh" in city_lower:
                            from_origin_code_for_prediction = "RAK"
                        elif "casablanca" in city_lower:
                             from_origin_code_for_prediction = "CMN"
                       
                        else:
                            from_origin_code_for_prediction = "CMN" 
                    else:
                        from_origin_code_for_prediction = "CMN" 
                    print(f"Localized prediction: User in Morocco ({user_city}), selected origin: {from_origin_code_for_prediction}")
                else:
                    
                    print(f"Localized prediction: User outside Morocco ({user_country_code}), using default origin: {from_origin_code_for_prediction}")
        else:
            print(f"Localized prediction: Geolocation API failed: {geo_data.get('message')}")
    except requests.RequestException as e_geo:
        print(f"Localized prediction: Geolocation API request error: {e_geo}")
    except ValueError as e_json: 
        print(f"Localized prediction: Geolocation API JSON decoding error: {e_json}")
    except Exception as e_other_geo:
        print(f"Localized prediction: Other error during geolocation: {e_other_geo}")
        traceback.print_exc()

    # Destination details for display
    destination_details_display = AIRPORT_DATA.get(destination_code.upper(),
                                     {"name": f"Destination {destination_code.upper()}",
                                      "image_url": AIRPORT_DATA["DEFAULT_DEST_IMG"],
                                      "country": "Unknown"})

    # Predict for a date in the near future 
    days_future = 30
    departure_date_obj = datetime.now() + timedelta(days=days_future)
    departure_date_str_for_pred = departure_date_obj.strftime('%Y-%m-%d')

    prediction_input_localized = {
        'from': "AGA", 
        'to': destination_code.upper(),
        'departure_date': departure_date_str_for_pred,
        'airline': 'Unknown',
        'stops': 0 
    }
    print(f"Localized prediction: Final prediction input: {prediction_input_localized}")

    predicted_price_val = price_predictor.predict_price(prediction_input_localized)
    print(f"Localized prediction: Raw predicted_price_val from predictor: {predicted_price_val}")

    price_trend_data = price_predictor.predict_price_trend(prediction_input_localized)
    print(f"Localized prediction: Price trend data: {price_trend_data}")


    predicted_price_display = f"{user_currency} {predicted_price_val:.2f}" if predicted_price_val is not None else "N/A"
    trend_display = price_trend_data.get('trend', 'stable') if price_trend_data else 'stable'

    # Prepare data for the chart
    chart_data_labels = []
    chart_data_prices = []
    if price_trend_data and isinstance(price_trend_data.get('future_prices'), dict):
        # Sort future prices by date to ensure correct order in chart
        sorted_future_prices = sorted(price_trend_data['future_prices'].items())
        for date_str, price_val in sorted_future_prices:
            if price_val is not None:
                try:
                    date_obj_chart = datetime.strptime(date_str, '%Y-%m-%d')
                    chart_data_labels.append(date_obj_chart.strftime('%b %d')) 
                    chart_data_prices.append(float(price_val))
                except ValueError: # Should not happen if date_str is YYYY-MM-DD
                    chart_data_labels.append(date_str) 
                    chart_data_prices.append(float(price_val))
            else:
                # Optionally, represent None prices differently or skip
                print(f"Localized prediction: Skipping None price for date {date_str} in chart data.")


    return render_template('localized_prediction.html',
                             destination_details=destination_details_display,
                             destination_code=destination_code.upper(),
                             user_location_display=f"{user_city}, {user_country_code}",
                             user_currency=user_currency,
                             predicted_price_display=predicted_price_display,
                             trend_display=trend_display,
                             price_trend_full_data=price_trend_data, 
                             chart_labels=chart_data_labels,
                             chart_prices=chart_data_prices,
                             user_origin_code_for_search=from_origin_code_for_prediction, 
                             default_departure_date_search=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'), 
                             datetime_module=datetime, 
                             timedelta_class=timedelta 
                            )

@app.route('/explore')
def explore():
    category = request.args.get('category', 'all')  
    
    return render_template('explore.html', category=category, datetime=datetime, AIRPORT_DATA=AIRPORT_DATA)

@app.route('/deals')
def deals():
    
    return render_template('deals.html', datetime=datetime, timedelta=timedelta, AIRPORT_DATA=AIRPORT_DATA)

@app.route('/contact')
def contact():
    return render_template('contact.html', AIRPORT_DATA=AIRPORT_DATA) 

@app.route('/signin')
def signin():
    return render_template('signin.html')


if __name__ == '__main__':
    initialize_model() 
    app.run(debug=True, host='0.0.0.0', port=5000)

