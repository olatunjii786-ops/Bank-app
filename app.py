# app.py — The Ultimate Banking Simulator (Multi-language + Per-user Bank Name)
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
        "premium": "Premium", "today": "Today", "yesterday": "Yesterday"
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
        "premium": "Premium", "today": "Hoy", "yesterday": "Ayer"
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
        "premium": "Premium", "today": "Aujourd'hui", "yesterday": "Hier"
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
        "premium": "Premium", "today": "Hoje", "yesterday": "Ontem"
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
        "premium": "Premium", "today": "Heute", "yesterday": "Gestern"
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
        "premium": "Premium", "today": "Oggi", "yesterday": "Ieri"
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
        "premium": "Premium", "today": "Òní", "yesterday": "Àná"
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
        "premium": "Premium", "today": "Yau", "yesterday": "Jiya"
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
        "premium": "Premium", "today": "Taa", "yesterday": "Ụnyaahụ"
    }
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
.avatar-wrap{position:relative}
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
}
if(localStorage.getItem('theme') === 'light'){ document.documentElement.setAttribute('data-theme', 'light'); }
</script>
"""

# ---------------- Pages ----------------

DASHBOARD_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>{{ name }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
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
  <div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div><div class="badge"><svg viewBox="0 0 24 24" fill="#fff" width="10" height="10"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div></div>
</div>
<div class="wrap">
  <div class="hero-card">
    <div class="hero-content">
      <div class="bank-logo-sm">
        <div class="icon"><svg viewBox="0 0 24 24" fill="#fff" width="14" height="14"><path d="M12 2L2 22h20L12 2z"/></svg></div>
        <div class="txt">{{ bank }}<br>{{ t('premium') }}</div>
      </div>
      <div class="balance-lbl">{{ t('total_balance') }}</div>
      <div class="balance">{{ currency }} {{ "%.2f"|format(balance) }}</div>
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
            <div><div class="ttl">{{ tx.name }}</div><div class="sub">{{ tx.date }}</div></div>
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
<!doctype html><html><head><meta charset="utf-8"><title>{{ t('history') }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar"><div class="greet">{{ t('history') }}<span>{{ t('history') }}</span></div><div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div></div>
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
            <div><div class="ttl">{{ tx.name }}</div><div class="sub">{{ tx.date }}</div></div>
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
<!doctype html><html><head><meta charset="utf-8"><title>{{ t('transfer') }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar"><div class="greet">{{ t('transfer') }}<span>{{ t('transfer') }}</span></div><div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div></div>
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
<!doctype html><html><head><meta charset="utf-8"><title>{{ t('cards') }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar"><div class="greet">{{ t('cards') }}<span>{{ t('cards') }}</span></div><div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div></div>
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
<!doctype html><html><head><meta charset="utf-8"><title>{{ t('settings') }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar"><div class="greet">{{ t('settings') }}<span>{{ t('settings') }}</span></div><div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div></div>
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
<!doctype html><html><head><meta charset="utf-8"><title>{{ t('login') }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
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
<!doctype html><html><head><meta charset="utf-8"><title>{{ t('statement') }} — {{ bank }}</title>
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
      <tr><td>{{ tx.date }}</td><td>{{ tx.name }}</td><td class="{{ 'amt-pos' if tx.amount > 0 else 'amt-neg' }}">{{ '+' if tx.amount > 0 else '-' }}{{ currency }} {{ "{:,.2f}".format(tx.amount|abs) }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
  <div style="margin-top:2rem;text-align:right"><p style="color:#666;font-size:.9rem">{{ t('ending_balance') }}</p><div style="font-size:1.5rem;font-weight:700;color:#111">{{ currency }} {{ "%.2f"|format(balance) }}</div></div>
  <div class="footer">{{ t('stmt_footer') }}<br>For inquiries, please contact support@{{ bank|lower|replace(' ','') }}.com</div>
</div>
<script>window.onload = function() { setTimeout(function(){ window.print(); }, 500); }</script>
</body></html>
"""

