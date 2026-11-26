# app.py — The Ultimate Banking Simulator (Multi-language + Custom Transactions + Full Admin Control)
import os, uuid, hashlib, secrets, time, json
import psycopg
from psycopg.rows import dict_row
from urllib.parse import quote
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, abort
from functools import wraps

DATABASE_URL     = os.environ.get("DATABASE_URL", "").strip()
WHATSAPP_NUMBER  = os.environ.get("WHATSAPP_NUMBER", "").strip()
BANK_NAME        = os.environ.get("BANK_NAME", "Aurora Trust Bank")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

import datetime

CURRENCIES = [
    "USD", "EUR", "GBP", "NGN", "JPY", "CAD", "AUD", "CHF", "CNY", "INR",
    "BRL", "RUB", "ZAR", "MXN", "SGD", "NZD", "HKD", "SEK", "KRW", "NOK",
    "TRY", "AED", "SAR", "ILS", "PLN", "THB", "IDR", "HUF", "CZK", "CLP",
    "PHP", "MYR", "COP", "ARS", "EGP", "KWD", "QAR", "PKR", "BDT", "VND",
    "UAH", "KZT", "DZD", "MAD", "TND", "KES", "GHS", "UGX", "TZS", "RWF"
]

def get_past_year_dates():
    today = datetime.date.today()
    past_year = today - datetime.timedelta(days=365)
    dates = []
    curr = today
    while curr >= past_year:
        dates.append(curr.strftime("%b %d, %Y"))
        curr -= datetime.timedelta(days=1)
    return dates

PAST_YEAR_DATES = get_past_year_dates()



# ---------------- Translations ----------------

LANGUAGES = {
    "af": "Afrikaans", "sq": "Albanian", "am": "Amharic", "ar": "Arabic", "hy": "Armenian", 
    "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian", "bn": "Bengali", "bs": "Bosnian", 
    "bg": "Bulgarian", "ca": "Catalan", "ceb": "Cebuano", "ny": "Chichewa", "zh": "Chinese", 
    "co": "Corsican", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch", 
    "en": "English", "eo": "Esperanto", "et": "Estonian", "tl": "Filipino", "fi": "Finnish", 
    "fr": "French", "fy": "Frisian", "gl": "Galician", "ka": "Georgian", "de": "German", 
    "el": "Greek", "gu": "Gujarati", "ht": "Haitian Creole", "ha": "Hausa", "haw": "Hawaiian", 
    "iw": "Hebrew", "hi": "Hindi", "hmn": "Hmong", "hu": "Hungarian", "is": "Icelandic", 
    "ig": "Igbo", "id": "Indonesian", "ga": "Irish", "it": "Italian", "ja": "Japanese", 
    "jw": "Javanese", "kn": "Kannada", "kk": "Kazakh", "km": "Khmer", "rw": "Kinyarwanda", 
    "ko": "Korean", "ku": "Kurdish", "ky": "Kyrgyz", "lo": "Lao", "la": "Latin", 
    "lv": "Latvian", "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian", "mg": "Malagasy", 
    "ms": "Malay", "ml": "Malayalam", "mt": "Maltese", "mi": "Maori", "mr": "Marathi", 
    "mn": "Mongolian", "my": "Myanmar", "ne": "Nepali", "no": "Norwegian", "or": "Odia", 
    "ps": "Pashto", "fa": "Persian", "pl": "Polish", "pt": "Portuguese", "pa": "Punjabi", 
    "ro": "Romanian", "ru": "Russian", "sm": "Samoan", "gd": "Scots Gaelic", "sr": "Serbian", 
    "st": "Sesotho", "sn": "Shona", "sd": "Sindhi", "si": "Sinhala", "sk": "Slovak", 
    "sl": "Slovenian", "so": "Somali", "es": "Spanish", "su": "Sundanese", "sw": "Swahili", 
    "sv": "Swedish", "tg": "Tajik", "ta": "Tamil", "tt": "Tatar", "te": "Telugu", 
    "th": "Thai", "tr": "Turkish", "tk": "Turkmen", "uk": "Ukrainian", "ur": "Urdu", 
    "ug": "Uyghur", "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh", "xh": "Xhosa", 
    "yi": "Yiddish", "yo": "Yoruba", "zu": "Zulu"
}

TRANSLATIONS = {
    "en": {
        "dashboard": "Dashboard", "history": "History", "transfer": "Transfer", "cards": "Vault", "settings": "Settings",
        "total_balance": "Total Balance", "account_number": "Account Number", "send_money": "Send Money",
        "recent_tx": "Recent Transactions", "see_all": "See all", "no_tx": "No transactions yet.",
        "account_settings": "Account Settings", "log_out": "Log Out", "card_status": "Card Status",
        "freeze_card": "Freeze Card", "view_cvv": "View CVV", "download_stmt": "Download Statement",
        "get_pdf": "Get your PDF record", "download": "Download", "bank_name": "Bank name", "account_no": "Account number",
        "amount": "Amount", "withdraw_code": "Withdrawal code", "confirm_transfer": "Confirm Transfer",
        "funds_sent_to": "Funds will be sent to the bank account you enter below.",
        "transfer_processed": "Transfer Processed", "funds_sent_msg": "Your funds have been sent. It may take a few minutes to reflect.",
        "processing": "Processing", "processing_msg": "Your transfer is being processed for security reasons.",
        "do_not_close": "Please do not close this page.", "welcome_back": "Welcome back", "enter_password": "Enter your password to access your account.",
        "password": "Password", "login": "Log In", "statement": "Account Statement", "date": "Date",
        "account_holder": "Account Holder", "currency": "Currency", "tx_history": "Transaction History",
        "description": "Description", "ending_balance": "Ending Balance", "stmt_footer": "This is a computer-generated statement and does not require a signature.",
        "email_notif": "Email Notifications", "dark_mode": "Dark Mode", "biometrics": "Face ID / Biometrics",
        "active": "Active", "opened": "Opened", "completed": "Completed", "pending": "Pending", "unopened": "Unopened",
        "transfer_to": "Transfer to", "just_now": "Just now", "success": "Success", "verifying": "verifying…",
        "premium": "Premium", "today": "Today", "yesterday": "Yesterday",
        "from": "From", "to": "To"
    },
    "es": {
        "dashboard": "Panel", "history": "Historial", "transfer": "Transferir", "cards": "Bóveda", "settings": "Ajustes",
        "total_balance": "Saldo Total", "account_number": "Número de Cuenta", "send_money": "Enviar Dinero",
        "recent_tx": "Transacciones Recientes", "see_all": "Ver todo", "no_tx": "Aún no hay transacciones.",
        "account_settings": "Ajustes de Cuenta", "log_out": "Cerrar Sesión", "card_status": "Estado de la Tarjeta",
        "freeze_card": "Congelar Tarjeta", "view_cvv": "Ver CVV", "download_stmt": "Descargar Extracto",
        "get_pdf": "Obtén tu registro en PDF", "download": "Descargar", "bank_name": "Nombre del banco", "account_no": "Número de cuenta",
        "amount": "Cantidad", "withdraw_code": "Código de retiro", "confirm_transfer": "Confirmar Transferencia",
        "funds_sent_to": "Los fondos se enviarán a la cuenta bancaria que ingreses.",
        "transfer_processed": "Transferencia Procesada", "funds_sent_msg": "Tus fondos han sido enviados. Puede tardar unos minutos en reflejarse.",
        "processing": "Procesando", "processing_msg": "Tu transferencia está siendo procesada por razones de seguridad.",
        "do_not_close": "Por favor, no cierres esta página.", "welcome_back": "Bienvenido de nuevo", "enter_password": "Ingresa tu contraseña para acceder.",
        "password": "Contraseña", "login": "Iniciar Sesión", "statement": "Extracto de Cuenta", "date": "Fecha",
        "account_holder": "Titular de la Cuenta", "currency": "Moneda", "tx_history": "Historial de Transacciones",
        "description": "Descripción", "ending_balance": "Saldo Final", "stmt_footer": "Este es un extracto generado por computadora y no requiere firma.",
        "email_notif": "Notificaciones por Correo", "dark_mode": "Modo Oscuro", "biometrics": "Face ID / Biometría",
        "active": "Activo", "opened": "Abierto", "completed": "Completado", "pending": "Pendiente", "unopened": "No abierto",
        "transfer_to": "Transferencia a", "just_now": "Justo ahora", "success": "Éxito", "verifying": "verificando…",
        "premium": "Premium", "today": "Hoy", "yesterday": "Ayer",
        "from": "De", "to": "Para"
    },
    "fr": {
        "dashboard": "Tableau de bord", "history": "Historique", "transfer": "Virement", "cards": "Coffre", "settings": "Paramètres",
        "total_balance": "Solde Total", "account_number": "Numéro de Compte", "send_money": "Envoyer de l'Argent",
        "recent_tx": "Transactions Récentes", "see_all": "Voir tout", "no_tx": "Aucune transaction pour le moment.",
        "account_settings": "Paramètres du Compte", "log_out": "Déconnexion", "card_status": "Statut de la Carte",
        "freeze_card": "Geler la Carte", "view_cvv": "Voir le CVV", "download_stmt": "Télécharger le Relevé",
        "get_pdf": "Obtenez votre relevé PDF", "download": "Télécharger", "bank_name": "Nom de la banque", "account_no": "Numéro de compte",
        "amount": "Montant", "withdraw_code": "Code de retrait", "confirm_transfer": "Confirmer le Virement",
        "funds_sent_to": "Les fonds seront envoyés sur le compte bancaire que vous indiquerez ci-dessous.",
        "transfer_processed": "Virement Traité", "funds_sent_msg": "Vos fonds ont été envoyés. Cela peut prendre quelques minutes.",
        "processing": "Traitement", "processing_msg": "Votre virement est en cours de traitement pour des raisons de sécurité.",
        "do_not_close": "Veuillez ne pas fermer cette page.", "welcome_back": "Bon retour", "enter_password": "Entrez votre mot de passe pour accéder à votre compte.",
        "password": "Mot de passe", "login": "Se Connecter", "statement": "Relevé de Compte", "date": "Date",
        "account_holder": "Titulaire du Compte", "currency": "Devise", "tx_history": "Historique des Transactions",
        "description": "Description", "ending_balance": "Solde Final", "stmt_footer": "Ceci est un relevé généré par ordinateur et ne nécessite pas de signature.",
        "email_notif": "Notifications par E-mail", "dark_mode": "Mode Sombre", "biometrics": "Face ID / Biométrie",
        "active": "Actif", "opened": "Ouvert", "completed": "Complété", "pending": "En attente", "unopened": "Non ouvert",
        "transfer_to": "Virement à", "just_now": "À l'instant", "success": "Succès", "verifying": "vérification…",
        "premium": "Premium", "today": "Aujourd'hui", "yesterday": "Hier",
        "from": "De", "to": "À"
    },
    "pt": {
        "dashboard": "Painel", "history": "Histórico", "transfer": "Transferir", "cards": "Cofre", "settings": "Configurações",
        "total_balance": "Saldo Total", "account_number": "Número da Conta", "send_money": "Enviar Dinheiro",
        "recent_tx": "Transações Recentes", "see_all": "Ver tudo", "no_tx": "Nenhuma transação ainda.",
        "account_settings": "Configurações da Conta", "log_out": "Sair", "card_status": "Status do Cartão",
        "freeze_card": "Bloquear Cartão", "view_cvv": "Ver CVV", "download_stmt": "Baixar Extrato",
        "get_pdf": "Obtenha seu registro em PDF", "download": "Baixar", "bank_name": "Nome do banco", "account_no": "Número da conta",
        "amount": "Valor", "withdraw_code": "Código de saque", "confirm_transfer": "Confirmar Transferência",
        "funds_sent_to": "Os fundos serão enviados para a conta bancária que você inserir abaixo.",
        "transfer_processed": "Transferência Processada", "funds_sent_msg": "Seus fundos foram enviados. Pode levar alguns minutos.",
        "processing": "Processando", "processing_msg": "Sua transferência está sendo processada por motivos de segurança.",
        "do_not_close": "Por favor, não feche esta página.", "welcome_back": "Bem-vindo de volta", "enter_password": "Digite sua senha para acessar.",
        "password": "Senha", "login": "Entrar", "statement": "Extrato da Conta", "date": "Data",
        "account_holder": "Titular da Conta", "currency": "Moeda", "tx_history": "Histórico de Transações",
        "description": "Descrição", "ending_balance": "Saldo Final", "stmt_footer": "Este é um extrato gerado por computador e não requer assinatura.",
        "email_notif": "Notificações por E-mail", "dark_mode": "Modo Escuro", "biometrics": "Face ID / Biometria",
        "active": "Ativo", "opened": "Aberto", "completed": "Concluído", "pending": "Pendente", "unopened": "Não aberto",
        "transfer_to": "Transferência para", "just_now": "Agora mesmo", "success": "Sucesso", "verifying": "verificando…",
        "premium": "Premium", "today": "Hoje", "yesterday": "Ontem",
        "from": "De", "to": "Para"
    },
    "de": {
        "dashboard": "Übersicht", "history": "Verlauf", "transfer": "Überweisen", "cards": "Tresor", "settings": "Einstellungen",
        "total_balance": "Gesamtguthaben", "account_number": "Kontonummer", "send_money": "Geld Senden",
        "recent_tx": "Letzte Transaktionen", "see_all": "Alle ansehen", "no_tx": "Noch keine Transaktionen.",
        "account_settings": "Kontoeinstellungen", "log_out": "Abmelden", "card_status": "Kartenstatus",
        "freeze_card": "Karte Sperren", "view_cvv": "CVV Anzeigen", "download_stmt": "Kontoauszug Herunterladen",
        "get_pdf": "PDF-Aufzeichnung abrufen", "download": "Herunterladen", "bank_name": "Bankname", "account_no": "Kontonummer",
        "amount": "Betrag", "withdraw_code": "Auszahlungscode", "confirm_transfer": "Überweisung Bestätigen",
        "funds_sent_to": "Das Geld wird auf das unten eingegebene Bankkonto überwiesen.",
        "transfer_processed": "Überweisung Verarbeitet", "funds_sent_msg": "Ihr Geld wurde gesendet. Es kann einige Minuten dauern.",
        "processing": "Wird Verarbeitet", "processing_msg": "Ihre Überweisung wird aus Sicherheitsgründen verarbeitet.",
        "do_not_close": "Bitte schließen Sie diese Seite nicht.", "welcome_back": "Willkommen zurück", "enter_password": "Geben Sie Ihr Passwort ein.",
        "password": "Passwort", "login": "Anmelden", "statement": "Kontoauszug", "date": "Datum",
        "account_holder": "Kontoinhaber", "currency": "Währung", "tx_history": "Transaktionsverlauf",
        "description": "Beschreibung", "ending_balance": "Endsaldo", "stmt_footer": "Dies ist ein computergenerierter Auszug und erfordert keine Unterschrift.",
        "email_notif": "E-Mail-Benachrichtigungen", "dark_mode": "Dunkelmodus", "biometrics": "Face ID / Biometrie",
        "active": "Aktiv", "opened": "Geöffnet", "completed": "Abgeschlossen", "pending": "Ausstehend", "unopened": "Ungelesen",
        "transfer_to": "Überweisung an", "just_now": "Gerade eben", "success": "Erfolg", "verifying": "überprüfen…",
        "premium": "Premium", "today": "Heute", "yesterday": "Gestern",
        "from": "Von", "to": "An"
    },
    "it": {
        "dashboard": "Dashboard", "history": "Cronologia", "transfer": "Trasferimento", "cards": "Cassaforte", "settings": "Impostazioni",
        "total_balance": "Saldo Totale", "account_number": "Numero di Conto", "send_money": "Invia Denaro",
        "recent_tx": "Transazioni Recenti", "see_all": "Vedi tutto", "no_tx": "Nessuna transazione.",
        "account_settings": "Impostazioni Account", "log_out": "Esci", "card_status": "Stato Carta",
        "freeze_card": "Blocca Carta", "view_cvv": "Visualizza CVV", "download_stmt": "Scarica Estratto Conto",
        "get_pdf": "Ottieni il tuo PDF", "download": "Scarica", "bank_name": "Nome della banca", "account_no": "Numero di conto",
        "amount": "Importo", "withdraw_code": "Codice di prelievo", "confirm_transfer": "Conferma Trasferimento",
        "funds_sent_to": "I fondi verranno inviati al conto bancario inserito di seguito.",
        "transfer_processed": "Trasferimento Elaborato", "funds_sent_msg": "I tuoi fondi sono stati inviati. Potrebbero volerci alcuni minuti.",
        "processing": "In Elaborazione", "processing_msg": "Il tuo trasferimento è in fase di elaborazione per motivi di sicurezza.",
        "do_not_close": "Non chiudere questa pagina.", "welcome_back": "Bentornato", "enter_password": "Inserisci la tua password per accedere.",
        "password": "Password", "login": "Accedi", "statement": "Estratto Conto", "date": "Data",
        "account_holder": "Titolare del Conto", "currency": "Valuta", "tx_history": "Cronologia Transazioni",
        "description": "Descrizione", "ending_balance": "Saldo Finale", "stmt_footer": "Questo è un estratto conto generato dal computer e non richiede firma.",
        "email_notif": "Notifiche Email", "dark_mode": "Modalità Scura", "biometrics": "Face ID / Biometria",
        "active": "Attivo", "opened": "Aperto", "completed": "Completato", "pending": "In sospeso", "unopened": "Non aperto",
        "transfer_to": "Trasferimento a", "just_now": "Proprio ora", "success": "Successo", "verifying": "verifica…",
        "premium": "Premium", "today": "Oggi", "yesterday": "Ieri",
        "from": "Da", "to": "A"
    },
    "yo": {
        "dashboard": "Pátákó", "history": "Ìtàn", "transfer": "Ìfowópamọ́", "cards": "Àpótí", "settings": "Àwọn Ètò",
        "total_balance": "Iye Owó", "account_number": "Nọ́mbà Àkọsílẹ̀", "send_money": "Fi Owó Ránṣẹ́",
        "recent_tx": "Àwọn Ìdúnàádúrà Tuntun", "see_all": "Wo gbogbo rẹ̀", "no_tx": "Ko si ìdúnàádúrà kankan.",
        "account_settings": "Ètò Àkọsílẹ̀", "log_out": "Jáde", "card_status": "Ipò Káàdì",
        "freeze_card": "Dè Káàdì", "view_cvv": "Wo CVV", "download_stmt": "Gba Ìwé Ìtàn",
        "get_pdf": "Gba ìwé PDF rẹ", "download": "Gba", "bank_name": "Orúkọ Banki", "account_no": "Nọ́mbà Àkọsílẹ̀",
        "amount": "Iye", "withdraw_code": "Kóòdù Ìyọkúrò", "confirm_transfer": "Jẹ́rìí Ìfowópamọ́",
        "funds_sent_to": "A óò fi owó ránṣẹ́ sí àkọsílẹ̀ banki tí o bá kọ sí isalẹ.",
        "transfer_processed": "Ìfowópamọ́ Ti Ṣe", "funds_sent_msg": "A ti fi owó rẹ ránṣẹ́. O lè gba ìṣẹ́jú díẹ̀.",
        "processing": "Ń Ṣiṣẹ́", "processing_msg": "A ń ṣe ìfowópamọ́ rẹ fún ààbò.",
        "do_not_close": "Jọ̀wọ́ má ṣe pa ojú-ìwé yìí.",
        "welcome_back": "Káàbọ̀ padà", "enter_password": "Tẹ ọ̀rọ̀ ìpamọ́ rẹ láti wọlé.",
        "password": "Ọ̀rọ̀ Ìpamọ́", "login": "Wọlé", "statement": "Ìwé Ìtàn Àkọsílẹ̀", "date": "Ọjọ́",
        "account_holder": "Ẹni Tó Ni Àkọsílẹ̀", "currency": "Owó", "tx_history": "Ìtàn Ìdúnàádúrà",
        "description": "Àpèjúwe", "ending_balance": "Iye Tó Kù", "stmt_footer": "Ìwé ìtàn kọ̀mpútà ni èyí, kò nílò ìbọwọ́.",
        "email_notif": "Ìfitọ́nà Email", "dark_mode": "Ipò Òkùnkùn", "biometrics": "Face ID / Biometrics",
        "active": "Ń Ṣiṣẹ́", "opened": "Tí a ṣí", "completed": "Ti parí", "pending": "Ń dúró", "unopened": "A kò ṣí",
        "transfer_to": "Fi ránṣẹ́ sí", "just_now": "Nísisìyí", "success": "Àṣeyọrí", "verifying": "ń yẹ̀wò…",
        "premium": "Premium", "today": "Òní", "yesterday": "Àná",
        "from": "Láti", "to": "Sí"
    },
    "ha": {
        "dashboard": "Dashboard", "history": "Tarihi", "transfer": "Canja wuri", "cards": "Ajiya", "settings": "Saituna",
        "total_balance": "Jimlar Kuɗi", "account_number": "Lambar Asusu", "send_money": "Aika Kuɗi",
        "recent_tx": "Sabbin Ma'amaloli", "see_all": "Duba duka", "no_tx": "Babu ma'amala tukuna.",
        "account_settings": "Saitunan Asusu", "log_out": "Fita", "card_status": "Matsayin Kati",
        "freeze_card": "Daskare Kati", "view_cvv": "Duba CVV", "download_stmt": "Sauke Bayani",
        "get_pdf": "Sami PDF ɗinka", "download": "Sauke", "bank_name": "Sunan Banki", "account_no": "Lambar asusu",
        "amount": "Adadi", "withdraw_code": "Lambar cirewa", "confirm_transfer": "Tabbatar da Canja wuri",
        "funds_sent_to": "Za a aika kuɗin zuwa asusun banki da ka shigar a ƙasa.",
        "transfer_processed": "An Sarrafa Canja wuri", "funds_sent_msg": "An aika kuɗinka. Yana iya ɗaukar mintuna kaɗan.",
        "processing": "Ana Sarrafawa", "processing_msg": "Ana sarrafa canja wurinka don dalilan tsaro.",
        "do_not_close": "Don Allah kar ka rufe wannan shafin.",
        "welcome_back": "Barka da dawowa", "enter_password": "Shigar da kalmar sirri don shiga.",
        "password": "Kalmar Sirri", "login": "Shiga", "statement": "Bayanin Asusu", "date": "Kwanan wata",
        "account_holder": "Mai Asusu", "currency": "Kudin", "tx_history": "Tarihin Ma'amaloli",
        "description": "Bayani", "ending_balance": "Kuɗin da ya rage", "stmt_footer": "Wannan bayani ne na kwamfuta kuma baya buƙatar sa hannu.",
        "email_notif": "Sanarwar Email", "dark_mode": "Yanayin Duhu", "biometrics": "Face ID / Biometrics",
        "active": "Aiki", "opened": "An buɗe", "completed": "An kammala", "pending": "Ana jira", "unopened": "Ba a buɗe ba",
        "transfer_to": "Canja wuri zuwa", "just_now": "Yanzu", "success": "Nasara", "verifying": "tabbatarwa…",
        "premium": "Premium", "today": "Yau", "yesterday": "Jiya",
        "from": "Daga", "to": "Zuwa"
    },
    "ig": {
        "dashboard": "Dashboard", "history": "Akụkọ", "transfer": "Nyefe", "cards": "Ebe nchekwa", "settings": "Ntọala",
        "total_balance": "Mkpokọta Ego", "account_number": "Nọmba Akaụntụ", "send_money": "Zipu Ego",
        "recent_tx": "Azụmahịa ọhụrụ", "see_all": "Hụ ihe niile", "no_tx": "Enweghị azụmahịa.",
        "account_settings": "Ntọala Akaụntụ", "log_out": "Pụọ", "card_status": "Ọnọdụ Kaadị",
        "freeze_card": "Kpochie Kaadị", "view_cvv": "Hụ CVV", "download_stmt": "Budata Nkwupụta",
        "get_pdf": "Nweta PDF gị", "download": "Budata", "bank_name": "Aha ụlọ akụ", "account_no": "Nọmba akaụntụ",
        "amount": "Ego", "withdraw_code": "Koodu mwepụ", "confirm_transfer": "Kwenye Nyefe",
        "funds_sent_to": "A ga-eziga ego na akaụntụ ụlọ akụ ị tinyere n'okpuru.",
        "transfer_processed": "Emechara Nyefe", "funds_sent_msg": "Ezitere ego gị. Ọ nwere ike were nkeji ole na ole.",
        "processing": "Na-eme", "processing_msg": "A na-ahazi nyefe gị maka nchekwa.",
        "do_not_close": "Biko emechiela peeji a.",
        "welcome_back": "Nnọọ ọzọ", "enter_password": "Tinye paswọọdụ gị iji banye.",
        "password": "Paswọọdụ", "login": "Banye", "statement": "Nkwupụta Akaụntụ", "date": "Ụbọchị",
        "account_holder": "Onye nwe akaụntụ", "currency": "Ego", "tx_history": "Akụkọ Azụmahịa",
        "description": "Nkọwa", "ending_balance": "Ego fọdụrụ", "stmt_footer": "Nke a bụ nkwupụta kọmputa na-achọghị mbinye aka.",
        "email_notif": "Nzi ozi Email", "dark_mode": "Ọnọdụ Ọchịchịrị", "biometrics": "Face ID / Biometrics",
        "active": "Na-arụ ọrụ", "opened": "Mepee", "completed": "Emechara", "pending": "Na-eche", "unopened": "Emegheghị",
        "transfer_to": "Nyefe na", "just_now": "Ugbu a", "success": "Ihe ịga nke ọma", "verifying": "na-enyocha…",
        "premium": "Premium", "today": "Taa", "yesterday": "Ụnyaahụ",
        "from": "Site na", "to": "Na"
    },
    "ko": {
        "dashboard": "대시보드", "history": "내역", "transfer": "송금", "cards": "금고", "settings": "설정",
        "total_balance": "총 잔액", "account_number": "계좌 번호", "send_money": "송금하기",
        "recent_tx": "최근 거래", "see_all": "모두 보기", "no_tx": "거래 내역이 없습니다.",
        "account_settings": "계정 설정", "log_out": "로그아웃", "card_status": "카드 상태",
        "freeze_card": "카드 정지", "view_cvv": "CVV 보기", "download_stmt": "명세서 다운로드",
        "get_pdf": "PDF 기록 받기", "download": "다운로드", "bank_name": "은행 이름", "account_no": "계좌 번호",
        "amount": "금액", "withdraw_code": "출금 코드", "confirm_transfer": "송금 확인",
        "funds_sent_to": "아래 입력한 은행 계좌로 자금이 송금됩니다.",
        "transfer_processed": "송금 완료", "funds_sent_msg": "자금이 송금되었습니다. 반영되기까지 몇 분이 걸릴 수 있습니다.",
        "processing": "처리 중", "processing_msg": "보안상의 이유로 송금이 처리 중입니다.",
        "do_not_close": "이 페이지를 닫지 마십시오.", "welcome_back": "환영합니다", "enter_password": "계정에 접근하려면 비밀번호를 입력하십시오.",
        "password": "비밀번호", "login": "로그인", "statement": "계좌 명세서", "date": "날짜",
        "account_holder": "예금주", "currency": "통화", "tx_history": "거래 내역",
        "description": "설명", "ending_balance": "최종 잔액", "stmt_footer": "본 명세서는 컴퓨터로 생성되었으며 서명이 필요하지 않습니다.",
        "email_notif": "이메일 알림", "dark_mode": "다크 모드", "biometrics": "Face ID / 생체 인식",
        "active": "활성", "opened": "열림", "completed": "완료됨", "pending": "대기 중", "unopened": "열지 않음",
        "transfer_to": "송금처", "just_now": "방금 전", "success": "성공", "verifying": "확인 중…",
        "premium": "프리미엄", "today": "오늘", "yesterday": "어제",
        "from": "보낸 사람", "to": "받는 사람"
    },
    "ja": {
        "dashboard": "ダッシュボード", "history": "履歴", "transfer": "振込", "cards": "保管庫", "settings": "設定",
        "total_balance": "総残高", "account_number": "口座番号", "send_money": "送金",
        "recent_tx": "最近の取引", "see_all": "すべて見る", "no_tx": "取引はありません。",
        "account_settings": "アカウント設定", "log_out": "ログアウト", "card_status": "カードの状態",
        "freeze_card": "カードを凍結", "view_cvv": "CVVを表示", "download_stmt": "明細書をダウンロード",
        "get_pdf": "PDF記録を取得", "download": "ダウンロード", "bank_name": "銀行名", "account_no": "口座番号",
        "amount": "金額", "withdraw_code": "引き出しコード", "confirm_transfer": "振込を確認",
        "funds_sent_to": "以下に入力した銀行口座に資金が送金されます。",
        "transfer_processed": "振込完了", "funds_sent_msg": "資金が送金されました。反映されるまで数分かかる場合があります。",
        "processing": "処理中", "processing_msg": "セキュリティ上の理由により、振込を処理しています。",
        "do_not_close": "このページを閉じないでください。", "welcome_back": "おかえりなさい", "enter_password": "アカウントにアクセスするにはパスワードを入力してください。",
        "password": "パスワード", "login": "ログイン", "statement": "口座明細書", "date": "日付",
        "account_holder": "口座名義人", "currency": "通貨", "tx_history": "取引履歴",
        "description": "説明", "ending_balance": "最終残高", "stmt_footer": "これはコンピュータ生成の明細書であり、署名は不要です。",
        "email_notif": "メール通知", "dark_mode": "ダークモード", "biometrics": "Face ID / 生体認証",
        "active": "有効", "opened": "開封済み", "completed": "完了", "pending": "保留中", "unopened": "未開封",
        "transfer_to": "振込先", "just_now": "たった今", "success": "成功", "verifying": "確認中…",
        "premium": "プレミアム", "today": "今日", "yesterday": "昨日",
        "from": "送信者", "to": "受信者"
    },
    "ar": {
        "dashboard": "لوحة القيادة", "history": "السجل", "transfer": "تحويل", "cards": "خزنة", "settings": "الإعدادات",
        "total_balance": "الرصيد الإجمالي", "account_number": "رقم الحساب", "send_money": "إرسال الأموال",
        "recent_tx": "المعاملات الأخيرة", "see_all": "عرض الكل", "no_tx": "لا توجد معاملات بعد.",
        "account_settings": "إعدادات الحساب", "log_out": "تسجيل الخروج", "card_status": "حالة البطاقة",
        "freeze_card": "تجميد البطاقة", "view_cvv": "عرض CVV", "download_stmt": "تحميل كشف الحساب",
        "get_pdf": "احصل على سجل PDF الخاص بك", "download": "تحميل", "bank_name": "اسم البنك", "account_no": "رقم الحساب",
        "amount": "المبلغ", "withdraw_code": "رمز السحب", "confirm_transfer": "تأكيد التحويل",
        "funds_sent_to": "سيتم إرسال الأموال إلى الحساب المصرفي الذي تدخله أدناه.",
        "transfer_processed": "تمت معالجة التحويل", "funds_sent_msg": "تم إرسال أموالك. قد يستغرق ظهورها بضع دقائق.",
        "processing": "قيد المعالجة", "processing_msg": "يتم معالجة تحويلك لأسباب أمنية.",
        "do_not_close": "يرجى عدم إغلاق هذه الصفحة.", "welcome_back": "مرحباً بعودتك", "enter_password": "أدخل كلمة المرور للوصول إلى حسابك.",
        "password": "كلمة المرور", "login": "تسجيل الدخول", "statement": "كشف الحساب", "date": "التاريخ",
        "account_holder": "صاحب الحساب", "currency": "العملة", "tx_history": "سجل المعاملات",
        "description": "الوصف", "ending_balance": "الرصيد النهائي", "stmt_footer": "هذا كشف تم إنشاؤه بواسطة الكمبيوتر ولا يتطلب توقيعاً.",
        "email_notif": "إشعارات البريد الإلكتروني", "dark_mode": "الوضع الداكن", "biometrics": "Face ID / القياسات الحيوية",
        "active": "نشط", "opened": "مفتوح", "completed": "مكتمل", "pending": "قيد الانتظار", "unopened": "غير مفتوح",
        "transfer_to": "تحويل إلى", "just_now": "الآن", "success": "نجاح", "verifying": "جارٍ التحقق…",
        "premium": "بريميوم", "today": "اليوم", "yesterday": "أمس",
        "from": "من", "to": "إلى"
    },
    "hi": {
        "dashboard": "डैशबोर्ड", "history": "इतिहास", "transfer": "स्थानांतरण", "cards": "तिजोरी", "settings": "सेटिंग्स",
        "total_balance": "कुल शेष", "account_number": "खाता संख्या", "send_money": "पैसे भेजें",
        "recent_tx": "हाल के लेनदेन", "see_all": "सभी देखें", "no_tx": "अभी तक कोई लेनदेन नहीं।",
        "account_settings": "खाता सेटिंग्स", "log_out": "लॉग आउट", "card_status": "कार्ड की स्थिति",
        "freeze_card": "कार्ड फ्रीज करें", "view_cvv": "CVV देखें", "download_stmt": "विवरण डाउनलोड करें",
        "get_pdf": "अपना पीडीएफ रिकॉर्ड प्राप्त करें", "download": "डाउनलोड करें", "bank_name": "बैंक का नाम", "account_no": "खाता संख्या",
        "amount": "राशि", "withdraw_code": "निकासी कोड", "confirm_transfer": "स्थानांतरण की पुष्टि करें",
        "funds_sent_to": "धनराशि उस बैंक खाते में भेजी जाएगी जो आप नीचे दर्ज करेंगे।",
        "transfer_processed": "स्थानांतरण संसाधित", "funds_sent_msg": "आपका धन भेज दिया गया है। इसे प्रतिबिंबित होने में कुछ मिनट लग सकते हैं।",
        "processing": "प्रसंस्करण", "processing_msg": "सुरक्षा कारणों से आपका स्थानांतरण संसाधित किया जा रहा है।",
        "do_not_close": "कृपया इस पृष्ठ को बंद न करें।", "welcome_back": "वापसी पर स्वागत है", "enter_password": "अपने खाते तक पहुँचने के लिए अपना पासवर्ड दर्ज करें।",
        "password": "पासवर्ड", "login": "लॉग इन करें", "statement": "खाता विवरण", "date": "तारीख",
        "account_holder": "खाता धारक", "currency": "मुद्रा", "tx_history": "लेनदेन इतिहास",
        "description": "विवरण", "ending_balance": "अंतिम शेष", "stmt_footer": "यह कंप्यूटर जनित विवरण है और इसके लिए हस्ताक्षर की आवश्यकता नहीं है।",
        "email_notif": "ईमेल सूचनाएं", "dark_mode": "डार्क मोड", "biometrics": "फेस आईडी / बायोमेट्रिक्स",
        "active": "सक्रिय", "opened": "खोला गया", "completed": "पूरा हुआ", "pending": "लंबित", "unopened": "अनखुला",
        "transfer_to": "को स्थानांतरण", "just_now": "अभी", "success": "सफलता", "verifying": "सत्यापन हो रहा है…",
        "premium": "प्रीमियम", "today": "आज", "yesterday": "कल",
        "from": "से", "to": "को"
    },
    "ru": {
        "dashboard": "Панель", "history": "История", "transfer": "Перевод", "cards": "Хранилище", "settings": "Настройки",
        "total_balance": "Общий баланс", "account_number": "Номер счета", "send_money": "Отправить деньги",
        "recent_tx": "Последние транзакции", "see_all": "Посмотреть все", "no_tx": "Транзакций пока нет.",
        "account_settings": "Настройки аккаунта", "log_out": "Выйти", "card_status": "Статус карты",
        "freeze_card": "Заморозить карту", "view_cvv": "Посмотреть CVV", "download_stmt": "Скачать выписку",
        "get_pdf": "Получить PDF-запись", "download": "Скачать", "bank_name": "Название банка", "account_no": "Номер счета",
        "amount": "Сумма", "withdraw_code": "Код вывода", "confirm_transfer": "Подтвердить перевод",
        "funds_sent_to": "Средства будут отправлены на банковский счет, который вы укажете ниже.",
        "transfer_processed": "Перевод обработан", "funds_sent_msg": "Ваши средства отправлены. Это может занять несколько минут.",
        "processing": "Обработка", "processing_msg": "Ваш перевод обрабатывается по соображениям безопасности.",
        "do_not_close": "Пожалуйста, не закрывайте эту страницу.", "welcome_back": "С возвращением", "enter_password": "Введите пароль для доступа к аккаунту.",
        "password": "Пароль", "login": "Войти", "statement": "Выписка по счету", "date": "Дата",
        "account_holder": "Владелец счета", "currency": "Валюта", "tx_history": "История транзакций",
        "description": "Описание", "ending_balance": "Конечный баланс", "stmt_footer": "Это выписка, сгенерированная компьютером, и она не требует подписи.",
        "email_notif": "Уведомления по электронной почте", "dark_mode": "Темный режим", "biometrics": "Face ID / Биометрия",
        "active": "Активный", "opened": "Открыт", "completed": "Завершен", "pending": "В ожидании", "unopened": "Не открыт",
        "transfer_to": "Перевод на", "just_now": "Только что", "success": "Успех", "verifying": "проверка…",
        "premium": "Премиум", "today": "Сегодня", "yesterday": "Вчера",
        "from": "От", "to": "Кому"
    },
    "zh": {
        "dashboard": "仪表盘", "history": "历史记录", "transfer": "转账", "cards": "金库", "settings": "设置",
        "total_balance": "总余额", "account_number": "账号", "send_money": "汇款",
        "recent_tx": "最近交易", "see_all": "查看全部", "no_tx": "暂无交易记录。",
        "account_settings": "账户设置", "log_out": "退出登录", "card_status": "卡片状态",
        "freeze_card": "冻结卡片", "view_cvv": "查看CVV", "download_stmt": "下载对账单",
        "get_pdf": "获取PDF记录", "download": "下载", "bank_name": "银行名称", "account_no": "账号",
        "amount": "金额", "withdraw_code": "提现密码", "confirm_transfer": "确认转账",
        "funds_sent_to": "资金将发送至您在下方输入的银行账户。",
        "transfer_processed": "转账已处理", "funds_sent_msg": "您的资金已发送。可能需要几分钟才能反映在账户中。",
        "processing": "处理中", "processing_msg": "出于安全原因，您的转账正在处理中。",
        "do_not_close": "请勿关闭此页面。", "welcome_back": "欢迎回来", "enter_password": "请输入密码以访问您的账户。",
        "password": "密码", "login": "登录", "statement": "账户对账单", "date": "日期",
        "account_holder": "账户持有人", "currency": "货币", "tx_history": "交易记录",
        "description": "描述", "ending_balance": "期末余额", "stmt_footer": "这是由计算机生成的对账单，无需签名。",
        "email_notif": "邮件通知", "dark_mode": "深色模式", "biometrics": "面容 ID / 生物识别",
        "active": "活跃", "opened": "已打开", "completed": "已完成", "pending": "待处理", "unopened": "未打开",
        "transfer_to": "转账至", "just_now": "刚刚", "success": "成功", "verifying": "验证中…",
        "premium": "高级版", "today": "今天", "yesterday": "昨天",
        "from": "来自", "to": "至"
    },
"af": {"dashboard": "Paneelbord", "history": "Geskiedenis", "transfer": "Oordrag", "cards": "Kluis", "settings": "Instellings", "total_balance": "Totale Balans", "account_number": "Rekeningnommer", "send_money": "Stuur Geld", "recent_tx": "Onlangse Transaksies", "see_all": "Sien alles", "no_tx": "Nog geen transaksies nie.", "account_settings": "Rekeninginstellings", "log_out": "Teken uit", "card_status": "Kaartstatus", "freeze_card": "Vries Kaart", "view_cvv": "Sien CVV", "download_stmt": "Laai Staat", "get_pdf": "Kry jou PDF-rekord", "download": "Laai af", "bank_name": "Banknaam", "account_no": "Rekeningnommer", "amount": "Bedrag", "withdraw_code": "Onttrekkingskode", "confirm_transfer": "Bevestig Oordrag", "funds_sent_to": "Fondse sal na die bankrekening gestuur word wat jy hieronder invoer.", "transfer_processed": "Oordrag Verwerk", "funds_sent_msg": "Jou fondse is gestuur. Dit kan 'n paar minute neem om te reflekteer.", "processing": "Verwerking", "processing_msg": "Jou oordrag word verwerk om veiligheidsredes.", "do_not_close": "Moenie hierdie bladsy sluit nie.", "welcome_back": "Welkom terug", "enter_password": "Voer jou wagwoord in om toegang te kry.", "password": "Wagwoord", "login": "Teken In", "statement": "Rekeningstaat", "date": "Datum", "account_holder": "Rekeninghouer", "currency": "Geldeenheid", "tx_history": "Transaksiegeskiedenis", "description": "Beskrywing", "ending_balance": "Eindbalans", "stmt_footer": "Dit is 'n rekenaargegenereerde staat en vereis nie 'n handtekening nie.", "email_notif": "E-pos Kennisgewings", "dark_mode": "Donker Modus", "biometrics": "Face ID / Biometrie", "active": "Aktief", "opened": "Oopgemaak", "completed": "Voltooi", "pending": "Hangende", "unopened": "Ongeopend", "transfer_to": "Oordrag na", "just_now": "Nou net", "success": "Sukses", "verifying": "verifieer…", "premium": "Premie", "today": "Vandag", "yesterday": "Gister", "from": "Van", "to": "Aan"},
    "sq": {"dashboard": "Paneli", "history": "Historiku", "transfer": "Transferim", "cards": "Kasaforta", "settings": "Cilësimet", "total_balance": "Bilanci Total", "account_number": "Numri i Llogarisë", "send_money": "Dërgo Para", "recent_tx": "Transaksionet e Fundit", "see_all": "Shiko të gjitha", "no_tx": "Nuk ka transaksione ende.", "account_settings": "Cilësimet e Llogarisë", "log_out": "Shkyç", "card_status": "Statusi i Kartës", "freeze_card": "Ngrini Kartën", "view_cvv": "Shiko CVV", "download_stmt": "Shkarko Deklaratën", "get_pdf": "Merr regjistrin tënd PDF", "download": "Shkarko", "bank_name": "Emri i bankës", "account_no": "Numri i llogarisë", "amount": "Shuma", "withdraw_code": "Kodi i tërheqjes", "confirm_transfer": "Konfirmo Transferimin", "funds_sent_to": "Fondet do të dërgohen në llogarinë bankare që futni më poshtë.", "transfer_processed": "Transferimi u Përpunua", "funds_sent_msg": "Fondet tuaja janë dërguar. Mund të duhen disa minuta për t'u reflektuar.", "processing": "Përpunimi", "processing_msg": "Transferimi juaj po përpunohet për arsye sigurie.", "do_not_close": "Ju lutemi mos e mbyllni këtë faqe.", "welcome_back": "Mirë se u ktheve", "enter_password": "Futni fjalëkalimin për të hyrë.", "password": "Fjalëkalimi", "login": "Hyr", "statement": "Deklarata e Llogarisë", "date": "Data", "account_holder": "Mbajtësi i Llogarisë", "currency": "Monedha", "tx_history": "Historiku i Transaksioneve", "description": "Përshkrimi", "ending_balance": "Bilanci Përfundimtar", "stmt_footer": "Kjo është një deklaratë e krijuar nga kompjuteri dhe nuk kërkon nënshkrim.", "email_notif": "Njoftime Email", "dark_mode": "Modaliteti i Errët", "biometrics": "Face ID / Biometria", "active": "Aktiv", "opened": "Hapur", "completed": "Përfunduar", "pending": "Në pritje", "unopened": "I pahapur", "transfer_to": "Transfero në", "just_now": "Sapo tani", "success": "Sukses", "verifying": "duke verifikuar…", "premium": "Premium", "today": "Sot", "yesterday": "Dje", "from": "Nga", "to": "Për"},
    "am": {"dashboard": "ዳሽቦርድ", "history": "ታሪክ", "transfer": "ዝውውር", "cards": "ቮልት", "settings": "ቅንብሮች", "total_balance": "ጠቅላላ ቀሪ ሂሳብ", "account_number": "የሂሳብ ቁጥር", "send_money": "ገንዘብ ላክ", "recent_tx": "የቅርብ ጊዜ ግብይቶች", "see_all": "ሁሉንም ይመልከቱ", "no_tx": "እስካሁን ምንም ግብይቶች የሉም።", "account_settings": "የሂሳብ ቅንብሮች", "log_out": "ውጣ", "card_status": "የካርድ ሁኔታ", "freeze_card": "ካርድ አቀዝቅዝ", "view_cvv": "CVV ይመልከቱ", "download_stmt": "መግለጫ አውርድ", "get_pdf": "የPDF መዝገብዎን ያግኙ", "download": "አውርድ", "bank_name": "የባንክ ስም", "account_no": "የሂሳብ ቁጥር", "amount": "መጠን", "withdraw_code": "የማውጣት ኮድ", "confirm_transfer": "ዝውውርን አረጋግጥ", "funds_sent_to": "ገንዘቡ ከታች ወደሚያስገቡት የባንክ ሂሳብ ይላካል።", "transfer_processed": "ዝውውር ተሰራ", "funds_sent_msg": "ገንዘብዎ ተልኳል። ለመንጸባረቅ ጥቂት ደቂቃዎች ሊወስድ ይችላል።", "processing": "በሂደት ላይ", "processing_msg": "ዝውውርዎ በደህንነት ምክንያቶች እየተካሄደ ነው።", "do_not_close": "እባክዎ ይህን ገጽ አይዝጉ።", "welcome_back": "እንኳን ደህና መጡ", "enter_password": "ለመግባት የይለፍ ቃልዎን ያስገቡ።", "password": "የይለፍ ቃል", "login": "ግባ", "statement": "የሂሳብ መግለጫ", "date": "ቀን", "account_holder": "የሂሳብ ባለቤት", "currency": "ገንዘብ", "tx_history": "የግብይት ታሪክ", "description": "መግለጫ", "ending_balance": "የመጨረሻ ቀሪ ሂሳብ", "stmt_footer": "ይህ በኮምፒተር የተፈጠረ መግለጫ ነው እና ፊርማ አያስፈልገውም።", "email_notif": "የኢሜል ማሳወቂያዎች", "dark_mode": "ጨለማ ሁነታ", "biometrics": "Face ID / ባዮሜትሪክስ", "active": "ንቁ", "opened": "ተከፍቷል", "completed": "ተጠናቅቋል", "pending": "በመጠባበቅ ላይ", "unopened": "ያልተከፈተ", "transfer_to": "ወደ", "just_now": "አሁን", "success": "ስኬት", "verifying": "በማረጋገጥ ላይ…", "premium": "ፕሪሚየም", "today": "ዛሬ", "yesterday": "ትናንት", "from": "ከ", "to": "ወደ"},
    "az": {"dashboard": "İdarə paneli", "history": "Tarixçə", "transfer": "Köçürmə", "cards": "Kassa", "settings": "Tənzimləmələr", "total_balance": "Ümumi Balans", "account_number": "Hesab Nömrəsi", "send_money": "Pul Göndər", "recent_tx": "Son Əməliyyatlar", "see_all": "Hamısına bax", "no_tx": "Hələ heç bir əməliyyat yoxdur.", "account_settings": "Hesab Tənzimləmələri", "log_out": "Çıxış", "card_status": "Kart Statusu", "freeze_card": "Kartı Dondur", "view_cvv": "CVV-yə bax", "download_stmt": "Çıxarışı Yüklə", "get_pdf": "PDF qeydini əldə edin", "download": "Yüklə", "bank_name": "Bank adı", "account_no": "Hesab nömrəsi", "amount": "Məbləğ", "withdraw_code": "Çıxarış kodu", "confirm_transfer": "Köçürməni Təsdiqlə", "funds_sent_to": "Vəsaitlər aşağıda daxil etdiyiniz bank hesabına göndəriləcək.", "transfer_processed": "Köçürmə Emal Edildi", "funds_sent_msg": "Vəsaitləriniz göndərildi. Əks olunması bir neçə dəqiqə çəkə bilər.", "processing": "Emal edilir", "processing_msg": "Təhlükəsizlik səbəblərindən köçürməniz emal olunur.", "do_not_close": "Zəhmət olmasa bu səhifəni bağlamayın.", "welcome_back": "Xoş gəldiniz", "enter_password": "Daxil olmaq üçün şifrənizi daxil edin.", "password": "Şifrə", "login": "Daxil ol", "statement": "Hesab Çıxarışı", "date": "Tarix", "account_holder": "Hesab Sahibi", "currency": "Valyuta", "tx_history": "Əməliyyat Tarixçəsi", "description": "Təsvir", "ending_balance": "Yekun Balans", "stmt_footer": "Bu kompüter tərəfindən yaradılmış çıxarışdır və imza tələb etmir.", "email_notif": "E-poçt Bildirişləri", "dark_mode": "Qaranlıq Rejim", "biometrics": "Face ID / Biometriya", "active": "Aktiv", "opened": "Açıldı", "completed": "Tamamlandı", "pending": "Gözləyir", "unopened": "Açılmamış", "transfer_to": "Köçürmə", "just_now": "İndi", "success": "Uğur", "verifying": "yoxlanılır…", "premium": "Premium", "today": "Bu gün", "yesterday": "Dünən", "from": "Kimdən", "to": "Kimə"},
    "eu": {"dashboard": "Arbela", "history": "Historia", "transfer": "Transferentzia", "cards": "Ganga", "settings": "Ezarpenak", "total_balance": "Balantze Osoa", "account_number": "Kontu Zenbakia", "send_money": "Bidali Dirua", "recent_tx": "Azken Transakzioak", "see_all": "Ikusi guztiak", "no_tx": "Oraindik ez dago transakziorik.", "account_settings": "Kontuaren Ezarpenak", "log_out": "Amaitu saioa", "card_status": "Txartelaren Egoera", "freeze_card": "Izoztu Txartela", "view_cvv": "Ikusi CVV", "download_stmt": "Deskargatu Egoera", "get_pdf": "Lortu zure PDF erregistroa", "download": "Deskargatu", "bank_name": "Bankuaren izena", "account_no": "Kontu zenbakia", "amount": "Zenbatekoa", "withdraw_code": "Ateratzeko kodea", "confirm_transfer": "Berretsi Transferentzia", "funds_sent_to": "Funtsak behean sartzen duzun banku kontura bidaliko dira.", "transfer_processed": "Transferentzia Prozesatua", "funds_sent_msg": "Zure funtsak bidali dira. Minutu batzuk behar izan daitezke islatzeko.", "processing": "Prozesatzen", "processing_msg": "Zure transferentzia prozesatzen ari da segurtasun arrazoiengatik.", "do_not_close": "Mesedez, ez itxi orri hau.", "welcome_back": "Ongi etorri berriro", "enter_password": "Sartu zure pasahitza kontura sartzeko.", "password": "Pasahitza", "login": "Hasi saioa", "statement": "Kontu Egoera", "date": "Data", "account_holder": "Kontuaren Titularra", "currency": "Moneta", "tx_history": "Transakzio Historia", "description": "Deskribapena", "ending_balance": "Amaierako Balantzea", "stmt_footer": "Hau ordenagailuak sortutako egoera bat da eta ez du sinadurarik behar.", "email_notif": "Posta Elektronikoko Jakinarazpenak", "dark_mode": "Modu Iluna", "biometrics": "Face ID / Biometria", "active": "Aktiboa", "opened": "Irekia", "completed": "Osatua", "pending": "Zain", "unopened": "Ireki gabe", "transfer_to": "Transferentzia", "just_now": "Oraintxe", "success": "Arrakasta", "verifying": "egiaztatzen…", "premium": "Premium", "today": "Gaur", "yesterday": "Atzo", "from": "Nondik", "to": "Nora"},
    "be": {"dashboard": "Панэль", "history": "Гісторыя", "transfer": "Перавод", "cards": "Сховішча", "settings": "Налады", "total_balance": "Агульны баланс", "account_number": "Нумар рахунку", "send_money": "Адправіць грошы", "recent_tx": "Апошнія транзакцыі", "see_all": "Пабачыць усе", "no_tx": "Пакуль няма транзакцый.", "account_settings": "Налады рахунку", "log_out": "Выйсці", "card_status": "Статус карты", "freeze_card": "Замярозіць карту", "view_cvv": "Пабачыць CVV", "download_stmt": "Спампаваць выпіску", "get_pdf": "Атрымаць PDF-запіс", "download": "Спампаваць", "bank_name": "Назва банка", "account_no": "Нумар рахунку", "amount": "Сума", "withdraw_code": "Код зняцця", "confirm_transfer": "Пацвердзіць перавод", "funds_sent_to": "Сродкі будуць адпраўленыя на банкаўскі рахунак, які вы ўвядзеце ніжэй.", "transfer_processed": "Перавод апрацаваны", "funds_sent_msg": "Вашы сродкі адпраўленыя. Гэта можа заняць некалькі хвілін.", "processing": "Апрацоўка", "processing_msg": "Ваш перавод апрацоўваецца з меркаванняў бяспекі.", "do_not_close": "Калі ласка, не закрывайце гэтую старонку.", "welcome_back": "З вяртаннем", "enter_password": "Увядзіце пароль для доступу да рахунку.", "password": "Пароль", "login": "Увайсці", "statement": "Выпіска па рахунку", "date": "Дата", "account_holder": "Уладальнік рахунку", "currency": "Валюта", "tx_history": "Гісторыя транзакцый", "description": "Апісанне", "ending_balance": "Канчатковы баланс", "stmt_footer": "Гэта выпіска, створаная камп'ютарам, і не патрабуе подпісу.", "email_notif": "Апавяшчэнні па электроннай пошце", "dark_mode": "Цёмны рэжым", "biometrics": "Face ID / Біяметрыя", "active": "Актыўны", "opened": "Адкрыты", "completed": "Завершаны", "pending": "У чаканні", "unopened": "Не адкрыты", "transfer_to": "Перавод на", "just_now": "Толькі што", "success": "Поспех", "verifying": "праверка…", "premium": "Прэміум", "today": "Сёння", "yesterday": "Учора", "from": "Ад", "to": "Каму"},
    "bn": {"dashboard": "ড্যাশবোর্ড", "history": "ইতিহাস", "transfer": "স্থানান্তর", "cards": "ভল্ট", "settings": "সেটিংস", "total_balance": "মোট ব্যালেন্স", "account_number": "অ্যাকাউন্ট নম্বর", "send_money": "টাকা পাঠান", "recent_tx": "সাম্প্রতিক লেনদেন", "see_all": "সব দেখুন", "no_tx": "এখনও কোন লেনদেন নেই।", "account_settings": "অ্যাকাউন্ট সেটিংস", "log_out": "লগ আউট", "card_status": "কার্ডের স্থিতি", "freeze_card": "কার্ড ফ্রিজ করুন", "view_cvv": "CVV দেখুন", "download_stmt": "স্টেটমেন্ট ডাউনলোড করুন", "get_pdf": "আপনার পিডিএফ রেকর্ড পান", "download": "ডাউনলোড", "bank_name": "ব্যাংকের নাম", "account_no": "অ্যাকাউন্ট নম্বর", "amount": "পরিমাণ", "withdraw_code": "উত্তোলন কোড", "confirm_transfer": "স্থানান্তর নিশ্চিত করুন", "funds_sent_to": "আপনি নিচে যে ব্যাংক অ্যাকাউন্টে প্রবেশ করবেন সেখানে তহবিল পাঠানো হবে।", "transfer_processed": "স্থানান্তর প্রক্রিয়া করা হয়েছে", "funds_sent_msg": "আপনার তহবিল পাঠানো হয়েছে। এটি প্রতিফলিত হতে কয়েক মিনিট সময় লাগতে পারে।", "processing": "প্রক্রিয়াকরণ", "processing_msg": "নিরাপত্তার কারণে আপনার স্থানান্তর প্রক্রিয়া করা হচ্ছে।", "do_not_close": "অনুগ্রহ করে এই পৃষ্ঠাটি বন্ধ করবেন না।", "welcome_back": "স্বাগতম", "enter_password": "আপনার অ্যাকাউন্ট অ্যাক্সেস করতে পাসওয়ার্ড লিখুন।", "password": "পাসওয়ার্ড", "login": "লগ ইন", "statement": "অ্যাকাউন্ট স্টেটমেন্ট", "date": "তারিখ", "account_holder": "অ্যাকাউন্ট হোল্ডার", "currency": "মুদ্রা", "tx_history": "লেনদেনের ইতিহাস", "description": "বর্ণনা", "ending_balance": "শেষ ব্যালেন্স", "stmt_footer": "এটি একটি কম্পিউটার-জেনারেটেড স্টেটমেন্ট এবং এটির জন্য স্বাক্ষরের প্রয়োজন নেই।", "email_notif": "ইমেল বিজ্ঞপ্তি", "dark_mode": "ডার্ক মোড", "biometrics": "ফেস আইডি / বায়োমেট্রিক্স", "active": "সক্রিয়", "opened": "খোলা হয়েছে", "completed": "সম্পন্ন", "pending": "মুলতুবি", "unopened": "খোলা হয়নি", "transfer_to": "স্থানান্তর করুন", "just_now": "এখনই", "success": "সফল", "verifying": "যাচাই করা হচ্ছে…", "premium": "প্রিমিয়াম", "today": "আজ", "yesterday": "গতকাল", "from": "থেকে", "to": "প্রতি"},
    "bs": {"dashboard": "Nadzorna ploča", "history": "Historija", "transfer": "Transfer", "cards": "Trezor", "settings": "Postavke", "total_balance": "Ukupni Saldo", "account_number": "Broj Računa", "send_money": "Pošalji Novac", "recent_tx": "Nedavne Transakcije", "see_all": "Vidi sve", "no_tx": "Još nema transakcija.", "account_settings": "Postavke Računa", "log_out": "Odjava", "card_status": "Status Kartice", "freeze_card": "Zamrzni Karticu", "view_cvv": "Vidi CVV", "download_stmt": "Preuzmi Izvod", "get_pdf": "Preuzmi PDF zapis", "download": "Preuzmi", "bank_name": "Ime banke", "account_no": "Broj računa", "amount": "Iznos", "withdraw_code": "Kod za podizanje", "confirm_transfer": "Potvrdi Transfer", "funds_sent_to": "Sredstva će biti poslana na bankovni račun koji unesete ispod.", "transfer_processed": "Transfer Obrađen", "funds_sent_msg": "Vaša sredstva su poslana. Može potrajati nekoliko minuta da se prikažu.", "processing": "Obrada", "processing_msg": "Vaš transfer se obrađuje iz sigurnosnih razloga.", "do_not_close": "Molimo vas da ne zatvarate ovu stranicu.", "welcome_back": "Dobrodošli natrag", "enter_password": "Unesite lozinku za pristup računu.", "password": "Lozinka", "login": "Prijava", "statement": "Izvod Računa", "date": "Datum", "account_holder": "Vlasnik Računa", "currency": "Valuta", "tx_history": "Historija Transakcija", "description": "Opis", "ending_balance": "Konačni Saldo", "stmt_footer": "Ovo je kompjuterski generisan izvod i ne zahtijeva potpis.", "email_notif": "Email Obavijesti", "dark_mode": "Tamni Način", "biometrics": "Face ID / Biometrija", "active": "Aktivan", "opened": "Otvoreno", "completed": "Završeno", "pending": "Na čekanju", "unopened": "Neotvoreno", "transfer_to": "Transfer na", "just_now": "Upravo sada", "success": "Uspjeh", "verifying": "provjera…", "premium": "Premium", "today": "Danas", "yesterday": "Jučer", "from": "Od", "to": "Za"},
    "bg": {"dashboard": "Табло", "history": "История", "transfer": "Трансфер", "cards": "Сейф", "settings": "Настройки", "total_balance": "Общ Баланс", "account_number": "Номер на сметка", "send_money": "Изпрати Пари", "recent_tx": "Последни Транзакции", "see_all": "Виж всички", "no_tx": "Все още няма транзакции.", "account_settings": "Настройки на сметката", "log_out": "Изход", "card_status": "Статус на картата", "freeze_card": "Замрази картата", "view_cvv": "Виж CVV", "download_stmt": "Изтегли извлечение", "get_pdf": "Вземи своя PDF запис", "download": "Изтегли", "bank_name": "Име на банката", "account_no": "Номер на сметка", "amount": "Сума", "withdraw_code": "Код за теглене", "confirm_transfer": "Потвърди трансфера", "funds_sent_to": "Средствата ще бъдат изпратени по банковата сметка, която въведете по-долу.", "transfer_processed": "Трансферът е обработен", "funds_sent_msg": "Средствата ви са изпратени. Може да отнеме няколко минути, за да се отразят.", "processing": "Обработка", "processing_msg": "Трансферът ви се обработва поради съображения за сигурност.", "do_not_close": "Моля, не затваряйте тази страница.", "welcome_back": "Добре дошли отново", "enter_password": "Въведете паролата си за достъп до акаунта.", "password": "Парола", "login": "Вход", "statement": "Извлечение от сметка", "date": "Дата", "account_holder": "Титуляр на сметка", "currency": "Валута", "tx_history": "История на транзакциите", "description": "Описание", "ending_balance": "Краен баланс", "stmt_footer": "Това е компютърно генерирано извлечение и не изисква подпис.", "email_notif": "Известия по имейл", "dark_mode": "Тъмен режим", "biometrics": "Face ID / Биометрия", "active": "Активен", "opened": "Отворен", "completed": "Завършен", "pending": "Изчакващ", "unopened": "Неотворен", "transfer_to": "Трансфер към", "just_now": "Току-що", "success": "Успех", "verifying": "проверка…", "premium": "Премиум", "today": "Днес", "yesterday": "Вчера", "from": "От", "to": "До"},
    "ca": {"dashboard": "Tauler", "history": "Historial", "transfer": "Transferència", "cards": "Caixa forta", "settings": "Configuració", "total_balance": "Saldo Total", "account_number": "Número de Compte", "send_money": "Enviar Diners", "recent_tx": "Transaccions Recents", "see_all": "Veure tot", "no_tx": "Encara no hi ha transaccions.", "account_settings": "Configuració del Compte", "log_out": "Tancar sessió", "card_status": "Estat de la Targeta", "freeze_card": "Congelar Targeta", "view_cvv": "Veure CVV", "download_stmt": "Descarregar Extracte", "get_pdf": "Obtén el teu registre PDF", "download": "Descarregar", "bank_name": "Nom del banc", "account_no": "Número de compte", "amount": "Import", "withdraw_code": "Codi de retirada", "confirm_transfer": "Confirmar Transferència", "funds_sent_to": "Els fons s'enviaran al compte bancari que introduïu a continuació.", "transfer_processed": "Transferència Processada", "funds_sent_msg": "Els teus fons s'han enviat. Pot trigar uns minuts a reflectir-se.", "processing": "Processant", "processing_msg": "La teva transferència s'està processant per motius de seguretat.", "do_not_close": "Si us plau, no tanquis aquesta pàgina.", "welcome_back": "Benvingut de nou", "enter_password": "Introdueix la teva contrasenya per accedir al compte.", "password": "Contrasenya", "login": "Iniciar sessió", "statement": "Extracte de Compte", "date": "Data", "account_holder": "Titular del Compte", "currency": "Moneda", "tx_history": "Historial de Transaccions", "description": "Descripció", "ending_balance": "Saldo Final", "stmt_footer": "Aquest és un extracte generat per ordinador i no requereix signatura.", "email_notif": "Notificacions per Correu", "dark_mode": "Mode Fosc", "biometrics": "Face ID / Biometria", "active": "Actiu", "opened": "Obert", "completed": "Completat", "pending": "Pendent", "unopened": "No obert", "transfer_to": "Transferència a", "just_now": "Ara mateix", "success": "Èxit", "verifying": "verificant…", "premium": "Premium", "today": "Avui", "yesterday": "Ahir", "from": "De", "to": "A"},
    "ceb": {"dashboard": "Dashboard", "history": "Kasaysayan", "transfer": "Pagbalhin", "cards": "Vault", "settings": "Mga Setting", "total_balance": "Kinatibuk-ang Balanse", "account_number": "Numero sa Account", "send_money": "Pagpadala og Kwarta", "recent_tx": "Bag-ong mga Transaksyon", "see_all": "Tan-awa tanan", "no_tx": "Wala pay mga transaksyon.", "account_settings": "Mga Setting sa Account", "log_out": "Pag-log Out", "card_status": "Status sa Kard", "freeze_card": "I-freeze ang Kard", "view_cvv": "Tan-awa ang CVV", "download_stmt": "I-download ang Statement", "get_pdf": "Kuhaa ang imong PDF record", "download": "I-download", "bank_name": "Ngalan sa bangko", "account_no": "Numero sa account", "amount": "Kantidad", "withdraw_code": "Code sa pag-withdraw", "confirm_transfer": "Kumpirmaha ang Pagbalhin", "funds_sent_to": "Ang pondo ipadala sa bank account nga imong isulod sa ubos.", "transfer_processed": "Naproseso ang Pagbalhin", "funds_sent_msg": "Ang imong pondo gipadala na. Mahimong magdugay og pila ka minuto aron maipakita.", "processing": "Giproseso", "processing_msg": "Ang imong pagbalhin giproseso tungod sa mga hinungdan sa seguridad.", "do_not_close": "Palihug ayaw isira kining panid.", "welcome_back": "Maayong pagbalik", "enter_password": "Isulod ang imong password aron maka-access.", "password": "Password", "login": "Pag-log In", "statement": "Statement sa Account", "date": "Petsa", "account_holder": "Tag-iya sa Account", "currency": "Salapi", "tx_history": "Kasaysayan sa Transaksyon", "description": "Paghulagway", "ending_balance": "Katapusang Balanse", "stmt_footer": "Kini usa ka computer-generated nga statement ug wala magkinahanglan og pirma.", "email_notif": "Mga Notipikasyon sa Email", "dark_mode": "Dark Mode", "biometrics": "Face ID / Biometrics", "active": "Aktibo", "opened": "Giablihan", "completed": "Nahuman", "pending": "Naghulat", "unopened": "Wala maablihi", "transfer_to": "Pagbalhin sa", "just_now": "Karon lang", "success": "Malampuson", "verifying": "gipanghimatuud…", "premium": "Premium", "today": "Karon", "yesterday": "Kagahapon", "from": "Gikan sa", "to": "Ngadto sa"},
    "ny": {"dashboard": "Dashboard", "history": "Mbiri", "transfer": "Kusamutsa", "cards": "Vault", "settings": "Zokonda", "total_balance": "Ndalama Zonse", "account_number": "Nambala ya Akaunti", "send_money": "Tumizani Ndalama", "recent_tx": "Zochitika Zaposachedwa", "see_all": "Onani zonse", "no_tx": "Palibe zochitika pakadali pano.", "account_settings": "Zokonda za Akaunti", "log_out": "Tulukani", "card_status": "Mkhalidwe wa Khadi", "freeze_card": "Imitsani Khadi", "view_cvv": "Onani CVV", "download_stmt": "Tsitsani Chikalata", "get_pdf": "Pezani mbiri yanu ya PDF", "download": "Tsitsani", "bank_name": "Dzina la banki", "account_no": "Nambala ya akaunti", "amount": "Kuchuluka", "withdraw_code": "Khodi yotulutsa", "confirm_transfer": "Tsimikizirani Kusamutsa", "funds_sent_to": "Ndalama zitumizidwa ku akaunti ya banki yomwe mwalowa pansipa.", "transfer_processed": "Kusamutsa Kwachitika", "funds_sent_msg": "Ndalama zanu zatumizidwa. Zitha kutenga mphindi zingapo kuti ziwonekere.", "processing": "Ikukonza", "processing_msg": "Kusamutsa kwanu kukukonzedwa chifukwa cha chitetezo.", "do_not_close": "Chonde musatseke tsamba iyi.", "welcome_back": "Takulandirani", "enter_password": "Lowetsani mawu achinsinsi kuti mulowe.", "password": "Mawu Achinsinsi", "login": "Lowani", "statement": "Chikalata cha Akaunti", "date": "Tsiku", "account_holder": "Mwini Akaunti", "currency": "Ndalama", "tx_history": "Mbiri ya Zochitika", "description": "Kufotokozera", "ending_balance": "Ndalama Zomaliza", "stmt_footer": "Ichi ndi chikalata chopangidwa ndi makompyuta ndipo sichifuna siginecha.", "email_notif": "Zidziwitso za Imelo", "dark_mode": "Mawonekedwe Akuda", "biometrics": "Face ID / Biometrics", "active": "Wogwira ntchito", "opened": "Watsegulidwa", "completed": "Watha", "pending": "Akudikira", "unopened": "Wosatsegulidwa", "transfer_to": "Kusamutsa ku", "just_now": "Pano", "success": "Kupambana", "verifying": "ikutsimikizira…", "premium": "Premium", "today": "Lero", "yesterday": "Dzulo", "from": "Kuchokera", "to": "Kwa"},
    "co": {"dashboard": "Dashboard", "history": "Storia", "transfer": "Trasferimentu", "cards": "Cofre", "settings": "Paràmetri", "total_balance": "Bilanciu Totale", "account_number": "Numeru di Contu", "send_money": "Mandà Soldi", "recent_tx": "Transazzioni Recenti", "see_all": "Veda tuttu", "no_tx": "Nisuna transazzioni.", "account_settings": "Paràmetri di u Contu", "log_out": "Sorta", "card_status": "Statu di a Carta", "freeze_card": "Ghiaccia a Carta", "view_cvv": "Veda u CVV", "download_stmt": "Scaricà l'Estrattu", "get_pdf": "Ottieni u toccu PDF", "download": "Scaricà", "bank_name": "Nome di a banca", "account_no": "Numeru di contu", "amount": "Importu", "withdraw_code": "Codice di ritirata", "confirm_transfer": "Cunfirmà u Trasferimentu", "funds_sent_to": "I fondi seranu inviati à u contu bancariu chì inserisci quì sottu.", "transfer_processed": "Trasferimentu Trattatu", "funds_sent_msg": "I to fondi sò stati inviati. Pò piglià qualchì minutu.", "processing": "Trattamentu", "processing_msg": "U to trasferimentu hè in corsu per ragioni di sicurità.", "do_not_close": "Per piacè ùn chjude micca sta pagina.", "welcome_back": "Bentornatu", "enter_password": "Inserisci a to parola d'ordine per accede.", "password": "Parola d'ordine", "login": "Cunnettà", "statement": "Estrattu di Contu", "date": "Data", "account_holder": "Titulare di u Contu", "currency": "Muneta", "tx_history": "Storia di e Transazzioni", "description": "Descrizzione", "ending_balance": "Bilanciu Finale", "stmt_footer": "Questu hè un estrattu generatu da l'urdinatore è ùn richiede micca una firma.", "email_notif": "Notificazioni Email", "dark_mode": "Modu Scuru", "biometrics": "Face ID / Biometria", "active": "Attivu", "opened": "Apertu", "completed": "Compitu", "pending": "In attesa", "unopened": "Micca apertu", "transfer_to": "Trasferimentu à", "just_now": "Avà", "success": "Successu", "verifying": "verificà…", "premium": "Premium", "today": "Oghje", "yesterday": "Eri", "from": "Da", "to": "À"},
    "hr": {"dashboard": "Nadzorna ploča", "history": "Povijest", "transfer": "Prijenos", "cards": "Trezor", "settings": "Postavke", "total_balance": "Ukupni Saldo", "account_number": "Broj Računa", "send_money": "Pošalji Novac", "recent_tx": "Nedavne Transakcije", "see_all": "Vidi sve", "no_tx": "Još nema transakcija.", "account_settings": "Postavke Računa", "log_out": "Odjava", "card_status": "Status Kartice", "freeze_card": "Zamrzni Karticu", "view_cvv": "Vidi CVV", "download_stmt": "Preuzmi Izvadak", "get_pdf": "Preuzmi PDF zapis", "download": "Preuzmi", "bank_name": "Ime banke", "account_no": "Broj računa", "amount": "Iznos", "withdraw_code": "Kod za podizanje", "confirm_transfer": "Potvrdi Prijenos", "funds_sent_to": "Sredstva će biti poslana na bankovni račun koji unesete ispod.", "transfer_processed": "Prijenos Obrađen", "funds_sent_msg": "Vaša sredstva su poslana. Može potrajati nekoliko minuta.", "processing": "Obrada", "processing_msg": "Vaš prijenos se obrađuje iz sigurnosnih razloga.", "do_not_close": "Molimo vas da ne zatvarate ovu stranicu.", "welcome_back": "Dobrodošli natrag", "enter_password": "Unesite lozinku za pristup računu.", "password": "Lozinka", "login": "Prijava", "statement": "Izvadak Računa", "date": "Datum", "account_holder": "Vlasnik Računa", "currency": "Valuta", "tx_history": "Povijest Transakcija", "description": "Opis", "ending_balance": "Konačni Saldo", "stmt_footer": "Ovo je računalno generiran izvadak i ne zahtijeva potpis.", "email_notif": "Email Obavijesti", "dark_mode": "Tamni Način", "biometrics": "Face ID / Biometrija", "active": "Aktivan", "opened": "Otvoreno", "completed": "Završeno", "pending": "Na čekanju", "unopened": "Neotvoreno", "transfer_to": "Prijenos na", "just_now": "Upravo sada", "success": "Uspjeh", "verifying": "provjera…", "premium": "Premium", "today": "Danas", "yesterday": "Jučer", "from": "Od", "to": "Za"},
    "cs": {"dashboard": "Nástěnka", "history": "Historie", "transfer": "Převod", "cards": "Trezor", "settings": "Nastavení", "total_balance": "Celkový Zůstatek", "account_number": "Číslo Účtu", "send_money": "Poslat Peníze", "recent_tx": "Nedávné Transakce", "see_all": "Zobrazit vše", "no_tx": "Zatím žádné transakce.", "account_settings": "Nastavení Účtu", "log_out": "Odhlásit se", "card_status": "Stav Karty", "freeze_card": "Zmrazit Kartu", "view_cvv": "Zobrazit CVV", "download_stmt": "Stáhnout Výpis", "get_pdf": "Získat PDF záznam", "download": "Stáhnout", "bank_name": "Název banky", "account_no": "Číslo účtu", "amount": "Částka", "withdraw_code": "Kód pro výběr", "confirm_transfer": "Potvrdit Převod", "funds_sent_to": "Prostředky budou odeslány na bankovní účet, který zadáte níže.", "transfer_processed": "Převod Zpracován", "funds_sent_msg": "Vaše prostředky byly odeslány. Může trvat několik minut, než se projeví.", "processing": "Zpracování", "processing_msg": "Váš převod se zpracovává z bezpečnostních důvodů.", "do_not_close": "Prosím nezavírejte tuto stránku.", "welcome_back": "Vítejte zpět", "enter_password": "Zadejte heslo pro přístup k účtu.", "password": "Heslo", "login": "Přihlásit se", "statement": "Výpis z Účtu", "date": "Datum", "account_holder": "Majitel Účtu", "currency": "Měna", "tx_history": "Historie Transakcí", "description": "Popis", "ending_balance": "Konečný Zůstatek", "stmt_footer": "Toto je počítačem generovaný výpis a nevyžaduje podpis.", "email_notif": "E-mailová Upozornění", "dark_mode": "Tmavý Režim", "biometrics": "Face ID / Biometrie", "active": "Aktivní", "opened": "Otevřeno", "completed": "Dokončeno", "pending": "Čeká na vyřízení", "unopened": "Neotevřeno", "transfer_to": "Převod do", "just_now": "Právě teď", "success": "Úspěch", "verifying": "ověřování…", "premium": "Premium", "today": "Dnes", "yesterday": "Včera", "from": "Od", "to": "Komu"},
    "da": {"dashboard": "Dashboard", "history": "Historik", "transfer": "Overførsel", "cards": "Boks", "settings": "Indstillinger", "total_balance": "Samlet Saldo", "account_number": "Kontonummer", "send_money": "Send Penge", "recent_tx": "Seneste Transaktioner", "see_all": "Se alle", "no_tx": "Ingen transaktioner endnu.", "account_settings": "Kontoindstillinger", "log_out": "Log Ud", "card_status": "Kortstatus", "freeze_card": "Frys Kort", "view_cvv": "Se CVV", "download_stmt": "Download Kontoudtog", "get_pdf": "Få din PDF-post", "download": "Download", "bank_name": "Banknavn", "account_no": "Kontonummer", "amount": "Beløb", "withdraw_code": "Udbetalingskode", "confirm_transfer": "Bekræft Overførsel", "funds_sent_to": "Pengene sendes til den bankkonto, du indtaster nedenfor.", "transfer_processed": "Overførsel Behandlet", "funds_sent_msg": "Dine penge er sendt. Det kan tage et par minutter at afspejle.", "processing": "Behandler", "processing_msg": "Din overførsel behandles af sikkerhedshensyn.", "do_not_close": "Luk venligst ikke denne side.", "welcome_back": "Velkommen tilbage", "enter_password": "Indtast din adgangskode for at få adgang.", "password": "Adgangskode", "login": "Log Ind", "statement": "Kontoudtog", "date": "Dato", "account_holder": "Kontohaver", "currency": "Valuta", "tx_history": "Transaktionshistorik", "description": "Beskrivelse", "ending_balance": "Slutsaldo", "stmt_footer": "Dette er et computerudtog og kræver ikke underskrift.", "email_notif": "Email Notifikationer", "dark_mode": "Mørk Tilstand", "biometrics": "Face ID / Biometri", "active": "Aktiv", "opened": "Åbnet", "completed": "Fuldført", "pending": "Afventer", "unopened": "Uåbnet", "transfer_to": "Overførsel til", "just_now": "Lige nu", "success": "Succes", "verifying": "bekræfter…", "premium": "Premium", "today": "I dag", "yesterday": "I går", "from": "Fra", "to": "Til"},
    "nl": {"dashboard": "Dashboard", "history": "Geschiedenis", "transfer": "Overschrijving", "cards": "Kluis", "settings": "Instellingen", "total_balance": "Totaal Saldo", "account_number": "Rekeningnummer", "send_money": "Geld Sturen", "recent_tx": "Recente Transacties", "see_all": "Bekijk alles", "no_tx": "Nog geen transacties.", "account_settings": "Account Instellingen", "log_out": "Uitloggen", "card_status": "Kaartstatus", "freeze_card": "Kaart Bevriezen", "view_cvv": "CVV Bekijken", "download_stmt": "Afschrift Downloaden", "get_pdf": "Ontvang je PDF-overzicht", "download": "Downloaden", "bank_name": "Banknaam", "account_no": "Rekeningnummer", "amount": "Bedrag", "withdraw_code": "Opnamecode", "confirm_transfer": "Bevestig Overschrijving", "funds_sent_to": "Het geld wordt overgemaakt naar de bankrekening die je hieronder invoert.", "transfer_processed": "Overschrijving Verwerkt", "funds_sent_msg": "Je geld is verzonden. Het kan een paar minuten duren voordat het zichtbaar is.", "processing": "Verwerken", "processing_msg": "Je overschrijving wordt om veiligheidsredenen verwerkt.", "do_not_close": "Sluit deze pagina niet.", "welcome_back": "Welkom terug", "enter_password": "Voer je wachtwoord in om toegang te krijgen.", "password": "Wachtwoord", "login": "Inloggen", "statement": "Rekeningafschrift", "date": "Datum", "account_holder": "Rekeninghouder", "currency": "Valuta", "tx_history": "Transactiegeschiedenis", "description": "Beschrijving", "ending_balance": "Eindsaldo", "stmt_footer": "Dit is een computergemaakt afschrift en vereist geen handtekening.", "email_notif": "E-mailmeldingen", "dark_mode": "Donkere Modus", "biometrics": "Face ID / Biometrie", "active": "Actief", "opened": "Geopend", "completed": "Voltooid", "pending": "In afwachting", "unopened": "Ongeopend", "transfer_to": "Overschrijving naar", "just_now": "Zojuist", "success": "Succes", "verifying": "verifiëren…", "premium": "Premium", "today": "Vandaag", "yesterday": "Gisteren", "from": "Van", "to": "Naar"},
    "eo": {"dashboard": "Panelo", "history": "Historio", "transfer": "Transdono", "cards": "Kelo", "settings": "Agordoj", "total_balance": "Totala Saldo", "account_number": "Kontonumero", "send_money": "Sendi Monon", "recent_tx": "Lastaj Transakcioj", "see_all": "Vidi ĉion", "no_tx": "Ankoraŭ neniuj transakcioj.", "account_settings": "Kontaj Agordoj", "log_out": "Elsaluti", "card_status": "Karta Statuso", "freeze_card": "Frostigi Karton", "view_cvv": "Vidi CVV", "download_stmt": "Elŝuti Deklaron", "get_pdf": "Akiri vian PDF-rikordon", "download": "Elŝuti", "bank_name": "Banknomo", "account_no": "Kontonumero", "amount": "Sumo", "withdraw_code": "Eltira Kodo", "confirm_transfer": "Konfirmi Transdonon", "funds_sent_to": "Fundoj estos senditaj al la banka konto, kiun vi enigos sube.", "transfer_processed": "Transdono Prilaborita", "funds_sent_msg": "Viaj fundoj estis senditaj. Povas daŭri kelkajn minutojn por reflekti.", "processing": "Prilaborado", "processing_msg": "Via transdono estas prilaborata pro sekurecaj kialoj.", "do_not_close": "Bonvolu ne fermi ĉi tiun paĝon.", "welcome_back": "Bonvenon reen", "enter_password": "Enigu vian pasvorton por aliri vian konton.", "password": "Pasvorto", "login": "Ensaluti", "statement": "Konta Deklaro", "date": "Dato", "account_holder": "Kontposedanto", "currency": "Valuto", "tx_history": "Transakcia Historio", "description": "Priskribo", "ending_balance": "Fina Saldo", "stmt_footer": "Ĉi tio estas komputile generita deklaro kaj ne postulas subskribon.", "email_notif": "Retpoŝtaj Sciigoj", "dark_mode": "Malhela Reĝimo", "biometrics": "Face ID / Biometrio", "active": "Aktiva", "opened": "Malfermita", "completed": "Finita", "pending": "Pritraktata", "unopened": "Ne malfermita", "transfer_to": "Transdono al", "just_now": "Ĝuste nun", "success": "Sukceso", "verifying": "kontrolante…", "premium": "Premio", "today": "Hodiaŭ", "yesterday": "Hieraŭ", "from": "De", "to": "Al"},
    "et": {"dashboard": "Armatuurlaud", "history": "Ajalugu", "transfer": "Ülekanne", "cards": "Seif", "settings": "Seaded", "total_balance": "Kogu Saldo", "account_number": "Konto Number", "send_money": "Saada Raha", "recent_tx": "Viimased Tehingud", "see_all": "Vaata kõiki", "no_tx": "Tehingud puuduvad.", "account_settings": "Konto Seaded", "log_out": "Logi välja", "card_status": "Kaardi Olek", "freeze_card": "Külmuta Kaart", "view_cvv": "Vaata CVV", "download_stmt": "Laadi Väljavõte", "get_pdf": "Hangi oma PDF-kirje", "download": "Laadi alla", "bank_name": "Panga nimi", "account_no": "Konto number", "amount": "Summa", "withdraw_code": "Väljavõtu kood", "confirm_transfer": "Kinnita Ülekanne", "funds_sent_to": "Vahendid saadetakse allpool sisestatud pangakontole.", "transfer_processed": "Ülekanne Töödeldud", "funds_sent_msg": "Teie vahendid on saadetud. Võib võtta paar minutit.", "processing": "Töötlemine", "processing_msg": "Teie ülekannet töödeldakse turvakaalutlustel.", "do_not_close": "Palun ärge sulgege seda lehte.", "welcome_back": "Tere tulemast tagasi", "enter_password": "Sisestage parool, et kontole juurde pääseda.", "password": "Parool", "login": "Logi sisse", "statement": "Konto Väljavõte", "date": "Kuupäev", "account_holder": "Konto Omanik", "currency": "Valuuta", "tx_history": "Tehingute Ajalugu", "description": "Kirjeldus", "ending_balance": "Lõppsaldo", "stmt_footer": "See on arvuti genereeritud väljavõte ja ei vaja allkirja.", "email_notif": "E-posti Teavitused", "dark_mode": "Tume Režiim", "biometrics": "Face ID / Biomeetria", "active": "Aktiivne", "opened": "Avatud", "completed": "Lõpetatud", "pending": "Ootel", "unopened": "Avamata", "transfer_to": "Ülekanne", "just_now": "Just praegu", "success": "Edu", "verifying": "kinnitamine…", "premium": "Premium", "today": "Täna", "yesterday": "Eile", "from": "Kellelt", "to": "Kellele"},
    "tl": {"dashboard": "Dashboard", "history": "Kasaysayan", "transfer": "Ilipat", "cards": "Vault", "settings": "Mga Setting", "total_balance": "Kabuuang Balanse", "account_number": "Numero ng Account", "send_money": "Magpadala ng Pera", "recent_tx": "Mga Kamakailang Transaksyon", "see_all": "Tingnan lahat", "no_tx": "Wala pang mga transaksyon.", "account_settings": "Mga Setting ng Account", "log_out": "Mag-log Out", "card_status": "Katayuan ng Card", "freeze_card": "I-freeze ang Card", "view_cvv": "Tingnan ang CVV", "download_stmt": "I-download ang Statement", "get_pdf": "Kunin ang iyong PDF record", "download": "I-download", "bank_name": "Pangalan ng bangko", "account_no": "Numero ng account", "amount": "Halaga", "withdraw_code": "Code ng pag-withdraw", "confirm_transfer": "Kumpirmahin ang Paglipat", "funds_sent_to": "Ang mga pondo ay ipapadala sa bank account na iyong ilalagay sa ibaba.", "transfer_processed": "Naproseso ang Paglipat", "funds_sent_msg": "Naipadala na ang iyong mga pondo. Maaaring tumagal ng ilang minuto bago ito magpakita.", "processing": "Pinoproseso", "processing_msg": "Ang iyong paglipat ay pinoproseso para sa mga kadahilanang pangseguridad.", "do_not_close": "Mangyaring huwag isara ang pahinang ito.", "welcome_back": "Maligayang pagbabalik", "enter_password": "Ilagay ang iyong password para ma-access ang account.", "password": "Password", "login": "Mag-log In", "statement": "Statement ng Account", "date": "Petsa", "account_holder": "May-ari ng Account", "currency": "Pera", "tx_history": "Kasaysayan ng Transaksyon", "description": "Paglalarawan", "ending_balance": "Panghuling Balanse", "stmt_footer": "Ito ay isang computer-generated na statement at hindi nangangailangan ng pirma.", "email_notif": "Mga Notification sa Email", "dark_mode": "Dark Mode", "biometrics": "Face ID / Biometrics", "active": "Aktibo", "opened": "Nabuksan", "completed": "Nakumpleto", "pending": "Nakabinbin", "unopened": "Hindi nabuksan", "transfer_to": "Ilipat sa", "just_now": "Ngayon lang", "success": "Tagumpay", "verifying": "nagbe-verify…", "premium": "Premium", "today": "Ngayon", "yesterday": "Kahapon", "from": "Mula kay", "to": "Para kay"},
    "fi": {"dashboard": "Kojelauta", "history": "Historia", "transfer": "Siirto", "cards": "Holvi", "settings": "Asetukset", "total_balance": "Kokonaissaldo", "account_number": "Tilinumero", "send_money": "Lähetä Rahaa", "recent_tx": "Viimeisimmät Tapahtumat", "see_all": "Näytä kaikki", "no_tx": "Ei tapahtumia vielä.", "account_settings": "Tilin Asetukset", "log_out": "Kirjaudu ulos", "card_status": "Kortin Tila", "freeze_card": "Jäädytä Kortti", "view_cvv": "Näytä CVV", "download_stmt": "Lataa Tiliote", "get_pdf": "Hanki PDF-tietueesi", "download": "Lataa", "bank_name": "Pankin nimi", "account_no": "Tilinumero", "amount": "Summa", "withdraw_code": "Nostokoodi", "confirm_transfer": "Vahvista Siirto", "funds_sent_to": "Varat lähetetään alla syöttämällesi pankkitilille.", "transfer_processed": "Siirto Käsitelty", "funds_sent_msg": "Varasi on lähetetty. Kestää muutaman minuutin.", "processing": "Käsittely", "processing_msg": "Siirtoasi käsitellään turvallisuussyistä.", "do_not_close": "Älä sulje tätä sivua.", "welcome_back": "Tervetuloa takaisin", "enter_password": "Syötä salasanasi päästäksesi tilillesi.", "password": "Salasana", "login": "Kirjaudu sisään", "statement": "Tiliote", "date": "Päivämäärä", "account_holder": "Tilinomistaja", "currency": "Valuutta", "tx_history": "Tapahtumahistoria", "description": "Kuvaus", "ending_balance": "Loppusaldo", "stmt_footer": "Tämä on tietokoneen luoma tiliote, eikä vaadi allekirjoitusta.", "email_notif": "Sähköposti-ilmoitukset", "dark_mode": "Tumma Tila", "biometrics": "Face ID / Biometria", "active": "Aktiivinen", "opened": "Avattu", "completed": "Valmis", "pending": "Odottaa", "unopened": "Avaamaton", "transfer_to": "Siirto vastaanottajalle", "just_now": "Juuri nyt", "success": "Onnistui", "verifying": "vahvistetaan…", "premium": "Premium", "today": "Tänään", "yesterday": "Eilen", "from": "Lähettäjä", "to": "Vastaanottaja"},
    "fy": {"dashboard": "Dashboard", "history": "Skiednis", "transfer": "Oerdracht", "cards": "Klûs", "settings": "Ynstellings", "total_balance": "Totaal Saldo", "account_number": "Rekkeningsnûmer", "send_money": "Jild Stjoere", "recent_tx": "Resinte Transaksjes", "see_all": "Sjoch alles", "no_tx": "Noch gjin transaksjes.", "account_settings": "Rekkenynstellings", "log_out": "Útlogge", "card_status": "Kaartstatus", "freeze_card": "Beferzje Kaart", "view_cvv": "Sjoch CVV", "download_stmt": "Download Ofskrift", "get_pdf": "Krij dyn PDF-record", "download": "Download", "bank_name": "Banknamme", "account_no": "Rekkeningsnûmer", "amount": "Bedrach", "withdraw_code": "Opnamekoade", "confirm_transfer": "Befêstigje Oerdracht", "funds_sent_to": "It jild wurdt stjoerd nei de bankrekening dy't jo hjirûnder ynfiere.", "transfer_processed": "Oerdracht Ferwurke", "funds_sent_msg": "Jo jild is stjoerd. It kin in pear minuten duorje.", "processing": "Ferwurkje", "processing_msg": "Jo oerdracht wurdt ferwurke om feiligensredenen.", "do_not_close": "Slút dizze side asjebleaft net.", "welcome_back": "Wolkom werom", "enter_password": "Fier jo wachtwurd yn foar tagong.", "password": "Wachtwurd", "login": "Ynlogge", "statement": "Rekkenôfskrift", "date": "Datum", "account_holder": "Rekkenhâlder", "currency": "Muntienheid", "tx_history": "Transaksjeskiednis", "description": "Beskriuwing", "ending_balance": "Einsaldo", "stmt_footer": "Dit is in kompjûtergenerearre ôfskrift en fereasket gjin hantekening.", "email_notif": "E-postmeldingen", "dark_mode": "Tsjustere Modus", "biometrics": "Face ID / Biometry", "active": "Aktyf", "opened": "Iepene", "completed": "Foltôge", "pending": "Yn ôfwachting", "unopened": "Net iepene", "transfer_to": "Oerdracht nei", "just_now": "Krekt no", "success": "Sukses", "verifying": "ferifiearje…", "premium": "Premium", "today": "Hjoed", "yesterday": "Juster", "from": "Fan", "to": "Nei"},
    "gl": {"dashboard": "Panel", "history": "Historial", "transfer": "Transferencia", "cards": "Caixa forte", "settings": "Axustes", "total_balance": "Saldo Total", "account_number": "Número de Conta", "send_money": "Enviar Diñeiro", "recent_tx": "Transaccións Recentes", "see_all": "Ver todo", "no_tx": "Aínda non hai transaccións.", "account_settings": "Axustes da Conta", "log_out": "Pechar sesión", "card_status": "Estado da Tarxeta", "freeze_card": "Conxelar Tarxeta", "view_cvv": "Ver CVV", "download_stmt": "Descargar Extracto", "get_pdf": "Obtén o teu rexistro PDF", "download": "Descargar", "bank_name": "Nome do banco", "account_no": "Número de conta", "amount": "Importe", "withdraw_code": "Código de retirada", "confirm_transfer": "Confirmar Transferencia", "funds_sent_to": "Os fondos enviaranse á conta bancaria que introduzas a continuación.", "transfer_processed": "Transferencia Procesada", "funds_sent_msg": "Os teus fondos foron enviados. Pode tardar uns minutos.", "processing": "Procesando", "processing_msg": "A túa transferencia estase procesando por motivos de seguridade.", "do_not_close": "Por favor, non peches esta páxina.", "welcome_back": "Benvido de novo", "enter_password": "Introduce o teu contrasinal para acceder.", "password": "Contrasinal", "login": "Iniciar sesión", "statement": "Extracto de Conta", "date": "Data", "account_holder": "Titular da Conta", "currency": "Moeda", "tx_history": "Historial de Transaccións", "description": "Descrición", "ending_balance": "Saldo Final", "stmt_footer": "Este é un extracto xerado por ordenador e non require sinatura.", "email_notif": "Notificacións por Correo", "dark_mode": "Modo Escuro", "biometrics": "Face ID / Biometría", "active": "Activo", "opened": "Aberto", "completed": "Completado", "pending": "Pendente", "unopened": "Non aberto", "transfer_to": "Transferencia a", "just_now": "Agora mesmo", "success": "Éxito", "verifying": "verificando…", "premium": "Premium", "today": "Hoxe", "yesterday": "Onte", "from": "De", "to": "A"},
    "ka": {"dashboard": "დაფა", "history": "ისტორია", "transfer": "გადარიცხვა", "cards": "სეიფი", "settings": "პარამეტრები", "total_balance": "სრული ბალანსი", "account_number": "ანგარიშის ნომერი", "send_money": "თანხის გაგზავნა", "recent_tx": "ბოლო ტრანზაქციები", "see_all": "ყველას ნახვა", "no_tx": "ტრანზაქციები ჯერ არ არის.", "account_settings": "ანგარიშის პარამეტრები", "log_out": "გასვლა", "card_status": "ბარათის სტატუსი", "freeze_card": "ბარათის გაყინვა", "view_cvv": "CVV-ის ნახვა", "download_stmt": "ამონაწერის ჩამოტვირთვა", "get_pdf": "მიიღეთ PDF ჩანაწერი", "download": "ჩამოტვირთვა", "bank_name": "ბანკის სახელი", "account_no": "ანგარიშის ნომერი", "amount": "თანხა", "withdraw_code": "გატანის კოდი", "confirm_transfer": "გადარიცხვის დადასტურება", "funds_sent_to": "თანხა გაიგზავნება ქვემოთ მითითებულ საბანკო ანგარიშზე.", "transfer_processed": "გადარიცხვა დამუშავებულია", "funds_sent_msg": "თქვენი თანხა გაიგზავნა. შეიძლება რამდენიმე წუთი დასჭირდეს.", "processing": "მუშავდება", "processing_msg": "თქვენი გადარიცხვა მუშავდება უსაფრთხოების მიზეზების გამო.", "do_not_close": "გთხოვთ, არ დახუროთ ეს გვერდი.", "welcome_back": "მოგესალმებით", "enter_password": "შეიყვანეთ პაროლი წვდომისთვის.", "password": "პაროლი", "login": "შესვლა", "statement": "ანგარიშის ამონაწერი", "date": "თარიღი", "account_holder": "ანგარიშის მფლობელი", "currency": "ვალუტა", "tx_history": "ტრანზაქციების ისტორია", "description": "აღწერა", "ending_balance": "საბოლოო ბალანსი", "stmt_footer": "ეს არის კომპიუტერულად გენერირებული ამონაწერი და ხელმოწერას არ საჭიროებს.", "email_notif": "ელფოსტის შეტყობინებები", "dark_mode": "მუქი რეჟიმი", "biometrics": "Face ID / ბიომეტრია", "active": "აქტიური", "opened": "გახსნილია", "completed": "დასრულებულია", "pending": "მოლოდინში", "unopened": "გაუხსნელი", "transfer_to": "გადარიცხვა", "just_now": "ახლახან", "success": "წარმატება", "verifying": "მოწმდება…", "premium": "პრემიუმ", "today": "დღეს", "yesterday": "გუშინ", "from": "ვისგან", "to": "ვის"},
    "el": {"dashboard": "Πίνακας", "history": "Ιστορικό", "transfer": "Μεταφορά", "cards": "Θυρίδα", "settings": "Ρυθμίσεις", "total_balance": "Συνολικό Υπόλοιπο", "account_number": "Αριθμός Λογαριασμού", "send_money": "Αποστολή Χρημάτων", "recent_tx": "Πρόσφατες Συναλλαγές", "see_all": "Προβολή όλων", "no_tx": "Δεν υπάρχουν συναλλαγές ακόμα.", "account_settings": "Ρυθμίσεις Λογαριασμού", "log_out": "Αποσύνδεση", "card_status": "Κατάσταση Κάρτας", "freeze_card": "Πάγωμα Κάρτας", "view_cvv": "Προβολή CVV", "download_stmt": "Λήψη Απόδειξης", "get_pdf": "Λάβετε το αρχείο PDF σας", "download": "Λήψη", "bank_name": "Όνομα τράπεζας", "account_no": "Αριθμός λογαριασμού", "amount": "Ποσό", "withdraw_code": "Κωδικός ανάληψης", "confirm_transfer": "Επιβεβαίωση Μεταφοράς", "funds_sent_to": "Τα κεφάλαια θα σταλούν στον τραπεζικό λογαριασμό που θα εισαγάγετε παρακάτω.", "transfer_processed": "Η Μεταφορά Επεξεργάστηκε", "funds_sent_msg": "Τα κεφάλαιά σας στάλθηκαν. Μπορεί να χρειαστούν λίγα λεπτά.", "processing": "Επεξεργασία", "processing_msg": "Η μεταφορά σας υποβάλλεται σε επεξεργασία για λόγους ασφαλείας.", "do_not_close": "Παρακαλώ μην κλείσετε αυτήν τη σελίδα.", "welcome_back": "Καλώς ορίσατε", "enter_password": "Εισαγάγετε τον κωδικό πρόσβασης για πρόσβαση.", "password": "Κωδικός πρόσβασης", "login": "Σύνδεση", "statement": "Απόδειξη Λογαριασμού", "date": "Ημερομηνία", "account_holder": "Κάτοχος Λογαριασμού", "currency": "Νόμισμα", "tx_history": "Ιστορικό Συναλλαγών", "description": "Περιγραφή", "ending_balance": "Τελικό Υπόλοιπο", "stmt_footer": "Αυτή είναι μια ηλεκτρονικά παραγόμενη απόδειξη και δεν απαιτεί υπογραφή.", "email_notif": "Ειδοποιήσεις Email", "dark_mode": "Σκοτεινή Λειτουργία", "biometrics": "Face ID / Βιομετρικά", "active": "Ενεργό", "opened": "Ανοιχτό", "completed": "Ολοκληρωμένο", "pending": "Σε εκκρεμότητα", "unopened": "Μη ανοιγμένο", "transfer_to": "Μεταφορά σε", "just_now": "Μόλις τώρα", "success": "Επιτυχία", "verifying": "επαλήθευση…", "premium": "Premium", "today": "Σήμερα", "yesterday": "Χθες", "from": "Από", "to": "Προς"},
    "gu": {"dashboard": "ડેશબોર્ડ", "history": "ઇતિહાસ", "transfer": "ટ્રાન્સફર", "cards": "વોલ્ટ", "settings": "સેટિંગ્સ", "total_balance": "કુલ સંતુલન", "account_number": "એકાઉન્ટ નંબર", "send_money": "પૈસા મોકલો", "recent_tx": "તાજેતરના વ્યવહારો", "see_all": "બધું જુઓ", "no_tx": "હજી સુધી કોઈ વ્યવહાર નથી.", "account_settings": "એકાઉન્ટ સેટિંગ્સ", "log_out": "લોગ આઉટ", "card_status": "કાર્ડ સ્થિતિ", "freeze_card": "કાર્ડ ફ્રીઝ કરો", "view_cvv": "CVV જુઓ", "download_stmt": "સ્ટેટમેન્ટ ડાઉનલોડ કરો", "get_pdf": "તમારો PDF રેકોર્ડ મેળવો", "download": "ડાઉનલોડ કરો", "bank_name": "બેંકનું નામ", "account_no": "એકાઉન્ટ નંબર", "amount": "રકમ", "withdraw_code": "ઉપાડ કોડ", "confirm_transfer": "ટ્રાન્સફરની પુષ્ટિ કરો", "funds_sent_to": "ભંડોળ તમે નીચે દાખલ કરો છો તે બેંક ખાતામાં મોકલવામાં આવશે.", "transfer_processed": "ટ્રાન્સફર પ્રોસેસ થયું", "funds_sent_msg": "તમારા ભંડોળ મોકલવામાં આવ્યા છે. પ્રતિબિંબિત થવામાં થોડી મિનિટો લાગી શકે છે.", "processing": "પ્રોસેસિંગ", "processing_msg": "સુરક્ષા કારણોસર તમારું ટ્રાન્સફર પ્રોસેસ થઈ રહ્યું છે.", "do_not_close": "કૃપા કરીને આ પૃષ્ઠ બંધ કરશો નહીં.", "welcome_back": "પાછા આવવા પર સ્વાગત છે", "enter_password": "એક્સેસ કરવા માટે તમારો પાસવર્ડ દાખલ કરો.", "password": "પાસવર્ડ", "login": "લોગ ઇન કરો", "statement": "એકાઉન્ટ સ્ટેટમેન્ટ", "date": "તારીખ", "account_holder": "એકાઉન્ટ ધારક", "currency": "કરન્સી", "tx_history": "વ્યવહાર ઇતિહાસ", "description": "વર્ણન", "ending_balance": "અંતિમ સંતુલન", "stmt_footer": "આ કમ્પ્યુટર-જનરેટેડ સ્ટેટમેન્ટ છે અને તેને સહીની જરૂર નથી.", "email_notif": "ઇમેઇલ સૂચનાઓ", "dark_mode": "ડાર્ક મોડ", "biometrics": "ફેસ આઈડી / બાયોમેટ્રિક્સ", "active": "સક્રિય", "opened": "ખોલ્યું", "completed": "પૂર્ણ", "pending": "બાકી", "unopened": "ન ખોલ્યું", "transfer_to": "આમાં ટ્રાન્સફર કરો", "just_now": "હમણાં જ", "success": "સફળતા", "verifying": "ચકાસી રહ્યું છે…", "premium": "પ્રીમિયમ", "today": "આજે", "yesterday": "ગઈકાલે", "from": "તરફથી", "to": "તરફ"},
    "ht": {"dashboard": "Dashboard", "history": "Istwa", "transfer": "Transfè", "cards": "Kòf", "settings": "Paramèt", "total_balance": "Balans Total", "account_number": "Nimewo Kont", "send_money": "Voye Lajan", "recent_tx": "Transaksyon Resan", "see_all": "Wè tout", "no_tx": "Pa gen transaksyon ankò.", "account_settings": "Paramèt Kont", "log_out": "Dekonekte", "card_status": "Estati Kat", "freeze_card": "Jele Kat", "view_cvv": "Wè CVV", "download_stmt": "Telechaje Deklarasyon", "get_pdf": "Jwenn dosye PDF ou", "download": "Telechaje", "bank_name": "Non bank", "account_no": "Nimewo kont", "amount": "Kantite", "withdraw_code": "Kòd retrè", "confirm_transfer": "Konfime Transfè", "funds_sent_to": "Lajan ap voye nan kont labank ou antre anba a.", "transfer_processed": "Transfè Trete", "funds_sent_msg": "Yo voye lajan w. Li ka pran kèk minit pou l parèt.", "processing": "Ap trete", "processing_msg": "Transfè w ap trete pou rezon sekirite.", "do_not_close": "Tanpri pa fèmen paj sa a.", "welcome_back": "Byenveni tounen", "enter_password": "Antre modpas ou pou w jwenn aksè.", "password": "Modpas", "login": "Konekte", "statement": "Deklarasyon Kont", "date": "Dat", "account_holder": "Mèt Kont", "currency": "Lajan", "tx_history": "Istwa Transaksyon", "description": "Deskripsyon", "ending_balance": "Balans Final", "stmt_footer": "Sa a se yon deklarasyon ki jenere pa òdinatè epi li pa mande siyati.", "email_notif": "Notifikasyon Imèl", "dark_mode": "Mòd Nwa", "biometrics": "Face ID / Biometrik", "active": "Aktif", "opened": "Ouvè", "completed": "Konplete", "pending": "An atant", "unopened": "Pa ouvè", "transfer_to": "Transfè nan", "just_now": "Kounye a", "success": "Siksè", "verifying": "ap verifye…", "premium": "Premium", "today": "Jodi a", "yesterday": "Yè", "from": "Soti nan", "to": "Pou"},
    "haw": {"dashboard": "Dashboard", "history": "Moolelo", "transfer": "Hoolohe", "cards": "Vault", "settings": "Hooholo", "total_balance": "Koea Nui", "account_number": "Helu Moʻokāki", "send_money": "Hoʻouna i ke kālā", "recent_tx": "Nā hana hou", "see_all": "Nānā a pau", "no_tx": "ʻAʻohe hana i kēia manawa.", "account_settings": "Nā hoʻonohonoho moʻokāki", "log_out": "Haʻalele", "card_status": "Ke kūlana o ke kāleka", "freeze_card": "Hoʻopaʻa i ke kāleka", "view_cvv": "Nānā i ka CVV", "download_stmt": "Hoʻoiho i ka ʻōlelo", "get_pdf": "Loaʻa kāu palapala PDF", "download": "Hoʻoiho", "bank_name": "Inoa o ka panakō", "account_no": "Helu moʻokāki", "amount": "Nui", "withdraw_code": "Kāleka unuhi", "confirm_transfer": "Hōʻoia i ka hoʻoili", "funds_sent_to": "E hoʻouna ʻia ke kālā i ka moʻokāki panakō āu e kākau ai ma lalo.", "transfer_processed": "Ua hana ʻia ka hoʻoili", "funds_sent_msg": "Ua hoʻouna ʻia kāu kālā. Hiki ke lōʻihi i kekahi mau minuke.", "processing": "Ke hana ʻia nei", "processing_msg": "Ke hana ʻia nei kāu hoʻoili no nā kumu palekana.", "do_not_close": "E ʻoluʻolu mai pani i kēia ʻaoʻao.", "welcome_back": "Welina mai", "enter_password": "E kākau i kāu ʻōlelo huna e komo ai.", "password": "ʻŌlelo huna", "login": "Komo", "statement": "ʻŌlelo moʻokāki", "date": "Lā", "account_holder": "Mea nona ka moʻokāki", "currency": "Kālā", "tx_history": "Moʻolelo o nā hana", "description": "Wehewehe", "ending_balance": "Koea hope", "stmt_footer": "He ʻōlelo i hana ʻia e ka lolouila kēia a ʻaʻole pono e pūlima.", "email_notif": "Nā leka uila", "dark_mode": "ʻAno pouli", "biometrics": "Face ID / Biometrics", "active": "Ola", "opened": "Wehe ʻia", "completed": "Hoʻopau ʻia", "pending": "Ke kali nei", "unopened": "ʻAʻole i wehe ʻia", "transfer_to": "Hoʻoili iā", "just_now": "I kēia manawa", "success": "Holomua", "verifying": "ke hōʻoia nei…", "premium": "Premium", "today": "I kēia lā", "yesterday": "I nehinei", "from": "Mai", "to": "Iā"},
"lo": {"dashboard": "ແດຊະບອດ", "history": "ປະຫວັດ", "transfer": "ໂອນ", "cards": "ຕູ້ນິຣະໄພ", "settings": "ການຕັ້ງຄ່າ", "total_balance": "ຍອດເງິນທັງໝົດ", "account_number": "ເລກບັນຊີ", "send_money": "ສົ່ງເງິນ", "recent_tx": "ທຸລະກຳຫຼ້າສຸດ", "see_all": "ເບິ່ງທັງໝົດ", "no_tx": "ຍັງບໍ່ມີທຸລະກຳ.", "account_settings": "ການຕັ້ງຄ່າບັນຊີ", "log_out": "ອອກຈາກລະບົບ", "card_status": "ສະຖານະບັດ", "freeze_card": "ລັອກບັດ", "view_cvv": "ເບິ່ງ CVV", "download_stmt": "ດາວໂຫລດລາຍງານ", "get_pdf": "ຮັບເອກະສານ PDF", "download": "ດາວໂຫລດ", "bank_name": "ຊື່ທະນາຄານ", "account_no": "ເລກບັນຊີ", "amount": "ຈຳນວນ", "withdraw_code": "ລະຫັດຖອນ", "confirm_transfer": "ຢືນຢັນການໂອນ", "funds_sent_to": "ເງິນຈະຖືກສົ່ງໄປບັນຊີທະນາຄານທີ່ທ່ານປ້ອນລຸ່ມນີ້.", "transfer_processed": "ການໂອນສຳເລັດ", "funds_sent_msg": "ເງິນຂອງທ່ານຖືກສົ່ງແລ້ວ. ອາດຈະໃຊ້ເວລາສອງສາມນາທີ.", "processing": "ກຳລັງດຳເນີນການ", "processing_msg": "ການໂອນຂອງທ່ານກຳລັງຖືກດຳເນີນການຍ້ອນຄວາມປອດໄພ.", "do_not_close": "ກະລຸນາຢ່າປິດໜ້ານີ້.", "welcome_back": "ຍິນດີຕ້ອນຮັບກັບຄືນ", "enter_password": "ປ້ອນລະຫັດຜ່ານເພື່ອເຂົ້າເຖິງບັນຊີ.", "password": "ລະຫັດຜ່ານ", "login": "ເຂົ້າສູ່ລະບົບ", "statement": "ລາຍງານບັນຊີ", "date": "ວັນທີ", "account_holder": "ເຈົ້າຂອງບັນຊີ", "currency": "ສະກຸນເງິນ", "tx_history": "ປະຫວັດທຸລະກຳ", "description": "ລາຍລະອຽດ", "ending_balance": "ຍອດເງິນສຸດທ້າຍ", "stmt_footer": "ນີ້ແມ່ນລາຍງານທີ່ສ້າງໂດຍຄອມພິວເຕີ ແລະ ບໍ່ຕ້ອງການລາຍເຊັນ.", "email_notif": "ການແຈ້ງເຕືອນທາງອີເມວ", "dark_mode": "ໂໝດມືດ", "biometrics": "Face ID / ຊີວະມິຕິ", "active": "ເຄື່ອນໄຫວ", "opened": "ເປີດແລ້ວ", "completed": "ສຳເລັດ", "pending": "ລໍຖ້າ", "unopened": "ບໍ່ໄດ້ເປີດ", "transfer_to": "ໂອນໄປຫາ", "just_now": "ຕອນນີ້", "success": "ສຳເລັດ", "verifying": "ກຳລັງກວດສອບ…", "premium": "ພຣີມຽມ", "today": "ມື້ນີ້", "yesterday": "ມື້ວານ", "from": "ຈາກ", "to": "ຫາ"},
    "th": {"dashboard": "แดชบอร์ด", "history": "ประวัติ", "transfer": "โอนเงิน", "cards": "ตู้นิรภัย", "settings": "การตั้งค่า", "total_balance": "ยอดคงเหลือทั้งหมด", "account_number": "หมายเลขบัญชี", "send_money": "ส่งเงิน", "recent_tx": "ธุรกรรมล่าสุด", "see_all": "ดูทั้งหมด", "no_tx": "ยังไม่มีธุรกรรม", "account_settings": "การตั้งค่าบัญชี", "log_out": "ออกจากระบบ", "card_status": "สถานะบัตร", "freeze_card": "อายัดบัตร", "view_cvv": "ดู CVV", "download_stmt": "ดาวน์โหลดใบแจ้งยอด", "get_pdf": "รับบันทึก PDF ของคุณ", "download": "ดาวน์โหลด", "bank_name": "ชื่อธนาคาร", "account_no": "หมายเลขบัญชี", "amount": "จำนวน", "withdraw_code": "รหัสถอนเงิน", "confirm_transfer": "ยืนยันการโอน", "funds_sent_to": "เงินจะถูกส่งไปยังบัญชีธนาคารที่คุณระบุด้านล่าง", "transfer_processed": "ดำเนินการโอนแล้ว", "funds_sent_msg": "เงินของคุณถูกส่งแล้ว อาจใช้เวลาสักครู่", "processing": "กำลังดำเนินการ", "processing_msg": "การโอนของคุณกำลังดำเนินการด้วยเหตุผลด้านความปลอดภัย", "do_not_close": "โปรดอย่าปิดหน้านี้", "welcome_back": "ยินดีต้อนรับกลับ", "enter_password": "ป้อนรหัสผ่านเพื่อเข้าถึงบัญชี", "password": "รหัสผ่าน", "login": "เข้าสู่ระบบ", "statement": "ใบแจ้งยอดบัญชี", "date": "วันที่", "account_holder": "เจ้าของบัญชี", "currency": "สกุลเงิน", "tx_history": "ประวัติธุรกรรม", "description": "คำอธิบาย", "ending_balance": "ยอดคงเหลือสุดท้าย", "stmt_footer": "นี่คือใบแจ้งยอดที่สร้างโดยคอมพิวเตอร์และไม่จำเป็นต้องมีลายเซ็น", "email_notif": "การแจ้งเตือนทางอีเมล", "dark_mode": "โหมดมืด", "biometrics": "Face ID / ไบโอเมตริกซ์", "active": "ใช้งานอยู่", "opened": "เปิดแล้ว", "completed": "เสร็จสิ้น", "pending": "รอดำเนินการ", "unopened": "ยังไม่เปิด", "transfer_to": "โอนไปยัง", "just_now": "เมื่อสักครู่", "success": "สำเร็จ", "verifying": "กำลังตรวจสอบ…", "premium": "พรีเมียม", "today": "วันนี้", "yesterday": "เมื่อวาน", "from": "จาก", "to": "ถึง"},
"hy": {"dashboard": "Վահանակ", "history": "Պատմություն", "transfer": "Փոխանցում", "cards": "Պահոց", "settings": "Կարգավորումներ", "total_balance": "Ընդհանուր Մնացորդ", "account_number": "Հաշվի Համար", "send_money": "Ուղարկել Գումար", "recent_tx": "Վերջին Գործարքներ", "see_all": "Տեսնել բոլորը", "no_tx": "Դեռ գործարքներ չկան:", "account_settings": "Հաշվի Կարգավորումներ", "log_out": "Դուրս գալ", "card_status": "Քարտի Կարգավիճակ", "freeze_card": "Սառեցնել Քարտը", "view_cvv": "Դիտել CVV", "download_stmt": "Ներբեռնել Քաղվածքը", "get_pdf": "Ստանալ ձեր PDF գրառումը", "download": "Ներբեռնել", "bank_name": "Բանկի անվանումը", "account_no": "Հաշվի համար", "amount": "Գումարը", "withdraw_code": "Դուրսբերման կոդ", "confirm_transfer": "Հաստատել Փոխանցումը", "funds_sent_to": "Միջոցները կուղարկվեն ստորև նշված ձեր բանկային հաշվին:", "transfer_processed": "Փոխանցումը Մշակված է", "funds_sent_msg": "Ձեր միջոցները ուղարկվել են: Դա կարող է տևել մի քանի րոպե:", "processing": "Մշակում", "processing_msg": "Ձեր փոխանցումը մշակվում է անվտանգության նկատառումներով:", "do_not_close": "Խնդրում ենք չփակել այս էջը:", "welcome_back": "Բարի վերադարձ", "enter_password": "Մուտքագրեք ձեր գաղտնաբառը մուտք գործելու համար:", "password": "Գաղտնաբառ", "login": "Մուտք", "statement": "Հաշվի Քաղվածք", "date": "Ամսաթիվ", "account_holder": "Հաշվի Սեփականատեր", "currency": "Արժույթ", "tx_history": "Գործարքների Պատմություն", "description": "Նկարագրություն", "ending_balance": "Վերջնական Մնացորդ", "stmt_footer": "Սա համակարգչային քաղվածք է և ստորագրություն չի պահանջում:", "email_notif": "Էլ. փոստի Ծանուցումներ", "dark_mode": "Մուգ Ռեժիմ", "biometrics": "Face ID / Կենսաչափություն", "active": "Ակտիվ", "opened": "Բացված", "completed": "Ավարտված", "pending": "Սպասման մեջ", "unopened": "Չբացված", "transfer_to": "Փոխանցում դեպի", "just_now": "Հենց հիմա", "success": "Հաջողություն", "verifying": "ստուգում…", "premium": "Պրեմիում", "today": "Այսօր", "yesterday": "Երեկ", "from": "Ից", "to": "Դեպի"},
    "km": {"dashboard": "ផ្ទាំងគ្រប់គ្រង", "history": "ប្រវត្តិ", "transfer": "ផ្ទេរប្រាក់", "cards": "ទូដាក់ប្រាក់", "settings": "ការកំណត់", "total_balance": "សមតុល្យសរុប", "account_number": "លេខគណនី", "send_money": "ផ្ញើប្រាក់", "recent_tx": "ប្រតិបត្តិការថ្មីៗ", "see_all": "មើលទាំងអស់", "no_tx": "មិនទាន់មានប្រតិបត្តិការនៅឡើយទេ។", "account_settings": "ការកំណត់គណនី", "log_out": "ចាកចេញ", "card_status": "ស្ថានភាពកាត", "freeze_card": "បង្កកកាត", "view_cvv": "មើល CVV", "download_stmt": "ទាញយករបាយការណ៍", "get_pdf": "ទទួលបានកំណត់ត្រា PDF របស់អ្នក", "download": "ទាញយក", "bank_name": "ឈ្មោះធនាគារ", "account_no": "លេខគណនី", "amount": "ចំនួនទឹកប្រាក់", "withdraw_code": "លេខកូដដកប្រាក់", "confirm_transfer": "បញ្ជាក់ការផ្ទេរប្រាក់", "funds_sent_to": "ប្រាក់នឹងត្រូវបានផ្ញើទៅគណនីធនាគារដែលអ្នកបញ្ចូលខាងក្រោម។", "transfer_processed": "ការផ្ទេរប្រាក់ត្រូវបានដំណើរការ", "funds_sent_msg": "ប្រាក់របស់អ្នកត្រូវបានផ្ញើ។ វាអាចចំណាយពេលពីរបីនាទី។", "processing": "កំពុងដំណើរការ", "processing_msg": "ការផ្ទេរប្រាក់របស់អ្នកកំពុងត្រូវបានដំណើរការដោយសារហេតុផលសន្តិសុខ។", "do_not_close": "សូមកុំបិទទំព័រនេះ។", "welcome_back": "សូមស្វាគមន៍ការត្រឡប់មកវិញ", "enter_password": "បញ្ចូលពាក្យសម្ងាត់របស់អ្នកដើម្បីចូលប្រើ។", "password": "ពាក្យសម្ងាត់", "login": "ចូល", "statement": "របាយការណ៍គណនី", "date": "កាលបរិច្ឆេទ", "account_holder": "ម្ចាស់គណនី", "currency": "រូបិយប័ណ្ណ", "tx_history": "ប្រវត្តិប្រតិបត្តិការ", "description": "ការពិពណ៌នា", "ending_balance": "សមតុល្យចុងក្រោយ", "stmt_footer": "នេះគឺជារបាយការណ៍ដែលបង្កើតដោយកុំព្យូទ័រ ហើយមិនត្រូវការហត្ថលេខាទេ។", "email_notif": "ការជូនដំណឹងតាមអ៊ីមែល", "dark_mode": "របៀបងងឹត", "biometrics": "Face ID / ជីវមាត្រ", "active": "សកម្ម", "opened": "បានបើក", "completed": "បានបញ្ចប់", "pending": "កំពុងរង់ចាំ", "unopened": "មិនបានបើក", "transfer_to": "ផ្ទេរទៅ", "just_now": "ទើបតែឥឡូវ", "success": "ជោគជ័យ", "verifying": "កំពុងផ្ទៀងផ្ទាត់…", "premium": "ពិសេស", "today": "ថ្ងៃនេះ", "yesterday": "ម្សិលមិញ", "from": "ពី", "to": "ទៅ"},
    "rw": {"dashboard": "Imbonerahamwe", "history": "Amateka", "transfer": "Kohereza", "cards": "Ububiko", "settings": "Igenamiterere", "total_balance": "Amafaranga Yose", "account_number": "Nomero ya Konti", "send_money": "Ohereza Amafaranga", "recent_tx": "Ibikorwa Biheruka", "see_all": "Reba byose", "no_tx": "Nta bikorwa birabaho.", "account_settings": "Igenamiterere rya Konti", "log_out": "Sohoka", "card_status": "Imiterere y'Ikarita", "freeze_card": "Hagarika Ikarita", "view_cvv": "Reba CVV", "download_stmt": "Kuramo Itangazo", "get_pdf": "Bonera inyandiko yawe ya PDF", "download": "Kuramo", "bank_name": "Izina rya Banki", "account_no": "Nomero ya Konti", "amount": "Umubare", "withdraw_code": "Kode yo Kubikuza", "confirm_transfer": "Emeza Kohereza", "funds_sent_to": "Amafaranga azajyanwa kuri konti ya banki winjiza hepfo.", "transfer_processed": "Kohereza Byakozwe", "funds_sent_msg": "Amafaranga yawe yoherejwe. Bishobora gufata iminota mike.", "processing": "Biratunganywa", "processing_msg": "Kohereza kwawe kuratunganywa kubera umutekano.", "do_not_close": "Nyamuneka ntufunge iyi paji.", "welcome_back": "Murakaza neza", "enter_password": "Injiza ijambo ry'ibanga kugira ngo winjire.", "password": "Ijambo ry'ibanga", "login": "Injira", "statement": "Itangazo rya Konti", "date": "Itariki", "account_holder": "Nyir'ikonti", "currency": "Ifaranga", "tx_history": "Amateka y'Ibikorwa", "description": "Ibisobanuro", "ending_balance": "Amafaranga Asigaye", "stmt_footer": "Iri ni itangazo ryakozwe na mudasobwa kandi ntirisaba umukono.", "email_notif": "Imenyesha rya Imeyili", "dark_mode": "Uburyo Bwijimye", "biometrics": "Face ID / Biometrics", "active": "Birakora", "opened": "Byafunguwe", "completed": "Byarangiye", "pending": "Bitegereje", "unopened": "Ntibyafunguwe", "transfer_to": "Ohereza kuri", "just_now": "Ubu nyine", "success": "Intsinzi", "verifying": "biragenzurwa…", "premium": "Premium", "today": "Uyu munsi", "yesterday": "Ejo hashize", "from": "Kuva kuri", "to": "Kuri"},
    "ku": {"dashboard": "Panêl", "history": "Dîrok", "transfer": "Veguheztin", "cards": "Qasa", "settings": "Mîheng", "total_balance": "Bilansa Giştî", "account_number": "Hejmara Hesabê", "send_money": "Pere Bixe", "recent_tx": "Danûstandinên Dawî", "see_all": "Hemûyan bibîne", "no_tx": "Hîn danûstandin tune.", "account_settings": "Mîhengên Hesabê", "log_out": "Derkeve", "card_status": "Rewşa Kartê", "freeze_card": "Kartê Qerisîne", "view_cvv": "CVV Binêre", "download_stmt": "Daxuyaniyê Dakêşîne", "get_pdf": "Tomara xwe ya PDF bistîne", "download": "Daxîne", "bank_name": "Navê bankê", "account_no": "Hejmara hesabê", "amount": "Biha", "withdraw_code": "Koda kişandinê", "confirm_transfer": "Veguheztinê Piştrast Bike", "funds_sent_to": "Pere dê ji hesabê bankê yê ku hûn li jêr binivîsin re were şandin.", "transfer_processed": "Veguheztin Hate Pêvajokirin", "funds_sent_msg": "Pereyên we hatin şandin. Dibe ku çend hûrdeman bigire.", "processing": "Pêvajokirin", "processing_msg": "Veguheztina we ji ber sedemên ewlehiyê tê pêvajokirin.", "do_not_close": "Ji kerema xwe vê rûpelê negire.", "welcome_back": "Bi xêr hatî", "enter_password": "Ji bo gihîştinê şîfreya xwe binivîse.", "password": "Şîfre", "login": "Têkeve", "statement": "Daxuyaniya Hesabê", "date": "Dîrok", "account_holder": "Xwediyê Hesabê", "currency": "Dirav", "tx_history": "Dîroka Danûstandinan", "description": "Ravekirin", "ending_balance": "Bilansa Dawî", "stmt_footer": "Ev daxuyaniyek ji hêla komputerê ve hatî çêkirin e û îmzeyê naxwaze.", "email_notif": "Agahdariyên E-nameyê", "dark_mode": "Moda Tarî", "biometrics": "Face ID / Biometrîk", "active": "Çalak", "opened": "Vekirî", "completed": "Qedandî", "pending": "Li benda", "unopened": "Venehatî", "transfer_to": "Veguheztin bo", "just_now": "Niha", "success": "Serkeftin", "verifying": "tê verastkirin…", "premium": "Premium", "today": "Îro", "yesterday": "Duh", "from": "Ji", "to": "Bo"},
    "ky": {"dashboard": "Башкаруу панели", "history": "Тарых", "transfer": "Которуу", "cards": "Кампа", "settings": "Жөндөөлөр", "total_balance": "Жалпы Баланс", "account_number": "Эсеп Номери", "send_money": "Акча Жөнөтүү", "recent_tx": "Акыркы Транзакциялар", "see_all": "Баарын көрүү", "no_tx": "Азырынча транзакциялар жок.", "account_settings": "Эсеп Жөндөөлөрү", "log_out": "Чыгуу", "card_status": "Картанын Абалы", "freeze_card": "Картаны Тоңдуруу", "view_cvv": "CVV көрүү", "download_stmt": "Ырастоону Жүктөө", "get_pdf": "PDF жазууңузду алыңыз", "download": "Жүктөө", "bank_name": "Банктын аталышы", "account_no": "Эсеп номери", "amount": "Сумма", "withdraw_code": "Алуу коддору", "confirm_transfer": "Которууну Ырастоо", "funds_sent_to": "Каражат төмөндө көрсөтүлгөн банк эсебиңизге жөнөтүлөт.", "transfer_processed": "Которуу Иштетилди", "funds_sent_msg": "Каражаттарыңыз жөнөтүлдү. Бир нече мүнөт талап кылынышы мүмкүн.", "processing": "Иштетүү", "processing_msg": "Которууңуз коопсуздук үчүн иштетилүүдө.", "do_not_close": "Сураныч, бул баракчаны жаппаңыз.", "welcome_back": "Кайра кош келиңиз", "enter_password": "Кирүү үчүн сырсөзүңүздү киргизиңиз.", "password": "Сырсөз", "login": "Кирүү", "statement": "Эсеп Ырастоосу", "date": "Күнү", "account_holder": "Эсеп Ээси", "currency": "Валюта", "tx_history": "Транзакциялардын Тарыхы", "description": "Сүрөттөмө", "ending_balance": "Акыркы Баланс", "stmt_footer": "Бул компьютер тарабынан түзүлгөн ырастоо жана кол тамга талап кылбайт.", "email_notif": "Электрондук Билдирүүлөр", "dark_mode": "Караңгы Режим", "biometrics": "Face ID / Биометрия", "active": "Активдүү", "opened": "Ачылды", "completed": "Аяктады", "pending": "Күтүүдө", "unopened": "Ачылбаган", "transfer_to": "Которуу", "just_now": "Азыр", "success": "Ийгилик", "verifying": "текшерүү…", "premium": "Премиум", "today": "Бүгүн", "yesterday": "Кечээ", "from": "Кимден", "to": "Кимге"},
    "la": {"dashboard": "Dashboard", "history": "Historia", "transfer": "Translatio", "cards": "Arca", "settings": "Optiones", "total_balance": "Summa Totalis", "account_number": "Numerus Rationis", "send_money": "Mitte Pecuniam", "recent_tx": "Recentissima Transactiones", "see_all": "Videre omnia", "no_tx": "Nullae transactiones adhuc.", "account_settings": "Optiones Rationis", "log_out": "Exire", "card_status": "Status Chartae", "freeze_card": "Congelare Chartam", "view_cvv": "Videre CVV", "download_stmt": "Download Statement", "get_pdf": "Accipere PDF record", "download": "Download", "bank_name": "Nomen Bank", "account_no": "Numerus Rationis", "amount": "Moles", "withdraw_code": "Code detrahere", "confirm_transfer": "Confirmare Translationem", "funds_sent_to": "Pecunia mittetur ad rationem argentariam quam infra inscribis.", "transfer_processed": "Translatio Processit", "funds_sent_msg": "Pecunia tua missa est. Paucis momentis capere potest.", "processing": "Processus", "processing_msg": "Translatio tua propter securitatem processit.", "do_not_close": "Quaeso noli claudere hanc paginam.", "welcome_back": "Salve reversus", "enter_password": "Intra tesseram tuam ut accedas.", "password": "Tessera", "login": "Intrare", "statement": "Ratio Statement", "date": "Dies", "account_holder": "Dominus Rationis", "currency": "Moneta", "tx_history": "Historia Transactionum", "description": "Descriptio", "ending_balance": "Finis Balance", "stmt_footer": "Hoc est computatorium generatum constitutionis et subscriptione non eget.", "email_notif": "Email Notificationes", "dark_mode": "Modus Tenebris", "biometrics": "Face ID / Biometrics", "active": "Activus", "opened": "Apertus", "completed": "Completus", "pending": "Pendens", "unopened": "Non apertus", "transfer_to": "Transferre ad", "just_now": "Modo nunc", "success": "Successus", "verifying": "comprobans…", "premium": "Premium", "today": "Hodie", "yesterday": "Heri", "from": "Ex", "to": "Ad"},
    "lv": {"dashboard": "Informācijas panelis", "history": "Vēsture", "transfer": "Pārskaitījums", "cards": "Seifs", "settings": "Iestatījumi", "total_balance": "Kopējais Atlikums", "account_number": "Konta Numurs", "send_money": "Sūtīt Naudu", "recent_tx": "Nesenie Darījumi", "see_all": "Skatīt visu", "no_tx": "Vēl nav darījumu.", "account_settings": "Konta Iestatījumi", "log_out": "Iziet", "card_status": "Kartes Statuss", "freeze_card": "Iesaldēt Karti", "view_cvv": "Skatīt CVV", "download_stmt": "Lejupielādēt Izrakstu", "get_pdf": "Iegūt savu PDF ierakstu", "download": "Lejupielādēt", "bank_name": "Bankas nosaukums", "account_no": "Konta numurs", "amount": "Summa", "withdraw_code": "Izņemšanas kods", "confirm_transfer": "Apstiprināt Pārskaitījumu", "funds_sent_to": "Līdzekļi tiks nosūtīti uz zemāk ievadīto bankas kontu.", "transfer_processed": "Pārskaitījums Apstrādāts", "funds_sent_msg": "Jūsu līdzekļi ir nosūtīti. Tas var aizņemt dažas minūtes.", "processing": "Apstrāde", "processing_msg": "Jūsu pārskaitījums tiek apstrādāts drošības apsvērumu dēļ.", "do_not_close": "Lūdzu, neaizveriet šo lapu.", "welcome_back": "Laipni lūdzam atpakaļ", "enter_password": "Ievadiet savu paroli, lai piekļūtu.", "password": "Parole", "login": "Pieteikties", "statement": "Konta Izraksts", "date": "Datums", "account_holder": "Konta Turētājs", "currency": "Valūta", "tx_history": "Darījumu Vēsture", "description": "Apraksts", "ending_balance": "Beigu Atlikums", "stmt_footer": "Šis ir datorizēts izraksts, un tam nav nepieciešams paraksts.", "email_notif": "E-pasta Paziņojumi", "dark_mode": "Tumšais Režīms", "biometrics": "Face ID / Biometrija", "active": "Aktīvs", "opened": "Atvērts", "completed": "Pabeigts", "pending": "Gaida", "unopened": "Neatvērts", "transfer_to": "Pārskaitījums uz", "just_now": "Tikko", "success": "Veiksme", "verifying": "pārbaude…", "premium": "Premium", "today": "Šodien", "yesterday": "Vakar", "from": "No", "to": "Uz"},
    "lt": {"dashboard": "Pagrindinis", "history": "Istorija", "transfer": "Pavedimas", "cards": "Seifas", "settings": "Nustatymai", "total_balance": "Bendras Likutis", "account_number": "Sąskaitos Numeris", "send_money": "Siųsti Pinigus", "recent_tx": "Naujausios Operacijos", "see_all": "Rodyti viską", "no_tx": "Operacijų dar nėra.", "account_settings": "Sąskaitos Nustatymai", "log_out": "Atsijungti", "card_status": "Kortelės Būsena", "freeze_card": "Užšaldyti Kortelę", "view_cvv": "Rodyti CVV", "download_stmt": "Atsisiųsti Išrašą", "get_pdf": "Gauti PDF įrašą", "download": "Atsisiųsti", "bank_name": "Banko pavadinimas", "account_no": "Sąskaitos numeris", "amount": "Suma", "withdraw_code": "Išėmimo kodas", "confirm_transfer": "Patvirtinti Pavedimą", "funds_sent_to": "Lėšos bus išsiųstos į žemiau nurodytą banko sąskaitą.", "transfer_processed": "Pavedimas Apdorotas", "funds_sent_msg": "Jūsų lėšos išsiųstos. Tai gali užtrukti kelias minutes.", "processing": "Apdorojama", "processing_msg": "Jūsų pavedimas apdorojamas dėl saugumo priežasčių.", "do_not_close": "Prašome neuždaryti šio puslapio.", "welcome_back": "Sveiki sugrįžę", "enter_password": "Įveskite slaptažodį, kad pasiektumėte paskyrą.", "password": "Slaptažodis", "login": "Prisijungti", "statement": "Sąskaitos Išrašas", "date": "Data", "account_holder": "Sąskaitos Savininkas", "currency": "Valiuta", "tx_history": "Operacijų Istorija", "description": "Aprašymas", "ending_balance": "Galutinis Likutis", "stmt_footer": "Tai kompiuterio sugeneruotas išrašas, kuriam nereikia parašo.", "email_notif": "El. Pašto Pranešimai", "dark_mode": "Tamsusis Režimas", "biometrics": "Face ID / Biometrija", "active": "Aktyvus", "opened": "Atidaryta", "completed": "Užbaigta", "pending": "Laukiama", "unopened": "Neatidaryta", "transfer_to": "Pavedimas į", "just_now": "Ką tik", "success": "Sėkmė", "verifying": "tikrinama…", "premium": "Premium", "today": "Šiandien", "yesterday": "Vakar", "from": "Nuo", "to": "Kam"},
    "lb": {"dashboard": "Dashboard", "history": "Geschicht", "transfer": "Iwwerweisung", "cards": "Koffers", "settings": "Astellungen", "total_balance": "Gesamtsaldo", "account_number": "Kontonummer", "send_money": "Geld Schécken", "recent_tx": "Rezent Transaktiounen", "see_all": "Alles gesinn", "no_tx": "Nach keng Transaktiounen.", "account_settings": "Konto Astellungen", "log_out": "Ausloggen", "card_status": "Kaart Status", "freeze_card": "Kaart Afréieren", "view_cvv": "CVV Gesinn", "download_stmt": "Auszuch Erofueren", "get_pdf": "Kréien Är PDF Opzeechnung", "download": "Erofueren", "bank_name": "Bank Numm", "account_no": "Kontonummer", "amount": "Betrag", "withdraw_code": "Ofhuebungs Code", "confirm_transfer": "Iwwerweisung Bestätegen", "funds_sent_to": "D'Suen ginn op de Bankkonto iwwerwisen, deen Dir hei drënner agitt.", "transfer_processed": "Iwwerweisung Veraarbecht", "funds_sent_msg": "Är Suen goufen geschéckt. Et kann e puer Minutten daueren.", "processing": "Aarbecht", "processing_msg": "Är Iwwerweisung gëtt aus Sécherheetsgrënn veraarbecht.", "do_not_close": "Weglaang dës Säit net zou.", "welcome_back": "Wëllkomm zréck", "enter_password": "Gitt Äert Passwuert an fir Zougang ze kréien.", "password": "Passwuert", "login": "Aloggen", "statement": "Konto Auszuch", "date": "Datum", "account_holder": "Konto Besëtzer", "currency": "Währung", "tx_history": "Transaktiouns Geschicht", "description": "Beschreiwung", "ending_balance": "Endsaldo", "stmt_footer": "Dëst ass e computer-generéierten Auszuch an erfuerdert keng Ënnerschrëft.", "email_notif": "E-Mail Notifikatiounen", "dark_mode": "Däischtere Modus", "biometrics": "Face ID / Biometrie", "active": "Aktiv", "opened": "Op", "completed": "Fäerdeg", "pending": "Amgaang", "unopened": "Net op", "transfer_to": "Iwwerweisung op", "just_now": "Just elo", "success": "Erfolleg", "verifying": "iwwerpréiwen…", "premium": "Premium", "today": "Haut", "yesterday": "Gëschter", "from": "Vun", "to": "Un"},
    "mk": {"dashboard": "Табла", "history": "Историја", "transfer": "Трансфер", "cards": "Сеф", "settings": "Поставки", "total_balance": "Вкупно Салдо", "account_number": "Број на Сметка", "send_money": "Испрати Пари", "recent_tx": "Неодамнешни Трансакции", "see_all": "Види ги сите", "no_tx": "Сè уште нема трансакции.", "account_settings": "Поставки за Сметка", "log_out": "Одјави се", "card_status": "Статус на Картичка", "freeze_card": "Замрзни Картичка", "view_cvv": "Види CVV", "download_stmt": "Преземи Извод", "get_pdf": "Земи го твојот PDF запис", "download": "Преземи", "bank_name": "Име на банка", "account_no": "Број на сметка", "amount": "Сума", "withdraw_code": "Код за подигнување", "confirm_transfer": "Потврди Трансфер", "funds_sent_to": "Средствата ќе бидат испратени на банкарската сметка што ќе ја внесете подолу.", "transfer_processed": "Трансферот е Обработен", "funds_sent_msg": "Вашите средства се испратени. Може да потрае неколку минути.", "processing": "Обработка", "processing_msg": "Вашиот трансфер се обработува од безбедносни причини.", "do_not_close": "Ве молиме не затворајте ја оваа страница.", "welcome_back": "Добредојдовте назад", "enter_password": "Внесете ја вашата лозинка за пристап.", "password": "Лозинка", "login": "Најави се", "statement": "Извод од Сметка", "date": "Датум", "account_holder": "Сопственик на Сметка", "currency": "Валута", "tx_history": "Историја на Трансакции", "description": "Опис", "ending_balance": "Конечно Салдо", "stmt_footer": "Ова е компјутерски генериран извод и не бара потпис.", "email_notif": "Известувања по Е-пошта", "dark_mode": "Темен Режим", "biometrics": "Face ID / Биометрија", "active": "Активен", "opened": "Отворен", "completed": "Завршен", "pending": "Во чекање", "unopened": "Неотворен", "transfer_to": "Трансфер до", "just_now": "Само што", "success": "Успех", "verifying": "проверка…", "premium": "Премиум", "today": "Денес", "yesterday": "Вчера", "from": "Од", "to": "До"},
    "mg": {"dashboard": "Tabila", "history": "Tantara", "transfer": "Famindrana", "cards": "Vault", "settings": "Fikirana", "total_balance": "Ny vola rehetra", "account_number": "Laharana kaonty", "send_money": "Handefa vola", "recent_tx": "Tafita farany", "see_all": "Hijery daholo", "no_tx": "Tsy mbola misy fifanakalozana.", "account_settings": "Fikirana kaonty", "log_out": "Hivoaka", "card_status": "Toetry ny karatra", "freeze_card": "Mamono ny karatra", "view_cvv": "Hijery CVV", "download_stmt": "Hampidina ny fanambarana", "get_pdf": "Alao ny rakitra PDF-nao", "download": "Hampidina", "bank_name": "Anaran'ny banky", "account_no": "Laharana kaonty", "amount": "Vola", "withdraw_code": "Kaody fanalana", "confirm_transfer": "Hamafiso ny famindrana", "funds_sent_to": "Halefa any amin'ny kaonty banky ampidirinao etsy ambany ny vola.", "transfer_processed": "Vita ny famindrana", "funds_sent_msg": "Lasa ny volanao. Mety haharitra minitra vitsy.", "processing": "Eo am-panaovana", "processing_msg": "Eo am-panaovana ny famindrana noho ny fiarovana.", "do_not_close": "Aza mikatona ity pejy ity.", "welcome_back": "Tongasoa indray", "enter_password": "Ampidiro ny tenimiafinao hidirana.", "password": "Tenimiafina", "login": "Hiditra", "statement": "Fanambarana kaonty", "date": "Daty", "account_holder": "Tompon'ny kaonty", "currency": "Vola", "tx_history": "Tantaran'ny fifanakalozana", "description": "Fanazavana", "ending_balance": "Vola sisa", "stmt_footer": "Fanambarana noforonin'ny solosaina ity ary tsy mila sonia.", "email_notif": "Fampandrenesana amin'ny mailaka", "dark_mode": "Maizina", "biometrics": "Face ID / Biometrics", "active": "Mavitrika", "opened": "Nosokafana", "completed": "Vita", "pending": "Miandry", "unopened": "Tsy nosokafana", "transfer_to": "Famindrana ho an'ny", "just_now": "Izao", "success": "Fahombiazana", "verifying": "manamarina…", "premium": "Premium", "today": "Androany", "yesterday": "Omaly", "from": "Avy amin'ny", "to": "Ho an'ny"},
    "ms": {"dashboard": "Papan Pemuka", "history": "Sejarah", "transfer": "Pemindahan", "cards": "Peti Besi", "settings": "Tetapan", "total_balance": "Jumlah Baki", "account_number": "Nombor Akaun", "send_money": "Hantar Wang", "recent_tx": "Transaksi Terkini", "see_all": "Lihat semua", "no_tx": "Tiada transaksi lagi.", "account_settings": "Tetapan Akaun", "log_out": "Log Keluar", "card_status": "Status Kad", "freeze_card": "Bekukan Kad", "view_cvv": "Lihat CVV", "download_stmt": "Muat Turun Penyata", "get_pdf": "Dapatkan rekod PDF anda", "download": "Muat Turun", "bank_name": "Nama bank", "account_no": "Nombor akaun", "amount": "Jumlah", "withdraw_code": "Kod pengeluaran", "confirm_transfer": "Sahkan Pemindahan", "funds_sent_to": "Dana akan dihantar ke akaun bank yang anda masukkan di bawah.", "transfer_processed": "Pemindahan Diproses", "funds_sent_msg": "Dana anda telah dihantar. Ia mungkin mengambil masa beberapa minit.", "processing": "Memproses", "processing_msg": "Pemindahan anda sedang diproses atas sebab keselamatan.", "do_not_close": "Sila jangan tutup halaman ini.", "welcome_back": "Selamat kembali", "enter_password": "Masukkan kata laluan anda untuk akses.", "password": "Kata Laluan", "login": "Log Masuk", "statement": "Penyata Akaun", "date": "Tarikh", "account_holder": "Pemegang Akaun", "currency": "Mata Wang", "tx_history": "Sejarah Transaksi", "description": "Penerangan", "ending_balance": "Baki Akhir", "stmt_footer": "Ini adalah penyata yang dijana komputer dan tidak memerlukan tandatangan.", "email_notif": "Pemberitahuan E-mel", "dark_mode": "Mod Gelap", "biometrics": "Face ID / Biometrik", "active": "Aktif", "opened": "Dibuka", "completed": "Selesai", "pending": "Menunggu", "unopened": "Belum dibuka", "transfer_to": "Pemindahan ke", "just_now": "Baru sahaja", "success": "Berjaya", "verifying": "mengesahkan…", "premium": "Premium", "today": "Hari ini", "yesterday": "Semalam", "from": "Dari", "to": "Kepada"},
    "ml": {"dashboard": "ഡാഷ്ബോർഡ്", "history": "ചരിത്രം", "transfer": "കൈമാറ്റം", "cards": "വോൾട്ട്", "settings": "ക്രമീകരണങ്ങൾ", "total_balance": "മൊത്തം ബാലൻസ്", "account_number": "അക്കൗണ്ട് നമ്പർ", "send_money": "പണം അയക്കുക", "recent_tx": "സമീപകാല ഇടപാടുകൾ", "see_all": "എല്ലാം കാണുക", "no_tx": "ഇതുവരെ ഇടപാടുകളില്ല.", "account_settings": "അക്കൗണ്ട് ക്രമീകരണങ്ങൾ", "log_out": "ലോഗ് ഔട്ട്", "card_status": "കാർഡ് നില", "freeze_card": "കാർഡ് മരവിപ്പിക്കുക", "view_cvv": "CVV കാണുക", "download_stmt": "സ്റ്റേറ്റ്മെന്റ് ഡൗൺലോഡ് ചെയ്യുക", "get_pdf": "നിങ്ങളുടെ PDF രേഖ നേടുക", "download": "ഡൗൺലോഡ്", "bank_name": "ബാങ്കിന്റെ പേര്", "account_no": "അക്കൗണ്ട് നമ്പർ", "amount": "തുക", "withdraw_code": "പിൻവലിക്കൽ കോഡ്", "confirm_transfer": "കൈമാറ്റം സ്ഥിരീകരിക്കുക", "funds_sent_to": "നിങ്ങൾ ചുവടെ നൽകുന്ന ബാങ്ക് അക്കൗണ്ടിലേക്ക് ഫണ്ട് അയക്കും.", "transfer_processed": "കൈമാറ്റം പ്രോസസ്സ് ചെയ്തു", "funds_sent_msg": "നിങ്ങളുടെ ഫണ്ട് അയച്ചു. കുറച്ച് മിനിറ്റുകൾ എടുത്തേക്കാം.", "processing": "പ്രോസസ്സിംഗ്", "processing_msg": "സുരക്ഷാ കാരണങ്ങളാൽ നിങ്ങളുടെ കൈമാറ്റം പ്രോസസ്സ് ചെയ്യുന്നു.", "do_not_close": "ദയവായി ഈ പേജ് അടയ്ക്കരുത്.", "welcome_back": "വീണ്ടും സ്വാഗതം", "enter_password": "ആക്സസ് ചെയ്യാൻ നിങ്ങളുടെ പാസ്‌വേഡ് നൽകുക.", "password": "പാസ്‌വേഡ്", "login": "ലോഗിൻ", "statement": "അക്കൗണ്ട് സ്റ്റേറ്റ്മെന്റ്", "date": "തീയതി", "account_holder": "അക്കൗണ്ട് ഉടമ", "currency": "കറൻസി", "tx_history": "ഇടപാട് ചരിത്രം", "description": "വിവരണം", "ending_balance": "അവസാന ബാലൻസ്", "stmt_footer": "ഇത് കമ്പ്യൂട്ടർ നിർമ്മിത സ്റ്റേറ്റ്മെന്റാണ്, ഒപ്പ് ആവശ്യമില്ല.", "email_notif": "ഇമെയിൽ അറിയിപ്പുകൾ", "dark_mode": "ഡാർക്ക് മോഡ്", "biometrics": "Face ID / ബയോമെട്രിക്സ്", "active": "സജീവം", "opened": "തുറന്നു", "completed": "പൂർത്തിയായി", "pending": "കാത്തിരിക്കുന്നു", "unopened": "തുറക്കാത്തത്", "transfer_to": "ഇതിലേക്ക് കൈമാറുക", "just_now": "ഇപ്പോൾ", "success": "വിജയം", "verifying": "സ്ഥിരീകരിക്കുന്നു…", "premium": "പ്രീമിയം", "today": "ഇന്ന്", "yesterday": "ഇന്നലെ", "from": "ഇതിൽ നിന്ന്", "to": "ഇതിലേക്ക്"},
    "mt": {"dashboard": "Dashboard", "history": "Storja", "transfer": "Trasferiment", "cards": "Vault", "settings": "Settings", "total_balance": "Bilanċ Totali", "account_number": "Numru tal-Kont", "send_money": "Ibgħat Flus", "recent_tx": "Tranżazzjonijiet Riċenti", "see_all": "Ara kollox", "no_tx": "L-ebda tranżazzjoni s'issa.", "account_settings": "Settings tal-Kont", "log_out": "Oħroġ", "card_status": "Status tal-Karta", "freeze_card": "Iffriża l-Karta", "view_cvv": "Ara CVV", "download_stmt": "Niżżel id-Dikjarazzjoni", "get_pdf": "Ikseb ir-rekord PDF tiegħek", "download": "Niżżel", "bank_name": "Isem tal-bank", "account_no": "Numru tal-kont", "amount": "Ammont", "withdraw_code": "Kodiċi tal-irtirar", "confirm_transfer": "Ikkonferma t-Trasferiment", "funds_sent_to": "Il-fondi se jintbagħtu lill-kont bankarju li ddaħħal hawn taħt.", "transfer_processed": "Trasferiment Ipproċessat", "funds_sent_msg": "Il-fondi tiegħek intbagħtu. Jista' jieħu ftit minuti.", "processing": "Qed jiġi pproċessat", "processing_msg": "It-trasferiment tiegħek qed jiġi pproċessat għal raġunijiet ta' sigurtà.", "do_not_close": "Jekk jogħġbok tagħlaqx din il-paġna.", "welcome_back": "Merħba lura", "enter_password": "Daħħal il-password tiegħek biex taċċessa.", "password": "Password", "login": "Idħol", "statement": "Dikjarazzjoni tal-Kont", "date": "Data", "account_holder": "Detentur tal-Kont", "currency": "Munita", "tx_history": "Storja tat-Tranżazzjonijiet", "description": "Deskrizzjoni", "ending_balance": "Bilanċ Finali", "stmt_footer": "Din hija dikjarazzjoni ġġenerata mill-kompjuter u m'għandhiex bżonn firma.", "email_notif": "Notifiki bl-Email", "dark_mode": "Modalità Skura", "biometrics": "Face ID / Bijometrija", "active": "Attiv", "opened": "Miftuħ", "completed": "Lest", "pending": "Pendenti", "unopened": "Mhux miftuħ", "transfer_to": "Trasferiment lil", "just_now": "Biss issa", "success": "Suċċess", "verifying": "qed jivverifika…", "premium": "Premium", "today": "Illum", "yesterday": "Ilbieraħ", "from": "Minn", "to": "Lil"},
    "mi": {"dashboard": "Papatohu", "history": "Hītori", "transfer": "Whakawhiti", "cards": "Pouaka", "settings": "Tautuhinga", "total_balance": "Tapeke Moni", "account_number": "Tau Pūkete", "send_money": "Tuku Moni", "recent_tx": "Ngā Whakawhitinga Hou", "see_all": "Tiro katoa", "no_tx": "Kāore anō he whakawhitinga.", "account_settings": "Tautuhinga Pūkete", "log_out": "Takiputa", "card_status": "Tūnga Kāri", "freeze_card": "Whakatio Kāri", "view_cvv": "Tiro CVV", "download_stmt": "Tiki Tauākī", "get_pdf": "Tikina tō rekoata PDF", "download": "Tiki", "bank_name": "Ingoa pēke", "account_no": "Tau pūkete", "amount": "Nui", "withdraw_code": "Waehere tangohanga", "confirm_transfer": "Whakaū Whakawhiti", "funds_sent_to": "Ka tukuna ngā moni ki te pūkete pēke ka whakauruhia e koe ki raro.", "transfer_processed": "Kua Oti te Whakawhiti", "funds_sent_msg": "Kua tukuna ō moni. Ka roa pea ētahi meneti.", "processing": "E tukatuka ana", "processing_msg": "E tukatukahia ana tō whakawhiti mō ngā take haumaru.", "do_not_close": "Kaua e katia tēnei whārangi.", "welcome_back": "Nau mai anō", "enter_password": "Whakauruhia tō kupuhipa kia uru ai.", "password": "Kupuhipa", "login": "Takiuru", "statement": "Tauākī Pūkete", "date": "Rā", "account_holder": "Kaipupuri Pūkete", "currency": "Moni", "tx_history": "Hītori Whakawhitinga", "description": "Whakamārama", "ending_balance": "Tapeke Mutunga", "stmt_footer": "He tauākī tēnei i hangaia e te rorohiko, ā, kāore e hiahiatia he haina.", "email_notif": "Ngā Whakamōhiotanga Īmēra", "dark_mode": "Aratau Pōuri", "biometrics": "Face ID / Biometrics", "active": "Hohe", "opened": "Kua huakina", "completed": "Kua oti", "pending": "E tatari ana", "unopened": "Kāore i huakina", "transfer_to": "Whakawhiti ki", "just_now": "Ināianei tonu", "success": "Angitū", "verifying": "e manatoko ana…", "premium": "Premium", "today": "Rānei", "yesterday": "Inanahi", "from": "Mai i", "to": "Ki"},
    "mr": {"dashboard": "डॅशबोर्ड", "history": "इतिहास", "transfer": "हस्तांतरण", "cards": "व्हॉल्ट", "settings": "सेटिंग्ज", "total_balance": "एकूण शिल्लक", "account_number": "खाते क्रमांक", "send_money": "पैसे पाठवा", "recent_tx": "अलीकडील व्यवहार", "see_all": "सर्व पहा", "no_tx": "अद्याप कोणतेही व्यवहार नाहीत.", "account_settings": "खाते सेटिंग्ज", "log_out": "लॉग आउट", "card_status": "कार्ड स्थिती", "freeze_card": "कार्ड फ्रीज करा", "view_cvv": "CVV पहा", "download_stmt": "स्टेटमेंट डाउनलोड करा", "get_pdf": "तुमचे पीडीएफ रेकॉर्ड मिळवा", "download": "डाउनलोड करा", "bank_name": "बँकेचे नाव", "account_no": "खाते क्रमांक", "amount": "रक्कम", "withdraw_code": "पैसे काढण्याचा कोड", "confirm_transfer": "हस्तांतरणाची पुष्टी करा", "funds_sent_to": "तुम्ही खाली प्रविष्ट केलेल्या बँक खात्यात निधी पाठवला जाईल.", "transfer_processed": "हस्तांतरण प्रक्रिया पूर्ण", "funds_sent_msg": "तुमचा निधी पाठवला गेला आहे. प्रतिबिंबित होण्यास काही मिनिटे लागू शकतात.", "processing": "प्रक्रिया करत आहे", "processing_msg": "सुरक्षेच्या कारणास्तव तुमचे हस्तांतरण प्रक्रिया करत आहे.", "do_not_close": "कृपया हे पृष्ठ बंद करू नका.", "welcome_back": "पुन्हा स्वागत आहे", "enter_password": "प्रवेश करण्यासाठी तुमचा पासवर्ड प्रविष्ट करा.", "password": "पासवर्ड", "login": "लॉग इन करा", "statement": "खाते स्टेटमेंट", "date": "तारीख", "account_holder": "खातेधारक", "currency": "चलन", "tx_history": "व्यवहार इतिहास", "description": "वर्णन", "ending_balance": "अंतिम शिल्लक", "stmt_footer": "हे संगणक-व्युत्पन्न स्टेटमेंट आहे आणि स्वाक्षरीची आवश्यकता नाही.", "email_notif": "ईमेल सूचना", "dark_mode": "डार्क मोड", "biometrics": "फेस आयडी / बायोमेट्रिक्स", "active": "सक्रिय", "opened": "उघडले", "completed": "पूर्ण", "pending": "प्रलंबित", "unopened": "न उघडलेले", "transfer_to": "येथे हस्तांतरित करा", "just_now": "आत्ताच", "success": "यश", "verifying": "सत्यापित करत आहे…", "premium": "प्रीमियम", "today": "आज", "yesterday": "काल", "from": "पासून", "to": "पर्यंत"},
    "mn": {"dashboard": "Хяналтын самбар", "history": "Түүх", "transfer": "Шилжүүлэг", "cards": "Хадгаламж", "settings": "Тохиргоо", "total_balance": "Нийт үлдэгдэл", "account_number": "Дансны дугаар", "send_money": "Мөнгө илгээх", "recent_tx": "Сүүлийн гүйлгээнүүд", "see_all": "Бүгдийг харах", "no_tx": "Одоогоор гүйлгээ байхгүй.", "account_settings": "Дансны тохиргоо", "log_out": "Гарах", "card_status": "Картын төлөв", "freeze_card": "Картыг царцаах", "view_cvv": "CVV харах", "download_stmt": "Хуулга татах", "get_pdf": "PDF бичлэгээ авах", "download": "Татах", "bank_name": "Банкны нэр", "account_no": "Дансны дугаар", "amount": "Дүн", "withdraw_code": "Мөнгө авах код", "confirm_transfer": "Шилжүүлгийг баталгаажуулах", "funds_sent_to": "Мөнгийг доор оруулсан банкны данс руу илгээх болно.", "transfer_processed": "Шилжүүлэг боловсруулагдсан", "funds_sent_msg": "Таны мөнгө илгээгдлээ. Хэдэн минут шаардагдаж магадгүй.", "processing": "Боловсруулж байна", "processing_msg": "Аюулгүй байдлын үүднээс шилжүүлгийг боловсруулж байна.", "do_not_close": "Энэ хуудсыг бүү хаа.", "welcome_back": "Тавтай морилно уу", "enter_password": "Нэвтрэхийн тулд нууц үгээ оруулна уу.", "password": "Нууц үг", "login": "Нэвтрэх", "statement": "Дансны хуулга", "date": "Огноо", "account_holder": "Данс эзэмшигч", "currency": "Валют", "tx_history": "Гүйлгээний түүх", "description": "Тайлбар", "ending_balance": "Эцсийн үлдэгдэл", "stmt_footer": "Энэ нь компьютерээр үүсгэгдсэн хуулга бөгөөд гарын үсэг шаардлагагүй.", "email_notif": "Имэйл мэдэгдэл", "dark_mode": "Харанхуй горим", "biometrics": "Face ID / Биометр", "active": "Идэвхтэй", "opened": "Нээгдсэн", "completed": "Дууссан", "pending": "Хүлээгдэж байна", "unopened": "Нээгдээгүй", "transfer_to": "Шилжүүлэх", "just_now": "Яг одоо", "success": "Амжилт", "verifying": "баталгаажуулж байна…", "premium": "Премиум", "today": "Өнөөдөр", "yesterday": "Өчигдөр", "from": "Хэнээс", "to": "Хэнд"},
    "my": {"dashboard": "ဒက်ရှ်ဘုတ်", "history": "မှတ်တမ်း", "transfer": "ငွေလွှဲခြင်း", "cards": "သေတ္တာ", "settings": "ဆက်တင်များ", "total_balance": "စုစုပေါင်းလက်ကျန်ငွေ", "account_number": "အကောင့်နံပါတ်", "send_money": "ငွေပို့ရန်", "recent_tx": "မကြာသေးမီ ငွေလွှဲမှုများ", "see_all": "အားလုံးကြည့်ရန်", "no_tx": "ငွေလွှဲမှု မရှိသေးပါ။", "account_settings": "အကောင့် ဆက်တင်များ", "log_out": "ထွက်ရန်", "card_status": "ကတ်အခြေအနေ", "freeze_card": "ကတ်ကို အေးခဲစေရန်", "view_cvv": "CVV ကြည့်ရန်", "download_stmt": "ငွေစာရင်းဒင်းရန်", "get_pdf": "သင့် PDF မှတ်တမ်းကို ရယူပါ", "download": "ဒင်းရန်", "bank_name": "ဘဏ်အမည်", "account_no": "အကောင့်နံပါတ်", "amount": "ပမာဏ", "withdraw_code": "ငွေထုတ်ကုဒ်", "confirm_transfer": "ငွေလွှဲမှုကို အတည်ပြုပါ", "funds_sent_to": "ငွေများကို သင်အောက်တွင် ထည့်သွင်းသော ဘဏ်အကောင့်သို့ ပို့ဆောင်ပါမည်။", "transfer_processed": "ငွေလွှဲမှု ပြီးစီးပါပြီ", "funds_sent_msg": "သင့်ငွေများ ပို့ပြီးပါပြီ။ မိနစ်အနည်းငယ် ကြာနိုင်ပါသည်။", "processing": "လုပ်ဆောင်နေသည်", "processing_msg": "လုံခြုံရေးအရ သင့်ငွေလွှဲမှုကို လုပ်ဆောင်နေပါသည်။", "do_not_close": "ဤစာမျက်နှာကို ပိတ်မထားပါနှင့်။", "welcome_back": "ပြန်လည်ကြိုဆိုပါသည်", "enter_password": "ဝင်ရောက်ရန် သင့်စကားဝှက်ကို ထည့်ပါ။", "password": "စကားဝှက်", "login": "ဝင်ရောက်ရန်", "statement": "အကောင့်ငွေစာရင်း", "date": "ရက်စွဲ", "account_holder": "အကောင့်ပိုင်ရှင်", "currency": "ငွေကြေး", "tx_history": "ငွေလွှဲမှုမှတ်တမ်း", "description": "ဖော်ပြချက်", "ending_balance": "လက်ကျန်ငွေ", "stmt_footer": "ဤသည် ကွန်ပျူတာမှ ထုတ်ပေးသော ငွေစာရင်းဖြစ်ပြီး လက်မှတ်ထိုးရန် မလိုအပ်ပါ။", "email_notif": "အီးမေးလ် အသိပေးချက်များ", "dark_mode": "အမှောင်မုဒ်", "biometrics": "Face ID / ဇီဝဗေဒဆိုင်ရာ", "active": "တက်ကြွ", "opened": "ဖွင့်ထားသည်", "completed": "ပြီးစီးသည်", "pending": "စောင့်ဆိုင်းနေသည်", "unopened": "မဖွင့်ရသေးပါ", "transfer_to": "သို့ လွှဲပြောင်းရန်", "just_now": "ယခုပင်", "success": "အောင်မြင်သည်", "verifying": "အတည်ပြုနေသည်…", "premium": "ပရီမီယံ", "today": "ယနေ့", "yesterday": "မနေ့က", "from": "မှ", "to": "သို့"},
    "ne": {"dashboard": "ड्यासबोर्ड", "history": "इतिहास", "transfer": "स्थानान्तरण", "cards": "भल्ट", "settings": "सेटिङहरू", "total_balance": "कुल ब्यालेन्स", "account_number": "खाता नम्बर", "send_money": "पैसा पठाउनुहोस्", "recent_tx": "हालका लेनदेनहरू", "see_all": "सबै हेर्नुहोस्", "no_tx": "अहिलेसम्म कुनै लेनदेन छैन।", "account_settings": "खाता सेटिङहरू", "log_out": "लगआउट", "card_status": "कार्ड स्थिति", "freeze_card": "कार्ड फ्रिज गर्नुहोस्", "view_cvv": "CVV हेर्नुहोस्", "download_stmt": "स्टेटमेन्ट डाउनलोड गर्नुहोस्", "get_pdf": "तपाईंको PDF रेकर्ड प्राप्त गर्नुहोस्", "download": "डाउनलोड गर्नुहोस्", "bank_name": "बैंकको नाम", "account_no": "खाता नम्बर", "amount": "रकम", "withdraw_code": "निकासी कोड", "confirm_transfer": "स्थानान्तरण पुष्टि गर्नुहोस्", "funds_sent_to": "तपाईंले तल प्रविष्ट गर्नुभएको बैंक खातामा रकम पठाइनेछ।", "transfer_processed": "स्थानान्तरण प्रशोधन भयो", "funds_sent_msg": "तपाईंको रकम पठाइएको छ। यो देखिन केही मिनेट लाग्न सक्छ।", "processing": "प्रशोधन हुँदै", "processing_msg": "सुरक्षा कारणले तपाईंको स्थानान्तरण प्रशोधन हुँदैछ।", "do_not_close": "कृपया यो पृष्ठ बन्द नगर्नुहोस्।", "welcome_back": "पुनः स्वागत छ", "enter_password": "पहुँच गर्न तपाईंको पासवर्ड प्रविष्ट गर्नुहोस्।", "password": "पासवर्ड", "login": "लगइन", "statement": "खाता स्टेटमेन्ट", "date": "मिति", "account_holder": "खाता धारक", "currency": "मुद्रा", "tx_history": "लेनदेन इतिहास", "description": "विवरण", "ending_balance": "अन्तिम ब्यालेन्स", "stmt_footer": "यो कम्प्युटर-उत्पन्न स्टेटमेन्ट हो र हस्ताक्षर आवश्यक पर्दैन।", "email_notif": "इमेल सूचनाहरू", "dark_mode": "डार्क मोड", "biometrics": "फेस आईडी / बायोमेट्रिक्स", "active": "सक्रिय", "opened": "खोलिएको", "completed": "सम्पन्न", "pending": "पर्खाइमा", "unopened": "नखोलिएको", "transfer_to": "यहाँ स्थानान्तरण गर्नुहोस्", "just_now": "अहिले", "success": "सफलता", "verifying": "प्रमाणित गर्दै…", "premium": "प्रिमियम", "today": "आज", "yesterday": "हिजो", "from": "बाट", "to": "लाई"},
    "no": {"dashboard": "Dashbord", "history": "Historikk", "transfer": "Overføring", "cards": "Hvelv", "settings": "Innstillinger", "total_balance": "Total Saldo", "account_number": "Kontonummer", "send_money": "Send Penger", "recent_tx": "Nylige Transaksjoner", "see_all": "Se alle", "no_tx": "Ingen transaksjoner ennå.", "account_settings": "Kontoinnstillinger", "log_out": "Logg ut", "card_status": "Kortstatus", "freeze_card": "Frys Kortet", "view_cvv": "Se CVV", "download_stmt": "Last ned Kontoutskrift", "get_pdf": "Få din PDF-post", "download": "Last ned", "bank_name": "Banknavn", "account_no": "Kontonummer", "amount": "Beløp", "withdraw_code": "Uttakskode", "confirm_transfer": "Bekreft Overføring", "funds_sent_to": "Pengene sendes til bankkontoen du oppgir nedenfor.", "transfer_processed": "Overføring Behandlet", "funds_sent_msg": "Pengene dine er sendt. Det kan ta noen minutter.", "processing": "Behandler", "processing_msg": "Overføringen din behandles av sikkerhetshensyn.", "do_not_close": "Vennligst ikke lukk denne siden.", "welcome_back": "Velkommen tilbake", "enter_password": "Skriv inn passordet ditt for å få tilgang.", "password": "Passord", "login": "Logg inn", "statement": "Kontoutskrift", "date": "Dato", "account_holder": "Kontoinnehaver", "currency": "Valuta", "tx_history": "Transaksjonshistorikk", "description": "Beskrivelse", "ending_balance": "Sluttsaldo", "stmt_footer": "Dette er en datamaskingenerert utskrift og krever ikke signatur.", "email_notif": "E-postvarsler", "dark_mode": "Mørk Modus", "biometrics": "Face ID / Biometri", "active": "Aktiv", "opened": "Åpnet", "completed": "Fullført", "pending": "Venter", "unopened": "Uåpnet", "transfer_to": "Overføring til", "just_now": "Akkurat nå", "success": "Suksess", "verifying": "verifiserer…", "premium": "Premium", "today": "I dag", "yesterday": "I går", "from": "Fra", "to": "Til"},
    "or": {"dashboard": "ଡ୍ୟାସବୋର୍ଡ", "history": "ଇତିହାସ", "transfer": "ସ୍ଥାନାନ୍ତର", "cards": "ଭାଲ୍ଟ", "settings": "ସେଟିଂସ", "total_balance": "ସମୁଦାୟ ବାଲାନ୍ସ", "account_number": "ଆକାଉଣ୍ଟ ନମ୍ବର", "send_money": "ଟଙ୍କା ପଠାନ୍ତୁ", "recent_tx": "ସାମ୍ପ୍ରତିକ କାରବାର", "see_all": "ସବୁ ଦେଖନ୍ତୁ", "no_tx": "ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି କାରବାର ନାହିଁ।", "account_settings": "ଆକାଉଣ୍ଟ ସେଟିଂସ", "log_out": "ଲଗ୍ ଆଉଟ୍", "card_status": "କାର୍ଡ ସ୍ଥିତି", "freeze_card": "କାର୍ଡ ଫ୍ରିଜ୍ କରନ୍ତୁ", "view_cvv": "CVV ଦେଖନ୍ତୁ", "download_stmt": "ଷ୍ଟେଟମେଣ୍ଟ ଡାଉନଲୋଡ୍ କରନ୍ତୁ", "get_pdf": "ଆପଣଙ୍କର PDF ରେକର୍ଡ ପାଆନ୍ତୁ", "download": "ଡାଉନଲୋଡ୍", "bank_name": "ବ୍ୟାଙ୍କର ନାମ", "account_no": "ଆକାଉଣ୍ଟ ନମ୍ବର", "amount": "ରାଶି", "withdraw_code": "ଉଠାଇବା କୋଡ୍", "confirm_transfer": "ସ୍ଥାନାନ୍ତର ନିଶ୍ଚିତ କରନ୍ତୁ", "funds_sent_to": "ଆପଣ ତଳେ ଦାଖଲ କରିଥିବା ବ୍ୟାଙ୍କ ଖାତାକୁ ଅର୍ଥ ପଠାଯିବ।", "transfer_processed": "ସ୍ଥାନାନ୍ତର ସମ୍ପନ୍ନ ହେଲା", "funds_sent_msg": "ଆପଣଙ୍କର ଅର୍ଥ ପଠାଯାଇଛି। ଏହା କିଛି ମିନିଟ୍ ସମୟ ନେଇପାରେ।", "processing": "ପ୍ରକ୍ରିୟାକରଣ", "processing_msg": "ସୁରକ୍ଷା କାରଣରୁ ଆପଣଙ୍କର ସ୍ଥାନାନ୍ତର ପ୍ରକ୍ରିୟାକରଣ ଚାଲିଛି।", "do_not_close": "ଦୟାକରି ଏହି ପୃଷ୍ଠାକୁ ବନ୍ଦ କରନ୍ତୁ ନାହିଁ।", "welcome_back": "ପୁନର୍ବାର ସ୍ୱାଗତ", "enter_password": "ପ୍ରବେଶ କରିବାକୁ ଆପଣଙ୍କର ପାସୱାର୍ଡ ଦାଖଲ କରନ୍ତୁ।", "password": "ପାସୱାର୍ଡ", "login": "ଲଗ୍ ଇନ୍", "statement": "ଆକାଉଣ୍ଟ ଷ୍ଟେଟମେଣ୍ଟ", "date": "ତାରିଖ", "account_holder": "ଆକାଉଣ୍ଟ ଧାରକ", "currency": "ମୁଦ୍ରା", "tx_history": "କାରବାର ଇତିହାସ", "description": "ବର୍ଣ୍ଣନା", "ending_balance": "ଅନ୍ତିମ ବାଲାନ୍ସ", "stmt_footer": "ଏହା ଏକ କମ୍ପ୍ୟୁଟର-ଉତ୍ପାଦିତ ଷ୍ଟେଟମେଣ୍ଟ ଏବଂ ସ୍ୱାକ୍ଷର ଆବଶ୍ୟକ କରେ ନାହିଁ।", "email_notif": "ଇମେଲ ବିଜ୍ଞପ୍ତି", "dark_mode": "ଡାର୍କ ମୋଡ୍", "biometrics": "ଫେସ୍ ଆଇଡି / ବାୟୋମେଟ୍ରିକ୍ସ", "active": "ସକ୍ରିୟ", "opened": "ଖୋଲା", "completed": "ସମ୍ପନ୍ନ", "pending": "ବିଚାରାଧୀନ", "unopened": "ନ ଖୋଲା", "transfer_to": "କୁ ସ୍ଥାନାନ୍ତର", "just_now": "ଏବେ", "success": "ସଫଳତା", "verifying": "ଯାଞ୍ଚ କରୁଛି…", "premium": "ପ୍ରିମିୟମ", "today": "ଆଜି", "yesterday": "ଗତକାଲି", "from": "ଠାରୁ", "to": "କୁ"},
    "ps": {"dashboard": "ډشبورډ", "history": "تاریخ", "transfer": "لیږد", "cards": "خزانه", "settings": "ترتیبات", "total_balance": "ټول بیلانس", "account_number": "د حساب شمیره", "send_money": "پیسي لیږل", "recent_tx": "وروستي معاملې", "see_all": "ټول وګوره", "no_tx": "تر اوسه هیڅ معامله نشته.", "account_settings": "د حساب ترتیبات", "log_out": "وتل", "card_status": "د کارت حالت", "freeze_card": "کارت کنګل کړئ", "view_cvv": "CVV وګوره", "download_stmt": "بیانیه ډاونلوډ کړئ", "get_pdf": "خپل PDF ریکارډ ترلاسه کړئ", "download": "ډاونلوډ", "bank_name": "د بانک نوم", "account_no": "د حساب شمیره", "amount": "اندازه", "withdraw_code": "د ایستلو کوډ", "confirm_transfer": "لیږد تایید کړئ", "funds_sent_to": "پیسي به هغه بانکي حساب ته ولیږل شي چې تاسو یې لاندې داخل کړئ.", "transfer_processed": "لیږد پروسس شو", "funds_sent_msg": "ستاسو پیسي ولیږل شوې. ممکن څو دقیقې وخت ونیسي.", "processing": "پروسس کول", "processing_msg": "ستاسو لیږد د امنیتي دلایلو له امله پروسس کیږي.", "do_not_close": "مهرباني وکړئ دا پاڼه مه بندوئ.", "welcome_back": "بیرته ښه راغلاست", "enter_password": "د لاسرسي لپاره خپل پاسورډ دننه کړئ.", "password": "پاسورډ", "login": "ننوتل", "statement": "د حساب بیانیه", "date": "نېټه", "account_holder": "د حساب خاوند", "currency": "اسعار", "tx_history": "د معاملو تاریخ", "description": "تشریح", "ending_balance": "وروستی بیلانس", "stmt_footer": "دا د کمپیوټر لخوا جوړه شوې بیانیه ده او لاسلیک ته اړتیا نلري.", "email_notif": "د بریښنالیک خبرتیاوې", "dark_mode": "تیاره حالت", "biometrics": "Face ID / بایومیټریکس", "active": "فعال", "opened": "پرانیستل شو", "completed": "بشپړ شو", "pending": "پاتې", "unopened": "نه پرانیستل شو", "transfer_to": "ته لیږدول", "just_now": "همدا اوس", "success": "بریالیتوب", "verifying": "تصدیق کول…", "premium": "پریمیم", "today": "نن", "yesterday": "پرون", "from": "له", "to": "ته"},
    "fa": {"dashboard": "داشبورد", "history": "تاریخچه", "transfer": "انتقال", "cards": "گاوصندوق", "settings": "تنظیمات", "total_balance": "موجودی کل", "account_number": "شماره حساب", "send_money": "ارسال پول", "recent_tx": "تراکنش‌های اخیر", "see_all": "مشاهده همه", "no_tx": "هنوز تراکنشی وجود ندارد.", "account_settings": "تنظیمات حساب", "log_out": "خروج", "card_status": "وضعیت کارت", "freeze_card": "مسدود کردن کارت", "view_cvv": "مشاهده CVV", "download_stmt": "دانلود صورت‌حساب", "get_pdf": "دریافت سابقه PDF", "download": "دانلود", "bank_name": "نام بانک", "account_no": "شماره حساب", "amount": "مبلغ", "withdraw_code": "کد برداشت", "confirm_transfer": "تایید انتقال", "funds_sent_to": "وجه به حساب بانکی که در زیر وارد می‌کنید ارسال می‌شود.", "transfer_processed": "انتقال انجام شد", "funds_sent_msg": "وجه شما ارسال شد. ممکن است چند دقیقه طول بکشد.", "processing": "در حال پردازش", "processing_msg": "انتقال شما به دلایل امنیتی در حال پردازش است.", "do_not_close": "لطفا این صفحه را نبندید.", "welcome_back": "خوش آمدید", "enter_password": "برای دسترسی رمز عبور خود را وارد کنید.", "password": "رمز عبور", "login": "ورود", "statement": "صورت‌حساب", "date": "تاریخ", "account_holder": "صاحب حساب", "currency": "ارز", "tx_history": "تاریخچه تراکنش‌ها", "description": "توضیحات", "ending_balance": "موجودی نهایی", "stmt_footer": "این یک صورت‌حساب کامپیوتری است و نیازی به امضا ندارد.", "email_notif": "اعلان‌های ایمیلی", "dark_mode": "حالت تاریک", "biometrics": "Face ID / بیومتریک", "active": "فعال", "opened": "باز شده", "completed": "تکمیل شده", "pending": "در انتظار", "unopened": "باز نشده", "transfer_to": "انتقال به", "just_now": "همین حالا", "success": "موفقیت", "verifying": "در حال تایید…", "premium": "ویژه", "today": "امروز", "yesterday": "دیروز", "from": "از", "to": "به"},
    "pl": {"dashboard": "Pulpit", "history": "Historia", "transfer": "Przelew", "cards": "Skarbiec", "settings": "Ustawienia", "total_balance": "Całkowite Saldo", "account_number": "Numer Konta", "send_money": "Wyślij Pieniądze", "recent_tx": "Ostatnie Transakcje", "see_all": "Zobacz wszystko", "no_tx": "Brak transakcji.", "account_settings": "Ustawienia Konta", "log_out": "Wyloguj", "card_status": "Status Karty", "freeze_card": "Zablokuj Kartę", "view_cvv": "Zobacz CVV", "download_stmt": "Pobierz Wyciąg", "get_pdf": "Pobierz zapis PDF", "download": "Pobierz", "bank_name": "Nazwa banku", "account_no": "Numer konta", "amount": "Kwota", "withdraw_code": "Kod wypłaty", "confirm_transfer": "Potwierdź Przelew", "funds_sent_to": "Środki zostaną wysłane na konto bankowe podane poniżej.", "transfer_processed": "Przelew Zrealizowany", "funds_sent_msg": "Twoje środki zostały wysłane. Może to zająć kilka minut.", "processing": "Przetwarzanie", "processing_msg": "Twój przelew jest przetwarzany ze względów bezpieczeństwa.", "do_not_close": "Proszę nie zamykać tej strony.", "welcome_back": "Witaj ponownie", "enter_password": "Wprowadź hasło, aby uzyskać dostęp.", "password": "Hasło", "login": "Zaloguj się", "statement": "Wyciąg z Konta", "date": "Data", "account_holder": "Właściciel Konta", "currency": "Waluta", "tx_history": "Historia Transakcji", "description": "Opis", "ending_balance": "Saldo Końcowe", "stmt_footer": "Jest to wyciąg wygenerowany komputerowo i nie wymaga podpisu.", "email_notif": "Powiadomienia E-mail", "dark_mode": "Tryb Ciemny", "biometrics": "Face ID / Biometria", "active": "Aktywny", "opened": "Otwarto", "completed": "Zakończono", "pending": "Oczekuje", "unopened": "Nieotwarte", "transfer_to": "Przelew do", "just_now": "Przed chwilą", "success": "Sukces", "verifying": "weryfikacja…", "premium": "Premium", "today": "Dzisiaj", "yesterday": "Wczoraj", "from": "Od", "to": "Do"},
    "pa": {"dashboard": "ਡੈਸ਼ਬੋਰਡ", "history": "ਇਤਿਹਾਸ", "transfer": "ਟ੍ਰਾਂਸਫਰ", "cards": "ਵਾਲਟ", "settings": "ਸੈਟਿੰਗਾਂ", "total_balance": "ਕੁੱਲ ਬਕਾਇਆ", "account_number": "ਖਾਤਾ ਨੰਬਰ", "send_money": "ਪੈਸੇ ਭੇਜੋ", "recent_tx": "ਤਾਜ਼ਾ ਲੈਣ-ਦੇਣ", "see_all": "ਸਭ ਦੇਖੋ", "no_tx": "ਹਾਲੇ ਕੋਈ ਲੈਣ-ਦੇਣ ਨਹੀਂ।", "account_settings": "ਖਾਤਾ ਸੈਟਿੰਗਾਂ", "log_out": "ਲੌਗ ਆਉਟ", "card_status": "ਕਾਰਡ ਸਥਿਤੀ", "freeze_card": "ਕਾਰਡ ਫ੍ਰੀਜ਼ ਕਰੋ", "view_cvv": "CVV ਦੇਖੋ", "download_stmt": "ਸਟੇਟਮੈਂਟ ਡਾਊਨਲੋਡ ਕਰੋ", "get_pdf": "ਆਪਣਾ PDF ਰਿਕਾਰਡ ਪ੍ਰਾਪਤ ਕਰੋ", "download": "ਡਾਊਨਲੋਡ", "bank_name": "ਬੈਂਕ ਦਾ ਨਾਮ", "account_no": "ਖਾਤਾ ਨੰਬਰ", "amount": "ਰਕਮ", "withdraw_code": "ਨਿਕਾਸੀ ਕੋਡ", "confirm_transfer": "ਟ੍ਰਾਂਸਫਰ ਦੀ ਪੁਸ਼ਟੀ ਕਰੋ", "funds_sent_to": "ਪੈਸੇ ਉਸ ਬੈਂਕ ਖਾਤੇ ਵਿੱਚ ਭੇਜੇ ਜਾਣਗੇ ਜੋ ਤੁਸੀਂ ਹੇਠਾਂ ਦਰਜ ਕਰਦੇ ਹੋ।", "transfer_processed": "ਟ੍ਰਾਂਸਫਰ ਪ੍ਰੋਸੈਸ ਹੋਇਆ", "funds_sent_msg": "ਤੁਹਾਡੇ ਪੈਸੇ ਭੇਜ ਦਿੱਤੇ ਗਏ ਹਨ। ਇਸ ਵਿੱਚ ਕੁਝ ਮਿੰਟ ਲੱਗ ਸਕਦੇ ਹਨ।", "processing": "ਪ੍ਰੋਸੈਸਿੰਗ", "processing_msg": "ਸੁਰੱਖਿਆ ਕਾਰਨਾਂ ਕਰਕੇ ਤੁਹਾਡਾ ਟ੍ਰਾਂਸਫਰ ਪ੍ਰੋਸੈਸ ਹੋ ਰਿਹਾ ਹੈ।", "do_not_close": "ਕਿਰਪਾ ਕਰਕੇ ਇਸ ਪੰਨੇ ਨੂੰ ਬੰਦ ਨਾ ਕਰੋ।", "welcome_back": "ਵਾਪਸ ਜੀ ਆਇਆਂ ਨੂੰ", "enter_password": "ਪਹੁੰਚ ਲਈ ਆਪਣਾ ਪਾਸਵਰਡ ਦਰਜ ਕਰੋ।", "password": "ਪਾਸਵਰਡ", "login": "ਲੌਗਇਨ", "statement": "ਖਾਤਾ ਸਟੇਟਮੈਂਟ", "date": "ਤਾਰੀਖ", "account_holder": "ਖਾਤਾ ਧਾਰਕ", "currency": "ਕਰੰਸੀ", "tx_history": "ਲੈਣ-ਦੇਣ ਦਾ ਇਤਿਹਾਸ", "description": "ਵੇਰਵਾ", "ending_balance": "ਅੰਤਿਮ ਬਕਾਇਆ", "stmt_footer": "ਇਹ ਕੰਪਿਊਟਰ ਦੁਆਰਾ ਤਿਆਰ ਕੀਤਾ ਗਿਆ ਸਟੇਟਮੈਂਟ ਹੈ ਅਤੇ ਇਸਨੂੰ ਦਸਤਖਤ ਦੀ ਲੋੜ ਨਹੀਂ ਹੈ।", "email_notif": "ਈਮੇਲ ਸੂਚਨਾਵਾਂ", "dark_mode": "ਡਾਰਕ ਮੋਡ", "biometrics": "ਫੇਸ ਆਈਡੀ / ਬਾਇਓਮੈਟ੍ਰਿਕਸ", "active": "ਸਰਗਰਮ", "opened": "ਖੋਲ੍ਹਿਆ", "completed": "ਪੂਰਾ ਹੋਇਆ", "pending": "ਬਕਾਇਆ", "unopened": "ਨਾ ਖੋਲ੍ਹਿਆ", "transfer_to": "ਇਸ ਵਿੱਚ ਟ੍ਰਾਂਸਫਰ ਕਰੋ", "just_now": "ਹੁਣੇ", "success": "ਸਫਲਤਾ", "verifying": "ਤਸਦੀਕ ਕਰ ਰਿਹਾ ਹੈ…", "premium": "ਪ੍ਰੀਮੀਅਮ", "today": "ਅੱਜ", "yesterday": "ਕੱਲ੍ਹ", "from": "ਤੋਂ", "to": "ਨੂੰ"},
    "ro": {"dashboard": "Panou", "history": "Istoric", "transfer": "Transfer", "cards": "Seif", "settings": "Setări", "total_balance": "Sold Total", "account_number": "Număr Cont", "send_money": "Trimite Bani", "recent_tx": "Tranzacții Recente", "see_all": "Vezi tot", "no_tx": "Nu există tranzacții încă.", "account_settings": "Setări Cont", "log_out": "Deconectare", "card_status": "Starea Cardului", "freeze_card": "Îngheață Cardul", "view_cvv": "Vezi CVV", "download_stmt": "Descarcă Extras", "get_pdf": "Obține înregistrarea PDF", "download": "Descarcă", "bank_name": "Numele băncii", "account_no": "Număr de cont", "amount": "Sumă", "withdraw_code": "Cod de retragere", "confirm_transfer": "Confirmă Transferul", "funds_sent_to": "Fondurile vor fi trimise în contul bancar pe care îl introduceți mai jos.", "transfer_processed": "Transfer Procesat", "funds_sent_msg": "Fondurile au fost trimise. Poate dura câteva minute.", "processing": "Procesare", "processing_msg": "Transferul dvs. este procesat din motive de securitate.", "do_not_close": "Vă rugăm să nu închideți această pagină.", "welcome_back": "Bine ai revenit", "enter_password": "Introdu parola pentru a accesa.", "password": "Parolă", "login": "Conectare", "statement": "Extras de Cont", "date": "Data", "account_holder": "Deținătorul Contului", "currency": "Monedă", "tx_history": "Istoric Tranzacții", "description": "Descriere", "ending_balance": "Sold Final", "stmt_footer": "Acesta este un extras generat de computer și nu necesită semnătură.", "email_notif": "Notificări Email", "dark_mode": "Mod Întunecat", "biometrics": "Face ID / Biometrie", "active": "Activ", "opened": "Deschis", "completed": "Finalizat", "pending": "În așteptare", "unopened": "Nedescis", "transfer_to": "Transfer către", "just_now": "Chiar acum", "success": "Succes", "verifying": "se verifică…", "premium": "Premium", "today": "Astăzi", "yesterday": "Ieri", "from": "De la", "to": "Către"},
    "sm": {"dashboard": "Dashboard", "history": "Tala'aga", "transfer": "Fesi'ota'i", "cards": "Vault", "settings": "Fa'atonuga", "total_balance": "Aofa'iga Paleni", "account_number": "Numera o le Teugatupe", "send_money": "Lafo Tupe", "recent_tx": "Fefa'ataua'iga Talu ai nei", "see_all": "Va'ai uma", "no_tx": "E leai ni fefa'ataua'iga.", "account_settings": "Fa'atonuga o le Teugatupe", "log_out": "Alu i fafo", "card_status": "Tulaga o le Kata", "freeze_card": "Fa'a'aisa le Kata", "view_cvv": "Va'ai le CVV", "download_stmt": "Si'i mai le Fa'amatalaga", "get_pdf": "Maua lau fa'amaumauga PDF", "download": "Si'i mai", "bank_name": "Igoa o le faletupe", "account_no": "Numera o le teugatupe", "amount": "Aofa'iga", "withdraw_code": "Fa'ailoga o le tosoina", "confirm_transfer": "Fa'amaonia le Fesi'ota'i", "funds_sent_to": "O le a lafo atu tupe i le teugatupe o lo'o e tusia i lalo.", "transfer_processed": "Ua Maea le Fesi'ota'i", "funds_sent_msg": "Ua lafo atu lau tupe. Atonu e umi ni nai minute.", "processing": "O lo'o fa'agaioia", "processing_msg": "O lo'o fa'agaioia lau fesi'ota'i ona o le saogalemu.", "do_not_close": "Fa'amolemole aua le tapunia lenei itulau.", "welcome_back": "Afio mai", "enter_password": "Ulufale i lau upu fa'alilolilo e maua ai.", "password": "Upu fa'alilolilo", "login": "Ulufale", "statement": "Fa'amatalaga o le Teugatupe", "date": "Aso", "account_holder": "E ona le Teugatupe", "currency": "Tupe", "tx_history": "Tala'aga o Fefa'ataua'iga", "description": "Fa'amatalaga", "ending_balance": "Paleni Fa'ai'u", "stmt_footer": "O se fa'amatalaga lea ua faia e le komepiuta ma e le mana'omia se saini.", "email_notif": "Fa'asilasilaga imeli", "dark_mode": "Pouliuli", "biometrics": "Face ID / Biometrics", "active": "Malosi", "opened": "Tatala", "completed": "Maea", "pending": "Fa'atali", "unopened": "Le'i tatalaina", "transfer_to": "Fesi'ota'i i", "just_now": "I le taimi nei", "success": "Manuia", "verifying": "fa'amaonia…", "premium": "Premium", "today": "Aso nei", "yesterday": "Ananafi", "from": "Mai", "to": "I"},
    "gd": {"dashboard": "Deas-bòrd", "history": "Eachdraidh", "transfer": "Gluasad", "cards": "Seòmar-tasgaidh", "settings": "Roghainnean", "total_balance": "Cothromachadh Iomlan", "account_number": "Àireamh Cunntais", "send_money": "Cuir Airgead", "recent_tx": "Gnothaichean O Chionn Ghoirid", "see_all": "Faic na h-uile", "no_tx": "Chan eil gnothaichean ann fhathast.", "account_settings": "Roghainnean Cunntais", "log_out": "Clàraich a-mach", "card_status": "Inbhe Cairt", "freeze_card": "Reòtaich a' Chairt", "view_cvv": "Faic CVV", "download_stmt": "Luchdaich a-nuas Aithris", "get_pdf": "Faigh do chlàr PDF", "download": "Luchdaich a-nuas", "bank_name": "Ainm a' bhanca", "account_no": "Àireamh cunntais", "amount": "Suim", "withdraw_code": "Còd tarraing a-mach", "confirm_transfer": "Dearbh Gluasad", "funds_sent_to": "Thèid an t-airgead a chuir chun chunntas banca a chuireas tu a-steach gu h-ìosal.", "transfer_processed": "Gluasad air a Phròiseasadh", "funds_sent_msg": "Chaidh an t-airgead agad a chuir. Dh'fhaodadh e beagan mhionaidean a ghabhail.", "processing": "A' pròiseasadh", "processing_msg": "Tha an gluasad agad air a phròiseasadh airson adhbharan tèarainteachd.", "do_not_close": "Feuch nach dùin thu an duilleag seo.", "welcome_back": "Fàilte air ais", "enter_password": "Cuir a-steach am facal-faire agad airson inntrigeadh.", "password": "Facal-faire", "login": "Clàraich a-steach", "statement": "Aithris Cunntais", "date": "Ceann-latha", "account_holder": "Sealbhadair Cunntais", "currency": "Airgead", "tx_history": "Eachdraidh Gnothaichean", "description": "Tuairisgeul", "ending_balance": "Cothromachadh Deireannach", "stmt_footer": "Is e aithris a chaidh a chruthachadh le coimpiutair a tha seo agus chan fheum e ainm-sgrìobhte.", "email_notif": "Fiosan Post-d", "dark_mode": "Modh Dorcha", "biometrics": "Face ID / Biometrics", "active": "Gnìomhach", "opened": "Fosgailte", "completed": "Crìochnaichte", "pending": "A' feitheamh", "unopened": "Gun fhosgladh", "transfer_to": "Gluais gu", "just_now": "An-dràsta fhèin", "success": "Soirbheachas", "verifying": "a' dearbhadh…", "premium": "Premium", "today": "An-diugh", "yesterday": "An-dè", "from": "Bho", "to": "Gu"},
    "sr": {"dashboard": "Контролна табла", "history": "Историја", "transfer": "Пренос", "cards": "Сеф", "settings": "Подешавања", "total_balance": "Укупан Салдо", "account_number": "Број Рачуна", "send_money": "Пошаљи Новац", "recent_tx": "Недавне Трансакције", "see_all": "Види све", "no_tx": "Још нема трансакција.", "account_settings": "Подешавања Рачуна", "log_out": "Одјави се", "card_status": "Статус Картице", "freeze_card": "Замрзни Картицу", "view_cvv": "Види CVV", "download_stmt": "Преузми Извод", "get_pdf": "Преузми PDF запис", "download": "Преузми", "bank_name": "Име банке", "account_no": "Број рачуна", "amount": "Износ", "withdraw_code": "Код за подизање", "confirm_transfer": "Потврди Пренос", "funds_sent_to": "Средства ће бити послата на банковни рачун који унесете испод.", "transfer_processed": "Пренос Обрађен", "funds_sent_msg": "Ваша средства су послата. Може потрајати неколико минута.", "processing": "Обрада", "processing_msg": "Ваш пренос се обрађује из безбедносних разлога.", "do_not_close": "Молимо вас да не затварате ову страницу.", "welcome_back": "Добродошли назад", "enter_password": "Унесите лозинку за приступ рачуну.", "password": "Лозинка", "login": "Пријава", "statement": "Извод Рачуна", "date": "Датум", "account_holder": "Власник Рачуна", "currency": "Валута", "tx_history": "Историја Трансакција", "description": "Опис", "ending_balance": "Коначни Салдо", "stmt_footer": "Ово је рачунарски генерисан извод и не захтева потпис.", "email_notif": "Емаил Обавештења", "dark_mode": "Тамни Режим", "biometrics": "Face ID / Биометрија", "active": "Активан", "opened": "Отворено", "completed": "Завршено", "pending": "На чекању", "unopened": "Неотворено", "transfer_to": "Пренос на", "just_now": "Управо сада", "success": "Успех", "verifying": "провера…", "premium": "Премиум", "today": "Данас", "yesterday": "Јуче", "from": "Од", "to": "За"},
    "st": {"dashboard": "Dashboard", "history": "Nalane", "transfer": "Phetisetso", "cards": "Vault", "settings": "Litlhophiso", "total_balance": "Kakaretso ea Balance", "account_number": "Nomoro ea Akhaonto", "send_money": "Romela Chelete", "recent_tx": "Litšebelisano tsa Haufinyane", "see_all": "Bona tsohle", "no_tx": "Ha ho na litšebelisano.", "account_settings": "Litlhophiso tsa Akhaonto", "log_out": "Tsoa", "card_status": "Boemo ba Karete", "freeze_card": "Hatella Karete", "view_cvv": "Bona CVV", "download_stmt": "Khoasolla Setifikeiti", "get_pdf": "Fumana rekoto ea hau ea PDF", "download": "Khoasolla", "bank_name": "Lebitso la banka", "account_no": "Nomoro ea akhaonto", "amount": "Chelete", "withdraw_code": "Khoutu ea ho ntša", "confirm_transfer": "Netefatsa Phetisetso", "funds_sent_to": "Chelete e tla romeloa ho akhaonto ea banka eo u e kenyang ka tlase.", "transfer_processed": "Phetisetso e Sebetsitsoe", "funds_sent_msg": "Chelete ea hau e rometsoe. Ho ka nka metsotso e seng mekae.", "processing": "E ntse e sebetsa", "processing_msg": "Phetisetso ea hau e ntse e sebetsa ka mabaka a ts'ireletso.", "do_not_close": "Ka kopo u se ke ua koala leqephe lena.", "welcome_back": "Rea u amohela hape", "enter_password": "Kenya phasewete ea hau ho kena.", "password": "Phasewete", "login": "Kena", "statement": "Setifikeiti sa Akhaonto", "date": "Letsatsi", "account_holder": "Mong'a Akhaonto", "currency": "Chelete", "tx_history": "Nalane ea Litšebelisano", "description": "Tlhaloso", "ending_balance": "Balance ea ho Qetela", "stmt_footer": "Sena ke setifikeiti se entsoeng ke khomphutha 'me ha se hloke ho saena.", "email_notif": "Tsebiso ea Imeile", "dark_mode": "Mokhoa o Lefifi", "biometrics": "Face ID / Biometrics", "active": "E sebetsang", "opened": "E butsoe", "completed": "E felile", "pending": "E emetse", "unopened": "Ha e butsoa", "transfer_to": "Phetisetsa ho", "just_now": "Hona joale", "success": "Katleho", "verifying": "e netefatsa…", "premium": "Premium", "today": "Kajeno", "yesterday": "Maobane", "from": "Ho tloha", "to": "Ho"},
    "sn": {"dashboard": "Dashboard", "history": "Nhoroondo", "transfer": "Kuchinjisa", "cards": "Vault", "settings": "Zvirongwa", "total_balance": "Mari Yese", "account_number": "Nhamba yeAkaunti", "send_money": "Tumira Mari", "recent_tx": "Kutengeserana Kuchangobva Kuitika", "see_all": "Ona zvese", "no_tx": "Hapasisina kutengeserana.", "account_settings": "Zvirongwa zveAkaunti", "log_out": "Buda", "card_status": "Mamiriro eKadhi", "freeze_card": "Dzima Kadhi", "view_cvv": "Ona CVV", "download_stmt": "Dhaunirodha Chirevo", "get_pdf": "Wana rekodhi yako yePDF", "download": "Dhaunirodha", "bank_name": "Zita rebhangi", "account_no": "Nhamba yeakaunti", "amount": "Mari", "withdraw_code": "Kodhi yekubudisa", "confirm_transfer": "Simbisa Kuchinjisa", "funds_sent_to": "Mari ichatumirwa kuakaunti yebhangi yaunopinda pazasi.", "transfer_processed": "Kuchinjisa Kwapera", "funds_sent_msg": "Mari yako yatumirwa. Zvinogona kutora maminetsi mashoma.", "processing": "Kugadzirisa", "processing_msg": "Kuchinjisa kwako kuri kugadziriswa nekuda kwekuchengetedza.", "do_not_close": "Ndapota usavhara peji rino.", "welcome_back": "Kuchiwana zvakare", "enter_password": "Pinda pashiworido rako kuti upinde.", "password": "Pashiworido", "login": "Pinda", "statement": "Chirevo cheAkaunti", "date": "Zuva", "account_holder": "Muridzi weAkaunti", "currency": "Mari", "tx_history": "Nhoroondo yeKutengeserana", "description": "Tsananguro", "ending_balance": "Mari Yekupedzisira", "stmt_footer": "Ichi chirevo chakagadzirwa nekombuta uye hachidi siginicha.", "email_notif": "Ziviso dzeEmail", "dark_mode": "Nzira Yerima", "biometrics": "Face ID / Biometrics", "active": "Inoshanda", "opened": "Yakavhurwa", "completed": "Yapera", "pending": "Yakamirira", "unopened": "Isina kuvhurwa", "transfer_to": "Kuchinjisa ku", "just_now": "Izvo zvino", "success": "Kubudirira", "verifying": "kuri kusimbisa…", "premium": "Premium", "today": "Nhasi", "yesterday": "Nezuro", "from": "Kubva", "to": "Ku"},
    "sd": {"dashboard": "ڊيش بورڊ", "history": "تاريخ", "transfer": "منتقلي", "cards": "ويلٽ", "settings": "سيٽنگون", "total_balance": "ڪل بيلنس", "account_number": "اڪائونٽ نمبر", "send_money": "پئسا موڪليو", "recent_tx": "تازو ٽرانزيڪشن", "see_all": "سڀ ڏسو", "no_tx": "اڃا ڪو ٽرانزيڪشن ناهي.", "account_settings": "اڪائونٽ سيٽنگون", "log_out": "لاگ آئوٽ", "card_status": "ڪارڊ جي حالت", "freeze_card": "ڪارڊ فريز ڪريو", "view_cvv": "CVV ڏسو", "download_stmt": "بيان ڊائون لوڊ ڪريو", "get_pdf": "پنهنجو PDF رڪارڊ حاصل ڪريو", "download": "ڊائون لوڊ", "bank_name": "بينڪ جو نالو", "account_no": "اڪائونٽ نمبر", "amount": "رقم", "withdraw_code": "ڪڍڻ جو ڪوڊ", "confirm_transfer": "منتقلي جي تصديق ڪريو", "funds_sent_to": "پئسا ان بئنڪ اڪائونٽ ڏانهن موڪليا ويندا جيڪو توهان هيٺ داخل ڪيو آهي.", "transfer_processed": "منتقلي پروسيس ٿي وئي", "funds_sent_msg": "توهان جا پئسا موڪليا ويا آهن. ڪجهه منٽ لڳي سگهن ٿا.", "processing": "پروسيسنگ", "processing_msg": "حفاظتي سببن جي ڪري توهان جي منتقلي پروسيس ٿي رهي آهي.", "do_not_close": "مهرباني ڪري هي صفحو بند نه ڪريو.", "welcome_back": "ڀلي ڪري آيا", "enter_password": "رسائي لاءِ پنهنجو پاسورڊ داخل ڪريو.", "password": "پاسورڊ", "login": "لاگ ان", "statement": "اڪائونٽ بيان", "date": "تاريخ", "account_holder": "اڪائونٽ هولڊر", "currency": "ڪرنسي", "tx_history": "ٽرانزيڪشن جي تاريخ", "description": "تفصيل", "ending_balance": "آخري بيلنس", "stmt_footer": "هي ڪمپيوٽر طرفان تيار ڪيل بيان آهي ۽ دستخط جي ضرورت ناهي.", "email_notif": "اي ميل اطلاع", "dark_mode": "ڊارڪ موڊ", "biometrics": "Face ID / بايوميٽرڪس", "active": "فعال", "opened": "کليل", "completed": "مڪمل ٿيل", "pending": "باقي", "unopened": "نه کليل", "transfer_to": "ڏانهن منتقل ڪريو", "just_now": "هاڻي", "success": "ڪاميابي", "verifying": "تصديق ڪندي…", "premium": "پريميم", "today": "اڄ", "yesterday": "ڪالهه", "from": "کان", "to": "ڏانهن"},
    "si": {"dashboard": "පාලක පුවරුව", "history": "ඉතිහාසය", "transfer": "මාරු කිරීම", "cards": "වෝල්ට්", "settings": "සැකසීම්", "total_balance": "මුළු ශේෂය", "account_number": "ගිණුම් අංකය", "send_money": "මුදල් යවන්න", "recent_tx": "මෑත ගනුදෙනු", "see_all": "සියල්ල බලන්න", "no_tx": "තවම ගනුදෙනු නැත.", "account_settings": "ගිණුම් සැකසීම්", "log_out": "පිටවන්න", "card_status": "කාඩ්පත් තත්ත්වය", "freeze_card": "කාඩ්පත කැටි කරන්න", "view_cvv": "CVV බලන්න", "download_stmt": "ප්‍රකාශය බාගන්න", "get_pdf": "ඔබේ PDF වාර්තාව ලබා ගන්න", "download": "බාගන්න", "bank_name": "බැංකුවේ නම", "account_no": "ගිණුම් අංකය", "amount": "මුදල", "withdraw_code": "ආපසු ගැනීමේ කේතය", "confirm_transfer": "මාරු කිරීම තහවුරු කරන්න", "funds_sent_to": "ඔබ පහත ඇතුළත් කරන බැංකු ගිණුමට මුදල් යවනු ලැබේ.", "transfer_processed": "මාරු කිරීම සකසන ලදී", "funds_sent_msg": "ඔබේ මුදල් යවා ඇත. එයට මිනිත්තු කිහිපයක් ගත විය හැක.", "processing": "සකසමින්", "processing_msg": "ආරක්ෂක හේතූන් මත ඔබේ මාරු කිරීම සකසමින් පවතී.", "do_not_close": "කරුණාකර මෙම පිටුව වසා නොදමන්න.", "welcome_back": "නැවත සාදරයෙන් පිළිගනිමු", "enter_password": "පිවිසීමට ඔබේ මුරපදය ඇතුළත් කරන්න.", "password": "මුරපදය", "login": "පිවිසෙන්න", "statement": "ගිණුම් ප්‍රකාශය", "date": "දිනය", "account_holder": "ගිණුම් හිමියා", "currency": "මුදල් ඒකකය", "tx_history": "ගනුදෙනු ඉතිහාසය", "description": "විස්තරය", "ending_balance": "අවසන් ශේෂය", "stmt_footer": "මෙය පරිගණකයෙන් ජනනය කරන ලද ප්‍රකාශයක් වන අතර අත්සනක් අවශ්‍ය නොවේ.", "email_notif": "විද්‍යුත් තැපැල් දැනුම්දීම්", "dark_mode": "අඳුරු මාදිලිය", "biometrics": "Face ID / ජෛවමිතික", "active": "ක්‍රියාකාරී", "opened": "විවෘත කර ඇත", "completed": "සම්පූර්ණයි", "pending": "පොරොත්තුවෙන්", "unopened": "නොවිවෘත", "transfer_to": "වෙත මාරු කරන්න", "just_now": "දැන්", "success": "සාර්ථකයි", "verifying": "සත්‍යාපනය කරමින්…", "premium": "ප්‍රීමියම්", "today": "අද", "yesterday": "ඊයේ", "from": "සිට", "to": "දක්වා"},
    "sk": {"dashboard": "Nástenka", "history": "História", "transfer": "Prevod", "cards": "Trezor", "settings": "Nastavenia", "total_balance": "Celkový Zostatok", "account_number": "Číslo Účtu", "send_money": "Poslať Peniaze", "recent_tx": "Nedávne Transakcie", "see_all": "Zobraziť všetko", "no_tx": "Zatiaľ žiadne transakcie.", "account_settings": "Nastavenia Účtu", "log_out": "Odhlásiť sa", "card_status": "Stav Karty", "freeze_card": "Zmraziť Kartu", "view_cvv": "Zobraziť CVV", "download_stmt": "Stiahnuť Výpis", "get_pdf": "Získať PDF záznam", "download": "Stiahnuť", "bank_name": "Názov banky", "account_no": "Číslo účtu", "amount": "Suma", "withdraw_code": "Kód na výber", "confirm_transfer": "Potvrdiť Prevod", "funds_sent_to": "Prostriedky budú odoslané na bankový účet, ktorý zadáte nižšie.", "transfer_processed": "Prevod Spracovaný", "funds_sent_msg": "Vaše prostriedky boli odoslané. Môže to trvať niekoľko minút.", "processing": "Spracovanie", "processing_msg": "Váš prevod sa spracováva z bezpečnostných dôvodov.", "do_not_close": "Prosím nezatvárajte túto stránku.", "welcome_back": "Vitajte späť", "enter_password": "Zadajte heslo pre prístup k účtu.", "password": "Heslo", "login": "Prihlásiť sa", "statement": "Výpis z Účtu", "date": "Dátum", "account_holder": "Majiteľ Účtu", "currency": "Mena", "tx_history": "História Transakcií", "description": "Popis", "ending_balance": "Konečný Zostatok", "stmt_footer": "Toto je počítačom generovaný výpis a nevyžaduje podpis.", "email_notif": "E-mailové Upozornenia", "dark_mode": "Tmavý Režim", "biometrics": "Face ID / Biometria", "active": "Aktívny", "opened": "Otvorené", "completed": "Dokončené", "pending": "Čaká sa", "unopened": "Neotvorené", "transfer_to": "Prevod do", "just_now": "Práve teraz", "success": "Úspech", "verifying": "overovanie…", "premium": "Premium", "today": "Dnes", "yesterday": "Včera", "from": "Od", "to": "Komu"},
    "sl": {"dashboard": "Nadzorna plošča", "history": "Zgodovina", "transfer": "Prenos", "cards": "Trezor", "settings": "Nastavitve", "total_balance": "Skupno Stanje", "account_number": "Številka Računa", "send_money": "Pošlji Denar", "recent_tx": "Nedavne Transakcije", "see_all": "Poglej vse", "no_tx": "Ni še transakcij.", "account_settings": "Nastavitve Računa", "log_out": "Odjava", "card_status": "Status Kartice", "freeze_card": "Zamrzni Kartico", "view_cvv": "Poglej CVV", "download_stmt": "Prenesi Izpisek", "get_pdf": "Pridobi svoj PDF zapis", "download": "Prenesi", "bank_name": "Ime banke", "account_no": "Številka računa", "amount": "Znesek", "withdraw_code": "Koda za dvig", "confirm_transfer": "Potrdi Prenos", "funds_sent_to": "Sredstva bodo poslana na bančni račun, ki ga vnesete spodaj.", "transfer_processed": "Prenos Obdelan", "funds_sent_msg": "Vaša sredstva so bila poslana. Lahko traja nekaj minut.", "processing": "Obdelava", "processing_msg": "Vaš prenos se obdeluje iz varnostnih razlogov.", "do_not_close": "Prosimo, ne zapirajte te strani.", "welcome_back": "Dobrodošli nazaj", "enter_password": "Vnesite geslo za dostop do računa.", "password": "Geslo", "login": "Prijava", "statement": "Izpisek Računa", "date": "Datum", "account_holder": "Lastnik Računa", "currency": "Valuta", "tx_history": "Zgodovina Transakcij", "description": "Opis", "ending_balance": "Končno Stanje", "stmt_footer": "To je računalniško ustvarjen izpisek in ne zahteva podpisa.", "email_notif": "E-poštna Obvestila", "dark_mode": "Temni Način", "biometrics": "Face ID / Biometrija", "active": "Aktiven", "opened": "Odprto", "completed": "Zaključeno", "pending": "V čakanju", "unopened": "Neodprto", "transfer_to": "Prenos na", "just_now": "Pravkar", "success": "Uspeh", "verifying": "preverjanje…", "premium": "Premium", "today": "Danes", "yesterday": "Včeraj", "from": "Od", "to": "Za"},
    "so": {"dashboard": "Dashboard", "history": "Taariikh", "transfer": "Wareejin", "cards": "Vault", "settings": "Dejinta", "total_balance": "Isku darka Guud", "account_number": "Lambarka Akoonka", "send_money": "Dir Lacag", "recent_tx": "Dhaqdhaqaaqyada Ugu Dambeeyay", "see_all": "Arag dhammaan", "no_tx": "Weli ma jiraan dhaqdhaqaaqyo.", "account_settings": "Dejinta Akoonka", "log_out": "Ka bax", "card_status": "Xaaladda Kaarka", "freeze_card": "Qabooji Kaarka", "view_cvv": "Arag CVV", "download_stmt": "Soo dejiso Bayaanka", "get_pdf": "Hel diiwaankaaga PDF", "download": "Soo dejiso", "bank_name": "Magaca bangiga", "account_no": "Lambarka akoonka", "amount": "Qadarka", "withdraw_code": "Koodhka lacag-bixinta", "confirm_transfer": "Xaqiiji Wareejinta", "funds_sent_to": "Lacagta waxaa loo diri doonaa akoonka bangiga ee aad hoos ku qorto.", "transfer_processed": "Wareejinta Waa La Farsameeyay", "funds_sent_msg": "Lacagtaada waa la diray. Waxay qaadan kartaa dhowr daqiiqo.", "processing": "Farsamaynta", "processing_msg": "Wareejintaada waa la farsamaynayaa sababo amni awgood.", "do_not_close": "Fadlan ha xirin boggan.", "welcome_back": "Ku soo dhawow", "enter_password": "Geli furahaaga sirta ah si aad u gasho.", "password": "Furaha Sirta", "login": "Gal", "statement": "Bayaanka Akoonka", "date": "Taariikhda", "account_holder": "Milkiilaha Akoonka", "currency": "Lacagta", "tx_history": "Taariikhda Dhaqdhaqaaqa", "description": "Sharaxaad", "ending_balance": "Isku darka Ugu Dambeeya", "stmt_footer": "Kani waa bayaan kombuyuutar soo saaray oo uma baahna saxeex.", "email_notif": "Ogeysiisyada Iimaylka", "dark_mode": "Muuqaalka Mugdiga", "biometrics": "Face ID / Biometrics", "active": "Firfircoon", "opened": "La furay", "completed": "La dhammeeyay", "pending": "Sugaya", "unopened": "Aan la furin", "transfer_to": "U wareeji", "just_now": "Hadda", "success": "Guul", "verifying": "xaqiijinta…", "premium": "Premium", "today": "Maanta", "yesterday": "Shalay", "from": "Ka yimid", "to": "U"},
    "su": {"dashboard": "Dasbor", "history": "Sajarah", "transfer": "Mindahkeun", "cards": "Vault", "settings": "Setélan", "total_balance": "Total Kasaimbangan", "account_number": "Nomer Rekening", "send_money": "Kirim Duit", "recent_tx": "Transaksi Anyar", "see_all": "Tingali sadayana", "no_tx": "Teu acan aya transaksi.", "account_settings": "Setélan Rekening", "log_out": "Kaluar", "card_status": "Status Kartu", "freeze_card": "Bekukeun Kartu", "view_cvv": "Tingali CVV", "download_stmt": "Undeur Pernyataan", "get_pdf": "Meunangkeun rékaman PDF anjeun", "download": "Undeur", "bank_name": "Ngaran bank", "account_no": "Nomer rekening", "amount": "Jumlah", "withdraw_code": "Kode panarikan", "confirm_transfer": "Konfirmasi Mindahkeun", "funds_sent_to": "Dana bakal dikirim ka rekening bank anu anjeun lebetkeun di handap.", "transfer_processed": "Mindahkeun Diprosés", "funds_sent_msg": "Dana anjeun parantos dikirim. Bisa nyandak sababaraha menit.", "processing": "Ngolah", "processing_msg": "Mindahkeun anjeun nuju diolah kusabab alesan kaamanan.", "do_not_close": "Punten entong tutup halaman ieu.", "welcome_back": "Wilujeng sumping deui", "enter_password": "Lebetkeun kecap akses anjeun pikeun aksés.", "password": "Kecap Akses", "login": "Lebet", "statement": "Pernyataan Rekening", "date": "Tanggal", "account_holder": "Pamilik Rekening", "currency": "Mata Uang", "tx_history": "Sajarah Transaksi", "description": "Katerangan", "ending_balance": "Kasaimbangan Ahir", "stmt_footer": "Ieu mangrupikeun pernyataan anu didamel ku komputer sareng henteu peryogi tanda tangan.", "email_notif": "Bewara Email", "dark_mode": "Mode Poék", "biometrics": "Face ID / Biometrik", "active": "Aktif", "opened": "Dibuka", "completed": "Réngsé", "pending": "Ngantosan", "unopened": "Henteu dibuka", "transfer_to": "Mindahkeun ka", "just_now": "Ayeuna", "success": "Suksés", "verifying": "ngécéskeun…", "premium": "Premium", "today": "Ayeuna", "yesterday": "Kamari", "from": "Ti", "to": "Ka"},
    "sw": {"dashboard": "Dashibodi", "history": "Historia", "transfer": "Uhamisho", "cards": "Vault", "settings": "Mipangilio", "total_balance": "Jumla ya Salio", "account_number": "Nambari ya Akaunti", "send_money": "Tuma Pesa", "recent_tx": "Miamala ya Hivi Karibuni", "see_all": "Tazama zote", "no_tx": "Hakuna miamala bado.", "account_settings": "Mipangilio ya Akaunti", "log_out": "Toka", "card_status": "Hali ya Kadi", "freeze_card": "Gandisha Kadi", "view_cvv": "Tazama CVV", "download_stmt": "Pakua Taarifa", "get_pdf": "Pata rekodi yako ya PDF", "download": "Pakua", "bank_name": "Jina la benki", "account_no": "Nambari ya akaunti", "amount": "Kiasi", "withdraw_code": "Msimbo wa kutoa", "confirm_transfer": "Thibitisha Uhamisho", "funds_sent_to": "Fedha zitatumwa kwenye akaunti ya benki unayoweka hapa chini.", "transfer_processed": "Uhamisho Umesindika", "funds_sent_msg": "Fedha zako zimetumwa. Inaweza kuchukua dakika chache.", "processing": "Inachakata", "processing_msg": "Uhamisho wako unachakatwa kwa sababu za usalama.", "do_not_close": "Tafadhali usifunge ukurasa huu.", "welcome_back": "Karibu tena", "enter_password": "Weka nenosiri lako ili kufikia.", "password": "Nenosiri", "login": "Ingia", "statement": "Taarifa ya Akaunti", "date": "Tarehe", "account_holder": "Mmiliki wa Akaunti", "currency": "Sarafu", "tx_history": "Historia ya Miamala", "description": "Maelezo", "ending_balance": "Salio la Mwisho", "stmt_footer": "Hii ni taarifa iliyozalishwa na kompyuta na haitaji sahihi.", "email_notif": "Arifa za Barua Pepe", "dark_mode": "Hali ya Giza", "biometrics": "Face ID / Biometria", "active": "Hai", "opened": "Imefunguliwa", "completed": "Imekamilika", "pending": "Inasubiri", "unopened": "Haijafunguliwa", "transfer_to": "Hamisha kwa", "just_now": "Sasa hivi", "success": "Mafanikio", "verifying": "inathibitisha…", "premium": "Premium", "today": "Leo", "yesterday": "Jana", "from": "Kutoka", "to": "Kwa"},
    "sv": {"dashboard": "Instrumentpanel", "history": "Historik", "transfer": "Överföring", "cards": "Valv", "settings": "Inställningar", "total_balance": "Totalt Saldo", "account_number": "Kontonummer", "send_money": "Skicka Pengar", "recent_tx": "Senaste Transaktioner", "see_all": "Se alla", "no_tx": "Inga transaktioner ännu.", "account_settings": "Kontoinställningar", "log_out": "Logga ut", "card_status": "Kortstatus", "freeze_card": "Frys Kortet", "view_cvv": "Visa CVV", "download_stmt": "Ladda ner Kontoutdrag", "get_pdf": "Hämta din PDF-post", "download": "Ladda ner", "bank_name": "Banknamn", "account_no": "Kontonummer", "amount": "Belopp", "withdraw_code": "Uttagskod", "confirm_transfer": "Bekräfta Överföring", "funds_sent_to": "Pengarna skickas till bankkontot du anger nedan.", "transfer_processed": "Överföring Behandlad", "funds_sent_msg": "Dina pengar har skickats. Det kan ta några minuter.", "processing": "Bearbetar", "processing_msg": "Din överföring bearbetas av säkerhetsskäl.", "do_not_close": "Stäng inte den här sidan.", "welcome_back": "Välkommen tillbaka", "enter_password": "Ange ditt lösenord för åtkomst.", "password": "Lösenord", "login": "Logga in", "statement": "Kontoutdrag", "date": "Datum", "account_holder": "Kontoinnehavare", "currency": "Valuta", "tx_history": "Transaktionshistorik", "description": "Beskrivning", "ending_balance": "Slutsaldo", "stmt_footer": "Detta är ett datorgenererat utdrag och kräver ingen signatur.", "email_notif": "E-postaviseringar", "dark_mode": "Mörkt Läge", "biometrics": "Face ID / Biometri", "active": "Aktiv", "opened": "Öppnad", "completed": "Slutförd", "pending": "Väntar", "unopened": "Oöppnad", "transfer_to": "Överföring till", "just_now": "Just nu", "success": "Framgång", "verifying": "verifierar…", "premium": "Premium", "today": "Idag", "yesterday": "Igår", "from": "Från", "to": "Till"},
    "tg": {"dashboard": "Лавҳа", "history": "Таърих", "transfer": "Интиқол", "cards": "Хазина", "settings": "Танзимотҳо", "total_balance": "Бақияи Умумӣ", "account_number": "Рақами Ҳисоб", "send_money": "Ирсоли Пул", "recent_tx": "Муомилаоти Охирин", "see_all": "Дидани ҳама", "no_tx": "Ҳанӯз муомилаот нест.", "account_settings": "Танзимоти Ҳисоб", "log_out": "Баромадан", "card_status": "Ҳолати Корт", "freeze_card": "Кортро Яхкунондан", "view_cvv": "Дидани CVV", "download_stmt": "Боргирии Ҳисобот", "get_pdf": "Сабти PDF-и худро гиред", "download": "Боргирӣ", "bank_name": "Номи бонк", "account_no": "Рақами ҳисоб", "amount": "Маблағ", "withdraw_code": "Рамзи баровардан", "confirm_transfer": "Тасдиқи Интиқол", "funds_sent_to": "Маблағ ба ҳисоби бонкии дар поён воридкардаатон фиристода мешавад.", "transfer_processed": "Интиқол Коркард Шуд", "funds_sent_msg": "Маблағи шумо фиристода шуд. Ин метавонад чанд дақиқа вақт гирад.", "processing": "Коркард", "processing_msg": "Интиқоли шумо бо сабабҳои амниятӣ коркард мешавад.", "do_not_close": "Лутфан ин саҳифаро напӯшед.", "welcome_back": "Хуш омадед", "enter_password": "Барои дастрасӣ рамзи худро ворид кунед.", "password": "Рамз", "login": "Даромадан", "statement": "Ҳисоботи Ҳисоб", "date": "Сана", "account_holder": "Соҳиби Ҳисоб", "currency": "Асъор", "tx_history": "Таърихи Муомилаот", "description": "Тавсиф", "ending_balance": "Бақияи Ниҳоӣ", "stmt_footer": "Ин ҳисоботи компютерӣ мебошад ва имзо талаб намекунад.", "email_notif": "Огоҳиномаҳои Email", "dark_mode": "Ҳолати Торик", "biometrics": "Face ID / Биометрия", "active": "Фаъол", "opened": "Кушода", "completed": "Анҷомёфта", "pending": "Дар интизорӣ", "unopened": "Кушоданашуда", "transfer_to": "Интиқол ба", "just_now": "Ҳозир", "success": "Муваффақият", "verifying": "тафтиш…", "premium": "Премиум", "today": "Имрӯз", "yesterday": "Дирӯз", "from": "Аз", "to": "Ба"},
    "ta": {"dashboard": "டாஷ்போர்டு", "history": "வரலாறு", "transfer": "பணப் பரிமாற்றம்", "cards": "பெட்டகம்", "settings": "அமைப்புகள்", "total_balance": "மொத்த இருப்பு", "account_number": "கணக்கு எண்", "send_money": "பணம் அனுப்பு", "recent_tx": "சமீபத்திய பரிவர்த்தனைகள்", "see_all": "அனைத்தையும் பார்", "no_tx": "இன்னும் பரிவர்த்தனைகள் இல்லை.", "account_settings": "கணக்கு அமைப்புகள்", "log_out": "வெளியேறு", "card_status": "அட்டை நிலை", "freeze_card": "அட்டையை முடக்கு", "view_cvv": "CVV பார்", "download_stmt": "அறிக்கையைப் பதிவிறக்கு", "get_pdf": "உங்கள் PDF பதிவைப் பெறுங்கள்", "download": "பதிவிறக்கு", "bank_name": "வங்கியின் பெயர்", "account_no": "கணக்கு எண்", "amount": "தொகை", "withdraw_code": "பணம் எடுக்கும் குறியீடு", "confirm_transfer": "பரிமாற்றத்தை உறுதிப்படுத்து", "funds_sent_to": "நீங்கள் கீழே உள்ளிடும் வங்கிக் கணக்கிற்கு பணம் அனுப்பப்படும்.", "transfer_processed": "பரிமாற்றம் செயலாக்கப்பட்டது", "funds_sent_msg": "உங்கள் பணம் அனுப்பப்பட்டது. சில நிமிடங்கள் ஆகலாம்.", "processing": "செயலாக்கப்படுகிறது", "processing_msg": "பாதுகாப்பு காரணங்களுக்காக உங்கள் பரிமாற்றம் செயலாக்கப்படுகிறது.", "do_not_close": "இந்தப் பக்கத்தை மூட வேண்டாம்.", "welcome_back": "மீண்டும் வருக", "enter_password": "அணுக உங்கள் கடவுச்சொல்லை உள்ளிடவும்.", "password": "கடவுச்சொல்", "login": "உள்நுழைக", "statement": "கணக்கு அறிக்கை", "date": "தேதி", "account_holder": "கணக்கு வைத்திருப்பவர்", "currency": "நாணயம்", "tx_history": "பரிவர்த்தனை வரலாறு", "description": "விளக்கம்", "ending_balance": "இறுதி இருப்பு", "stmt_footer": "இது கணினியால் உருவாக்கப்பட்ட அறிக்கை, கையொப்பம் தேவையில்லை.", "email_notif": "மின்னஞ்சல் அறிவிப்புகள்", "dark_mode": "இருண்ட பயன்முறை", "biometrics": "Face ID / பயோமெட்ரிக்ஸ்", "active": "செயலில்", "opened": "திறக்கப்பட்டது", "completed": "முடிந்தது", "pending": "நிலுவையில்", "unopened": "திறக்கப்படவில்லை", "transfer_to": "இதற்கு மாற்று", "just_now": "இப்போது", "success": "வெற்றி", "verifying": "சரிபார்க்கிறது…", "premium": "பிரீமியம்", "today": "இன்று", "yesterday": "நேற்று", "from": "இருந்து", "to": "க்கு"},
    "tt": {"dashboard": "Панель", "history": "Тарих", "transfer": "Күчерү", "cards": "Сейф", "settings": "Көйләүләр", "total_balance": "Гомуми Баланс", "account_number": "Хисап Номеры", "send_money": "Акча Җибәрү", "recent_tx": "Соңгы Транзакцияләр", "see_all": "Барысын да карау", "no_tx": "Әлегә транзакцияләр юк.", "account_settings": "Хисап Көйләүләре", "log_out": "Чыгу", "card_status": "Карта Статусы", "freeze_card": "Картаны Туңдыру", "view_cvv": "CVV Карау", "download_stmt": "Өземне Йөкләү", "get_pdf": "PDF язмаңызны алыгыз", "download": "Йөкләү", "bank_name": "Банк исеме", "account_no": "Хисап номеры", "amount": "Сумма", "withdraw_code": "Алу Коды", "confirm_transfer": "Күчерүне Раслау", "funds_sent_to": "Акча түбәндә күрсәтелгән банк хисабыгызга җибәреләчәк.", "transfer_processed": "Күчерү Эшкәртелде", "funds_sent_msg": "Акчагыз җибәрелде. Берничә минут вакыт алырга мөмкин.", "processing": "Эшкәртү", "processing_msg": "Күчерүегез иминлек сәбәпләре буенча эшкәртелә.", "do_not_close": "Зинһар, бу битне япмагыз.", "welcome_back": "Кайтуыгыз белән", "enter_password": "Керү өчен серсүзегезне керетегез.", "password": "Серсүз", "login": "Керү", "statement": "Хисап Өземе", "date": "Дата", "account_holder": "Хисап Хуҗасы", "currency": "Валюта", "tx_history": "Транзакцияләр Тарихы", "description": "Тасвирлама", "ending_balance": "Соңгы Баланс", "stmt_footer": "Бу компьютерда ясалган өзем һәм имза таләп итми.", "email_notif": "Электрон Почта Хәбәрләре", "dark_mode": "Караңгы Режим", "biometrics": "Face ID / Биометрия", "active": "Актив", "opened": "Ачылды", "completed": "Тәмамланды", "pending": "Көтүдә", "unopened": "Ачылмаган", "transfer_to": "Күчерү", "just_now": "Хәзер", "success": "Уңыш", "verifying": "тикшерү…", "premium": "Премиум", "today": "Бүген", "yesterday": "Кичә", "from": "Кемнән", "to": "Кемгә"},
    "te": {"dashboard": "డాష్‌బోర్డ్", "history": "చరిత్ర", "transfer": "బదిలీ", "cards": "వాల్ట్", "settings": "సెట్టింగ్‌లు", "total_balance": "మొత్తం బ్యాలెన్స్", "account_number": "ఖాతా సంఖ్య", "send_money": "డబ్బు పంపండి", "recent_tx": "ఇటీవలి లావాదేవీలు", "see_all": "అన్నీ చూడండి", "no_tx": "ఇంకా లావాదేవీలు లేవు.", "account_settings": "ఖాతా సెట్టింగ్‌లు", "log_out": "లాగ్ అవుట్", "card_status": "కార్డ్ స్థితి", "freeze_card": "కార్డ్ ఫ్రీజ్ చేయండి", "view_cvv": "CVV చూడండి", "download_stmt": "స్టేట్‌మెంట్ డౌన్‌లోడ్ చేయండి", "get_pdf": "మీ PDF రికార్డును పొందండి", "download": "డౌన్‌లోడ్", "bank_name": "బ్యాంకు పేరు", "account_no": "ఖాతా సంఖ్య", "amount": "మొత్తం", "withdraw_code": "ఉపసంహరణ కోడ్", "confirm_transfer": "బదిలీని నిర్ధారించండి", "funds_sent_to": "మీరు క్రింద నమోదు చేసిన బ్యాంకు ఖాతాకు నిధులు పంపబడతాయి.", "transfer_processed": "బదిలీ ప్రాసెస్ చేయబడింది", "funds_sent_msg": "మీ నిధులు పంపబడ్డాయి. కొన్ని నిమిషాలు పట్టవచ్చు.", "processing": "ప్రాసెసింగ్", "processing_msg": "భద్రతా కారణాల దృష్ట్యా మీ బదిలీ ప్రాసెస్ చేయబడుతోంది.", "do_not_close": "దయచేసి ఈ పేజీని మూసివేయవద్దు.", "welcome_back": "తిరిగి స్వాగతం", "enter_password": "యాక్సెస్ చేయడానికి మీ పాస్‌వర్డ్‌ను నమోదు చేయండి.", "password": "పాస్‌వర్డ్", "login": "లాగిన్", "statement": "ఖాతా స్టేట్‌మెంట్", "date": "తేదీ", "account_holder": "ఖాతాదారు", "currency": "కరెన్సీ", "tx_history": "లావాదేవీల చరిత్ర", "description": "వివరణ", "ending_balance": "ముగింపు బ్యాలెన్స్", "stmt_footer": "ఇది కంప్యూటర్ రూపొందించిన స్టేట్‌మెంట్ మరియు సంతకం అవసరం లేదు.", "email_notif": "ఇమెయిల్ నోటిఫికేషన్‌లు", "dark_mode": "డార్క్ మోడ్", "biometrics": "ఫేస్ ఐడీ / బయోమెట్రిక్స్", "active": "క్రియాశీలం", "opened": "తెరవబడింది", "completed": "పూర్తయింది", "pending": "పెండింగ్‌లో ఉంది", "unopened": "తెరవబడలేదు", "transfer_to": "బదిలీ చేయండి", "just_now": "ఇప్పుడే", "success": "విజయం", "verifying": "ధృవీకరిస్తోంది…", "premium": "ప్రీమియం", "today": "నేడు", "yesterday": "నిన్న", "from": "నుండి", "to": "కి"},
    "tr": {"dashboard": "Panel", "history": "Geçmiş", "transfer": "Transfer", "cards": "Kasa", "settings": "Ayarlar", "total_balance": "Toplam Bakiye", "account_number": "Hesap Numarası", "send_money": "Para Gönder", "recent_tx": "Son İşlemler", "see_all": "Tümünü gör", "no_tx": "Henüz işlem yok.", "account_settings": "Hesap Ayarları", "log_out": "Çıkış Yap", "card_status": "Kart Durumu", "freeze_card": "Kartı Dondur", "view_cvv": "CVV Görüntüle", "download_stmt": "Ekstre İndir", "get_pdf": "PDF kaydınızı alın", "download": "İndir", "bank_name": "Banka adı", "account_no": "Hesap numarası", "amount": "Miktar", "withdraw_code": "Para çekme kodu", "confirm_transfer": "Transferi Onayla", "funds_sent_to": "Para, aşağıda girdiğiniz banka hesabına gönderilecektir.", "transfer_processed": "Transfer İşlendi", "funds_sent_msg": "Paranız gönderildi. Yansıması birkaç dakika sürebilir.", "processing": "İşleniyor", "processing_msg": "Transferiniz güvenlik nedeniyle işleniyor.", "do_not_close": "Lütfen bu sayfayı kapatmayın.", "welcome_back": "Tekrar hoş geldiniz", "enter_password": "Erişim için şifrenizi girin.", "password": "Şifre", "login": "Giriş Yap", "statement": "Hesap Ekstresi", "date": "Tarih", "account_holder": "Hesap Sahibi", "currency": "Para Birimi", "tx_history": "İşlem Geçmişi", "description": "Açıklama", "ending_balance": "Bitiş Bakiyesi", "stmt_footer": "Bu bilgisayar tarafından oluşturulmuş bir ekstredir ve imza gerektirmez.", "email_notif": "E-posta Bildirimleri", "dark_mode": "Karanlık Mod", "biometrics": "Face ID / Biyometri", "active": "Aktif", "opened": "Açıldı", "completed": "Tamamlandı", "pending": "Beklemede", "unopened": "Açılmadı", "transfer_to": "Şuraya transfer et", "just_now": "Az önce", "success": "Başarılı", "verifying": "doğrulanıyor…", "premium": "Premium", "today": "Bugün", "yesterday": "Dün", "from": "Kimden", "to": "Kime"},
    "tk": {"dashboard": "Panel", "history": "Taryh", "transfer": "Geçirim", "cards": "Seýf", "settings": "Sazlamalar", "total_balance": "Jemi Balans", "account_number": "Hasap Belgisi", "send_money": "Pul Iber", "recent_tx": "Soňky Geçirimler", "see_all": "Hemmesini gör", "no_tx": "Häzirlikçe geçirim ýok.", "account_settings": "Hasap Sazlamalary", "log_out": "Çykyş", "card_status": "Kart Ýagdaýy", "freeze_card": "Karty Doňdur", "view_cvv": "CVV Gör", "download_stmt": "Hasabatyny Ýükle", "get_pdf": "PDF ýazgyňyzy alyň", "download": "Ýükle", "bank_name": "Bank ady", "account_no": "Hasap belgisi", "amount": "Mukdary", "withdraw_code": "Pul çykarmak kody", "confirm_transfer": "Geçirimi Tassykla", "funds_sent_to": "Pul aşakda girizen bank hasabyňyza iberiler.", "transfer_processed": "Geçirim Işlendi", "funds_sent_msg": "Puluňyz iberildi. Birnäçe minut dowam edip biler.", "processing": "Işlenýär", "processing_msg": "Geçirimiňiz howpsuzlyk sebäpli işlenýär.", "do_not_close": "Sahypany ýapmaň.", "welcome_back": "Täzeden hoş geldiňiz", "enter_password": "Girmek üçin parolyňyzy giriziň.", "password": "Parol", "login": "Gir", "statement": "Hasap Hasabaty", "date": "Sene", "account_holder": "Hasap Eýesi", "currency": "Walýuta", "tx_history": "Geçirim Taryhy", "description": "Düşündiriş", "ending_balance": "Ahyrky Balans", "stmt_footer": "Bu kompýuter tarapyndan döredilen hasabat we gol çekmegi talap etmeýär.", "email_notif": "E-poçta Habarnamalary", "dark_mode": "Garaňky Režim", "biometrics": "Face ID / Biometriýa", "active": "Işjeň", "opened": "Açyldy", "completed": "Tamamlandy", "pending": "Garaşylýar", "unopened": "Açylmadyk", "transfer_to": "Şu ýere geçir", "just_now": "Häzir", "success": "Üstünlik", "verifying": "barlanýar…", "premium": "Premium", "today": "Şu gün", "yesterday": "Düýn", "from": "Kimden", "to": "Kime"},
    "uk": {"dashboard": "Панель", "history": "Історія", "transfer": "Переказ", "cards": "Сховище", "settings": "Налаштування", "total_balance": "Загальний Баланс", "account_number": "Номер Рахунку", "send_money": "Надіслати Гроші", "recent_tx": "Останні Транзакції", "see_all": "Переглянути все", "no_tx": "Транзакцій ще немає.", "account_settings": "Налаштування Рахунку", "log_out": "Вийти", "card_status": "Статус Картки", "freeze_card": "Заморозити Картку", "view_cvv": "Переглянути CVV", "download_stmt": "Завантажити Виписку", "get_pdf": "Отримати PDF-запис", "download": "Завантажити", "bank_name": "Назва банку", "account_no": "Номер рахунку", "amount": "Сума", "withdraw_code": "Код зняття", "confirm_transfer": "Підтвердити Переказ", "funds_sent_to": "Кошти будуть надіслані на банківський рахунок, який ви введете нижче.", "transfer_processed": "Переказ Оброблено", "funds_sent_msg": "Ваші кошти надіслано. Це може зайняти кілька хвилин.", "processing": "Обробка", "processing_msg": "Ваш переказ обробляється з міркувань безпеки.", "do_not_close": "Будь ласка, не закривайте цю сторінку.", "welcome_back": "З поверненням", "enter_password": "Введіть пароль для доступу до рахунку.", "password": "Пароль", "login": "Увійти", "statement": "Виписка по Рахунку", "date": "Дата", "account_holder": "Власник Рахунку", "currency": "Валюта", "tx_history": "Історія Транзакцій", "description": "Опис", "ending_balance": "Кінцевий Баланс", "stmt_footer": "Це виписка, створена комп'ютером, і вона не потребує підпису.", "email_notif": "Сповіщення Електронною Поштою", "dark_mode": "Темний Режим", "biometrics": "Face ID / Біометрія", "active": "Активний", "opened": "Відкрито", "completed": "Завершено", "pending": "В очікуванні", "unopened": "Не відкрито", "transfer_to": "Переказ на", "just_now": "Щойно", "success": "Успіх", "verifying": "перевірка…", "premium": "Преміум", "today": "Сьогодні", "yesterday": "Вчора", "from": "Від", "to": "Кому"},
    "ur": {"dashboard": "ڈیش بورڈ", "history": "تاریخ", "transfer": "منتقلی", "cards": "والٹ", "settings": "ترتیبات", "total_balance": "کل بیلنس", "account_number": "اکاؤنٹ نمبر", "send_money": "پیسے بھیجیں", "recent_tx": "حالیہ لین دین", "see_all": "سب دیکھیں", "no_tx": "ابھی تک کوئی لین دین نہیں ہے۔", "account_settings": "اکاؤنٹ کی ترتیبات", "log_out": "لاگ آؤٹ", "card_status": "کارڈ کی حیثیت", "freeze_card": "کارڈ منجمد کریں", "view_cvv": "CVV دیکھیں", "download_stmt": "بیان ڈاؤن لوڈ کریں", "get_pdf": "اپنا PDF ریکارڈ حاصل کریں", "download": "ڈاؤن لوڈ کریں", "bank_name": "بینک کا نام", "account_no": "اکاؤنٹ نمبر", "amount": "رقم", "withdraw_code": "نکالنے کا کوڈ", "confirm_transfer": "منتقلی کی تصدیق کریں", "funds_sent_to": "رقم اس بینک اکاؤنٹ میں بھیجی جائے گی جو آپ نیچے درج کریں گے۔", "transfer_processed": "منتقلی پر کارروائی ہو گئی", "funds_sent_msg": "آپ کی رقم بھیج دی گئی ہے۔ اس میں کچھ منٹ لگ سکتے ہیں۔", "processing": "کارروائی ہو رہی ہے", "processing_msg": "حفاظتی وجوہات کی بنا پر آپ کی منتقلی پر کارروائی ہو رہی ہے۔", "do_not_close": "براہ کرم یہ صفحہ بند نہ کریں۔", "welcome_back": "خوش آمدید", "enter_password": "رسائی کے لیے اپنا پاس ورڈ درج کریں۔", "password": "پاس ورڈ", "login": "لاگ ان کریں", "statement": "اکاؤنٹ کا بیان", "date": "تاریخ", "account_holder": "اکاؤنٹ ہولڈر", "currency": "کرنسی", "tx_history": "لین دین کی تاریخ", "description": "تفصیل", "ending_balance": "اختتامی بیلنس", "stmt_footer": "یہ کمپیوٹر کے ذریعے تیار کردہ بیان ہے اور اس پر دستخط کی ضرورت نہیں ہے۔", "email_notif": "ای میل اطلاعات", "dark_mode": "ڈارک موڈ", "biometrics": "فیس آئی ڈی / بائیو میٹرکس", "active": "فعال", "opened": "کھول دیا گیا", "completed": "مکمل ہو گیا", "pending": "زیر التواء", "unopened": "نہیں کھولا گیا", "transfer_to": "منتقل کریں", "just_now": "ابھی", "success": "کامیابی", "verifying": "تصدیق ہو رہی ہے…", "premium": "پریمیم", "today": "آج", "yesterday": "کل", "from": "سے", "to": "کو"},
    "ug": {"dashboard": "باشقۇرۇش تاختىسى", "history": "تارىخ", "transfer": "يۆتكەش", "cards": "ئامبار", "settings": "تەڭشەكلەر", "total_balance": "ئومۇمىي قالدۇق", "account_number": "ھېسابات نومۇرى", "send_money": "پۇل ئەۋەتىش", "recent_tx": "يېقىنقى سودىلار", "see_all": "ھەممىنى كۆرۈش", "no_tx": "تېخى سودا يوق.", "account_settings": "ھېسابات تەڭشەكلىرى", "log_out": "چېكىنىش", "card_status": "كارتا ھالىتى", "freeze_card": "كارتا توختىتىش", "view_cvv": "CVV كۆرۈش", "download_stmt": "ھېساباتنى چۈشۈرۈش", "get_pdf": "PDF خاتىرىڭىزنى ئېلىڭ", "download": "چۈشۈرۈش", "bank_name": "بانكا ئىسمى", "account_no": "ھېسابات نومۇرى", "amount": "سومما", "withdraw_code": "ئېلىش كودى", "confirm_transfer": "يۆتكەشنى جەزملەشتۈرۈش", "funds_sent_to": "پۇل تۆۋەندە كىرگۈزگەن بانكا ھېساباتىڭىزغا ئەۋەتىلىدۇ.", "transfer_processed": "يۆتكەش بىر تەرەپ قىلىندى", "funds_sent_msg": "پۇلىڭىز ئەۋەتىلدى. بىر نەچچە مىنۇت ئېلىشى مۇمكىن.", "processing": "بىر تەرەپ قىلىنىۋاتىدۇ", "processing_msg": "يۆتكىلىشىڭىز بىخەتەرلىك سەۋەبىدىن بىر تەرەپ قىلىنىۋاتىدۇ.", "do_not_close": "بۇ بەتنى تاقىماڭ.", "welcome_back": "قايتىپ كەلگىنىڭىزگە مەرھابا", "enter_password": "كىرىش ئۈچۈن پارولىڭىزنى كىرگۈزۈڭ.", "password": "پارول", "login": "كىرىش", "statement": "ھېسابات ئەھۋالى", "date": "چېسلا", "account_holder": "ھېسابات ئىگىسى", "currency": "پۇل بىرلىكى", "tx_history": "سودا تارىخى", "description": "چۈشەندۈرۈش", "ending_balance": "ئاخىرقى قالدۇق", "stmt_footer": "بۇ كومپيۇتېر تەرىپىدىن قۇرۇلغان ھېسابات بولۇپ، ئىمزا تەلەپ قىلمايدۇ.", "email_notif": "ئېلخەت ئۇقتۇرۇشى", "dark_mode": "قاراڭغۇ ھالەت", "biometrics": "Face ID / بىيومېترىكا", "active": "ئاكتىپ", "opened": "ئېچىلدى", "completed": "تاماملاندى", "pending": "ساقلىنىۋاتىدۇ", "unopened": "ئېچىلمىدى", "transfer_to": "يۆتكەش", "just_now": "ھازىر", "success": "مۇۋەپپەقىيەت", "verifying": "دەلىللەۋاتىدۇ…", "premium": "ئالىي", "today": "بۈگۈن", "yesterday": "تۈنۈگۈن", "from": "دىن", "to": "گە"},
    "uz": {"dashboard": "Boshqaruv paneli", "history": "Tarix", "transfer": "O'tkazma", "cards": "Seyf", "settings": "Sozlamalar", "total_balance": "Umumiy Balans", "account_number": "Hisob Raqami", "send_money": "Pul Yuborish", "recent_tx": "So'nggi Tranzaksiyalar", "see_all": "Barchasini ko'rish", "no_tx": "Hali tranzaksiyalar yo'q.", "account_settings": "Hisob Sozlamalari", "log_out": "Chiqish", "card_status": "Karta Holati", "freeze_card": "Kartani Muzlatish", "view_cvv": "CVV Ko'rish", "download_stmt": "Hisobni Yuklab Olish", "get_pdf": "PDF yozuvingizni oling", "download": "Yuklab olish", "bank_name": "Bank nomi", "account_no": "Hisob raqami", "amount": "Miqdor", "withdraw_code": "Pul yechish kodi", "confirm_transfer": "O'tkazmani Tasdiqlash", "funds_sent_to": "Mablag' quyida kiritgan bank hisobingizga yuboriladi.", "transfer_processed": "O'tkazma Amalga Oshirildi", "funds_sent_msg": "Mablag'ingiz yuborildi. Bu bir necha daqiqa vaqt olishi mumkin.", "processing": "Qayta ishlanmoqda", "processing_msg": "O'tkazmangiz xavfsizlik sababli qayta ishlanmoqda.", "do_not_close": "Iltimos, bu sahifani yopmang.", "welcome_back": "Xush kelibsiz", "enter_password": "Kirish uchun parolingizni kiriting.", "password": "Parol", "login": "Kirish", "statement": "Hisob Bayonoti", "date": "Sana", "account_holder": "Hisob Egasi", "currency": "Valyuta", "tx_history": "Tranzaksiyalar Tarixi", "description": "Tavsif", "ending_balance": "Yakuniy Balans", "stmt_footer": "Bu kompyuter tomonidan yaratilgan bayonot va imzo talab qilmaydi.", "email_notif": "Elektron Pochta Bildirishnomalari", "dark_mode": "Qorong'u Rejim", "biometrics": "Face ID / Biometriya", "active": "Faol", "opened": "Ochildi", "completed": "Tugallandi", "pending": "Kutilmoqda", "unopened": "Ochilmagan", "transfer_to": "O'tkazish", "just_now": "Hozir", "success": "Muvaffaqiyat", "verifying": "tekshirilmoqda…", "premium": "Premium", "today": "Bugun", "yesterday": "Kecha", "from": "Kimdan", "to": "Kimga"},
    "vi": {"dashboard": "Bảng điều khiển", "history": "Lịch sử", "transfer": "Chuyển khoản", "cards": "Két sắt", "settings": "Cài đặt", "total_balance": "Tổng số dư", "account_number": "Số tài khoản", "send_money": "Gửi tiền", "recent_tx": "Giao dịch gần đây", "see_all": "Xem tất cả", "no_tx": "Chưa có giao dịch nào.", "account_settings": "Cài đặt tài khoản", "log_out": "Đăng xuất", "card_status": "Trạng thái thẻ", "freeze_card": "Đóng băng thẻ", "view_cvv": "Xem CVV", "download_stmt": "Tải sao kê", "get_pdf": "Nhận bản ghi PDF của bạn", "download": "Tải xuống", "bank_name": "Tên ngân hàng", "account_no": "Số tài khoản", "amount": "Số tiền", "withdraw_code": "Mã rút tiền", "confirm_transfer": "Xác nhận chuyển khoản", "funds_sent_to": "Tiền sẽ được gửi đến tài khoản ngân hàng bạn nhập bên dưới.", "transfer_processed": "Đã xử lý chuyển khoản", "funds_sent_msg": "Tiền của bạn đã được gửi. Có thể mất vài phút để hiển thị.", "processing": "Đang xử lý", "processing_msg": "Giao dịch của bạn đang được xử lý vì lý do bảo mật.", "do_not_close": "Vui lòng không đóng trang này.", "welcome_back": "Chào mừng trở lại", "enter_password": "Nhập mật khẩu để truy cập.", "password": "Mật khẩu", "login": "Đăng nhập", "statement": "Sao kê tài khoản", "date": "Ngày", "account_holder": "Chủ tài khoản", "currency": "Tiền tệ", "tx_history": "Lịch sử giao dịch", "description": "Mô tả", "ending_balance": "Số dư cuối kỳ", "stmt_footer": "Đây là sao kê do máy tính tạo ra và không cần chữ ký.", "email_notif": "Thông báo Email", "dark_mode": "Chế độ tối", "biometrics": "Face ID / Sinh trắc học", "active": "Hoạt động", "opened": "Đã mở", "completed": "Hoàn thành", "pending": "Đang chờ", "unopened": "Chưa mở", "transfer_to": "Chuyển đến", "just_now": "Vừa xong", "success": "Thành công", "verifying": "đang xác minh…", "premium": "Cao cấp", "today": "Hôm nay", "yesterday": "Hôm qua", "from": "Từ", "to": "Đến"},
    "cy": {"dashboard": "Dangosfwrdd", "history": "Hanes", "transfer": "Trosglwyddo", "cards": "Claddgell", "settings": "Gosodiadau", "total_balance": "Cyfanswm Balans", "account_number": "Rhif Cyfrif", "send_money": "Anfon Arian", "recent_tx": "Trafodion Diweddar", "see_all": "Gweld popeth", "no_tx": "Dim trafodion eto.", "account_settings": "Gosodiadau Cyfrif", "log_out": "Allgofnodi", "card_status": "Statws Cerdyn", "freeze_card": "Rhewi Cerdyn", "view_cvv": "Gweld CVV", "download_stmt": "Lawrlwytho Datganiad", "get_pdf": "Cael eich cofnod PDF", "download": "Lawrlwytho", "bank_name": "Enw'r banc", "account_no": "Rhif cyfrif", "amount": "Swm", "withdraw_code": "Cod tynnu", "confirm_transfer": "Cadarnhau Trosglwyddiad", "funds_sent_to": "Bydd yr arian yn cael ei anfon i'r cyfrif banc rydych chi'n ei nodi isod.", "transfer_processed": "Trosglwyddiad Wedi'i Brosesu", "funds_sent_msg": "Mae eich arian wedi'i anfon. Gall gymryd ychydig funudau.", "processing": "Prosesu", "processing_msg": "Mae eich trosglwyddiad yn cael ei brosesu am resymau diogelwch.", "do_not_close": "Peidiwch â chau'r dudalen hon.", "welcome_back": "Croeso nôl", "enter_password": "Nodwch eich cyfrinair i gael mynediad.", "password": "Cyfrinair", "login": "Mewngofnodi", "statement": "Datganiad Cyfrif", "date": "Dyddiad", "account_holder": "Deiliad Cyfrif", "currency": "Arian Cyfred", "tx_history": "Hanes Trafodion", "description": "Disgrifiad", "ending_balance": "Balans Terfynol", "stmt_footer": "Mae hwn yn ddatganiad a gynhyrchwyd gan gyfrifiadur ac nid oes angen llofnod.", "email_notif": "Hysbysiadau E-bost", "dark_mode": "Modd Tywyll", "biometrics": "Face ID / Biometreg", "active": "Gweithredol", "opened": "Wedi'i agor", "completed": "Wedi'i gwblhau", "pending": "Yn aros", "unopened": "Heb ei agor", "transfer_to": "Trosglwyddo i", "just_now": "Nawr", "success": "Llwyddiant", "verifying": "yn gwirio…", "premium": "Premium", "today": "Heddiw", "yesterday": "Ddoe", "from": "O", "to": "I"},
    "xh": {"dashboard": "Ideshibhodi", "history": "Imbali", "transfer": "Ukudlulisa", "cards": "Ivault", "settings": "Iisetingi", "total_balance": "Ibhalansi Iyonke", "account_number": "Inombolo yeAkhawunti", "send_money": "Thumela Imali", "recent_tx": "Iintengiselwano zamva nje", "see_all": "Jonga konke", "no_tx": "Azikho iintengiselwano okwangoku.", "account_settings": "Iisetingi zeAkhawunti", "log_out": "Phuma", "card_status": "Ubume beKhadi", "freeze_card": "Misa iKhadi", "view_cvv": "Jonga i-CVV", "download_stmt": "Khuphela iSitatimenti", "get_pdf": "Fumana irekhodi yakho ye-PDF", "download": "Khuphela", "bank_name": "Igama lebhanki", "account_no": "Inombolo yeakhawunti", "amount": "Isixa", "withdraw_code": "Ikhowudi yokutsala", "confirm_transfer": "Qinisekisa uKudlulisa", "funds_sent_to": "Imali iya kuthunyelwa kwiakhawunti yebhanki oyifaka ngezantsi.", "transfer_processed": "Ukudlulisa Kuqhubekile", "funds_sent_msg": "Imali yakho ithunyelwe. Kungathatha imizuzu embalwa.", "processing": "Iyaqhubeka", "processing_msg": "Ukudlulisa kwakho kuyaqhubeka ngenxa yezizathu zokhuseleko.", "do_not_close": "Nceda musa ukuvala eli phepha.", "welcome_back": "Wamkelekile kwakhona", "enter_password": "Faka igama lakho lokugqithisa ukufikelela.", "password": "Igama lokugqithisa", "login": "Ngena", "statement": "Isitatimenti seAkhawunti", "date": "Umhla", "account_holder": "Umnikazi weAkhawunti", "currency": "Imali", "tx_history": "Imbali yeentengiselwano", "description": "Inkcazo", "ending_balance": "Ibhalansi yokugqibela", "stmt_footer": "Esi sisitatimenti esenziwe yikhompyutha kwaye asifuni sayina.", "email_notif": "Izaziso nge-imeyile", "dark_mode": "Imowudi emnyama", "biometrics": "Face ID / Biometrics", "active": "Iyasebenza", "opened": "Ivuliwe", "completed": "Igqityiwe", "pending": "Ilindile", "unopened": "Ayikavulwa", "transfer_to": "Dlulisela ku", "just_now": "Ngoku", "success": "Impumelelo", "verifying": "iyaqinisekisa…", "premium": "Premium", "today": "Namhlanje", "yesterday": "Izolo", "from": "Ukusuka", "to": "Kuya"},
    "yi": {"dashboard": "דאַשבאָרד", "history": "געשיכטע", "transfer": "איבערפירן", "cards": "וואָלץ", "settings": "סעטינגס", "total_balance": "גאַנץ באַלאַנס", "account_number": "חשבון נומער", "send_money": "שיקן געלט", "recent_tx": "לעצטע טראַנזאַקשאַנז", "see_all": "זען אַלץ", "no_tx": "נאָך נישטאָ קיין טראַנזאַקשאַנז.", "account_settings": "חשבון סעטינגס", "log_out": "לאָג אויס", "card_status": "קאָרט סטאַטוס", "freeze_card": "פרירן קאָרט", "view_cvv": "זען CVV", "download_stmt": "אראפקאפיע סטעיטמענט", "get_pdf": "באַקומען דיין PDF רעקאָרד", "download": "אראפקאפיע", "bank_name": "באַנק נאָמען", "account_no": "חשבון נומער", "amount": "סומע", "withdraw_code": "אַרויסנעמען קאָד", "confirm_transfer": "באַשטעטיקן איבערפירן", "funds_sent_to": "געלט וועט ווערן געשיקט צו די באַנק חשבון איר אַרייַן אונטן.", "transfer_processed": "איבערפירן פּראַסעסט", "funds_sent_msg": "דיין געלט איז געשיקט געווארן. עס קען דויערן עטלעכע מינוט.", "processing": "פּראַסעסינג", "processing_msg": "דיין איבערפירן ווערט פּראַסעסט פֿאַר זיכערהייט סיבות.", "do_not_close": "ביטע נישט פֿאַרמאַכן דעם בלאַט.", "welcome_back": "ברוכים הבאים צוריק", "enter_password": "אַרייַן דיין פּאַראָל צו אַקסעס.", "password": "פּאַראָל", "login": "לאָגין", "statement": "חשבון סטעיטמענט", "date": "דאַטע", "account_holder": "חשבון האָלדער", "currency": "וואַלוטע", "tx_history": "טראַנזאַקשאַן געשיכטע", "description": "באַשרייַבונג", "ending_balance": "סאָף באַלאַנס", "stmt_footer": "דאָס איז אַ קאָמפּיוטער-דזשענערייטאַד סטעיטמענט און דאַרף נישט קיין חתימה.", "email_notif": "אימעיל נאָוטאַפאַקיישאַנז", "dark_mode": "טונקל מאָדע", "biometrics": "Face ID / בייאָמעטריקס", "active": "אַקטיוו", "opened": "געעפנט", "completed": "פאַרענדיקט", "pending": "פּענדינג", "unopened": "נישט געעפנט", "transfer_to": "איבערפירן צו", "just_now": "פּונקט איצט", "success": "הצלחה", "verifying": "וועריפייינג…", "premium": "פּרעמיום", "today": "היינט", "yesterday": "נעכטן", "from": "פון", "to": "צו"},
    "zu": {"dashboard": "Ideshibhodi", "history": "Umlando", "transfer": "Ukudlulisa", "cards": "I-Vault", "settings": "Izilungiselelo", "total_balance": "Ibhalansi Ephelele", "account_number": "Inombolo Ye-akhawunti", "send_money": "Thumela Imali", "recent_tx": "Ukuthengiselana Kwamuva", "see_all": "Buka konke", "no_tx": "Akukho ukuthengiselana okwamanje.", "account_settings": "Izilungiselelo Ze-akhawunti", "log_out": "Phuma", "card_status": "Isimo Sekhadi", "freeze_card": "Misa Ikhadi", "view_cvv": "Buka i-CVV", "download_stmt": "Landa Isitatimende", "get_pdf": "Thola irekhodi lakho le-PDF", "download": "Landa", "bank_name": "Igama lebhange", "account_no": "Inombolo ye-akhawunti", "amount": "Inani", "withdraw_code": "Ikhodi yokukhipha", "confirm_transfer": "Qinisekisa Ukudlulisa", "funds_sent_to": "Imali izothunyelwa ku-akhawunti yasebhange oyifaka ngezansi.", "transfer_processed": "Ukudlulisa Kuqediwe", "funds_sent_msg": "Imali yakho ithunyelwe. Kungathatha imizuzu embalwa.", "processing": "Kuyacutshungulwa", "processing_msg": "Ukudlulisa kwakho kuyacutshungulwa ngenxa yezizathu zokuphepha.", "do_not_close": "Sicela ungayivali leli khasi.", "welcome_back": "Siyakwamukela futhi", "enter_password": "Faka iphasiwedi yakho ukuze ufinyelele.", "password": "Iphasiwedi", "login": "Ngena", "statement": "Isitatimende Se-akhawunti", "date": "Usuku", "account_holder": "Umnikazi we-akhawunti", "currency": "Imali", "tx_history": "Umlando Wokuthengiselana", "description": "Incazelo", "ending_balance": "Ibhalansi Yokugcina", "stmt_footer": "Lesi isitatimende esikhiqizwe yikhompyutha futhi asidingi sayina.", "email_notif": "Izaziso ze-imeyili", "dark_mode": "Imodi Emnyama", "biometrics": "Face ID / Biometrics", "active": "Isebenza", "opened": "Kuvuliwe", "completed": "Kuqediwe", "pending": "Kusalindile", "unopened": "Akukavulwa", "transfer_to": "Dlulisela ku", "just_now": "Manje", "success": "Impumelelo", "verifying": "kuyaqinisekisa…", "premium": "Premium", "today": "Namuhla", "yesterday": "Izolo", "from": "Kusuka", "to": "Kuya"}
}

def t(lang, key):
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["en"].get(key, key))

# ---------------- db ----------------

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    slug TEXT PRIMARY KEY, name TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',
                    balance REAL NOT NULL DEFAULT 0, withdraw_code TEXT NOT NULL, password_hash TEXT,
                    transactions TEXT, withdrawn BOOLEAN NOT NULL DEFAULT FALSE, bank TEXT, account TEXT,
                    withdrawn_amount REAL, created BIGINT NOT NULL, opened_at BIGINT, withdrawn_at BIGINT, pending_until BIGINT,
                    language TEXT DEFAULT 'en', custom_bank TEXT
                );
            """)
            for col, typ in [
                ("opened_at", "BIGINT"), ("withdrawn_at", "BIGINT"), ("pending_until", "BIGINT"), 
                ("password_hash", "TEXT"), ("transactions", "TEXT"), ("language", "TEXT DEFAULT 'en'"), 
                ("custom_bank", "TEXT")
            ]:
                try: cur.execute(f"ALTER TABLE links ADD COLUMN IF NOT EXISTS {col} {typ}")
                except Exception: pass
        conn.commit()

def get_admin_hash():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM config WHERE key='admin_hash'")
        row = cur.fetchone()
        return row['value'] if row else None

def set_admin_hash(h):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO config (key, value) VALUES ('admin_hash', %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (h,))
        conn.commit()

def hash_pw(pw):
    if not pw: return None
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + pw).encode()).hexdigest()

def check_pw(pw, stored):
    if not stored or not pw: return False
    try: salt, h = stored.split(":", 1)
    except ValueError: return False
    return hashlib.sha256((salt + pw).encode()).hexdigest() == h

def db_list_links():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM links ORDER BY created DESC")
        return cur.fetchall()

def db_get_link(slug):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM links WHERE slug=%s", (slug,))
        return cur.fetchone()

def db_put_link(rec):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO links (slug, name, currency, balance, withdraw_code, password_hash, transactions, withdrawn, bank, account, withdrawn_amount, created, opened_at, withdrawn_at, pending_until, language, custom_bank)
            VALUES (%(slug)s, %(name)s, %(currency)s, %(balance)s, %(withdraw_code)s, %(password_hash)s, %(transactions)s, %(withdrawn)s, %(bank)s, %(account)s, %(withdrawn_amount)s, %(created)s, %(opened_at)s, %(withdrawn_at)s, %(pending_until)s, %(language)s, %(custom_bank)s)
            ON CONFLICT (slug) DO UPDATE SET
                name=EXCLUDED.name, currency=EXCLUDED.currency, balance=EXCLUDED.balance,
                withdraw_code=EXCLUDED.withdraw_code, password_hash=EXCLUDED.password_hash,
                transactions=EXCLUDED.transactions, withdrawn=EXCLUDED.withdrawn,
                bank=EXCLUDED.bank, account=EXCLUDED.account, withdrawn_amount=EXCLUDED.withdrawn_amount,
                opened_at=EXCLUDED.opened_at, withdrawn_at=EXCLUDED.withdrawn_at, pending_until=EXCLUDED.pending_until,
                language=EXCLUDED.language, custom_bank=EXCLUDED.custom_bank
        """, rec)
        conn.commit()

def db_delete_link(slug):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM links WHERE slug=%s", (slug,))
        conn.commit()

# ---------------- auth ----------------

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"): return redirect(url_for("admin_page"))
        return f(*a, **k)
    return w

def user_required(f):
    @wraps(f)
    def w(slug, *a, **k):
        rec = db_get_link(slug)
        if not rec: abort(404)
        if session.get("admin"): session[f"auth_{slug}"] = True
        if rec.get("password_hash") and not session.get(f"auth_{slug}"):
            return redirect(url_for("user_login", slug=slug))
        if not rec.get("opened_at"):
            rec["opened_at"] = int(time.time())
            db_put_link(rec)
        return f(slug, *a, **k)
    return w

# ---------------- UI Assets ----------------

BANK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--bg:#080b12;--surface:#111827;--border:#1f2a44;--text:#ffffff;--text-muted:#9aa7c7;--accent:#34d399;--icon-bg:#141926;--tab-bg:#0b0f19}
[data-theme="light"]{--bg:#f3f4f6;--surface:#ffffff;--border:#e5e7eb;--text:#111827;--text-muted:#6b7280;--accent:#10b981;--icon-bg:#e5e7eb;--tab-bg:#ffffff}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent;transition:background .3s,color .3s}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;margin:0;padding-bottom:110px;overflow-x:hidden}



.topbar{display:flex;align-items:center;justify-content:space-between;padding:2rem 1.5rem 1rem}
.greet{font-size:1.4rem;font-weight:600;line-height:1.2}
.greet span{display:block;font-size:1.6rem}
.avatar-wrap{position:relative;display:flex;align-items:center;gap:1rem}
.theme-btn{cursor:pointer;background:none;border:none;padding:0;color:var(--text-muted);display:flex;align-items:center;justify-content:center}
.theme-btn svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.avatar{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#8b5cf6,#60a5fa);display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:600;color:#fff}
.badge{position:absolute;bottom:0;right:-2px;background:#3b82f6;border:2px solid var(--bg);border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center}
.wrap{max-width:500px;margin:0 auto;padding:0 1rem}
.section-title{font-size:1rem;font-weight:600;margin:0 0 1rem;display:flex;justify-content:space-between;align-items:center}
.section-title a{color:var(--accent);font-size:.8rem;text-decoration:none;cursor:pointer}
.ticker-wrap{width:100%;overflow:hidden;background:var(--surface);border-bottom:1px solid var(--border);padding:.4rem 0;font-size:.75rem;color:var(--text-muted);white-space:nowrap}
.ticker{display:inline-block;animation:ticker 20s linear infinite}
@keyframes ticker{0%{transform:translateX(100%)}100%{transform:translateX(-100%)}}
.ticker span{margin:0 1rem}
.ticker .up{color:#4ade80}.ticker .down{color:#f87171}
.hero-card{background:linear-gradient(135deg, #2d2b55 0%, #1e3a8a 40%, #0f766e 100%);border-radius:24px;padding:1.5rem;position:relative;overflow:hidden;box-shadow:0 20px 40px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.2);margin-bottom:2rem}
.hero-card::before{content:"";position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:conic-gradient(from 180deg at 50% 50%, rgba(74,222,128,.2) 0deg, rgba(96,165,250,.2) 120deg, transparent 240deg);animation:spin 15s linear infinite;z-index:0;filter:blur(30px)}
@keyframes spin{100%{transform:rotate(360deg)}}
.hero-content{position:relative;z-index:1}
.bank-logo-sm{display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem}
.bank-logo-sm .icon{width:24px;height:24px;border-radius:6px;background:linear-gradient(135deg,#2dd4bf,#60a5fa);display:flex;align-items:center;justify-content:center}
.bank-logo-sm .txt{font-size:.75rem;font-weight:500;color:rgba(255,255,255,.9);line-height:1.1}
.balance-lbl{font-size:.75rem;color:rgba(255,255,255,.7)}
.balance{font-size:2.2rem;font-weight:700;margin:.2rem 0 .4rem;letter-spacing:-.5px;color:#fff}
.acct-info{font-size:.75rem;color:rgba(255,255,255,.7);margin-bottom:1.5rem}
.action-btns{display:flex;gap:.8rem}
.action-btns button{flex:1;padding:.7rem;border-radius:12px;font-size:.85rem;font-weight:600;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.1);color:#fff;backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;gap:.4rem;cursor:pointer;transition:.2s}
.action-btns button:hover{transform:scale(1.02)}
.quick-actions{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:2rem;text-align:center}
.qa{display:flex;flex-direction:column;align-items:center;gap:.4rem;cursor:pointer;text-decoration:none;color:var(--text)}
.qa-icon{width:54px;height:54px;border-radius:50%;background:var(--icon-bg);display:flex;align-items:center;justify-content:center;transition:.2s}
.qa-icon svg{width:24px;height:24px;fill:none;stroke:#60a5fa;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.qa:hover .qa-icon{background:#1f2a44;transform:translateY(-2px)}
.qa span{font-size:.7rem;color:var(--text-muted);font-weight:500}
.tx-list{background:var(--surface);border-radius:20px;padding:.5rem 1.2rem;margin-bottom:1.5rem;min-height:80px;border:1px solid var(--border)}
.tx{display:flex;justify-content:space-between;align-items:center;padding:1.2rem 0;border-bottom:1px solid var(--border)}
.tx:last-child{border-bottom:0}
.tx .left{display:flex;gap:1rem;align-items:center}
.tx .dot{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;flex-shrink:0}
.tx .dot.pos{background:rgba(74,222,128,.15)}.tx .dot.pos svg{stroke:#4ade80}
.tx .dot.neg{background:rgba(248,113,113,.15)}.tx .dot.neg svg{stroke:#f87171}
.tx .dot svg{width:20px;height:20px;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.tx .ttl{font-size:.9rem;font-weight:600}
.tx .sub{font-size:.7rem;color:var(--text-muted);margin-top:.2rem}
.tx .amt{font-weight:600;font-size:.9rem}
.tx .amt.pos{color:#4ade80}.tx .amt.neg{color:#f87171}
.empty-tx{text-align:center;color:var(--text-muted);font-size:.85rem;padding:2rem 0}
.tabbar{position:fixed;bottom:0;left:0;right:0;background:var(--tab-bg);border-top:1px solid var(--border);display:flex;justify-content:space-around;padding:.6rem .5rem 1.2rem;z-index:50;padding-bottom:calc(1.2rem + env(safe-area-inset-bottom))}
.tab{flex:1;display:flex;flex-direction:column;align-items:center;gap:.3rem;padding:.5rem;color:var(--text-muted);text-decoration:none;font-size:.65rem;font-weight:600;cursor:pointer;background:none;border:0;transition:.2s}
.tab.active{color:#60a5fa}
.tab.active .ico-wrap{background:rgba(96,165,250,.1);border-radius:12px}
.ico-wrap{padding:.3rem .8rem;display:flex;align-items:center;justify-content:center;transition:.2s}
.tab svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.card{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:1.5rem;margin-bottom:1.5rem}
label{display:block;font-size:.8rem;color:var(--text-muted);margin-top:1rem;font-weight:500}
input,select{width:100%;padding:1rem;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:14px;box-sizing:border-box;margin-top:.4rem;font-size:.95rem;font-family:inherit;outline:none}
input:focus{border-color:#3b82f6;box-shadow:0 0 0 2px rgba(59,130,246,.2)}
button.primary{width:100%;padding:1rem;border:0;border-radius:14px;cursor:pointer;font-weight:700;background:var(--accent);color:#06210f;font-size:1rem;margin-top:1.5rem;transition:.2s}
button.primary:hover{filter:brightness(1.1)}
button.primary:disabled{opacity:.6;cursor:not-allowed}
.msg{margin-top:1rem;font-size:.85rem;padding:1rem;border-radius:12px;display:none;text-align:center;font-weight:500}
.msg.show{display:block}
.msg.err{color:#fca5a5;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3)}
.msg.ok{color:#86efac;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3)}
.pw-wrap{position:relative}
.pw-wrap input{padding-right:3rem}
.pw-toggle{position:absolute;right:1rem;top:50%;transform:translateY(-50%);cursor:pointer;color:var(--text-muted);background:none;border:none;padding:0;margin:0;display:flex;align-items:center;justify-content:center}
.pw-toggle svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pw-toggle:hover{color:var(--text)}
"""

THEME_SCRIPT = """
<script>
function toggleTheme(){
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  if(isLight){ document.documentElement.removeAttribute('data-theme'); localStorage.setItem('theme', 'dark'); }
  else { document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('theme', 'light'); }
  updateThemeIcon();
}
function updateThemeIcon(){
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const btn = document.getElementById('theme-btn');
  if(!btn) return;
  if(isLight){
    btn.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
  } else {
    btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
  }
}
if(localStorage.getItem('theme') === 'light'){ document.documentElement.setAttribute('data-theme', 'light'); }
document.addEventListener('DOMContentLoaded', updateThemeIcon);
</script>



"""

# ---------------- Pages ----------------

DASHBOARD_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
{{ theme_script|safe }}
<div class="ticker-wrap">
  <div class="ticker">
    <span>USD/NGN 1,540.20 <b class="up">+0.4%</b></span>
    <span>EUR/USD 1.08 <b class="down">-0.1%</b></span>
    <span>GBP/USD 1.26 <b class="up">+0.2%</b></span>
    <span>BTC/USD 64,200 <b class="up">+2.1%</b></span>
  </div>
</div>
<div class="topbar">
  <div class="greet">{{ t('dashboard') }},<span>{{ name.split(' ')[0] }}</span></div>
  <div class="avatar-wrap">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()"></button>
    <div style="position:relative"><div class="avatar">{{ name[0]|upper }}</div><div class="badge"><svg viewBox="0 0 24 24" fill="#fff" width="10" height="10"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div></div>
  </div>
</div>
<div class="wrap">
  <div class="hero-card">
    <div class="hero-content">
      <div class="bank-logo-sm">
        <div class="icon"><svg viewBox="0 0 24 24" fill="#fff" width="14" height="14"><path d="M12 2L2 22h20L12 2z"/></svg></div>
        <div class="txt">{{ bank }}<br>{{ t('premium') }}</div>
      </div>
      <div class="balance-lbl">{{ t('total_balance') }}</div>
      <div class="balance">{{ currency }} {{ "{:,.2f}".format(balance) }}</div>
      <div class="acct-info">{{ t('account_number') }} {{ acct_full }} · {{ bank }}</div>
      <div class="action-btns">
        <a href="{{ url_for('user_page', slug=slug, page='transfer') }}" style="flex:1;text-decoration:none">
          <button style="width:100%"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>{{ t('send_money') }}</button>
        </a>
      </div>
    </div>
  </div>
  <div class="quick-actions">
    <a href="{{ url_for('user_page', slug=slug, page='transfer') }}" class="qa"><div class="qa-icon"><svg viewBox="0 0 24 24"><path d="M17 1l4 4-4 4"></path><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><path d="M7 23l-4-4 4-4"></path><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg></div><span>{{ t('transfer') }}</span></a>
    <a href="{{ url_for('user_page', slug=slug, page='cards') }}" class="qa"><div class="qa-icon"><svg viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg></div><span>{{ t('cards') }}</span></a>
    <a href="{{ url_for('user_page', slug=slug, page='history') }}" class="qa"><div class="qa-icon"><svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg></div><span>{{ t('history') }}</span></a>
    <a href="{{ url_for('user_page', slug=slug, page='settings') }}" class="qa"><div class="qa-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg></div><span>{{ t('settings') }}</span></a>
  </div>
  <div class="section-title">{{ t('recent_tx') }} <a href="{{ url_for('user_page', slug=slug, page='history') }}">{{ t('see_all') }}</a></div>
  <div class="tx-list">
    {% if tx_list %}
      {% for tx in tx_list %}
        <div class="tx">
          <div class="left">
            <div class="dot {{ 'pos' if tx.amount > 0 else 'neg' }}">
              {% if tx.amount > 0 %}<svg viewBox="0 0 24 24"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
              {% else %}<svg viewBox="0 0 24 24"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>{% endif %}
            </div>
            <div>
              <div class="ttl">{{ t('from') if tx.amount > 0 else t('to') }}: {{ tx.name }}</div>
              <div class="sub">{{ tx.date }}</div>
            </div>
          </div>
          <div class="amt {{ 'pos' if tx.amount > 0 else 'neg' }}">{{ '+' if tx.amount > 0 else '-' }}{{ currency }} {{ "{:,.2f}".format(tx.amount|abs) }}</div>
        </div>
      {% endfor %}
    {% else %}<div class="empty-tx">{{ t('no_tx') }}</div>{% endif %}
  </div>
</div>
{{ tab|safe }}
</body></html>
"""

HISTORY_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Transactions — Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
{{ theme_script|safe }}
<div class="topbar">
  <div class="greet">{{ t('history') }}<span>{{ t('history') }}</span></div>
  <div class="avatar-wrap">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()"></button>
    <div class="avatar">{{ name[0]|upper }}</div>
  </div>
</div>
<div class="wrap">
  <div class="card" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
    <div><div style="font-size:.9rem;font-weight:600">{{ t('download_stmt') }}</div><div style="font-size:.75rem;color:var(--text-muted);margin-top:.2rem">{{ t('get_pdf') }}</div></div>
    <a href="{{ url_for('user_statement', slug=slug) }}" target="_blank" style="background:var(--accent);color:#06210f;text-decoration:none;padding:.5rem 1rem;border-radius:8px;font-size:.8rem;font-weight:700">{{ t('download') }}</a>
  </div>
  <div class="tx-list">
    {% if tx_list %}
      {% for tx in tx_list %}
        <div class="tx">
          <div class="left">
            <div class="dot {{ 'pos' if tx.amount > 0 else 'neg' }}">
              {% if tx.amount > 0 %}<svg viewBox="0 0 24 24"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
              {% else %}<svg viewBox="0 0 24 24"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>{% endif %}
            </div>
            <div>
              <div class="ttl">{{ t('from') if tx.amount > 0 else t('to') }}: {{ tx.name }}</div>
              <div class="sub">{{ tx.date }}</div>
            </div>
          </div>
          <div class="amt {{ 'pos' if tx.amount > 0 else 'neg' }}">{{ '+' if tx.amount > 0 else '-' }}{{ currency }} {{ "{:,.2f}".format(tx.amount|abs) }}</div>
        </div>
      {% endfor %}
    {% else %}<div class="empty-tx" style="padding:4rem 0">{{ t('no_tx') }}</div>{% endif %}
  </div>
</div>
{{ tab|safe }}
</body></html>
"""

TRANSFER_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Transfer — Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
{{ theme_script|safe }}
<div class="topbar">
  <div class="greet">{{ t('transfer') }}<span>{{ t('transfer') }}</span></div>
  <div class="avatar-wrap">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()"></button>
    <div class="avatar">{{ name[0]|upper }}</div>
  </div>
</div>
<div class="wrap">
  {% if withdrawn %}
    <div class="card" style="text-align:center;padding:2.5rem 1.5rem;margin-top:2rem">
      <div style="font-size:3rem;margin-bottom:1rem">✅</div>
      <h2 style="margin:0 0 .5rem;font-size:1.2rem">{{ t('transfer_processed') }}</h2>
      <p style="color:var(--text-muted);font-size:.9rem;margin:0">{{ t('funds_sent_msg') }}</p>
    </div>
  {% elif pending_until %}
    <div class="card" style="text-align:center;padding:2.5rem 1.5rem;margin-top:2rem">
      <div style="font-size:3rem;margin-bottom:1rem">⏳</div>
      <h2 style="margin:0 0 .5rem;font-size:1.2rem">{{ t('processing') }}</h2>
      <p style="color:var(--text-muted);font-size:.9rem;margin:0 0 1.5rem">{{ t('processing_msg') }}</p>
      <div style="font-size:2rem;font-weight:700;color:var(--accent)" id="timer">30s</div>
      <p style="color:var(--text-muted);font-size:.75rem;margin-top:.5rem">{{ t('do_not_close') }}</p>
    </div>
    <script>
      let seconds = {{ pending_until }} - Math.floor(Date.now() / 1000);
      if(seconds < 0) seconds = 0;
      const timer = document.getElementById('timer');
      const interval = setInterval(() => { if(seconds <= 0){ clearInterval(interval); location.reload(); } else { seconds--; timer.textContent = seconds + 's'; } }, 1000);
    </script>
  {% else %}
    <div class="card">
      <p style="color:var(--text-muted);font-size:.9rem;margin:0 0 1rem">{{ t('funds_sent_to') }}</p>
      <label>{{ t('bank_name') }}</label><input id="bank" placeholder="e.g. Chase, GTBank" autocomplete="off">
      <label>{{ t('account_no') }}</label><input id="acct" placeholder="10-digit account number" inputmode="numeric" autocomplete="off">
      <label>{{ t('amount') }} ({{ currency }})</label><input id="amt" type="number" step="0.01" placeholder="0.00" inputmode="decimal">
      <label>{{ t('withdraw_code') }}</label>
      <div class="pw-wrap"><input id="code" type="password" placeholder="code from your banker" autocomplete="off"><button type="button" class="pw-toggle" onclick="togglePw('code')"><svg id="eye-code" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button></div>
      <button class="primary" id="btn" onclick="go()">{{ t('confirm_transfer') }}</button>
      <div class="msg" id="msg"></div>
    </div>
  {% endif %}
</div>
{{ tab|safe }}
<script>
function togglePw(id){
  const el = document.getElementById(id); const icon = document.getElementById('eye-'+id);
  if(el.type === 'password'){ el.type = 'text'; icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>'; }
  else { el.type = 'password'; icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>'; }
}
async function go(){
  const btn=document.getElementById('btn'); const msg=document.getElementById('msg');
  const body={bank:document.getElementById('bank').value.trim(), account:document.getElementById('acct').value.trim(), amount:parseFloat(document.getElementById('amt').value||'0'), code:document.getElementById('code').value};
  if(!body.bank){ msg.className='msg err show'; msg.textContent='bank name required'; return; }
  if(!body.account){ msg.className='msg err show'; msg.textContent='account number required'; return; }
  if(!(body.amount>0)){ msg.className='msg err show'; msg.textContent='enter a valid amount'; return; }
  if(!body.code){ msg.className='msg err show'; msg.textContent='withdrawal code required'; return; }
  btn.disabled=true; msg.className='msg show'; msg.textContent='processing…';
  try{
    const r=await fetch('/v/{{slug}}/withdraw/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    if(r.ok&&d.ok){ msg.className='msg ok show'; msg.textContent='Approved — starting transfer…'; setTimeout(()=>location.reload(),600); }
    else { msg.className='msg err show'; msg.textContent=d.error||'failed'; btn.disabled=false; }
  }catch(e){ msg.className='msg err show'; msg.textContent='network error — try again'; btn.disabled=false; }
}
</script>
</body></html>
"""

CARDS_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Cards — Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
{{ theme_script|safe }}
<div class="topbar">
  <div class="greet">{{ t('cards') }}<span>{{ t('cards') }}</span></div>
  <div class="avatar-wrap">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()"></button>
    <div class="avatar">{{ name[0]|upper }}</div>
  </div>
</div>
<div class="wrap">
  <div class="hero-card" style="height:200px;display:flex;flex-direction:column;justify-content:space-between">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;position:relative;z-index:1">
      <div class="bank-logo-sm" style="margin:0"><div class="txt">{{ bank }}<br>Debit</div></div>
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" width="24" height="24"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
    </div>
    <div style="position:relative;z-index:1">
      <div style="font-family:monospace;font-size:1.4rem;letter-spacing:2px;margin-bottom:.5rem;color:#fff">•••• •••• •••• {{ acct_last }}</div>
      <div style="display:flex;justify-content:space-between;font-size:.75rem;color:rgba(255,255,255,.7)"><span>{{ name|upper }}</span><span>09/28</span></div>
    </div>
  </div>
  <div class="card" style="margin-top:1rem">
    <h3 style="margin:0 0 .5rem;font-size:1rem">{{ t('card_status') }}</h3>
    <p style="color:var(--text-muted);font-size:.9rem;margin:0 0 1rem">Your virtual card is active and ready.</p>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:1rem 0;border-top:1px solid var(--border)">
      <span style="font-size:.9rem">{{ t('freeze_card') }}</span><input type="checkbox" style="width:40px;height:20px;margin:0" onclick="alert('Card frozen/unfrozen.')">
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:1rem 0;border-top:1px solid var(--border)">
      <span style="font-size:.9rem">{{ t('view_cvv') }}</span><button id="cvv-btn" onclick="showCVV('{{ cvv }}')" style="background:var(--icon-bg);border:0;color:var(--text);padding:.4rem .8rem;border-radius:8px;font-size:.75rem">{{ t('view_cvv') }}</button>
    </div>
  </div>
</div>
{{ tab|safe }}
<script>
function showCVV(cvv){ const btn = document.getElementById('cvv-btn'); btn.textContent = cvv; btn.style.background = 'transparent'; btn.style.fontFamily = 'monospace'; btn.style.fontSize = '1rem'; btn.style.fontWeight = '700'; btn.style.color = '#34d399'; }
</script>
</body></html>
"""

SETTINGS_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Settings — Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
{{ theme_script|safe }}
<div class="topbar">
  <div class="greet">{{ t('settings') }}<span>{{ t('settings') }}</span></div>
  <div class="avatar-wrap">
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()"></button>
    <div class="avatar">{{ name[0]|upper }}</div>
  </div>
</div>
<div class="wrap">
  <div class="card" style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem">
    <div class="avatar" style="width:60px;height:60px;font-size:1.5rem">{{ name[0]|upper }}</div>
    <div><div style="font-size:1.1rem;font-weight:600">{{ name }}</div><div style="font-size:.85rem;color:var(--text-muted)">Account: {{ acct_full }}</div></div>
  </div>
  <div class="card" style="padding:0;overflow:hidden">
    <div style="padding:1.2rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.9rem;font-weight:500">{{ t('email_notif') }}</span><input type="checkbox" checked style="width:40px;height:20px;margin:0">
    </div>
    <div style="padding:1.2rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.9rem;font-weight:500">{{ t('dark_mode') }}</span>
      <label style="display:inline-block;position:relative;width:40px;height:20px;margin:0"><input type="checkbox" id="theme-toggle" style="opacity:0;width:0;height:0" onclick="toggleTheme()"><span style="position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#1f2a44;border-radius:20px;transition:.4s"></span><span style="position:absolute;content:'';height:16px;width:16px;left:2px;bottom:2px;background:#fff;border-radius:50%;transition:.4s" id="theme-slider"></span></label>
    </div>
    <div style="padding:1.2rem;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.9rem;font-weight:500">{{ t('biometrics') }}</span><input type="checkbox" checked style="width:40px;height:20px;margin:0">
    </div>
  </div>
  <a href="{{ url_for('user_logout', slug=slug) }}" style="text-decoration:none"><button class="primary" style="background:#2a0f14;color:#fca5a5;margin-top:0">{{ t('log_out') }}</button></a>
</div>
{{ tab|safe }}
<script>
function updateSlider(){ const isLight = document.documentElement.getAttribute('data-theme') === 'light'; const slider = document.getElementById('theme-slider'); const cb = document.getElementById('theme-toggle'); if(isLight){ cb.checked = true; slider.style.transform = 'translateX(20px)'; } else { cb.checked = false; slider.style.transform = 'translateX(0)'; } }
document.getElementById('theme-toggle').addEventListener('click', () => { setTimeout(updateSlider, 50); });
updateSlider();
</script>
</body></html>
"""

LOGIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Login — Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
{{ theme_script|safe }}
<div class="wrap" style="margin-top:20vh">
  <div class="card" style="text-align:center">
    <div class="hero-content" style="margin-bottom:2rem">
      <div class="bank-logo-sm" style="justify-content:center"><div class="icon"><svg viewBox="0 0 24 24" fill="#fff" width="14" height="14"><path d="M12 2L2 22h20L12 2z"/></svg></div><div class="txt">{{ bank }}</div></div>
      <h2 style="font-size:1.3rem;margin:1rem 0 0">{{ t('welcome_back') }}, {{ name }}</h2>
      <p style="color:var(--text-muted);font-size:.9rem;margin-top:.5rem">{{ t('enter_password') }}</p>
    </div>
    <div style="text-align:left">
      <label>{{ t('password') }}</label>
      <div class="pw-wrap"><input id="pw" type="password" placeholder="••••••••"><button type="button" class="pw-toggle" onclick="togglePw('pw')"><svg id="eye-pw" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button></div>
    </div>
    <button class="primary" onclick="doLogin()">{{ t('login') }}</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
function togglePw(id){ const el = document.getElementById(id); const icon = document.getElementById('eye-'+id); if(el.type === 'password'){ el.type = 'text'; icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>'; } else { el.type = 'password'; icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>'; } }
async function doLogin(){
  const btn=document.querySelector('button.primary'); const msg=document.getElementById('msg'); const pw=document.getElementById('pw').value;
  if(!pw){ msg.className='msg err show'; msg.textContent='password required'; return; }
  btn.disabled=true; msg.className='msg show'; msg.textContent='verifying…';
  try{
    const r=await fetch('/v/{{slug}}/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})});
    const d=await r.json();
    if(r.ok&&d.ok){ msg.className='msg ok show'; msg.textContent='Success — redirecting…'; setTimeout(()=>location.href='/v/{{slug}}/dashboard',600); }
    else { msg.className='msg err show'; msg.textContent=d.error||'wrong password'; btn.disabled=false; }
  }catch(e){ msg.className='msg err show'; msg.textContent='network error'; btn.disabled=false; }
}
</script>
</body></html>
"""

STATEMENT_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Statement — Client Portal</title>
<style>
body{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;background:#fff;color:#333;margin:0;padding:2rem}
.page{max-width:800px;margin:0 auto;background:#fff}
.header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #2563eb;padding-bottom:1rem;margin-bottom:2rem}
.logo{font-size:1.5rem;font-weight:700;color:#2563eb}
h2{margin:0 0 .5rem;font-size:1.2rem}
p{margin:0 0 1rem;font-size:.9rem;color:#666}
table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.85rem}
th,td{padding:.8rem;text-align:left;border-bottom:1px solid #e5e7eb}
th{background:#f9fafb;font-weight:600;color:#111}
.amt-pos{color:#059669;font-weight:600}
.amt-neg{color:#dc2626;font-weight:600}
.footer{margin-top:3rem;text-align:center;font-size:.75rem;color:#9ca3af;border-top:1px solid #e5e7eb;padding-top:1rem}
</style></head><body>
<div class="page">
  <div class="header">
    <div><div class="logo">{{ bank }}</div><p style="margin-top:.5rem">Premium Banking<br>123 Financial District, New York, NY</p></div>
    <div style="text-align:right"><h2>{{ t('statement') }}</h2><p>{{ t('date') }}: {{ date }}<br>{{ t('account_number') }}: {{ acct_full }}</p></div>
  </div>
  <div style="margin-bottom:2rem"><h3 style="margin:0 0 .5rem;font-size:1rem">{{ t('account_holder') }}</h3><p style="color:#111;font-weight:600;font-size:1rem;margin-bottom:.2rem">{{ name }}</p><p>{{ t('currency') }}: {{ currency }}</p></div>
  <h3 style="margin:0 0 .5rem;font-size:1rem">{{ t('tx_history') }}</h3>
  <table>
    <thead><tr><th>{{ t('date') }}</th><th>{{ t('description') }}</th><th>{{ t('amount') }}</th></tr></thead>
    <tbody>
      {% for tx in tx_list %}
      <tr><td>{{ tx.date }}</td><td>{{ t('from') if tx.amount > 0 else t('to') }}: {{ tx.name }}</td><td class="{{ 'amt-pos' if tx.amount > 0 else 'amt-neg' }}">{{ '+' if tx.amount > 0 else '-' }}{{ currency }} {{ "{:,.2f}".format(tx.amount|abs) }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
  <div style="margin-top:2rem;text-align:right"><p style="color:#666;font-size:.9rem">{{ t('ending_balance') }}</p><div style="font-size:1.5rem;font-weight:700;color:#111">{{ currency }} {{ "{:,.2f}".format(balance) }}</div></div>
  <div class="footer">{{ t('stmt_footer') }}<br>For inquiries, please contact support@{{ bank|lower|replace(' ','') }}.com</div>
</div>
<script>window.onload = function() { setTimeout(function(){ window.print(); }, 500); }</script>
</body></html>
"""

# ---------------- Routing ----------------

def build_tab(slug, active, lang):
    return f"""
    <div class="tabbar">
      <a class="tab {'active' if active=='dashboard' else ''}" href="/v/{slug}/dashboard"><div class="ico-wrap"><svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg></div><span>{t(lang, 'dashboard')}</span></a>
      <a class="tab {'active' if active=='history' else ''}" href="/v/{slug}/history"><div class="ico-wrap"><svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg></div><span>{t(lang, 'history')}</span></a>
      <a class="tab {'active' if active=='transfer' else ''}" href="/v/{slug}/transfer"><div class="ico-wrap"><svg viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg></div><span>{t(lang, 'transfer')}</span></a>
      <a class="tab {'active' if active=='cards' else ''}" href="/v/{slug}/cards"><div class="ico-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div><span>{t(lang, 'cards')}</span></a>
      <a class="tab {'active' if active=='settings' else ''}" href="/v/{slug}/settings"><div class="ico-wrap"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg></div><span>{t(lang, 'settings')}</span></a>
    </div>
    """

@app.route("/v/<slug>/login")
def user_login(slug):
    rec = db_get_link(slug)
    if not rec: abort(404)
    if not rec.get("password_hash"): return redirect(url_for("user_page", slug=slug, page="dashboard"))
    lang = rec.get("language") or "en"
    bank = rec.get("custom_bank") or BANK_NAME
    return render_template_string(LOGIN_HTML, css=BANK_CSS, bank=bank, name=rec["name"], slug=slug, t=lambda k: t(lang, k), theme_script=THEME_SCRIPT)

@app.route("/v/<slug>/auth", methods=["POST"])
def user_auth(slug):
    d = request.get_json(force=True)
    rec = db_get_link(slug)
    if not rec: return jsonify({"error":"not found"}), 404
    if session.get("admin") or check_pw(d.get("password",""), rec.get("password_hash")):
        session[f"auth_{slug}"] = True
        if not rec.get("opened_at"):
            rec["opened_at"] = int(time.time())
            db_put_link(rec)
        return jsonify({"ok": True})
    return jsonify({"error": "incorrect password"}), 401

@app.route("/v/<slug>/logout")
def user_logout(slug):
    session.pop(f"auth_{slug}", None)
    return redirect(url_for("user_login", slug=slug))

@app.route("/v/<slug>")
def view_account_redirect(slug):
    return redirect(url_for('user_page', slug=slug, page='dashboard'))

@app.route("/v/<slug>/<page>")
@user_required
def user_page(slug, page):
    rec = db_get_link(slug)
    if page not in ['dashboard', 'history', 'transfer', 'cards', 'settings']:
        return redirect(url_for('user_page', slug=slug, page='dashboard'))
        
    lang = rec.get("language") or "en"
    bank = rec.get("custom_bank") or BANK_NAME
    
    withdrawn_amount = rec.get("withdrawn_amount") or 0
    opening = rec["balance"] + withdrawn_amount
    acct_full = "0123" + str(abs(hash(slug)) % 10000000).zfill(7)
    acct_last = acct_full[-4:]
    cvv = str((abs(hash(slug)) % 900) + 100)

    tx_list = []
    if rec.get("transactions"):
        try:
            raw_tx = json.loads(rec["transactions"])
            tx_list = raw_tx
        except Exception as e:
            print("tx parse err:", e)
        
    if rec.get("withdrawn"):
        tx_list.insert(0, {"name": f"{rec.get('bank')}", "date": time.strftime('%b %d, %Y', time.localtime(rec.get("withdrawn_at") or time.time())), "amount": -(rec.get("withdrawn_amount") or 0)})

    pending_until = rec.get("pending_until")
    if pending_until:
        if int(time.time()) >= pending_until:
            rec["withdrawn"] = True
            rec["withdrawn_at"] = int(time.time())
            rec["pending_until"] = None
            db_put_link(rec)
            pending_until = None

    tab = build_tab(slug, page, lang)
    
    kwargs = dict(
        css=BANK_CSS, tab=tab, slug=slug, bank=bank, name=rec["name"], currency=rec["currency"],
        balance=rec["balance"], withdrawn=rec.get("withdrawn", False), withdrawn_amount=withdrawn_amount, 
        opening=opening, acct_full=acct_full, acct_last=acct_last, cvv=cvv, bank_dest=rec.get("bank") or "Bank",
        tx_list=tx_list, pending_until=pending_until, t=lambda k: t(lang, k), theme_script=THEME_SCRIPT, lang=lang
    )
    
    if page == 'dashboard': return render_template_string(DASHBOARD_HTML, **kwargs)
    elif page == 'history': return render_template_string(HISTORY_HTML, **kwargs)
    elif page == 'transfer': return render_template_string(TRANSFER_HTML, **kwargs)
    elif page == 'cards': return render_template_string(CARDS_HTML, **kwargs)
    elif page == 'settings': return render_template_string(SETTINGS_HTML, **kwargs)

@app.route("/v/<slug>/statement")
@user_required
def user_statement(slug):
    rec = db_get_link(slug)
    if not rec: abort(404)
    lang = rec.get("language") or "en"
    bank = rec.get("custom_bank") or BANK_NAME
    
    acct_full = "0123" + str(abs(hash(slug)) % 10000000).zfill(7)
    tx_list = []
    if rec.get("transactions"):
        try:
            raw_tx = json.loads(rec["transactions"])
            tx_list = raw_tx
        except Exception: pass
    if rec.get("withdrawn"):
        tx_list.insert(0, {"name": f"{rec.get('bank')}", "date": time.strftime('%b %d, %Y', time.localtime(rec.get("withdrawn_at") or time.time())), "amount": -(rec.get("withdrawn_amount") or 0)})

    return render_template_string(STATEMENT_HTML, bank=bank, name=rec["name"], currency=rec["currency"], 
        balance=rec["balance"], acct_full=acct_full, tx_list=tx_list, date=time.strftime('%B %d, %Y'), t=lambda k: t(lang, k))

@app.route("/v/<slug>/withdraw/submit", methods=["POST"])
@user_required
def withdraw_submit(slug):
    d = request.get_json(force=True)
    rec = db_get_link(slug)
    if not rec: return jsonify({"error":"not found"}), 404
    if rec.get("withdrawn"): return jsonify({"error":"already processed"}), 400
    if rec.get("pending_until") and int(time.time()) < rec["pending_until"]: return jsonify({"error":"transfer already processing"}), 400
    if (d.get("code") or "").strip() != rec["withdraw_code"]: return jsonify({"error":"invalid withdrawal code"}), 403
    
    bank = (d.get("bank") or "").strip()
    acct = (d.get("account") or "").strip()
    if not bank or not acct: return jsonify({"error":"bank and account required"}), 400
    amt = float(d.get("amount") or 0)
    if amt <= 0 or amt > rec["balance"]: return jsonify({"error":"invalid amount"}), 400
    
    rec["balance"] -= amt
    rec["bank"] = bank
    rec["account"] = acct
    rec["withdrawn_amount"] = amt
    rec["pending_until"] = int(time.time()) + 30
    db_put_link(rec)
    return jsonify({"ok": True})

# ---------------- Landing ----------------

NOT_A_USER_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Client Portal</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#080b12;color:#ffffff;font-family:'Inter',system-ui,sans-serif;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1.5rem}
.card{max-width:440px;width:100%;text-align:center;background:#111827;border:1px solid #1f2a44;border-radius:24px;padding:3rem 2rem;box-shadow:0 30px 80px rgba(0,0,0,.8)}
.logo{font-weight:700;color:#60a5fa;margin-bottom:1.5rem;font-size:1rem;display:flex;align-items:center;justify-content:center;gap:.5rem}
.oops{font-size:4rem;margin:0;line-height:1}
h1{font-size:1.4rem;margin:1.5rem 0 .5rem;font-weight:600}
p{color:#9aa7c7;line-height:1.5;margin:0 0 2rem;font-size:.9rem}
.btn{display:inline-flex;align-items:center;gap:.6rem;justify-content:center;background:#34d399;color:#06210f;text-decoration:none;font-weight:700;padding:1rem 1.5rem;border-radius:14px;width:100%;font-size:.95rem;transition:.2s}
.btn:hover{background:#10b981;transform:scale(1.02)}
.btn svg{width:22px;height:22px;flex-shrink:0}
.foot{margin-top:2rem;font-size:.75rem;color:#4b5876}
</style></head><body>
<div class="card">
  <div class="logo"><svg viewBox="0 0 24 24" fill="#60a5fa" width="24" height="24"><path d="M12 2L2 22h20L12 2z"/></svg> {{ bank }}</div>
  <div class="oops">😕</div>
  <h1>Oops — you're not a user yet</h1>
  <p>Looks like you don't have an account with us. Message the admin on WhatsApp and they'll set you up.</p>
  <a class="btn" href="https://wa.me/{{ phone }}?text={{ msg }}" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 14.4c-.3-.1-1.7-.8-1.9-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.4-2.3-1.4-.8-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.4 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.4 0 1.4 1 2.8 1.2 3 .1.2 2 3.1 4.9 4.3.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.5-.1 1.7-.7 1.9-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3z"/></svg>
    Message admin on WhatsApp
  </a>
  <div class="foot">{{ bank }} · secure portal</div>
</div></body></html>
"""

def render_landing():
    msg = quote("Hi, I'd like to be set up as a user of " + BANK_NAME + ".")
    return render_template_string(NOT_A_USER_HTML, bank=BANK_NAME, phone=WHATSAPP_NUMBER, msg=msg)

@app.route("/")
def index(): return render_landing()

@app.route("/favicon.ico")
def favicon(): return "", 204

@app.errorhandler(404)
def not_found(e): return render_landing(), 404

# ---------------- Admin ----------------

ADMIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Admin</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#0b0f1a;color:#e8eefc;font-family:system-ui,sans-serif;margin:0;padding:2rem}
.container{max-width:1200px;margin:0 auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem}
@media(max-width:900px){.grid{grid-template-columns:1fr}body{padding:1rem}}
.card{background:#111827;padding:1.5rem;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
label{display:block;font-size:.85rem;color:#9aa7c7;margin-top:.8rem}
input,select,textarea{width:100%;padding:.6rem;margin-top:.3rem;background:#0b1220;border:1px solid #1f2a44;color:#e8eefc;border-radius:8px;box-sizing:border-box;font-family:inherit}
button{padding:.7rem 1.2rem;background:#2563eb;color:#fff;border:0;border-radius:8px;cursor:pointer;font-weight:600;margin-top:1rem}
table{width:100%;border-collapse:collapse;margin-top:1rem}
th,td{padding:.6rem;border-bottom:1px solid #1f2a44;text-align:left;font-size:.9rem;vertical-align:top}
th{color:#9aa7c7;font-weight:500}
a{color:#60a5fa;word-break:break-all}
.code{font-family:monospace;background:#0b1220;padding:.15rem .4rem;border-radius:6px}
.err{color:#f87171}.ok{color:#4ade80}
.tx-row{display:grid;grid-template-columns:1.5fr 1fr 1.5fr 1fr 30px;gap:.5rem;margin-bottom:.5rem;align-items:center}
.tx-row input, .tx-row select{margin:0}
.tx-row button{margin:0;padding:0;background:#7f1d1d;border-radius:8px;height:36px}
.status{font-size:.75rem;padding:.2rem .5rem;border-radius:4px;background:#1f2a44;display:inline-block}
.status.pending{background:#78350f;color:#fcd34d}
.status.done{background:#064e3b;color:#6ee7b7}
.status.open{background:#1e3a8a;color:#93c5fd}
.pw-wrap{position:relative}
.pw-wrap input{padding-right:2.5rem}
.pw-toggle{position:absolute;right:0.8rem;top:50%;transform:translateY(-50%);cursor:pointer;color:#7d8bab;background:none;border:none;padding:0;margin:0;display:flex;align-items:center}
.pw-toggle svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pw-toggle:hover{color:#e8eefc}
</style></head><body>
<div class="container">
{% if not authed %}
  <div class="card" style="max-width:380px;margin:4rem auto">
    <h3 style="margin-top:0">{{ 'Set admin password' if first_run else 'Admin login' }}</h3>
    <form method="post" action="{{ url_for('admin_setpw' if first_run else 'admin_login') }}">
      <label>Password</label>
      <div class="pw-wrap">
        <input name="password" type="password" required autofocus>
        <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
      </div>
      {% if first_run %}
      <label>Confirm</label>
      <div class="pw-wrap">
        <input name="confirm" type="password" required>
        <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
      </div>
      {% endif %}
      <button>{{ 'Set password' if first_run else 'Sign in' }}</button>
    </form>
    {% if error %}<div class="err" style="margin-top:.8rem">{{ error }}</div>{% endif %}
  </div>
{% else %}
  <h1 style="margin-top:0">Admin Dashboard</h1>
  <div class="grid">
    <div class="card">
      <h3 style="margin-top:0">Generate share link</h3>
      <form id="gen">
        <label>Display name</label><input name="name" required>
        
        <label>User Password (for login)</label>
        <div class="pw-wrap">
          <input name="user_password" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
        </div>

        <label>Custom Bank Name (optional)</label>
        <input name="custom_bank" placeholder="e.g. Chase, Barclays, Access Bank">

        <label>Language</label>
        <select name="language">
          {% for code, name in languages.items() %}
          <option value="{{ code }}" {% if code == 'en' %}selected{% endif %}>{{ name }}</option>
          {% endfor %}
        </select>

        <label>Currency</label>
        <select name="currency">
          {% for c in currencies %}
          <option value="{{ c }}">{{ c }}</option>
          {% endfor %}
        </select>
        <label>Balance</label><input name="balance" type="number" step="0.01" required value="0">
        
        <label>Withdrawal code</label>
        <div class="pw-wrap">
          <input name="withdraw_code" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
        </div>
        
        <label style="margin-top:1.5rem">Fake Transactions (optional)</label>
        <div id="tx-container"></div>
        <button type="button" onclick="addTxRow()" style="background:#1f2a44;font-size:.8rem;padding:.4rem .8rem">+ Add Transaction</button>
        <button style="margin-top:1.5rem;width:100%">Generate Link</button>
      </form>
      <div id="out" style="margin-top:1rem"></div>
      
      <hr style="border-color:#1f2a44;margin:1.5rem 0">
      <h4 style="margin-top:0">Change admin password</h4>
      <form id="chpw">
        <label>Current</label>
        <div class="pw-wrap">
          <input name="current" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
        </div>
        <label>New</label>
        <div class="pw-wrap">
          <input name="new" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
        </div>
        <button>Update</button>
      </form>
      <div id="pwmsg" style="margin-top:.6rem"></div>

    </div>

    <div class="card">
      <h3 style="margin-top:0">Existing links</h3>
      <div id="list" style="overflow-x:auto">loading…</div>
    </div>
  </div>
{% endif %}
</div>

<script>
function togglePw(btn){
  const input = btn.previousElementSibling;
  const icon = btn.querySelector('svg');
  if(input.type === 'password'){
    input.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
  } else {
    input.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
  }
}

const dateOptions = `{% for d in dates %}<option value="{{ d }}">{{ d }}</option>{% endfor %}`;
function addTxRow(name='', amt='', date='', type='in') {
  const div = document.createElement('div');
  div.className = 'tx-row';
  div.innerHTML = `
    <select class="tx-type">
      <option value="in" ${type === 'in' ? 'selected' : ''}>Incoming (From)</option>
      <option value="out" ${type === 'out' ? 'selected' : ''}>Outgoing (To)</option>
    </select>
    <select class="tx-date">${dateOptions}</select>
    <input class="tx-name" placeholder="Recipient name" value="${name}">
    <input class="tx-amt" type="number" step="0.01" placeholder="Amount" value="${amt}">
    <button type="button" onclick="this.parentElement.remove()">×</button>
  `;
  document.getElementById('tx-container').appendChild(div);
}

function editUser(slug){ window.location.href = '/admin/edit/' + slug; }

async function load(){
  const r=await fetch('/admin/api/links');
  const data=await r.json();
  const el=document.getElementById('list');
  if(!data.length){el.textContent='no links yet';return;}
  let h='<table><tr><th>User</th><th>Lang</th><th>Bal</th><th>Status</th><th>Actions</th></tr>';
  for(const l of data){
    let statusClass = l.withdrawn ? 'done' : (l.pending_until ? 'pending' : (l.opened_at ? 'open' : ''));
    let statusText = l.withdrawn ? 'Completed' : (l.pending_until ? 'Pending' : (l.opened_at ? 'Opened' : 'Unopened'));
    let displayBank = l.custom_bank || '{{ bank_name }}';
    h+=`<tr>
      <td><b>${l.name}</b><br><span class="code">${displayBank}</span></td>
      <td>${l.language || 'en'}</td>
      <td><span class="code">${l.currency} ${l.balance}</span></td>
      <td><span class="status ${statusClass}">${statusText}</span></td>
      <td>
        <button onclick="editUser('${l.slug}')" style="background:#1f2a44;padding:.4rem .8rem;font-size:.8rem;margin:0">Edit</button>
        <a href="/v/${l.slug}/dashboard" target="_blank" style="text-decoration:none"><button style="background:#1e3a8a;padding:.4rem .8rem;font-size:.8rem;margin:0">Preview</button></a>
        <button onclick="delUser('${l.slug}')" style="background:#7f1d1d;padding:.4rem .8rem;font-size:.8rem;margin:0">Del</button>
      </td>
    </tr>`;
  }
  el.innerHTML=h+'</table>';
}

async function delUser(slug){ if(!confirm('delete?'))return; await fetch('/admin/api/links/'+slug,{method:'DELETE'}); load(); }

document.getElementById('gen').onsubmit=async(e)=>{
  e.preventDefault();
  const formData = new FormData(e.target);
  const txs = [];
  document.querySelectorAll('.tx-row').forEach(row => {
    const type = row.querySelector('.tx-type').value;
    const date = row.querySelector('.tx-date').value;
    const name = row.querySelector('.tx-name').value.trim();
    let amt = parseFloat(row.querySelector('.tx-amt').value);
    if(name && !isNaN(amt) && amt !== 0){
      if(type === 'out') amt = -Math.abs(amt); else amt = Math.abs(amt);
      txs.push({name: name, amount: amt, date: date});
    }
  });
  const body = Object.fromEntries(formData.entries());
  body.balance = parseFloat(body.balance);
  body.transactions = JSON.stringify(txs);
  
  const r=await fetch('/admin/api/links',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  const url=location.origin+'/v/'+d.slug+'/dashboard';
  document.getElementById('out').innerHTML=`link: <a href="${url}" target="_blank">${url}</a>`;
  e.target.reset(); document.getElementById('tx-container').innerHTML=''; load();
};

document.getElementById('chpw').onsubmit=async(e)=>{
  e.preventDefault();
  const body=Object.fromEntries(new FormData(e.target).entries());
  const r=await fetch('/admin/api/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  const m=document.getElementById('pwmsg');
  m.textContent=d.ok?'password updated':(d.error||'failed');
  m.className=d.ok?'ok':'err';
  if(d.ok) e.target.reset();
};

load();
</script>
</body></html>
"""

ADMIN_EDIT_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Edit User</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#0b0f1a;color:#e8eefc;font-family:system-ui,sans-serif;margin:0;padding:2rem}
.card{max-width:600px;margin:0 auto;background:#111827;padding:1.5rem;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
label{display:block;font-size:.85rem;color:#9aa7c7;margin-top:.8rem}
input,select{width:100%;padding:.6rem;margin-top:.3rem;background:#0b1220;border:1px solid #1f2a44;color:#e8eefc;border-radius:8px;box-sizing:border-box;font-family:inherit}
button{padding:.7rem 1.2rem;background:#2563eb;color:#fff;border:0;border-radius:8px;cursor:pointer;font-weight:600;margin-top:1rem}
a{color:#60a5fa}
.pw-wrap{position:relative}
.pw-wrap input{padding-right:2.5rem}
.pw-toggle{position:absolute;right:0.8rem;top:50%;transform:translateY(-50%);cursor:pointer;color:#7d8bab;background:none;border:none;padding:0;margin:0;display:flex;align-items:center}
.pw-toggle svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pw-toggle:hover{color:#e8eefc}
.tx-row{display:grid;grid-template-columns:1.5fr 1fr 1.5fr 1fr 30px;gap:.5rem;margin-bottom:.5rem;align-items:center}
.tx-row input, .tx-row select{margin:0}
.tx-row button{margin:0;padding:0;background:#7f1d1d;border-radius:8px;height:36px}
</style></head><body>
<div class="card">
  <a href="/admin" style="text-decoration:none">&larr; Back to Admin</a>
  <h2 style="margin-top:1rem">Edit: {{ rec.name }}</h2>
  
  <div style="background:#0b1220;padding:1rem;border-radius:8px;margin-bottom:1.5rem;border:1px solid #1f2a44">
    <label style="margin-top:0">User Link</label>
    <a href="/v/{{ rec.slug }}/dashboard" target="_blank" style="font-size:.9rem">/v/{{ rec.slug }}/dashboard</a>
  </div>

  <form id="edit">
    <label>Custom Bank Name</label>
    <input name="custom_bank" value="{{ rec.custom_bank or '' }}" placeholder="{{ bank_name }}">
    
    <label>Language</label>
    <select name="language">
      {% for code, name in languages.items() %}
      <option value="{{ code }}" {% if rec.language == code %}selected{% endif %}>{{ name }}</option>
      {% endfor %}
    </select>

    <label>Balance</label>
    <input name="balance" type="number" step="0.01" value="{{ rec.balance }}" required>
    
    <label>Withdrawal Code (leave blank to keep current)</label>
    <div class="pw-wrap">
      <input name="withdraw_code" type="password" placeholder="{{ rec.withdraw_code }}">
      <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
    </div>

    <label>User Password (leave blank to keep current)</label>
    <div class="pw-wrap">
      <input name="user_password" type="password" placeholder="New password">
      <button type="button" class="pw-toggle" onclick="togglePw(this)"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
    </div>
    
    <label style="margin-top:1.5rem">Transactions</label>
    <div id="tx-container"></div>
    <button type="button" onclick="addTxRow()" style="background:#1f2a44;font-size:.8rem;padding:.4rem .8rem">+ Add Transaction</button>
    
    <div style="margin-top:2rem;display:flex;gap:1rem">
      <button type="submit">Save Changes</button>
      <a href="/v/{{ rec.slug }}/dashboard" target="_blank" style="text-decoration:none;padding:.7rem 1.2rem;background:#1e3a8a;border-radius:8px;font-weight:600;font-size:.9rem;display:inline-block">Preview as User</a>
    </div>
    <div id="msg" style="margin-top:1rem;color:#4ade80"></div>
  </form>
</div>
<script>
let initialTx = [];
try { initialTx = JSON.parse('{{ rec.transactions | safe }}'); } catch(e){}

function togglePw(btn){
  const input = btn.previousElementSibling;
  const icon = btn.querySelector('svg');
  if(input.type === 'password'){
    input.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
  } else {
    input.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
  }
}

const dateOptions = `{% for d in dates %}<option value="{{ d }}">{{ d }}</option>{% endfor %}`;
function addTxRow(name='', amt='', date='', type='in') {
  const div = document.createElement('div');
  div.className = 'tx-row';
  div.innerHTML = `
    <select class="tx-type">
      <option value="in" ${type === 'in' ? 'selected' : ''}>Incoming (From)</option>
      <option value="out" ${type === 'out' ? 'selected' : ''}>Outgoing (To)</option>
    </select>
    <select class="tx-date">${dateOptions}</select>
    <input class="tx-name" placeholder="Recipient name" value="${name}">
    <input class="tx-amt" type="number" step="0.01" placeholder="Amount" value="${amt}">
    <button type="button" onclick="this.parentElement.remove()">×</button>
  `;
  document.getElementById('tx-container').appendChild(div);
}

initialTx.forEach(tx => {
  const type = tx.amount < 0 ? 'out' : 'in';
  const amt = Math.abs(tx.amount);
  addTxRow(tx.name, amt, tx.date, type);
});

document.getElementById('edit').onsubmit = async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  
  const txs = [];
  document.querySelectorAll('.tx-row').forEach(row => {
    const type = row.querySelector('.tx-type').value;
    const date = row.querySelector('.tx-date').value;
    const name = row.querySelector('.tx-name').value.trim();
    let amt = parseFloat(row.querySelector('.tx-amt').value);
    if(name && !isNaN(amt) && amt !== 0){
      if(type === 'out') amt = -Math.abs(amt); else amt = Math.abs(amt);
      txs.push({name: name, amount: amt, date: date});
    }
  });
  
  const body = Object.fromEntries(formData.entries());
  body.transactions = JSON.stringify(txs);
  
  const r = await fetch('/admin/api/edit/{{ rec.slug }}', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  });
  const d = await r.json();
  if(d.ok) document.getElementById('msg').textContent = 'Saved successfully!';
  else document.getElementById('msg').textContent = d.error || 'Failed';
};
</script>
</body></html>
"""

def render_admin(authed=False, first_run=False, error=None):
    return render_template_string(ADMIN_HTML, authed=authed, first_run=first_run, error=error, languages=LANGUAGES, bank_name=BANK_NAME, currencies=CURRENCIES, dates=PAST_YEAR_DATES)

@app.route("/admin")
def admin_page():
    if session.get("admin"): return render_admin(authed=True)
    return render_admin(authed=False, first_run=get_admin_hash() is None)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    if check_pw(request.form.get("password",""), get_admin_hash()):
        session["admin"]=True
        return redirect(url_for("admin_page"))
    return render_admin(authed=False, error="wrong password")

@app.route("/admin/setpw", methods=["POST"])
def admin_setpw():
    if get_admin_hash() is not None: return redirect(url_for("admin_page"))
    pw=request.form.get("password",""); cf=request.form.get("confirm","")
    if pw!=cf or len(pw)<4: return render_admin(authed=False, first_run=True, error="passwords must match (min 4)")
    set_admin_hash(hash_pw(pw))
    session["admin"]=True
    return redirect(url_for("admin_page"))

@app.route("/admin/api/password", methods=["POST"])
@admin_required
def change_pw():
    d=request.get_json(force=True)
    if not check_pw(d.get("current",""), get_admin_hash()):
        return jsonify({"error":"current password wrong"}),403
    n=d.get("new","")
    if len(n)<4: return jsonify({"error":"min 4 chars"}),400
    set_admin_hash(hash_pw(n))
    return jsonify({"ok":True})

@app.route("/admin/edit/<slug>")
@admin_required
def admin_edit(slug):
    rec = db_get_link(slug)
    if not rec: abort(404)
    return render_template_string(ADMIN_EDIT_HTML, rec=rec, languages=LANGUAGES, bank_name=BANK_NAME, currencies=CURRENCIES, dates=PAST_YEAR_DATES)

@app.route("/admin/api/edit/<slug>", methods=["POST"])
@admin_required
def admin_api_edit(slug):
    rec = db_get_link(slug)
    d = request.get_json(force=True)
    if "balance" in d: rec["balance"] = float(d["balance"])
    if "language" in d: rec["language"] = d["language"]
    if "custom_bank" in d: rec["custom_bank"] = d["custom_bank"].strip() or None
    if "transactions" in d: rec["transactions"] = d["transactions"]
    if d.get("withdraw_code"): rec["withdraw_code"] = d["withdraw_code"].strip()
    if d.get("user_password"): rec["password_hash"] = hash_pw(d["user_password"].strip())
    db_put_link(rec)
    return jsonify({"ok": True})

@app.route("/admin/api/links", methods=["GET"])
@admin_required
def list_links(): return jsonify(db_list_links())

@app.route("/admin/api/links", methods=["POST"])
@admin_required
def create_link():
    d=request.get_json(force=True)
    name=(d.get("name") or "").strip()
    cur=(d.get("currency") or "USD").strip()
    bal=float(d.get("balance") or 0)
    code=(d.get("withdraw_code") or "").strip()
    user_pw=(d.get("user_password") or "").strip()
    txs=(d.get("transactions") or "[]")
    lang=(d.get("language") or "en").strip()
    custom_bank=(d.get("custom_bank") or "").strip() or None
    
    if not name or not code or not user_pw: return jsonify({"error":"name, code, and user_password required"}),400
    slug=uuid.uuid4().hex
    rec={
        "slug":slug,"name":name,"currency":cur,"balance":bal,
        "withdraw_code":code,"password_hash":hash_pw(user_pw),
        "transactions":txs,"withdrawn":False,"bank":None,
        "account":None,"withdrawn_amount":None,"created":int(time.time()),
        "opened_at":None,"withdrawn_at":None,"pending_until":None,
        "language":lang, "custom_bank":custom_bank
    }
    db_put_link(rec)
    return jsonify({"slug":slug})

@app.route("/admin/api/links/<slug>", methods=["DELETE"])
@admin_required
def delete_link(slug):
    db_delete_link(slug)
    return jsonify({"ok":True})

# ---------------- boot ----------------

init_db()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))