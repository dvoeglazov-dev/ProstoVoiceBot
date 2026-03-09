import logging
import os
from dotenv import load_dotenv
from gtts import gTTS
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Включим логирование, чтобы видеть ошибки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден! Проверьте файл .env")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я могу озвучить твой текст голосом.\n"
        "Просто отправь мне любой текст, и я пришлю голосовое сообщение."
    )

# Функция для команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь мне текст, и я прочитаю его вслух.")

# Основная функция обработки текстовых сообщений
async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем текст сообщения от пользователя
    user_text = update.message.text

    # Проверяем, что текст не слишком длинный (ограничение Telegram на голосовые - 50 МБ, но gTTS может глючить с огромными текстами)
    if len(user_text) > 3000:
        await update.message.reply_text("Текст слишком длинный. Пожалуйста, отправь не более 3000 символов.")
        return

    # Сообщаем пользователю, что процесс начался
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text("🎤 Генерирую голосовое сообщение, подожди секунду...")

    try:
        # Создаем объект gTTS
        # Язык 'ru' - русский. Можно поменять на 'en' для английского
        tts = gTTS(text=user_text, lang='ru', slow=False)

        # Сохраняем в временный файл
        audio_file = "voice.ogg" # Telegram лучше понимает .ogg или .mp3
        tts.save(audio_file)

        # Отправляем голосовое сообщение
        with open(audio_file, 'rb') as audio:
            # Используем send_voice для отправки как голосового сообщения
            await update.message.reply_voice(voice=audio)

        # Удаляем файл после отправки, чтобы не засорять сервер
        os.remove(audio_file)

    except Exception as e:
        logger.error(f"Ошибка при озвучке: {e}")
        await update.message.reply_text("Произошла ошибка при генерации голоса. Попробуй другой текст или позже.")

# Функция обработки ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик текстовых сообщений (не команд)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота (polling - метод постоянного опроса серверов Telegram)
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()