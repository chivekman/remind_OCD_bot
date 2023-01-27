from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# start keyboard with buttons add, show, delete and check
button_add = KeyboardButton('Add')
button_check = KeyboardButton('Check')
button_show = KeyboardButton('Show')
button_delete = KeyboardButton('Delete')
start_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_add, button_show, button_delete, button_check)
