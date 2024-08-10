#attempt8
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# Replace with your own credentials
TELEGRAM_BOT_TOKEN = '7088554458:AAH_AvRCVBS53SjEXGaQeFGqi0cxg053T9o'
WEATHER_API_KEY = '79dc321827af407f77876e87f2795ed2'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Location for weather updates
LOCATION_LAT = 23.8103  # Latitude for Dhaka
LOCATION_LON = 90.4125  # Longitude for Dhaka


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [['Get Weather', 'Notify Me']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to the Bangladesh Weather Bot! Type 'Get Weather' to get the current weather in Dhaka.",
        reply_markup=reply_markup
    )


async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Get weather data for Dhaka
        weather_data = get_weather_data(LOCATION_LAT, LOCATION_LON)

        # Send weather data to the user
        await update.message.reply_text(f"Weather in Dhaka:\n{weather_data}")

    except Exception as e:
        # Log the exception and notify the user
        logger.error(f"Error fetching weather data: {str(e)}")
        await update.message.reply_text("Sorry, something went wrong while fetching the weather data.")


async def update_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get weather data for Dhaka
    weather_data = get_weather_data(LOCATION_LAT, LOCATION_LON)
    await update.message.reply_text(f"Updated weather in Dhaka:\n{weather_data}")


async def notify_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("You will be notified of extreme weather conditions in Dhaka.")
    context.job_queue.run_repeating(check_weather_conditions, interval=3600, first=10, chat_id=update.message.chat_id)


async def check_weather_conditions(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    weather_data = get_weather_data(LOCATION_LAT, LOCATION_LON)
    if is_extreme_weather(weather_data):
        await context.bot.send_message(chat_id, f"Extreme weather alert:\n{weather_data}")


def get_weather_data(lat: float, lon: float) -> str:
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        feels_like = data['main']['feels_like']
        temp_min = data['main']['temp_min']
        temp_max = data['main']['temp_max']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        return (f"Description: {weather_description}\n"
                f"Temperature: {temperature}°C (Feels like: {feels_like}°C)\n"
                f"Min/Max Temperature: {temp_min}°C/{temp_max}°C\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} m/s")
    except requests.RequestException as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        return "Failed to fetch weather data"


def is_extreme_weather(weather_data: str) -> bool:
    extreme_conditions = ['rain', 'thunderstorm', 'heat wave']
    return any(condition in weather_data.lower() for condition in extreme_conditions)


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # You can directly access the job_queue from the application
    job_queue = application.job_queue

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_weather", get_weather))
    application.add_handler(CommandHandler("update", update_weather))
    application.add_handler(CommandHandler("notify_me", notify_me))

    # Start the JobQueue before running the bot
    job_queue.start()

    application.run_polling()

if __name__ == '__main__':
    main()
