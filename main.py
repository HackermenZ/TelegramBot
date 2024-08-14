# #attempt8
# import logging
# from telegram import Update, ReplyKeyboardMarkup
# from telegram.ext import Application, CommandHandler, ContextTypes
# import requests

# # Replace with your own credentials
# TELEGRAM_BOT_TOKEN = '7088554458:AAH_AvRCVBS53SjEXGaQeFGqi0cxg053T9o'
# WEATHER_API_KEY = '79dc321827af407f77876e87f2795ed2'

# # Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Location for weather updates
# LOCATION_LAT = 23.8103  # Latitude for Dhaka
# LOCATION_LON = 90.4125  # Longitude for Dhaka


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     keyboard = [['Get Weather', 'Notify Me']]
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
#     await update.message.reply_text(
#         "Welcome to the Bangladesh Weather Bot! Type 'Get Weather' to get the current weather in Dhaka.",
#         reply_markup=reply_markup
#     )


# async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     try:
#         # Get weather data for Dhaka
#         weather_data = get_weather_data(LOCATION_LAT, LOCATION_LON)

#         # Send weather data to the user
#         await update.message.reply_text(f"Weather in Dhaka:\n{weather_data}")

#     except Exception as e:
#         # Log the exception and notify the user
#         logger.error(f"Error fetching weather data: {str(e)}")
#         await update.message.reply_text("Sorry, something went wrong while fetching the weather data.")


# async def update_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     # Get weather data for Dhaka
#     weather_data = get_weather_data(LOCATION_LAT, LOCATION_LON)
#     await update.message.reply_text(f"Updated weather in Dhaka:\n{weather_data}")


# async def notify_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text("You will be notified of extreme weather conditions in Dhaka.")
#     context.job_queue.run_repeating(check_weather_conditions, interval=3600, first=10, chat_id=update.message.chat_id)


# async def check_weather_conditions(context: ContextTypes.DEFAULT_TYPE) -> None:
#     chat_id = context.job.chat_id
#     weather_data = get_weather_data(LOCATION_LAT, LOCATION_LON)
#     if is_extreme_weather(weather_data):
#         await context.bot.send_message(chat_id, f"Extreme weather alert:\n{weather_data}")


# def get_weather_data(lat: float, lon: float) -> str:
#     url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for HTTP errors
#         data = response.json()

#         weather_description = data['weather'][0]['description']
#         temperature = data['main']['temp']
#         feels_like = data['main']['feels_like']
#         temp_min = data['main']['temp_min']
#         temp_max = data['main']['temp_max']
#         humidity = data['main']['humidity']
#         wind_speed = data['wind']['speed']

#         return (f"Description: {weather_description}\n"
#                 f"Temperature: {temperature}°C (Feels like: {feels_like}°C)\n"
#                 f"Min/Max Temperature: {temp_min}°C/{temp_max}°C\n"
#                 f"Humidity: {humidity}%\n"
#                 f"Wind Speed: {wind_speed} m/s")
#     except requests.RequestException as e:
#         logger.error(f"Error fetching weather data: {str(e)}")
#         return "Failed to fetch weather data"


# def is_extreme_weather(weather_data: str) -> bool:
#     extreme_conditions = ['rain', 'thunderstorm', 'heat wave']
#     return any(condition in weather_data.lower() for condition in extreme_conditions)


# def main() -> None:
#     application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

#     # You can directly access the job_queue from the application
#     job_queue = application.job_queue

#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("get_weather", get_weather))
#     application.add_handler(CommandHandler("update", update_weather))
#     application.add_handler(CommandHandler("notify_me", notify_me))

#     # Start the JobQueue before running the bot
#     job_queue.start()

#     application.run_polling()

# if __name__ == '__main__':
#     main()




import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import requests

# Replace with your own credentials
TELEGRAM_BOT_TOKEN = '7088554458:AAH_AvRCVBS53SjEXGaQeFGqi0cxg053T9o'
WEATHER_API_KEY = '79dc321827af407f77876e87f2795ed2'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Stages of the conversation
ASK_CITY, ASK_THANA, GET_LOCATION_FOR_UPDATE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [['Get Weather', 'Notify Me']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to the Bangladesh Weather Bot! Please enter your city to get started.",
        reply_markup=reply_markup
    )
    return ASK_CITY

async def ask_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    context.user_data['city'] = city
    await update.message.reply_text(f"Great! Now, please enter your Thana in {city}:")
    return ASK_THANA