# ---------------- Routing ----------------

def build_tab(slug, active, lang):
    return THEME_SCRIPT + f"""
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
    return render_template_string(LOGIN_HTML, css=BANK_CSS, bank=bank, name=rec["name"], slug=slug, t=lambda k: t(lang, k))

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
            for tx in raw_tx:
                key = (tx.get("date") or "").lower()
                if key in ("today", "yesterday"):
                    tx["date"] = t(lang, key)
            tx_list = raw_tx
        except Exception as e:
            print("tx parse err:", e)
        
    if rec.get("withdrawn"):
        tx_list.insert(0, {"name": f"{t(lang, 'transfer_to')} {rec.get('bank')}", "date": time.strftime('%b %d, %Y', time.localtime(rec.get("withdrawn_at") or time.time())), "amount": -(rec.get("withdrawn_amount") or 0)})

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
        tx_list=tx_list, pending_until=pending_until, t=lambda k: t(lang, k)
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
            for tx in raw_tx:
                key = (tx.get("date") or "").lower()
                if key in ("today", "yesterday"):
                    tx["date"] = t(lang, key)
            tx_list = raw_tx
        except Exception: pass
    if rec.get("withdrawn"):
        tx_list.insert(0, {"name": f"{t(lang, 'transfer_to')} {rec.get('bank')}", "date": time.strftime('%b %d, %Y', time.localtime(rec.get("withdrawn_at") or time.time())), "amount": -(rec.get("withdrawn_amount") or 0)})

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
<!doctype html><html><head><meta charset="utf-8"><title>{{ bank }} — Not a user</title>
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
        <select name="currency"><option>USD</option><option>EUR</option><option>GBP</option><option>NGN</option><option>JPY</option><option>CAD</option></select>
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

function addTxRow() {
  const div = document.createElement('div');
  div.className = 'tx-row';
  div.innerHTML = `
    <select class="tx-type"><option value="in">Incoming</option><option value="out">Outgoing</option></select>
    <select class="tx-date"><option value="today">Today</option><option value="yesterday">Yesterday</option><option value="dec14">Dec 14</option><option value="dec13">Dec 13</option></select>
    <input class="tx-name" placeholder="Recipient name">
    <input class="tx-amt" type="number" step="0.01" placeholder="Amount">
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
</style></head><body>
<div class="card">
  <a href="/admin" style="text-decoration:none">&larr; Back to Admin</a>
  <h2 style="margin-top:1rem">Edit: {{ rec.name }}</h2>
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
    
    <div style="margin-top:2rem;display:flex;gap:1rem">
      <button type="submit">Save Changes</button>
      <a href="/v/{{ rec.slug }}/dashboard" target="_blank" style="text-decoration:none;padding:.7rem 1.2rem;background:#1e3a8a;border-radius:8px;font-weight:600;font-size:.9rem;display:inline-block">Preview as User</a>
    </div>
    <div id="msg" style="margin-top:1rem;color:#4ade80"></div>
  </form>
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

document.getElementById('edit').onsubmit = async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target).entries());
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
    return render_template_string(ADMIN_HTML, authed=authed, first_run=first_run, error=error, languages=LANGUAGES, bank_name=BANK_NAME)

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
    return render_template_string(ADMIN_EDIT_HTML, rec=rec, languages=LANGUAGES, bank_name=BANK_NAME)

@app.route("/admin/api/edit/<slug>", methods=["POST"])
@admin_required
def admin_api_edit(slug):
    rec = db_get_link(slug)
    d = request.get_json(force=True)
    if "balance" in d: rec["balance"] = float(d["balance"])
    if "language" in d: rec["language"] = d["language"]
    if "custom_bank" in d: rec["custom_bank"] = d["custom_bank"].strip() or None
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