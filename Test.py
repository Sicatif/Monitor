import requests
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask
import threading  # Importer le module threading

# Créer l'application Flask
app = Flask(__name__)

# Configurer les options pandas pour afficher toutes les colonnes
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)

# Fonction pour récupérer les données de l'API CoinMarketCap
def get_cryptos_data():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    headers = {
        'X-CMC_PRO_API_KEY': '5ce9d8f1-29cb-45c8-8548-f8da597bab83',  # Remplace par ta clé API CoinMarketCap
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

    # Extraction des informations pertinentes
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
    from_email = "zorrogmall@gmail.com"  # Remplace par ton adresse e-mail
    from_password = "hwbs plqw vgip nrua"  # Remplace par ton mot de passe ou un mot de passe spécifique pour l'application (si Gmail)

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connexion au serveur SMTP de Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("E-mail envoyé avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail: {e}")

# Fonction principale qui vérifie régulièrement les prix
def monitor_cryptos():
    # Prix spécifiques à surveiller
    target_prices = {
        'bitcoin': 78337.95,  # Seuil de prix pour Bitcoin
        'ethereum': 2002,  # Seuil de prix pour Ethereum
        'xrp': 1.96,  # Seuil de prix pour XRP
        'cardano': 0.5,  # Seuil de prix pour Cardano
    }

    # Boucle infinie qui vérifie les prix toutes les 10 minutes (600 secondes)
    while True:
        crypto_data = get_cryptos_data()

        if crypto_data:
            # Filtrer les cryptos d'intérêt
            df_filtered = filter_cryptos(crypto_data)

            # Vérifier si les prix sont en dessous des seuils définis
            for index, row in df_filtered.iterrows():
                crypto_name = row['Nom'].lower()
                current_price = row['Prix actuel (USD)']

                if crypto_name in target_prices and current_price <= target_prices[crypto_name]:
                    # Si le prix est inférieur ou égal au seuil, envoyer un e-mail
                    subject = f"Alerta : {crypto_name.capitalize()} a atteint le seuil"
                    body = f"{crypto_name.capitalize()} a atteint un prix de {current_price} USD.\n\n" \
                           f"Le seuil était fixé à {target_prices[crypto_name]} USD."
                    to_email = "sicatif@yahoo.fr"  # Remplace par l'adresse e-mail de destination
                    send_email(subject, body, to_email)

        # Attendre 10 minutes avant de vérifier à nouveau
        time.sleep(600)

# Route de Flask pour afficher une page simple
@app.route('/')
def index():
    return "Ton script fonctionne et est en ligne 24/7 !"

# Lancer la fonction de monitoring dans un thread séparé
def run_monitoring():
    monitor_cryptos()

# Lancer l'application Flask dans le thread principal
if __name__ == "__main__":
    # Démarrer le monitoring dans un thread
    thread = threading.Thread(target=run_monitoring)
    thread.daemon = True  # Cela permet d'arrêter le thread lorsque le serveur Flask s'arrête
    thread.start()

    # Lancer le serveur Flask
    app.run(host="0.0.0.0", port=5000)  # Utilise le port 5000 (ou 3000 si nécessaire pour Replit)
