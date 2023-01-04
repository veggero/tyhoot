from __future__ import annotations
import telegram
import logging
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from dataclasses import dataclass, field
from typing import Optional

TOKEN = "5489320195:AAFD5AjaIdITFj9c0Fp_jmAlWVpRyfShmKM"

NEXT, TIME = "Next question, please", "Time is up!"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

bot = telegram.Bot(TOKEN)

def keyb(options):
    return ReplyKeyboardMarkup([[a] for a in options])

@dataclass
class Question:
    prompt: str
    options_n: int
    correct_index: int

    score: int = 1000

    def correct(self, m):
        try: return int(m) == self.correct_index
        except ValueError: return False

@dataclass
class User:
    user_id: int
    username: str
    name: str
    score: int = 0
    streak: int = 0

    won: bool = False
    lost: bool = False

@dataclass
class Game:
    questions: list[Question]
    admin: int
    question_index: int = -1
    playing: bool = False

    def __post_init__(self):
        try: self.users = eval(open('data.py').read())
        except: self.users = []
        logging.info(f'Users are {self.users}')

    def save(self): open('data.py', 'w').write(repr(self.users))

    @property
    def leaderboard(self):
        return "_Leaderboard:_\n" + \
            '\n'.join(f'*{u.name}*: {u.score} ' + '🔥'*min(u.streak, 5)
                      for u in self.users)

    @property
    def question(self): return self.questions[self.question_index]

    def user_by_id(self, user_id):
        return next(u for u in self.users if u.user_id == user_id)

    def answer(self, user, message):
        if user.won or user.lost:
            return bot.send_message(user.user_id, "Sorry, you already choose!")
        bot.send_message(self.admin, f"One vote for {message}!")
        if self.question.correct(message):
            user.won = True
            user.score += self.question.score + 100*user.streak
            self.question.score -= 100
            if self.question.score <= 100: self.question.score = 100
            user.streak += 1
        else:
            user.lost = True
            user.streak = 0
        bot.send_message(user.user_id, "Answer saved!",
                         reply_markup=ReplyKeyboardRemove())

    def end_question(self):
        self.playing = False
        for user in self.users:
            if user.won:
                user.won = False
                bot.send_message(user.user_id,
                                 "Hey, that was indeed *correct!*",
                                 parse_mode="Markdown")
            elif user.lost:
                user.lost = False
                bot.send_message(user.user_id,
                                 "Sorry, that was *incorrect!*",
                                 parse_mode="Markdown")
            else:
                bot.send_message(user.user_id,
                                 "Time is up! No answer was given :(")
            bot.send_message(user.user_id, self.leaderboard,
                             parse_mode="Markdown")
        bot.send_message(self.admin, self.leaderboard,
                         reply_markup=keyb([NEXT]),
                         parse_mode="Markdown")
        self.save()

    def next_question(self):
        self.question_index += 1
        self.playing = True
        bot.send_message(self.admin, "...",
                         reply_markup=keyb([TIME]),
                         parse_mode="Markdown")
        k = keyb(range(self.question.options_n))
        for user in self.users:
            bot.send_message(user.user_id, self.question.prompt,
                             reply_markup=k, parse_mode="Markdown")
        self.save()

    def get_user(self, user_id, username, name):
        if user_id in [u.user_id for u in self.users]:
            return self.user_by_id(user_id)
        else:
            user = User(user_id, username, name)
            if user_id != game.admin: self.users.append(user)
            self.save()
            bot.send_message(self.admin, f'Current users: {len(self.users)}')
            return user

game = Game([
    Question('Is this going to be a cool talk?', 4, 1),
    Question('Which one of these is NOT an expression?', 4, 2),
    Question('Which one executes, in an expression, multiple expressions in order', 4, 2),
    Question('When can I use (exp1) or (exp2) to execute the expressions and return the last value?', 4, 1),
    Question('Which one does NOT assign some values to a variable inside an expression?', 4, 3),
    Question('What should be use to transform into a single expression this kind of pattern?' +
"""
```
l = []
    for el in gen:
        if not cond(el): continue
        l.append(f(el))
```
""", 4, 1),
    Question('What if I have to build a dictionary? a tuple? a set?', 4, 2),
    Question('Which one of these expressions does NOT import the library and lets us use it similarly to import?', 2, 1),
    Question('What about declaring functions?', 4, 1),
    Question('What about try except blocks?', 4, 3),
    Question('What about creating a new class!?', 4, 0),
    Question('What about using if then else!??', 2, 0),
    Question('Okay, wait, but what about setting properties of objects inside an expression?', 4, 2),
    Question('Bonus. What about simplifying this?' +
"""
```
if key in dictionary:
    var = dictionary[key]
else:
    var = default
```
""", 4, 3),
    Question('What about decorators!?', 4, 1),
    Question('Ok, so. Can you actually do ANY program in one line!?', 3, 1),
    Question('Ok, so. Can we actually only use lambdas in a py and get the correct output!?', 3, 2),
    Question('Ok, let\'s start with boolans in lambda calculus. How could we represent true?', 4, 3),
    Question('...and how we translate that into normal bools again?', 4, 1),
    Question('How do we define or?', 4, 1),
    Question('How do we define and?', 4, 2),
    Question('How could we define naturals... like, as an example, 2?', 4, 0),
    Question('And how do we convert back?', 4, 1),
    Question('What about a function to add one?', 4, 1),
    Question('What about adding two numbers?', 4, 0),
    Question('What about a function that creates a pair of numbers?', 4, 3),
    Question('How do we actually get the first element?', 4, 1),
    Question('Was this fun?', 4, 0)
    ], 302001216)

def reply(update, context):
    user = game.get_user(update.effective_chat.id,
                         update.message.chat.username,
                         (update.message.chat.first_name or '') + ' ' +
                         (update.message.chat.last_name or ''))
    if update.message.text == NEXT and user.user_id == game.admin:
        game.next_question()
    if update.message.text == TIME and user.user_id == game.admin:
        game.end_question()
    if user.user_id == game.admin: return
    if game.playing: game.answer(user, update.message.text)
    else: update.message.reply_text("Not playing yet, but I registered you!")


dispatcher.add_handler(MessageHandler(Filters.text, reply))
updater.start_polling()

bot.send_message(game.admin, "Bot started!",
                    reply_markup=keyb([NEXT]),
                    parse_mode="Markdown")
