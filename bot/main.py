import os
import logging
import asyncio
import traceback
import firebase_admin
from firebase_admin import credentials, firestore
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN environment variable not found.")
    raise ValueError("You need to set the TELEGRAM_TOKEN environment variable in the .env file.")
else:
    logger.info("TELEGRAM_TOKEN loaded successfully.")

try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing Firebase: {e}")
    traceback.print_exc()
    exit(1)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class UserForm(StatesGroup):
    name = State()
    major = State()
    degree = State()
    year = State()
    country = State()
    likes = State()
    description = State()
    photo = State()
    menu = State()

class ChangeForm(StatesGroup):
    field = State()

class DeleteForm(StatesGroup):
    confirm = State()

class FeedbackForm(StatesGroup):
    waiting_for_feedback = State()

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Go Back", callback_data="go_back")]
    ])

degree_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Bachelor 🎓", callback_data="degree_Bachelor"),
        InlineKeyboardButton(text="Masters 🎓", callback_data="degree_Masters"),
    ],
    [
        InlineKeyboardButton(text="PhD 🧑‍🔬", callback_data="degree_PhD"),
        InlineKeyboardButton(text="Professor 🧑‍🏫", callback_data="degree_Professor"),
    ],
    [
        InlineKeyboardButton(text="Other 🤔", callback_data="degree_Other")
    ],
    [
        InlineKeyboardButton(text="🔙 Go Back", callback_data="go_back")
    ]
])

