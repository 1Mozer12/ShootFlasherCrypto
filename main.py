import logging
import os
import json
from urllib import request as urlrequest
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN") or "8744840927:AAG4ibdC1O1s9lueUh0rxccL4oh4gIOt_Gs"
OXAPAY_MERCHANT_KEY = os.getenv("OXAPAY_MERCHANT_KEY")

if not TOKEN:
    raise ValueError("Brak BOT_TOKEN w zmiennych środowiskowych!")
if not OXAPAY_MERCHANT_KEY:
    raise ValueError("Brak OXAPAY_MERCHANT_KEY w zmiennych środowiskowych!")

LANGUAGES = {
    'pl': 'Polski 🇵🇱',
    'en': 'English 🇬🇧',
    'ru': 'Русский 🇷🇺'
}

TEXTS = {
    'pl': {
        'welcome_first': "Wybierz język / Choose language / Выберите язык:",
        'welcome': "Witaj! Jestem botem do zakupu licencji na **Crypto Flasher** 🚀",
        'main_menu_text': "Co chcesz zrobić?\n\nKliknij przycisk poniżej, żeby zobaczyć opcje zakupu licencji.",
        'buy_license': "Kup licencję Crypto Flasher",
        'change_language': "Zmień język",
        'prices_title': "Wybierz plan licencji:",
        'back_to_menu': "Wróć do menu głównego",

        'test_flash': "Wybrałeś **Test flash – 1 USD**\nPrzekierowuję do płatności...",
        '7days': "Wybrałeś **7 dni – 10 USD**\nPrzekierowuję do płatności...",
        '1month': "Wybrałeś **1 miesiąc – 15 USD**\nPrzekierowuję do płatności...",
        'lifetime': "Wybrałeś **Lifetime – 40 USD**\nPrzekierowuję do płatności...",

        'payment_link': "Kliknij poniżej, żeby zapłacić crypto (OxaPay):",
        'test_key': "TESTOWY KLUCZ (tymczasowy):\n`TEST-KEY-{plan}-{random}`\n\nPo zapłacie napisz do admina, żeby aktywować klucz.",

        'error_invoice': "Błąd przy tworzeniu płatności. Sprawdź logi lub napisz do admina.",
        'help_title': "📋 Dostępne komendy:",
        'help_text': "/start – rozpocznij / wróć do menu\n/language – zmień język\n/pomoc – ten spis komend",
    },
    'en': {
        'welcome_first': "Choose your language / Wybierz język / Выберите язык:",
        'welcome': "Welcome! I'm the bot for purchasing **Crypto Flasher** license 🚀",
        'main_menu_text': "What would you like to do?\n\nClick below to see license purchase options.",
        'buy_license': "Buy Crypto Flasher License",
        'change_language': "Change language",
        'prices_title': "Choose license plan:",
        'back_to_menu': "Back to main menu",

        'test_flash': "You selected **Test flash – 1 USD**\nRedirecting to payment...",
        '7days': "You selected **7 days – 10 USD**\nRedirecting to payment...",
        '1month': "You selected **1 month – 15 USD**\nRedirecting to payment...",
        'lifetime': "You selected **Lifetime – 40 USD**\nRedirecting to payment...",

        'payment_link': "Click below to pay with crypto (OxaPay):",
        'test_key': "TEST KEY (temporary):\n`TEST-KEY-{plan}-{random}`\n\nAfter payment contact admin to activate the key.",

        'error_invoice': "Error creating payment. Check logs or contact admin.",
        'help_title': "📋 Available commands:",
        'help_text': "/start – start / return to main menu\n/language – change language\n/pomoc – this help message",
    },
    'ru': {
        'welcome_first': "Выберите язык / Choose your language / Wybierz język:",
        'welcome': "Привет! Я бот для покупки лицензии на **Crypto Flasher** 🚀",
        'main_menu_text': "Что вы хотите сделать?\n\nНажмите ниже, чтобы увидеть варианты покупки лицензии.",
        'buy_license': "Купить лицензию Crypto Flasher",
        'change_language': "Изменить язык",
        'prices_title': "Выберите план лицензии:",
        'back_to_menu': "Вернуться в главное меню",

        'test_flash': "Вы выбрали **Test flash – 1 USD**\nПереходим к оплате...",
        '7days': "Вы выбрали **7 дней – 10 USD**\nПереходим к оплате...",
        '1month': "Вы выбрали **1 месяц – 15 USD**\nПереходим к оплате...",
        'lifetime': "Вы выбрали **Lifetime – 40 USD**\nПереходим к оплате...",

        'payment_link': "Нажмите ниже, чтобы оплатить криптовалютой (OxaPay):",
        'test_key': "ТЕСТОВЫЙ КЛЮЧ (временный):\n`TEST-KEY-{plan}-{random}`\n\nПосле оплаты напишите админу для активации ключа.",

        'error_invoice': "Ошибка при создании платежа. Проверьте логи или напишите админу.",
        'help_title': "📋 Доступные команды:",
        'help_text': "/start – начать / вернуться в меню\n/language – сменить язык\n/pomoc – эта справка",
    }
}

DEFAULT_LANG = 'en'

def get_text(lang: str, key: str, **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS[DEFAULT_LANG]).get(key, "Brak tłumaczenia")
    return text.format(**kwargs)