async def ask_thana(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    thana = update.message.text
    city = context.user_data['city']
    location = f"{thana}, {city}, Bangladesh"

    lat, lon = get_location_from_osm(location)

    if lat is not None and lon is not None:
        context.user_data['lat'] = lat
        context.user_data['lon'] = lon
        weather_data = get_weather_data(lat, lon)
        await update.message.reply_text(f"Weather in {thana}, {city}:\n{weather_data}")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Sorry, I couldn't find your location. Please use /start to set your location again.")
        return ConversationHandler.END

async def update_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'lat' in context.user_data and 'lon' in context.user_data:
        lat = context.user_data['lat']
        lon = context.user_data['lon']
        weather_data = get_weather_data(lat, lon)
        await update.message.reply_text(f"Updated weather for your location:\n{weather_data}")
    else:
        await update.message.reply_text("Please click /start first.")
        return GET_LOCATION_FOR_UPDATE
    return ConversationHandler.END

async def get_location_for_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    context.user_data['city'] = city
    await update.message.reply_text(f"Please enter your Thana in {city}:")
    return GET_LOCATION_FOR_UPDATE

async def set_location_for_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    thana = update.message.text
    city = context.user_data['city']
    location = f"{thana}, {city}, Bangladesh"

    lat, lon = get_location_from_osm(location)

    if lat is not None and lon is not None:
        context.user_data['lat'] = lat
        context.user_data['lon'] = lon
        weather_data = get_weather_data(lat, lon)
        await update.message.reply_text(f"Location updated. Current weather:\n{weather_data}")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Sorry, I couldn't find your location. Please use /start to set your location again.")
        return ConversationHandler.END

async def notify_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if 'lat' in context.user_data and 'lon' in context.user_data:
        await update.message.reply_text("You will be notified of extreme weather conditions in your location.")

        # Remove any existing job for this chat_id to avoid duplicates
        existing_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in existing_jobs:
            job.schedule_removal()

        # Schedule a new job
        context.job_queue.run_repeating(check_weather_conditions, interval=3600, first=10, chat_id=chat_id, data=context.user_data)
    else:
        await update.message.reply_text("Location not set. Please set your location first using /start.")

async def check_weather_conditions(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    user_data = context.job.data
    lat = user_data.get('lat')
    lon = user_data.get('lon')

    if lat is None or lon is None:
        logger.warning(f"Location not set for chat_id {chat_id}.")
        await context.bot.send_message(chat_id, "Location not set. Please set your location first using /start.")
        return

    try:
        weather_data = get_weather_data(lat, lon)
        if weather_data and is_extreme_weather(weather_data):
            await context.bot.send_message(chat_id, f"Extreme weather alert:\n{weather_data}")
    except Exception as e:
        logger.error(f"Error in checking weather conditions: {e}")
        await context.bot.send_message(chat_id, "Failed to retrieve weather data. Please try again later.")

def get_location_from_osm(location: str) -> tuple:
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    try:
        response = requests.get(url, headers={"User-Agent": "telegram-weather-bot"})
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
        else:
            return None, None
    except requests.RequestException as e:
        logger.error(f"Error fetching location data: {str(e)}")
        return None, None

def get_weather_data(lat: float, lon: float) -> str:
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if not data or 'weather' not in data:
            logger.error("Invalid response received from weather API.")
            return None

        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        feels_like = data['main']['feels_like']
        temp_min = data['main']['temp_min']
        temp_max = data['main']['temp_max']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        # Get timezone offset in seconds
        timezone_offset = data['timezone']

        # Convert sunrise and sunset times from UTC to local time
        sunrise_utc = datetime.utcfromtimestamp(data['sys']['sunrise'])
        sunset_utc = datetime.utcfromtimestamp(data['sys']['sunset'])

        # Calculate local timezone offset
        local_offset = timedelta(seconds=timezone_offset)

        # Convert UTC to local time
        sunrise_local = sunrise_utc + local_offset
        sunset_local = sunset_utc + local_offset

        # Format times to '5:31 AM'
        sunrise = sunrise_local.strftime('%I:%M %p')
        sunset = sunset_local.strftime('%I:%M %p')

        return (f"Description: {weather_description}\n"
                f"Temperature: {temperature}°C (Feels like: {feels_like}°C)\n"
                f"Min Temperature: {temp_min}°C\n"
                f"Max Temperature: {temp_max}°C\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} m/s\n"
                f"Sunrise: {sunrise}\n"
                f"Sunset: {sunset}")
    except requests.RequestException as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        return None

def is_extreme_weather(weather_data: str) -> bool:
    if not weather_data:
        return False
    extreme_conditions = ['rain', 'thunderstorm', 'heat wave', 'drizzle', 'shower']
    return any(condition in weather_data.lower() for condition in extreme_conditions)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Conversation cancelled. Please use /start to begin again.")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_city)],
            ASK_THANA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_thana)],
            GET_LOCATION_FOR_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location_for_update)],
            GET_LOCATION_FOR_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_location_for_update)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("update", update_weather))
    application.add_handler(CommandHandler("notify_me", notify_me))

    application.run_polling()

if __name__ == '__main__':
     main()