def get_menu_keyboard(is_active=True):
    buttons = [
        [InlineKeyboardButton(text="📄 My Profile", callback_data="my_profile")],
        [InlineKeyboardButton(text="✏️ Change Personal Information", callback_data="change_info")]
    ]
    if is_active:
        buttons.append([InlineKeyboardButton(text="🔄 Pause Matching", callback_data="pause_matching")])
    else:
        buttons.append([InlineKeyboardButton(text="▶️ Resume Matching", callback_data="resume_matching")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_next_monday():
    today = datetime.now()
    days_ahead = 7 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    return next_monday.strftime('%A, %d %B %Y')

def update_db(user_id, data):
    try:
        user_ref = db.collection('users').document(str(user_id))
        user_ref.set(data, merge=True)
        logger.info(f"Updated Firestore for user {user_id}: {data}")
    except Exception as e:
        logger.error(f"Error updating Firestore: {e}")

def delete_user_data(user_id):
    try:
        user_ref = db.collection('users').document(str(user_id))
        user_ref.delete()
        logger.info(f"Deleted user data for user {user_id}")
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")

def get_user_data(user_id):
    try:
        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()
        if user_doc.exists:
            return user_doc.to_dict()
        else:
            return None
    except Exception as e:
        logger.error(f"Error retrieving user data: {e}")
        return None

@dp.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    if user_data:
        await state.set_state(UserForm.menu)
        await message.answer("👋 Welcome back!")
        await open_menu(message, state)
    else:
        await state.clear()
        await message.answer("👋 Hey there! Let's get you started!")
        await message.answer("Please write your first and last name:")
        await state.set_state(UserForm.name)

@dp.message(UserForm.name, F.content_type.in_([ContentType.TEXT]))
async def ask_major(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("What is your major? 📚", reply_markup=get_back_button())
    await state.set_state(UserForm.major)

@dp.callback_query(F.data == 'go_back')
async def handle_go_back(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    state_order = [
        UserForm.name,
        UserForm.major,
        UserForm.degree,
        UserForm.year,
        UserForm.country,
        UserForm.likes,
        UserForm.description,
        UserForm.photo
    ]
    if current_state in [s.state for s in state_order]:
        current_index = state_order.index(next(s for s in state_order if s.state == current_state))
        if current_index > 0:
            previous_state = state_order[current_index - 1]
            await state.set_state(previous_state)
            prompt = {
                UserForm.name: "Please write your first and last name:",
                UserForm.major: "What is your major? 📚",
                UserForm.degree: "What is your current degree? 🎓",
                UserForm.year: "What year are you in? 🗓 (1-3)",
                UserForm.country: "Which country are you from? 🌍",
                UserForm.likes: "List a few things that you like, separated by commas (e.g., music, sports, books): 🎵⚽📖",
                UserForm.description: "Please drop a few lines about yourself: ✍️",
                UserForm.photo: "Please send your photo: 📸"
            }
            if previous_state == UserForm.degree:
                await callback_query.message.edit_text(prompt[previous_state], reply_markup=degree_keyboard)
            else:
                await callback_query.message.edit_text(prompt[previous_state], reply_markup=get_back_button())
        else:
            await callback_query.answer("You are at the first step.")
    else:
        await callback_query.answer("Cannot go back from here.")

@dp.message(UserForm.major, F.content_type.in_([ContentType.TEXT]))
async def ask_degree(message: types.Message, state: FSMContext):
    await state.update_data(major=message.text)
    await message.answer("What is your current degree? 🎓", reply_markup=degree_keyboard)
    await state.set_state(UserForm.degree)

@dp.callback_query(F.data.startswith("degree_"), UserForm.degree)
async def handle_degree_selection(callback_query: types.CallbackQuery, state: FSMContext):
    degree = callback_query.data.split('_')[1]
    await state.update_data(degree=degree)
    await callback_query.message.edit_text("What year are you in? 🗓 (1-3)", reply_markup=get_back_button())
    await state.set_state(UserForm.year)

@dp.message(UserForm.year, F.content_type.in_([ContentType.TEXT]))
async def ask_country(message: types.Message, state: FSMContext):
    if message.text not in ['1', '2', '3']:
        await message.reply("Please enter a valid year (1, 2, or 3). 🔢", reply_markup=get_back_button())
    else:
        await state.update_data(year=message.text)
        await message.answer("Which country are you from? 🌍", reply_markup=get_back_button())
        await state.set_state(UserForm.country)

@dp.message(UserForm.country, F.content_type.in_([ContentType.TEXT]))
async def ask_likes(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("List a few things that you like, separated by commas (e.g., music, sports, books): 🎵⚽📖", reply_markup=get_back_button())
    await state.set_state(UserForm.likes)

@dp.message(UserForm.likes, F.content_type.in_([ContentType.TEXT]))
async def ask_description(message: types.Message, state: FSMContext):
    interests = [interest.strip() for interest in message.text.split(',')]
    await state.update_data(likes=interests)
    await message.answer("Please drop a few lines about yourself: ✍️", reply_markup=get_back_button())
    await state.set_state(UserForm.description)

@dp.message(UserForm.description, F.content_type.in_([ContentType.TEXT]))
async def ask_photo(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Please send your photo: 📸", reply_markup=get_back_button())
    await state.set_state(UserForm.photo)

@dp.message(UserForm.photo, F.content_type.in_([ContentType.PHOTO]))
async def finish_registration(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo=photo_file_id)
    user_data = await state.get_data()
    user_id = message.from_user.id
    user_info = {
        'tg_id': str(user_id),
        'full_name': user_data.get('name'),
        'major': user_data.get('major'),
        'degree': user_data.get('degree'),
        'year': user_data.get('year'),
        'country': user_data.get('country'),
        'interests': user_data.get('likes'),
        'description': user_data.get('description'),
        'photo': photo_file_id,
        'is_active': True,
        'last_matched': None
    }
    update_db(user_id, user_info)
    await message.answer("🎉 Alright, you’re in the pool!")
    next_monday = get_next_monday()
    await message.answer(f"📅 You’ll be matched on Monday: {next_monday}")
    await state.set_state(UserForm.menu)
    await open_menu(message, state)

@dp.message(UserForm.photo)
async def photo_error(message: types.Message, state: FSMContext):
    await message.reply("Please send a valid photo. 📸", reply_markup=get_back_button())

@dp.callback_query(F.data == 'change_info')
async def change_info(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Which information would you like to change? ✏️", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Name 📝", callback_data="change_name")],
            [InlineKeyboardButton(text="Major 📚", callback_data="change_major")],
            [InlineKeyboardButton(text="Degree 🎓", callback_data="change_degree")],
            [InlineKeyboardButton(text="Year 🗓", callback_data="change_year")],
            [InlineKeyboardButton(text="Country 🌍", callback_data="change_country")],
            [InlineKeyboardButton(text="Interests 🎵⚽📖", callback_data="change_likes")],
            [InlineKeyboardButton(text="Description ✍️", callback_data="change_description")],
            [InlineKeyboardButton(text="Photo 📸", callback_data="change_photo")],
            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_menu")]
        ]
    ))

@dp.callback_query(F.data == 'my_profile')
async def my_profile(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = get_user_data(user_id)
    if user_data:
        likes_formatted = ', '.join(user_data.get('interests', []))
        user_info = (
            f"📄 <b>Your Profile:</b>\n"
            f"<b>Name:</b> {user_data.get('full_name', 'Not provided')}\n"
            f"<b>Major:</b> {user_data.get('major', 'Not provided')}\n"
            f"<b>Degree:</b> {user_data.get('degree', 'Not provided')}\n"
            f"<b>Year:</b> {user_data.get('year', 'Not provided')}\n"
            f"<b>Country:</b> {user_data.get('country', 'Not provided')}\n"
            f"<b>Interests:</b> {likes_formatted}\n"
            f"<b>Description:</b> {user_data.get('description', 'Not provided')}"
        )
        await callback_query.message.delete()
        delete_button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_menu")]
            ]
        )
        await bot.send_photo(
            chat_id=user_id,
            photo=user_data.get('photo'),
            caption=user_info,
            parse_mode='HTML',
            reply_markup=delete_button
        )
    else:
        await state.clear()
        await callback_query.message.answer("It seems you are not registered yet. Let's get started!")
        await callback_query.message.answer("Please write your first and last name:")
        await state.set_state(UserForm.name)

@dp.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await open_menu(callback_query.message, state)

@dp.callback_query(F.data.startswith("change_"))
async def handle_change(callback_query: types.CallbackQuery, state: FSMContext):
    data_key = callback_query.data.split('_')[1]
    prompts = {
        "name": "Please enter your new name: 📝",
        "major": "Please enter your new major: 📚",
        "degree": "What is your new degree? 🎓",
        "year": "Please enter your new year (1-3): 🗓",
        "country": "Please enter your new country: 🌍",
        "likes": "Please enter the things you like, separated by commas: 🎵⚽📖",
        "description": "Please enter your new description: ✍️",
        "photo": "Please send your new photo: 📸"
    }
    await state.update_data(change_field=data_key)
    if data_key == 'degree':
        await callback_query.message.edit_text(prompts[data_key], reply_markup=degree_keyboard)
    else:
        await callback_query.message.edit_text(prompts[data_key])
    await state.set_state(ChangeForm.field)

@dp.message(ChangeForm.field)
async def process_change(message: types.Message, state: FSMContext):
    field_to_change = (await state.get_data()).get('change_field')
    user_id = message.from_user.id

    if field_to_change == 'photo':
        if message.content_type == ContentType.PHOTO:
            value = message.photo[-1].file_id
        else:
            await message.reply("Please send a valid photo. 📸")
            return
    elif field_to_change == 'year':
        if message.text not in ['1', '2', '3']:
            await message.reply("Please enter a valid year (1, 2, or 3). 🔢")
            return
        else:
            value = message.text
    elif field_to_change == 'likes':
        value = [interest.strip() for interest in message.text.split(',')]
    else:
        if message.content_type == ContentType.TEXT:
            value = message.text
        else:
            await message.reply("Please send text input.")
            return

    firestore_fields = {
        'name': 'full_name',
        'major': 'major',
        'degree': 'degree',
        'year': 'year',
        'country': 'country',
        'likes': 'interests',
        'description': 'description',
        'photo': 'photo'
    }

    firestore_field = firestore_fields.get(field_to_change)

    update_db(user_id, {firestore_field: value})

    await message.reply(f"{field_to_change.capitalize()} updated successfully! ✅")
    await state.set_state(UserForm.menu)
    await open_menu(message, state)

@dp.callback_query(F.data.startswith("degree_"), ChangeForm.field)
async def change_degree_selection(callback_query: types.CallbackQuery, state: FSMContext):
    degree = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    update_db(user_id, {'degree': degree})
    await state.update_data(degree=degree)
    await callback_query.message.edit_text("Degree updated successfully! ✅")
    await state.set_state(UserForm.menu)
    await open_menu(callback_query.message, state)

@dp.callback_query(F.data == 'pause_matching')
async def pause_matching(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    update_db(user_id, {'is_active': False})
    await callback_query.answer("🔄 Matching has been paused.")
    await open_menu(callback_query, state)

@dp.callback_query(F.data == 'resume_matching')
async def resume_matching(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    update_db(user_id, {'is_active': True})
    await callback_query.answer("▶️ Matching has been resumed.")
    await open_menu(callback_query, state)

async def open_menu(message_or_query, state: FSMContext):
    user_id = message_or_query.from_user.id
    user_data = get_user_data(user_id)
    is_active = user_data.get('is_active', True) if user_data else True
    menu_text = "🔸 <b>Main Menu</b> 🔸"
    menu_keyboard = get_menu_keyboard(is_active)
    
    if isinstance(message_or_query, types.Message):
        await message_or_query.answer(menu_text, reply_markup=menu_keyboard, parse_mode='HTML')
    elif isinstance(message_or_query, types.CallbackQuery):
        await message_or_query.message.edit_text(menu_text, reply_markup=menu_keyboard, parse_mode='HTML')

@dp.message()
async def handle_unrecognized_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()

    if current_state is None:
        user_data = get_user_data(user_id)
        if user_data:
            await state.set_state(UserForm.menu)
            await message.answer("👋 Welcome back!")
            await open_menu(message, state)
        else:
            await state.set_state(UserForm.name)
            await message.answer("It seems you are not registered yet. Let's get started!")
            await message.answer("Please write your first and last name:")
    elif current_state == UserForm.menu.state:
        await message.reply("Oops! Command not recognized. Use the menu below to navigate. 👇", reply_markup=get_menu_keyboard())
    elif current_state == ChangeForm.field.state:
        await process_change(message, state)
    elif current_state == DeleteForm.confirm.state:
        await message.reply("Please use the buttons to confirm or cancel the deletion.")
    else:
        await message.reply("Please follow the instructions to complete registration. ℹ️", reply_markup=get_back_button())

async def send_match_notifications():
    try:
        history_ref = db.collection('history').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1)
        latest_history = next(history_ref.stream(), None)

        if latest_history:
            history_data = latest_history.to_dict()
            match_pairs = history_data.get('match_pairs', [])
            for pair in match_pairs:
                await send_match_notification(pair['user1_id'], pair['user2_id'])
                await send_match_notification(pair['user2_id'], pair['user1_id'])
        else:
            logger.info("No match pairs found in the latest history.")
    except Exception as e:
        logger.error(f"Error fetching match pairs: {e}")

async def send_match_notification(user_id, match_id):
    try:
        match_data = get_user_data(match_id)
        if not match_data:
            logger.error(f"User data not found for user {match_id}")
            return

        try:
            chat = await bot.get_chat(int(match_id))
            username = chat.username
        except Exception as e:
            logger.error(f"Error fetching username for user {match_id}: {e}")
            username = None

        if username:
            contact_info = f"@{username}"
        else:
            contact_info = "This user does not have a Telegram username set."

        message_text = (
            f"👥 <b>You've been matched!</b>\n"
            f"You have been matched with <b>{match_data.get('full_name', 'A user')}</b>.\n"
            f"Here's their profile:\n\n"
            f"<b>Name:</b> {match_data.get('full_name', 'Not provided')}\n"
            f"<b>Description:</b> {match_data.get('description', 'Not provided')}\n"
            f"<b>Contact:</b> {contact_info}\n"
            f"Feel free to reach out and schedule a meeting!"
        )
        await bot.send_photo(
            chat_id=int(user_id),
            photo=match_data.get('photo'),
            caption=message_text,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending match notification to user {user_id}: {e}")

async def collect_feedback():
    while True:
        berlin_tz = timezone('Europe/Berlin')
        now = datetime.now(berlin_tz)
        next_run_time = now.replace(hour=13, minute=0, second=0, microsecond=0)
        days_until_wednesday = (2 - now.weekday()) % 7
        if days_until_wednesday == 0 and now >= next_run_time:
            days_until_wednesday = 7
        next_run_time += timedelta(days=days_until_wednesday)
        time_until_next_run = (next_run_time - now).total_seconds()

        await asyncio.sleep(time_until_next_run)

        try:
            history_ref = db.collection('history').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1)
            latest_history = next(history_ref.stream(), None)

            if latest_history:
                history_id = latest_history.id
                match_pairs = latest_history.to_dict().get('match_pairs', [])
                for pair in match_pairs:
                    await send_feedback_request(pair['user1_id'], pair['user2_id'], history_id)
                    await send_feedback_request(pair['user2_id'], pair['user1_id'], history_id)
            else:
                logger.info("No match pairs found in the latest history.")
        except Exception as e:
            logger.error(f"Error during feedback collection: {e}")

async def send_feedback_request(user_id, match_id, history_id):
    try:
        message_text = (
            "👋 <b>We'd love to hear from you!</b>\n"
            "Did your meeting with your match take place?"
        )
        feedback_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Yes", callback_data=f"meeting_yes_{history_id}_{match_id}"),
                    InlineKeyboardButton(text="❌ No", callback_data=f"meeting_no_{history_id}_{match_id}")
                ]
            ]
        )
        await bot.send_message(chat_id=int(user_id), text=message_text, reply_markup=feedback_keyboard, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error sending feedback request to user {user_id}: {e}")

@dp.callback_query(F.data.startswith("meeting_"))
async def handle_meeting_feedback(callback_query: types.CallbackQuery, state: FSMContext):
    data_parts = callback_query.data.split('_')
    response = data_parts[1]
    history_id = data_parts[2]
    match_id = data_parts[3]
    user_id = str(callback_query.from_user.id)

    history_ref = db.collection('history').document(history_id)
    history_doc = history_ref.get()
    if history_doc.exists:
        match_pairs = history_doc.to_dict().get('match_pairs', [])
        for pair in match_pairs:
            if pair['user1_id'] == user_id and pair['user2_id'] == match_id:
                pair['meeting_happened'] = True if response == 'yes' else False
                break
            elif pair['user2_id'] == user_id and pair['user1_id'] == match_id:
                pair['meeting_happened'] = True if response == 'yes' else False
                break
        history_ref.update({'match_pairs': match_pairs})

        if response == 'yes':
            await callback_query.message.edit_text("Great! Did you enjoy the meeting?")
            await state.update_data(history_id=history_id, match_id=match_id)
            await state.set_state(FeedbackForm.waiting_for_feedback)
        else:
            await callback_query.message.edit_text("We're sorry to hear that. We'll try to improve future matches.")
            await state.set_state(UserForm.menu)
            await open_menu(callback_query.message, state)
    else:
        await callback_query.message.answer("Error: Match history not found.")

@dp.message(FeedbackForm.waiting_for_feedback)
async def handle_feedback_response(message: types.Message, state: FSMContext):
    feedback_text = message.text.lower()
    user_id = str(message.from_user.id)
    data = await state.get_data()
    history_id = data.get('history_id')
    match_id = data.get('match_id')

    if 'yes' in feedback_text or 'like' in feedback_text:
        feedback_value = 1
    elif 'no' in feedback_text or 'dislike' in feedback_text:
        feedback_value = -1
    else:
        await message.reply("Please respond with 'Yes' or 'No'.")
        return

    history_ref = db.collection('history').document(history_id)
    history_doc = history_ref.get()
    if history_doc.exists:
        match_pairs = history_doc.to_dict().get('match_pairs', [])
        for pair in match_pairs:
            if pair['user1_id'] == user_id and pair['user2_id'] == match_id:
                pair['user1_isLike'] = feedback_value
                break
            elif pair['user2_id'] == user_id and pair['user1_id'] == match_id:
                pair['user2_isLike'] = feedback_value
                break
        history_ref.update({'match_pairs': match_pairs})
        next_monday = get_next_monday()

        if feedback_value == 1:
            await message.reply(f"Thank you for your feedback! We are glad that you were able to meet and you liked it. The next match will be on {next_monday}.")
        else:
            await message.reply(f"Thank you for your feedback. We're sorry to hear that you didn't enjoy the meeting. Next time will surely be better! The next match will be on {next_monday}.")

        await state.clear()
        await state.set_state(UserForm.menu)
        await open_menu(message, state)
    else:
        await message.reply("Error: Match history not found.")

def on_send_field_change(doc_snapshot, changes, read_time, loop):
    for doc in doc_snapshot:
        data = doc.to_dict()
        send_value = data.get('send', False)
        if send_value:
            logger.info("'send' field changed to True. Triggering send_match_notifications.")

            asyncio.run_coroutine_threadsafe(send_match_notifications(), loop)

            doc.reference.update({'send': False})

async def main():
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)

    loop = asyncio.get_running_loop()

    config_ref = db.collection('config').document('matching')
    config_watch = config_ref.on_snapshot(
        lambda doc_snapshot, changes, read_time: on_send_field_change(doc_snapshot, changes, read_time, loop)
    )

    asyncio.create_task(schedule_send_match_notifications())
    asyncio.create_task(collect_feedback())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def schedule_send_match_notifications():
    while True:
        berlin_tz = timezone('Europe/Berlin')
        now = datetime.now(berlin_tz)
        next_run_time = now.replace(hour=1, minute=0, second=0, microsecond=0)
        days_until_monday = (0 - now.weekday()) % 7
        if days_until_monday == 0 and now >= next_run_time:
            days_until_monday = 7
        next_run_time += timedelta(days=days_until_monday)
        time_until_next_run = (next_run_time - now).total_seconds()

        await asyncio.sleep(time_until_next_run)

        config_ref = db.collection('config').document('matching')
        config_ref.set({'send': True}, merge=True)
        logger.info("Set 'send' field to True in Firestore.")

async def startup():
    logger.info("Bot started successfully.")

async def shutdown():
    logger.info("Bot is shutting down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        traceback.print_exc()
