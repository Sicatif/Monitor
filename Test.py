import os
import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurer pandas pour un affichage optimal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)

# Variables d'environnement
CMC_API_KEY = os.getenv("CMC_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
FROM_PASS = os.getenv("FROM_PASS")
TO_EMAILS = [email.strip() for email in os.getenv("TO_EMAIL", "").split(",") if email.strip()]

# Récupérer les données de CoinMarketCap avec gestion d'erreur améliorée
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

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Lève une exception pour les codes 4xx/5xx
        return response.json()['data']
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API CoinMarketCap: {e}")
        return None
    except KeyError as e:
        print(f"❌ Données API invalides: {e}")
        return None

# Filtrer les cryptos ciblées
def filter_cryptos(data):
    target_cryptos = ['bitcoin', 'ethereum', 'xrp', 'cardano', 'polkadot', 'litecoin']
    filtered_data = [crypto for crypto in data if crypto['slug'] in target_cryptos]
    
    if not filtered_data:
        print("⚠️ Aucune crypto correspondante trouvée")
        return pd.DataFrame()
    
    df = pd.DataFrame(filtered_data)

    df_filtered = pd.DataFrame({
        'Nom': df['name'],
        'Symbole': df['symbol'],
        'Prix actuel (USD)': df['quote'].apply(lambda x: round(x['USD']['price'], 4)),
        'Change 1h (%)': df['quote'].apply(lambda x: round(x['USD']['percent_change_1h'], 2)),
        'Change 24h (%)': df['quote'].apply(lambda x: round(x['USD']['percent_change_24h'], 2)),
        'Change 7d (%)': df['quote'].apply(lambda x: round(x['USD']['percent_change_7d'], 2))
    })

    return df_filtered

# Envoyer un email avec meilleure gestion d'erreur
def send_email(subject, body, to_emails):
    if not to_emails:
        print("⚠️ Aucun email destinataire configuré")
        return

    for to_email in to_emails:
        try:
            msg = MIMEMultipart()
            msg['From'] = FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(FROM_EMAIL, FROM_PASS)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
            server.quit()
            print(f"✅ Email envoyé à {to_email}")
            
        except Exception as e:
            print(f"❌ Erreur envoi email à {to_email}: {e}")

# Fonction principale de monitoring
def monitor_cryptos():
    # Seuils de prix (modifiables)
    target_prices = {
        'bitcoin': 78337.95,
        'ethereum': 2002,
        'xrp': 2.00,
        'cardano': 0.25,
        'polkadot': 2.10,
        'litecoin': 63.00,
    }

    print("🔄 Récupération des données crypto...")
    crypto_data = get_cryptos_data()
    
    if not crypto_data:
        print("❌ Impossible de récupérer les données")
        return

    df_filtered = filter_cryptos(crypto_data)
    
    if df_filtered.empty:
        print("❌ Aucune donnée à analyser")
        return

    print("📊 Données récupérées :")
    print(df_filtered.to_string(index=False))
    
    # Vérifier les seuils
    alerts_sent = 0
    for index, row in df_filtered.iterrows():
        crypto_name = row['Nom'].lower()
        current_price = row['Prix actuel (USD)']
        
        if crypto_name in target_prices and current_price <= target_prices[crypto_name]:
            subject = f"🚨 Alerte Prix: {crypto_name.capitalize()} sous {target_prices[crypto_name]} USD"
            body = f"""
Alerte de prix déclenchée !

Crypto: {crypto_name.capitalize()}
Prix actuel: {current_price} USD
Seuil: {target_prices[crypto_name]} USD
Différence: {round(target_prices[crypto_name] - current_price, 4)} USD

Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            print(f"🚨 Seuil atteint pour {crypto_name}: {current_price} <= {target_prices[crypto_name]}")
            send_email(subject, body, TO_EMAILS)
            alerts_sent += 1
    
    if alerts_sent == 0:
        print("✅ Aucun seuil déclenché - tous les prix sont au-dessus des seuils")

# Exécution principale
if __name__ == "__main__":
    print("🚀 Démarrage du monitoring crypto...")
    monitor_cryptos()
    print("✅ Monitoring terminé avec succès!")
