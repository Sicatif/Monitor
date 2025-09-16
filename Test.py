import os
import requests
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask
import threading

# Créer l'application Flask
app = Flask(__name__)

# Configurer les options pandas pour afficher toutes les colonnes
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)

# Récupération des variables d'environnement
CMC_API_KEY = os.getenv("CMC_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
FROM_PASS = os.getenv("FROM_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")

# Fonction pour récupérer les données de l'API CoinMarketCap
def get_cryptos_data():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    headers = {
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
        'Accept': 'application/json'
    }
    params = {
        'start': '1',
        'limit': '10',
        'convert': 'USD',
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['data']
    else:
        print(f"Erreur lors de la récupération des données : {response.status_code}")
        return None

# Fonction pour filtrer et organiser les données
def filter_cryptos(data):
    target_cryptos = ['bitcoin', 'ethereum', 'xrp', 'cardano']
    filtered_data = [crypto for crypto in data if crypto['slug'] in target_cryptos]
    df = pd.DataFrame(filtered_data)

    df_filtered = pd.DataFrame({
        'Nom': df['name'],
        'Symbole': df['symbol'],
        'Prix actuel (USD)': df['quote'].apply(lambda x: x['USD']['price']),
        'Change 1h (%)': df['quote'].apply(lambda x: x['USD']['percent_change_1h']),
        'Change 24h (%)': df['quote'].apply(lambda x: x['USD']['percent_change_24h']),
        'Change 7d (%)': df['quote'].apply(lambda x: x['USD']['percent_change_7d'])
    })

    return df_filtered

# Fonction pour envoyer un email de notification
def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(FROM_EMAIL, FROM_PASS)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        print("E-mail envoyé avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail: {e}")

# Fonction principale qui vérifie régulièrement les prix
def monitor_cryptos():
    target_prices = {
        'bitcoin': 78337.95,
        'ethereum': 2002,
        'xrp': 2.00,
        'cardano': 0.5,
    }

    while True:
        crypto_data = get_cryptos_data()

        if crypto_data:
            df_filtered = filter_cryptos(crypto_data)
            for index, row in df_filtered.iterrows():
                crypto_name = row['Nom'].lower()
                current_price = row['Prix actuel (USD)']

                if crypto_name in target_prices and current_price <= target_prices[crypto_name]:
                    subject = f"Alerte : {crypto_name.capitalize()} a atteint le seuil"
                    body = f"{crypto_name.capitalize()} a atteint un prix de {current_price} USD.\n\n" \
                           f"Le seuil était fixé à {target_prices[crypto_name]} USD."
                    send_email(subject, body, TO_EMAIL)

        time.sleep(600)

# Route de Flask pour afficher une page simple
@app.route('/')
def index():
    return "Ton script fonctionne et est en ligne 24/7 !"

# Lancer le monitoring dans un thread séparé
def run_monitoring():
    monitor_cryptos()

if __name__ == "__main__":
    thread = threading.Thread(target=run_monitoring)
    thread.daemon = True
    thread.start()
    app.run(host="0.0.0.0", port=5000)