def create_oxapay_invoice(amount: float, description: str, order_id: str) -> str | None:
    url = "https://api.oxapay.com/v1/payment/invoice"
    payload = {
        "merchant_api_key": OXAPAY_MERCHANT_KEY,
        "amount": amount,
        "currency": "USD",
        "lifeTime": 3600,
        "feePaidByPayer": 0,
        "underPaidCover": 0.0,
        "toCurrency": "USDT",
        "description": description,
        "orderId": order_id,
        "returnUrl": "https://t.me/ShootFlasherBot"
    }

    data = json.dumps(payload).encode('utf-8')
    headers = {"Content-Type": "application/json"}

    req = urlrequest.Request(url, data=data, headers=headers, method='POST')

    try:
        with urlrequest.urlopen(req) as response:
            result_text = response.read().decode('utf-8')
            logger.info(f"OxaPay raw response: {result_text}")
            result = json.loads(result_text)
            if result.get("result") == 100:
                pay_link = result["data"].get("payLink") or result["data"].get("invoiceUrl")
                if pay_link:
                    return pay_link
                else:
                    logger.error("Brak payLink w odpowiedzi")
                    return None
            else:
                logger.error(f"OxaPay zwrócił błąd: {result}")
                return None
    except Exception as e:
        logger.error(f"Błąd urllib: {str(e)}")
        return None

async def show_main_menu(message_or_query, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'buy_license'), callback_data='show_plans')],
        [InlineKeyboardButton(get_text(lang, 'change_language'), callback_data='change_lang')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = get_text(lang, 'welcome') + "\n\n" + get_text(lang, 'main_menu_text')

    if hasattr(message_or_query, 'reply_text'):
        await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await message_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_plans_menu(message_or_query, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    keyboard = [
        [InlineKeyboardButton("Test flash – 1 USD", callback_data='plan_test')],
        [InlineKeyboardButton("7 days – 10 USD", callback_data='plan_7days')],
        [InlineKeyboardButton("1 month – 15 USD", callback_data='plan_1month')],
        [InlineKeyboardButton("Lifetime – 40 USD", callback_data='plan_lifetime')],
        [InlineKeyboardButton(get_text(lang, 'back_to_menu'), callback_data='back_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = get_text(lang, 'prices_title')

    if hasattr(message_or_query, 'reply_text'):
        await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await message_or_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    lang = user_data.get('language')

    if lang in LANGUAGES:
        await show_main_menu(update, context, lang)
        return

    keyboard = [
        [
            InlineKeyboardButton(LANGUAGES['pl'], callback_data='setlang_pl'),
            InlineKeyboardButton(LANGUAGES['en'], callback_data='setlang_en'),
            InlineKeyboardButton(LANGUAGES['ru'], callback_data='setlang_ru'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        get_text(DEFAULT_LANG, 'welcome_first'),
        reply_markup=reply_markup
    )

async def pomoc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get('language', DEFAULT_LANG)
    text = f"{get_text(lang, 'help_title')}\n\n{get_text(lang, 'help_text')}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    user_data = context.user_data
    lang = user_data.get('language', DEFAULT_LANG)
    user_id = query.from_user.id

    if data.startswith('setlang_'):
        lang_code = data.split('_')[1]
        if lang_code in LANGUAGES:
            user_data['language'] = lang_code
            confirm = get_text(lang_code, 'language_set').format(LANGUAGES[lang_code])
            await query.edit_message_text(confirm + "\n\n" + get_text(lang_code, 'main_menu_text'))
            await show_main_menu(query, context, lang_code)

    elif data == 'show_plans':
        await show_plans_menu(query, context, lang)

    elif data == 'change_lang':
        keyboard = [
            [
                InlineKeyboardButton(LANGUAGES['pl'], callback_data='setlang_pl'),
                InlineKeyboardButton(LANGUAGES['en'], callback_data='setlang_en'),
                InlineKeyboardButton(LANGUAGES['ru'], callback_data='setlang_ru'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            get_text(lang, 'change_language'),
            reply_markup=reply_markup
        )

    elif data == 'back_menu':
        await show_main_menu(query.message, context, lang)

    elif data.startswith('plan_'):
        plan_key = data.split('_')[1]
        plan_amount = {'test': 1.0, '7days': 10.0, '1month': 15.0, 'lifetime': 40.0}.get(plan_key, 1.0)
        description = f"Licencja Crypto Flasher - {plan_key} dla użytkownika {user_id}"
        order_id = f"order-{user_id}-{plan_key}-{uuid.uuid4().hex[:8]}"

        invoice_url = create_oxapay_invoice(plan_amount, description, order_id)

        if invoice_url:
            keyboard = [[InlineKeyboardButton("Zapłać teraz (OxaPay)", url=invoice_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                get_text(lang, 'payment_link'),
                reply_markup=reply_markup
            )

            test_key = f"TEST-KEY-{plan_key.upper()}-{uuid.uuid4().hex[:8]}"
            await query.message.reply_text(
                get_text(lang, 'test_key', plan=plan_key, random=test_key),
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text(get_text(lang, 'error_invoice'))

def main():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .read_timeout(30.0) \
        .write_timeout(30.0) \
        .connect_timeout(30.0) \
        .pool_timeout(30.0) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pomoc", pomoc))
    app.add_handler(CallbackQueryHandler(button_callback))

    async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = context.user_data.get('language', DEFAULT_LANG)
        await update.message.reply_text("Użyj /start lub /pomoc 😊")

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print("Bot wystartował – polling aktywny")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()