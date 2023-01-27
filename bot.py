import logging
import os
import typing
import time

from keybords import start_kb
from file import save, read, read_list, get_check, check_done, check_not_done, checkups_to_false, delete

from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils.callback_data import CallbackData

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
START_MESSAGE = "✏ Add to add more check-ups\n" \
                "✅ Check to start check!\n" \
                "📃 Show to show list of check-ups\n" \
                "🗑 Delete to delete chosen check-up"

logging.basicConfig(level=logging.INFO)  # configure logging

# initialize bot and dispatcher
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=storage)

# callback data for checks
check_cb = CallbackData('check', 'action')


# states
class Form(StatesGroup):
    start = State()  # state for start of the bot (buttons add, shwo, delete and check)
    add = State()  # state for adding new check-ups (handle adding check-ups)
    check = State()  # state to start checking (start check-up)
    delete = State()  # state to delete chosen check-up (handle deleting check-ups)


# command handler /start
@dp.message_handler(regexp=".")  # start message when state is None with any symbol
@dp.message_handler(commands=["start"], state='*')
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    await Form.start.set()  # set state to 'start'
    await message.answer(f"Hello! This bot will help you to check everything before leaving the house.\n"
                         f"{START_MESSAGE}", reply_markup=start_kb)


# add command to start handling adding check ups (state = start)
@dp.message_handler(Text(equals='add', ignore_case=True), state=Form.start)
async def add_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    await Form.add.set()  # set state to 'add'
    await message.answer("Now you can add some check-ups by typing messages.\n"
                         "Each message is treated as new check-up.\n"
                         "To stop adding check-ups type 'end'")

    # try to load file for current user to show curr list of check-ups
    try:
        list_of_checkups = read(user_id)
        if list_of_checkups:
            await message.answer(list_of_checkups)
            await message.answer(f"This is the list of check-ups:\n{list_of_checkups}")
        else:
            await message.answer("Your list of check-ups is empty yet")
    except FileNotFoundError:
        await message.answer("Your list of check-ups is empty yet")


# adding check ups handler (state == 'add')
@dp.message_handler(regexp='[^end]', state=Form.add)
async def add_new_checks_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    # try to save recieved check-up in file
    try:
        save(message.text, user_id=user_id)
        await message.answer(f"New check-up was added:\n{message.text}")
    except FileNotFoundError:
        await message.answer("Can't save data")


# stop adding after 'end' message (state == 'add')
@dp.message_handler(Text(equals='end', ignore_case=True), state=Form.add)
async def stop_add_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    await Form.start.set()  # reset state to 'start'
    await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)


# check handler to start check-up
@dp.message_handler(Text(equals='check', ignore_case=True), state=Form.start)
async def check_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    await Form.check.set()  # set state to 'check'
    # try to read next check-up
    try:
        check = get_check(user_id=user_id)
        if check == "%CHECKED%":
            # restart if no check-ups in file
            await message.answer("Add some new check-ups to start check!")
            await Form.start.set()
            await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)
        else:
            # create inline button with current check-up
            await message.answer(f"{check}", reply_markup=types.InlineKeyboardMarkup().row(
                types.InlineKeyboardButton('✅', callback_data=check_cb.new(action='passed')),
                types.InlineKeyboardButton('❌', callback_data=check_cb.new(action='failed'))))

    except FileNotFoundError:
        await message.answer("There is nothing to check, try to add more check-ups")
        await Form.start.set()
        await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)


# check-up query handler for inline button with check-ups
@dp.callback_query_handler(check_cb.filter(action=['passed', 'failed']), state=Form.check)
async def callback_check_action(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    user_id = query.from_user.id
    user_full_name = query.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    await query.answer()
    callback_data_action = callback_data['action']

    # process callback from user (button '✅' and '❌'
    if callback_data_action == 'passed':  # if check passed
        check_done(user_id=user_id)  # mark check with True value
        next_check = get_check(user_id=user_id)  # get next check-up
    else:  # if failed
        check_not_done(user_id=user_id)  # put curr check-up to the end of the file
        next_check = get_check(user_id=user_id)  # get next check-up

    if next_check == "%CHECKED%":  # if all check-ups have True value (checked)
        checkups_to_false(user_id=user_id)
        await bot.edit_message_text("All checks done", user_id, query.message.message_id)
        await Form.start.set()  # reset to 'start' state
        await bot.send_message(user_id, f"{START_MESSAGE}", reply_markup=start_kb)
    else:
        try:
            # edit message with check-up button for new check-up
            await bot.edit_message_text(f"{next_check}", user_id, query.message.message_id,
                                        reply_markup=types.InlineKeyboardMarkup().row(
                                            types.InlineKeyboardButton('✅',
                                                                       callback_data=check_cb.new(action='passed')),
                                            types.InlineKeyboardButton('❌',
                                                                       callback_data=check_cb.new(action='failed'))))
        except MessageNotModified:  # case of last check-up remaining
            await bot.send_message(user_id, "It is last check-up!")


# show command to show list of check-ups (state == 'start')
@dp.message_handler(Text(equals='show', ignore_case=True), state=Form.start)
async def add_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    # try to load list of check-ups
    try:
        list_of_checkups = read(user_id)
        if list_of_checkups:
            await message.answer(f"This is the list of check-ups:\n{list_of_checkups}")
            await Form.start.set()
            await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)
        else:
            await message.answer("Your list is empty yet")
            await Form.start.set()
            await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)
    except FileNotFoundError:
        await message.answer("Can't read data, try to add more check-ups")
        await Form.start.set()
        await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)


# delete command to delete chosen check-up by number
@dp.message_handler(Text(equals='delete', ignore_case=True), state=Form.start)
async def add_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()}')

    await Form.delete.set()  # set state to 'delete'
    # try to load list of check-ups
    try:
        list_of_checkups = read(user_id)
        if list_of_checkups:
            await message.answer(list_of_checkups)
            await message.answer("Enter number/s of check-ups you want to delete (e.g.: 1 2 3 or 1,2,3 or 1.2.3)")
        else:
            await message.answer("Your list is empty yet, nothing to delete")
            await Form.start.set()
            await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)
    except FileNotFoundError:
        await message.answer("You have no data, or file couldn't be read")
        await Form.start.set()
        await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)


# process numbers to delete chosen check-ups by number (state == 'delete')
@dp.message_handler(regexp="(\d+[,. ]*)+", state=Form.delete)
async def add_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'user {user_full_name} with ID:{user_id} connected at {time.asctime()} to delete {message.text}')

    numbers_to_delete = message.text
    # try to delete check-ups with recieved indexes
    try:
        delete(user_id=user_id, nums=numbers_to_delete)
        await message.answer("This is your new list of check-ups")
        list_of_checkups = read(user_id)
        if list_of_checkups:
            await message.answer(list_of_checkups)
        else:
            await message.answer("Your list is empty")
    except FileNotFoundError:
        await message.answer("Can't delete, check your check-up numbers")
    except ValueError:
        await message.answer("Wrong arguments to delete command")


    await Form.start.set()  # reset to start state
    await message.answer(f"{START_MESSAGE}", reply_markup=start_kb)


if __name__ == "__main__":
    executor.start_polling(dp)
