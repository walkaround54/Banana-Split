import telebot
from telebot import types, TeleBot

expenses = []
users = []

bot = telebot.TeleBot("6667301029:AAHw6oGORh3Hw3j3tGQ1_H_-Zdj5UjmRxNc")

class User():
    def __init__(self):
        self.id = None
        self.name = None
        self.book = {}
        self.ratio = None
        
    def set_id(self, id):
        self.id = id
    
    def set_name(self, name):
        self.name = name

    def update_personal(self, expense):
        if expense.payer is self: # if user is the payer
            for user in expense.owers.keys():
                if user not in self.book.keys():
                    self.book[user] = 0
                self.book[user] -= expense.owers[user]

        elif self in expense.owers: # if user is an ower
            if expense.payer not in self.book.keys():
                self.book[expense.payer] = 0
            self.book[expense.payer] += expense.owers[self]
    
    def set_ratio(self, ratio):
        self.ratio = ratio
        
class Expense():
    def __init__(self):
        self.name = None
        self.amount = None
        self.payer = None
        self.owers = {}

    def set_name(self, name):
        self.name = name
    
    def add_ower(self, person):
        if person in self.owers:
            pass
        self.owers[person]=None
        for person in self.owers:
            self.owers[person] = 0 #self.amount / (len(self.owers)+1)
    
    def update_expense(self):
        for person in self.owers:
            self.owers[person]=self.amount/(len(self.owers)+1)

    def remove_ower(self, person):
        if person not in self.owers:
            pass
        del self.owers[person]
    
    def set_payer(self, person):
        self.payer = person

    def set_amount(self, amt):
        self.amount = float(amt)


# Define a list of BotCommand objects
commands = [
    types.BotCommand("start", "Start the bot"),
    types.BotCommand("help", "Get help"),
    types.BotCommand("join", "Join group"),
    types.BotCommand("clear", "Reset bot"),
    types.BotCommand("add", "Add expense"),
    types.BotCommand("show_users", "Show users"),
    types.BotCommand("show_book", "Show Current Balance"),
    types.BotCommand("show_expenses", "Shows Breakdown of Expenses")

    # Add more commands as needed
]

# Set these commands for the bot
bot.set_my_commands(commands)


# Initialise Bot
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")



# Join Group
@bot.message_handler(commands=['join'])
def join(message):
    if message.from_user.id in list(map(lambda x: x.id, users)):
        bot.send_message(message.chat.id, f"{message.from_user.first_name} already joined group.")
    else:
        newuser = User()
        newuser.set_name(message.from_user.first_name)
        newuser.set_id(message.from_user.id)
        bot.reply_to(message, f"{newuser.name} has joined the group")
        users.append(newuser)


# list users in group
@bot.message_handler(commands=['show_users'])
def show_users(message):
    text = "List of users:\n"
    for user in users:
        text +=  ("\n" + user.name)
    bot.send_message(message.chat.id, text)


# Add expense, ask for name of expense
@bot.message_handler(commands=['add'])
def add_expense_start(message):
    newexpense = Expense()
    expenses.append(newexpense)
    msg = bot.reply_to(message, "Enter the name of the expense:")
    bot.register_next_step_handler(msg, process_expense_name)


# Ask for expense amount
def process_expense_name(message):
    expenses[-1].set_name(message.text)
    currUser = None
    for user in users:
        if message.from_user.id == user.id:
            currUser = user
    expenses[-1].set_payer(currUser)
    msg = bot.reply_to(message, "Enter the expense amount:")
    bot.register_next_step_handler(msg, process_expense_amount)


# Show choices of users, get user to choose who owes
def process_expense_amount(message):
    expenses[-1].set_amount(int(message.text))
    # present user with choices of users who owe,  take in selected users store them as list
   # Implementing user selection for payees
    markup = telebot.types.InlineKeyboardMarkup()
    for user in users:
        #exclude user(payer) themself from list
        if user.id == message.from_user.id:
            continue
        markup.add(telebot.types.InlineKeyboardButton(f"{user.name}", callback_data=user.id))
    markup.add(telebot.types.InlineKeyboardButton("End", callback_data="End"))
    bot.send_message(message.chat.id, "Select users who owe for this expense:", reply_markup=markup)
    bot.register_next_step_handler(message, process_payees)


# Show output of selected users
@bot.callback_query_handler(func=lambda call: True)
def process_payees(call):
    if call.data != "End":
        # Extract user ID from callback data
        user_id = int(call.data)
        currOwer = None
        for user in users:
            if user.id == user_id:
                currOwer = user
        if currOwer in expenses[-1].owers:
            expenses[-1].remove_ower(currOwer)
            bot.send_message(call.message.chat.id, "Removed user " + str(currOwer.name) + " from expense " + expenses[-1].name)
        else:
            expenses[-1].add_ower(currOwer)
        #bot.answer_callback_query(call.id, "Selected user " + str(user_id))
        # More logic to finalize the payees selection process
            bot.send_message(call.message.chat.id, "Added user " + str(currOwer.name) + " to expense " + expenses[-1].name)
    
    else:
        expenses[-1].update_expense()
        for user in users:
            user.update_personal(expenses[-1])
        bot.send_message(call.message.chat.id, "Selection Complete.")
        bot.clear_step_handler_by_chat_id(call.message.chat.id)


@bot.message_handler(commands=['show_book'])
def show_book(message):
    for user in users:
        for inner in user.book.items():
            other = inner[0].name
            amt = inner[1]
            if amt > 0:
                bot.send_message(message.chat.id, user.name + " owes " + str(other) + " $" + str(round(amt,2)))

@bot.message_handler(commands=['show_expenses'])

def show_expenses(message):
    pass


# Resets Bot
@bot.message_handler(commands=['clear'])
def clear(message):
    global expenses, users
    expenses = []  # Reset expenses
    users = []  # Reset users
    bot.reply_to(message, "Bot has been reset.")

bot.polling()