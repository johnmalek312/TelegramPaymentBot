import asyncio
import signal

import datetime
import html
import time
import os
from datetime import timedelta
import pathlib
import traceback
from typing import Union, List
from telegram.ext import JobQueue, CallbackContext
import threading
import requests
import telegram
import telegram.constants
from telegram import Update, constants, InputMediaAudio, InputMediaPhoto, InputMediaDocument, InputMediaVideo, \
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.ext import Application, MessageHandler, filters, ConversationHandler
from telegram.ext.filters import MessageFilter
from flask import Flask, request, jsonify
import hashlib
import hmac
import json
import sql
from settings import TELEGRAM_SUPPORT_CHAT_ID, TELEGRAM_TOKEN, PAYMENT_URL, TELEGRAM_PREMIUM_CHAT_ID
import asyncio
import discord
from discord.ext import commands, tasks
from dateutil.relativedelta import relativedelta
import qrcode
import clipboard
import tempfile
import secrets
import random
import string
from dotenv import load_dotenv

application = None
disToken = ""  
intents = discord.Intents.all()
disBot = commands.Bot(command_prefix='.', intents=intents)

welcome_message: str = html.escape(os.getenv("WELCOME_MESSAGE", ""))
how_it_works_message: str = html.escape(os.getenv("HOW_IT_WORKS_MESSAGE", ""))
prices_message: str = html.escape(os.getenv("PRICES_MESSAGE", ""))
free_link_message: str = html.escape(os.getenv("FREE_LINK_MESSAGE", "")) + "<a href=\"" + os.getenv("FREE_LINK_URL", "") + "\">here</a>" + html.escape(" to join!")
vip_info_message: str = html.escape(os.getenv("VIP_INFO_MESSAGE", ""))
support_message: str = html.escape(os.getenv("SUPPORT_MESSAGE", ""))
how_to_pay_message: str = html.escape(os.getenv("HOW_TO_PAY_MESSAGE", ""))
button_text: dict = {"how_it_works": "❓How does it work?", "prices": "💲VIP Prices", "how_to_pay": "💳How to Pay",
                     "vip_info": "🥇VIP Info", "support": "👨‍💻Support",
                     "free_channel_link": "↪️Free Channel link"}

ipn_call_back_url = "https://telegram.sparked.network/ipn"
token = TELEGRAM_TOKEN

bot = None


class ButtonCommandFilter(MessageFilter):
    def filter(self, message):
        if message.text in button_text.values():
            return True
        return False


button_command_filter = ButtonCommandFilter()

# NowPayments


class NOWPaymentsAPI:
    # def __init__(self, api_key, secret_key):
    def __init__(self, api_key):
        self.api_key = api_key
        # self.secret_key = secret_key

        # self.base_url = 'https://api-sandbox.nowpayments.io/v1'  # test environment
        self.base_url = 'https://api.nowpayments.io/v1'

    # NowPayments
    def create_payment(self, price: float, price_currency: str = "usd", pay_currency: str = "USDTTRC20",
                       ipn_callback_url: str = None, order_id: str = None,
                       order_description: str = None, payment_link_title: str = None, stop: bool = False):
        try:
            url = f'{self.base_url}/payment'
            headers = {'x-api-key': self.api_key}
            data = {'price_amount': price, 'price_currency': price_currency, 'pay_currency': pay_currency,
                    'is_fee_paid_by_user': False, 'is_fixed_rate': True}
            if ipn_callback_url:
                data['ipn_callback_url'] = ipn_callback_url
            if order_id:
                data['order_id'] = order_id
            if order_description:
                data['order_description'] = order_description.replace(
                    '{', '').replace('}', '')
            if payment_link_title:
                data['payment_link_title'] = payment_link_title

            response = requests.post(url, headers=headers, json=data)
            print(response.status_code)
            print(response.json())

            if (response.status_code == 200) or (response.status_code == 201):
                return response.json()
            else:
                if "pay_address" in response.json().keys():
                    return response.json()
                if not stop:
                    if "pay_address" in response.json().keys():
                        return response.json()
                    else:
                        return self.create_payment(price=price, price_currency=price_currency,
                                                   pay_currency=pay_currency, ipn_callback_url=ipn_callback_url,
                                                   order_description=order_description, order_id=order_id,
                                                   payment_link_title=payment_link_title, stop=True)
        except Exception as error:
            print(traceback.format_exc())

    def create_invoice(self, price: float, price_currency: str = "usd", pay_currency: str = "USDTTRC20",
                       ipn_callback_url: str = None, order_id: str = None,
                       order_description: str = None, payment_link_title: str = None, stop=False):
        try:
            url = f'{self.base_url}/invoice'
            headers = {'x-api-key': self.api_key}
            data = {'price_amount': price, 'price_currency': price_currency, 'pay_currency': pay_currency,
                    'is_fee_paid_by_user': True, 'is_fixed_rate': True}
            if ipn_callback_url:
                data['ipn_callback_url'] = ipn_callback_url
            if order_id:
                data['order_id'] = order_id
            if order_description:
                data['order_description'] = order_description
            if payment_link_title:
                data['payment_link_title'] = payment_link_title
            response = requests.post(url, headers=headers, json=data)
            if (response.status_code == 200) or (response.status_code == 201):
                return response.json()
            else:
                print(response.status_code)
                print(response.json())
                if "invoice_url" in response.json().keys():
                    return response.json()
                if not stop:
                    if "invoice_url" in response.json().keys():
                        return response.json()
                    else:
                        return self.create_invoice(price=price, price_currency=price_currency,
                                                   pay_currency=pay_currency, ipn_callback_url=ipn_callback_url,
                                                   order_description=order_description, order_id=order_id,
                                                   payment_link_title=payment_link_title, stop=True)
        except Exception as error:
            print(traceback.format_exc())

    def create_invoice_payment(self, invoice_id, pay_currency: str = "USDTTRC20", stop: bool = False):
        try:
            url = f"{self.base_url}/invoice-payment"
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "iid": invoice_id,
                "pay_currency": pay_currency,
            }

            response = requests.post(url, headers=headers, json=payload)

            if (response.status_code == 200) or (response.status_code == 201):
                return response.json()
            else:
                print(response.status_code)
                print(response.json())
                if "pay_address" in response.json().keys():
                    return response.json()
                if not stop:
                    if "pay_address" in response.json().keys():
                        return response.json()
                    else:
                        return self.create_invoice_payment(invoice_id=invoice_id, pay_currency=pay_currency, stop=True)
        except Exception as error:
            print(traceback.format_exc())

    def get_payment_status(self, payment_id: int):
        try:
            url = f'{self.base_url}/payment/{payment_id}'
            headers = {'x-api-key': self.api_key}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()['payment_status']
            else:
                response.raise_for_status()
        except Exception as error:
            print(traceback.format_exc())


async def give_premium(user_id: int, plan: int):
    client = sql.db.add_plan_client(user_id, plan)
    await bot.send_message(user_id, "Payment successfully received, use /join command to join premium channel.")
    message = html.escape("#Premium_Purchase\nFrom: ") + bold((await bot.get_chat_member(user_id, user_id)).user.mention_html()) + " (#u" + str(user_id) + ")\n" + get_time() + html.escape("\nPurchased premium plan id: " + str(plan))
    await bot.send_message(TELEGRAM_SUPPORT_CHAT_ID, message, parse_mode=telegram.constants.ParseMode.HTML)



# NowPayments
api_key = os.getenv("NOWPAYMENTS_API_KEY")

# Binance
# nowpayments_api = BinancePayAPI(api_key, secret_key)

# NowPayments
nowpayments_api = NOWPaymentsAPI(api_key)



async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = []
        plans = sql.db.get_plans()
        if plans is not None:
            for plan in plans:
                keyboard.append([InlineKeyboardButton(f"{plan[1]}:  ${plan[2]:g}/{plan[3]} {plan[4]}",
                                                      callback_data=json.dumps(
                                                          {"action": "buy_plan", "plan_id": plan[0]}))])

  

        reply_markup = InlineKeyboardMarkup(keyboard)
        user = update.effective_user
        await update.callback_query.edit_message_text(
            f"Hi, {user.full_name}!\nType /help to read about my abilities :)",
            reply_markup=reply_markup)
    except Exception as error:
        print(traceback.format_exc())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        buttons = [
            [KeyboardButton(text=button_text["how_it_works"])],
            [KeyboardButton(text=button_text["prices"]), KeyboardButton(
                text=button_text["how_to_pay"])],
            [KeyboardButton(
                text=button_text["vip_info"])],
            [KeyboardButton(text=button_text["support"]),
             KeyboardButton(text=button_text["free_channel_link"])],
        ]

        inline_buttons = [
            [
                InlineKeyboardButton(
                    "Join premium channel!",
                    url=PAYMENT_URL
                )
            ]
        ]
        reply_keyboard_markup = ReplyKeyboardMarkup(buttons)
        reply_inline_keyboard_markup = InlineKeyboardMarkup(inline_buttons)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # print(dir_path)
        if update.channel_post is not None:
            if update.channel_post.text == "/start":
                await context.bot.send_photo(chat_id=update.channel_post.chat_id, photo=pathlib.Path("./payment_bot/logo.png"))
                await context.bot.send_message(chat_id=update.channel_post.chat_id, text=welcome_message,
                                               reply_markup=reply_inline_keyboard_markup, parse_mode=telegram.constants.ParseMode.HTML)
        else:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=pathlib.Path("./payment_bot/logo.png"), reply_markup=reply_keyboard_markup)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message,
                                           reply_markup=reply_inline_keyboard_markup, parse_mode=telegram.constants.ParseMode.HTML)

    except Exception as error:
        print(traceback.format_exc())


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        keyboard = []

        user_id = update.effective_user.id
        if sql.db.is_client_premium(user_id):
            chat_ids = sql.db.get_chats()
            if chat_ids is not None:
                for chat_id in chat_ids:
                    try:
                        chat: telegram.Chat = await context.bot.get_chat(chat_id=chat_id)
                        if chat.type.lower() == "supergroup":
                            typo = "group"
                        else:
                            typo = chat.type.lower()
                        keyboard.append([InlineKeyboardButton(f"Join {typo} {chat.title}",
                                                              callback_data=json.dumps(
                                                                  {"action": "join", "chat_id": chat_id}))])
                    except Exception as e:
                        print(traceback.format_exc())
                keyboard.append([InlineKeyboardButton("↩️ Back to the main menu",
                                                      callback_data=json.dumps({"action": "goto", "dest": "menu"}))])
            # keyboard = [
            #    [
            #        InlineKeyboardButton("Option 1", callback_data="1")],
            #    [InlineKeyboardButton("Option 3", callback_data="3")],
            # ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Below you'll find a list with the chats I manage.\n\nPlease select the one you're interested in and I'll help you to get in.",
                reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("Subscribe.",
                                              callback_data=json.dumps({"action": "goto", "dest": "subscribe"}))],
                        [InlineKeyboardButton("↩️ Back to the main menu",
                                              callback_data=json.dumps({"action": "goto", "dest": "menu"}))]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "It seems like you don't have an active membership.",
                reply_markup=reply_markup)
    except Exception as error:
        print(traceback.format_exc())


async def url_join(chat_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        invite_url = await create_invite(chat_id, context=context)
        chat = await context.bot.get_chat(chat_id=chat_id)
        if chat.type.lower() == "supergroup":
            typo = "group"
        else:
            typo = chat.type.lower()
        keyboard = [[InlineKeyboardButton(
            f"Join {typo} {chat.title}", url=invite_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(f"Click on the button below to join the chat.",
                                                      reply_markup=reply_markup)
    except Exception as error:
        print(traceback.format_exc())


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        """Sends a message with three inline buttons attached."""
        keyboard = [[InlineKeyboardButton("↩️ Back to the main menu",
                                          callback_data=json.dumps({"action": "goto", "dest": "menu"}))]]

        # keyboard = [
        #    [
        #        InlineKeyboardButton("Option 1", callback_data="1")],
        #    [InlineKeyboardButton("Option 3", callback_data="3")],
        # ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"You are not authorised to perform this action.",
                                        reply_markup=reply_markup)
    except Exception as error:
        print(traceback.format_exc())


async def membershipstatus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        keyboard = []

        user_id = update.effective_user.id
        if sql.db.is_client_premium(user_id):
            date_text = sql.db.get_client_formatted_expiration_date(user_id=user_id)[
                0]
            if date_text is not None:
                keyboard = [[InlineKeyboardButton("Renew subscription.",
                                                  callback_data=json.dumps({"action": "goto", "dest": "subscribe"}))],
                            [InlineKeyboardButton("↩️ Back to the main menu",
                                                  callback_data=json.dumps({"action": "goto", "dest": "menu"}))]]
                # keyboard = [
                #    [
                #        InlineKeyboardButton("Option 1", callback_data="1")],
                #    [InlineKeyboardButton("Option 3", callback_data="3")],
                # ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"Your membership is valid until:\n📅 {date_text}",
                    reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("Subscribe.",
                                              callback_data=json.dumps({"action": "goto", "dest": "subscribe"}))],
                        [InlineKeyboardButton("↩️ Back to the main menu",
                                              callback_data=json.dumps({"action": "goto", "dest": "menu"}))]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "It seems like you don't have an active membership.",
                reply_markup=reply_markup)
    except Exception as error:
        print(traceback.format_exc())


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.effective_user.id == 1956335032 or update.effective_user.id == 1525103352:
            help_message = "Below you'll find a list with the commands available in this bot.\n\n*GENERAL*\n/help - Open the help menu.\n/start - Get started - show the initial message.\n\n*SUBSCRIPTION*\n/accesstoken\n/addpremium ```user_id``` ```duration``` - Add some days premium to user\n/addpremiump ```user_id``` ```plan``` - Add premium plan to user.\n/join - Join the chats this bot manages.\n/membershipstatus - Renew or cancel your subscription.\n/subscribe - Become a member."
        else:
            help_message = "Below you'll find a list with the commands available in this bot.\n\n*GENERAL*\n/help - Open the help menu.\n/start - Get started - show the initial message.\n\n*SUBSCRIPTION*\n/accesstoken\n/join - Join the chats this bot manages.\n/membershipstatus - Renew or cancel your subscription.\n/subscribe - Become a member."

        await update.message.reply_text(help_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    except Exception as error:
        print(traceback.format_exc())


async def create_invite(chat_id, context: ContextTypes.DEFAULT_TYPE):
    invite = await context.bot.create_chat_invite_link(chat_id=chat_id, creates_join_request=False, member_limit=1, name="Join Premium Channel Now! This link only valid for 1 people only!")
    return invite.invite_link


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()
        data = json.loads(query.data)
        if data["action"] == "goto":
            if data["dest"] == "menu":
                await menu(update, context)
        elif data["action"] == "join":
            await url_join(data["chat_id"], update=update, context=context)
        elif data["action"] == "subscribe":
            await buy_handle(update=update, context=context, payment_method=data["dest"])
        elif data["action"] == "buy_plan":
            await buy_crypto(update=update, context=context, plan_id=data["plan_id"])
        elif data["action"] == "addpremium":
            data["admin_id"]

        # await query.edit_message_text(text=f"Selected option: {query.data}")
    except Exception as error:
        print(traceback.format_exc())


async def buy_handle(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_method: str):
    try:
        if payment_method == "crypto":
            keyboard = []
            plans = sql.db.get_plans()
            if plans is not None:
                for plan in plans:
                    keyboard.append([InlineKeyboardButton(f"{plan[1]}:  ${plan[2]:g}/{plan[3]} {plan[4]}",
                                                          callback_data=json.dumps(
                                                              {"action": "buy_plan", "plan_id": plan[0]}))])
            print(keyboard)
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.edit_text(f"Select a plan from the list below:",
                                                          reply_markup=reply_markup)
    except:
        print(traceback.format_exc())


async def buy_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
    try:
        plan = sql.db.get_plan(plan_id)
        if plan is not None:
            payment = nowpayments_api.create_payment(price=plan[2], ipn_callback_url=ipn_call_back_url,
                                                     order_description=f"{{\"id\": \"ve_tg_subscription\", \"user_id\": {update.effective_user.id}, \"plan\": {plan_id}}}")
            address = payment["pay_address"]
            await update.callback_query.message.edit_text("<em><strong>" + html.escape(
                "—Payment method: USDT TRC20") + f"</strong></em>\r\n<code>{address}</code>" + html.escape(
                "\r\n(") + "<b><u>Click to copy the address</u></b>" + html.escape(")\r\n\r\nSend ")+f"<code>{str(round(payment['pay_amount'], 2))}</code>"+html.escape(" USDT to the address above.\r\n\r\nYou can pay directly through the TRC20 Network. If you encounter any problems, please send a message below and it will be forwarded to our support team. "),
                parse_mode=telegram.constants.ParseMode.HTML)
    except:
        print(traceback.format_exc())


async def chat_join_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if sql.db.is_client_premium(user_id=user_id) and chat_id in sql.db.get_chats():
            await update.chat_join_request.approve()
    except:
        print(traceback.format_exc())


START, OnGoing = range(2)


def get_time(time: datetime.datetime = datetime.datetime.now()) -> str:
    # Get the current time in UTC
    now_utc = time

    tz_utc = datetime.timezone.utc

    # Convert the time to the desired timezone
    tz = datetime.timezone(datetime.timedelta(hours=0))
    local_time = now_utc.astimezone(tz)

    # Format the time string
    time_string = local_time.strftime('%d %b \'%y, %H:%M (%Z)')
    return time_string


def bool_to_string(value) -> str:
    if value in [False, None, '', set(), [], {}]:
        return 'No'
    else:
        return 'Yes'


def is_true(value):
    if value in [False, None, '', set(), [], {}]:
        return False
    else:
        return True


def bold(text) -> str:
    try:
        if text is not str:
            text = str(text)
        return "<b>" + text + "</b>"
    except Exception as error:
        print(traceback.format_exc())


def reformat(update: Update, message) -> str:
    if message is None:
        message = ""
    user = update.effective_user
    message = "#Built_in_Support\nFrom: " + user.mention_html() + " (#u" + str(
        user.id) + ")\n" + get_time() + "\nHas an active membership: " + bool_to_string(
        sql.db.is_client_premium(user.id)) + "\n-- -- -- -- -- -- -- -- --\n" + html.escape(message)
    return message


async def forward_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """{
        'message_id': 5,
        'date': 1605106546,
        'chat': {'id': 49820636, 'type': 'private', 'username': 'danokhlopkov', 'first_name': 'Daniil', 'last_name': 'Okhlopkov'},
        'text': 'TEST QOO', 'entities': [], 'caption_entities': [], 'photo': [], 'new_chat_members': [], 'new_chat_photo': [], 'delete_chat_photo': False, 'group_chat_created': False, 'supergroup_chat_created': False, 'channel_chat_created': False,
        'from': {'id': 49820636, 'first_name': 'Daniil', 'is_bot': False, 'last_name': 'Okhlopkov', 'username': 'danokhlopkov', 'language_code': 'en'}
    }"""
    try:
        message = update.message
        caption = (message.caption or "")
        text = (message.text or "")
        # print(message.to_json())
        # print(type(message.photo))
        sent = False

        if text in button_text.values():
            if text == button_text["how_it_works"]:
                await message.chat.send_message(text=how_it_works_message, parse_mode=telegram.constants.ParseMode.HTML)
            elif text == button_text["prices"]:
                await message.chat.send_message(text=prices_message, parse_mode=telegram.constants.ParseMode.HTML)
            elif text == button_text["how_to_pay"]:
                await payment_method(update=update, context=context)
            elif text == button_text["vip_info"]:
                await message.chat.send_message(text=vip_info_message, parse_mode=telegram.constants.ParseMode.HTML)
            elif text == button_text["support"]:
                await message.chat.send_message(text=support_message, parse_mode=telegram.constants.ParseMode.HTML)
            elif text == button_text["free_channel_link"]:
                await message.chat.send_message(text=free_link_message, parse_mode=telegram.constants.ParseMode.HTML)

        if message.effective_attachment is not None:
            input_media: List[Union[InputMediaAudio, InputMediaDocument,
                                    InputMediaPhoto, InputMediaVideo]] = []
            attachment = message.effective_attachment
            att_type = type(attachment)
            if att_type == list or att_type == tuple:
                input_media.append(InputMediaPhoto(attachment[-1].file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                context.bot_data[mess.message_id] = update.effective_user.id
                sent = True
            elif att_type == telegram.Video:
                input_media.append(InputMediaVideo(attachment.file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                sent = True
                context.bot_data[mess.message_id] = update.effective_user.id
            elif att_type == telegram.Audio:
                input_media.append(InputMediaAudio(attachment.file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                sent = True
                context.bot_data[mess.message_id] = update.effective_user.id
            elif att_type == telegram.Document:
                input_media.append(InputMediaDocument(attachment.file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                context.bot_data[mess.message_id] = update.effective_user.id
            # elif att_type == telegram.Sticker:
            #    user_id = update.message.from_user.id
            #    profile_url = f"https://t.me/{update.effective_user.username}"
            #    button = telegram.InlineKeyboardButton(
            #        text=f"From: {update.effective_user.full_name}",
            #    )
            #    reply_markup = telegram.InlineKeyboardMarkup(
            #        [[button]]
            #    )
            #    await context.bot.send_sticker(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
            #                                   sticker=message.sticker.file_id, reply_markup=reply_markup)
        else:
            mess = await context.bot.send_message(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                  text=reformat(
                                                      update=update, message=text),
                                                  entities=message.entities,
                                                  parse_mode=telegram.constants.ParseMode.HTML)
            context.bot_data[mess.message_id] = update.effective_user.id
            sent = True
        if sent:
            pass
    except Exception as error:
        print(traceback.format_exc())


async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Via PayPal", url=os.getenv("UPGRADE_CHAT_LINK"))],
                [InlineKeyboardButton("Via Crypto",
                                      callback_data=json.dumps({"action": "subscribe", "dest": "crypto"}))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.chat.send_message(text=how_to_pay_message, parse_mode=telegram.constants.ParseMode.HTML,
                                           reply_markup=reply_markup)


async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """{
        'message_id': 5,
        'date': 1605106546,
        'chat': {'id': 49820636, 'type': 'private', 'username': 'danokhlopkov', 'first_name': 'Daniil', 'last_name': 'Okhlopkov'},
        'text': 'TEST QOO', 'entities': [], 'caption_entities': [], 'photo': [], 'new_chat_members': [], 'new_chat_photo': [], 'delete_chat_photo': False, 'group_chat_created': False, 'supergroup_chat_created': False, 'channel_chat_created': False,
        'from': {'id': 49820636, 'first_name': 'Daniil', 'is_bot': False, 'last_name': 'Okhlopkov', 'username': 'danokhlopkov', 'language_code': 'en'}
    }"""
    try:
        message = update.message
        sent = False
        if message.effective_attachment is not None:
            input_media: List[Union[InputMediaAudio, InputMediaDocument,
                                    InputMediaPhoto, InputMediaVideo]] = []
            attachment = message.effective_attachment
            att_type = type(attachment)
            if att_type == list or att_type == tuple:
                input_media.append(InputMediaPhoto(attachment[-1].file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=message.caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                context.bot_data[mess.message_id] = update.effective_user.id
                sent = True
            elif att_type == telegram.Video:
                input_media.append(InputMediaVideo(attachment.file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=message.caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                sent = True
                context.bot_data[mess.message_id] = update.effective_user.id
            elif att_type == telegram.Audio:
                input_media.append(InputMediaAudio(attachment.file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=message.caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                sent = True
                context.bot_data[mess.message_id] = update.effective_user.id
            elif att_type == telegram.Document:
                input_media.append(InputMediaDocument(attachment.file_id))
                mess = await context.bot.send_media_group(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                          caption=reformat(
                                                              update=update, message=message.caption),
                                                          caption_entities=message.entities,
                                                          parse_mode=telegram.constants.ParseMode.HTML, media=input_media)
                sent = True
                context.bot_data[mess.message_id] = update.effective_user.id
            # elif att_type == telegram.Sticker:
            #    user_id = update.message.from_user.id
            #    profile_url = f"https://t.me/{update.effective_user.username}"
            #    button = telegram.InlineKeyboardButton(
            #        text=f"From: {update.effective_user.full_name}",
            #    )
            #    reply_markup = telegram.InlineKeyboardMarkup(
            #        [[button]]
            #    )
            #    await context.bot.send_sticker(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
            #                                   sticker=message.sticker.file_id, reply_markup=reply_markup)
        else:
            mess = await context.bot.send_message(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                  text=reformat(
                                                      update=update, message=message.text),
                                                  entities=message.entities,
                                                  parse_mode=telegram.constants.ParseMode.HTML)
            sent = True
            context.bot_data[mess.message_id] = update.effective_user.id
        if sent:
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text="\nI am forwarding your message to the administrator.\nPlease bear with us, we will get back to you as soon as possible.\nThank you.\n")
            return OnGoing
    except Exception as error:
        print(traceback.format_exc())


async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        # Check if the message is a reply
        if message.reply_to_message:
            # Get the replied message
            replied_message = message.reply_to_message
            # Check if the original message was sent by this bot
            if replied_message.from_user.id == context.bot.id:
                # Check if all entities in the replied message are mentions
                # print(replied_message.to_json())
                value = context.bot_data.get(
                    replied_message.message_id, 'Not found')
                if (value != 'Not found' and value != None):
                    await context.bot.copy_message(chat_id=value, from_chat_id=update.message.chat_id,
                                                   message_id=message.message_id)
                    await message.chat.send_message(text="Sent Message")
    except Exception as error:
        print(traceback.format_exc())


async def premiuma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = context.args[0]
        duration = context.args[1]
        if update.effective_user.id == 1956335032 or update.effective_user.id == 1525103352:
            client = sql.db.add_premium_client(user_id, float(duration))
            await context.bot.send_message(user_id, f"You have received {duration} days premium from Admin, use /join command to join premium channel.")
        else:
            await context.bot.send_message(update.effective_user.id, "You don't have permission to do this!")
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await context.bot.send_message(update.effective_user.id, "Unknow error!")


async def premiumadd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = context.args[0]
        plan_id = context.args[1]
        if update.effective_user.id == 1956335032 or update.effective_user.id == 1525103352:
            client = sql.db.add_plan_client(user_id, plan_id)
            plan = sql.db.get_plan(plan_id)
            await context.bot.send_message(user_id, f"You have received {plan[1]} premium plan from Admin, use /join command to join premium channel.")
        else:
            await context.bot.send_message(update.effective_user.id, "You don't have permission to do this!")
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        await context.bot.send_message(update.effective_user.id, "Unknow error!")


async def job(context: CallbackContext):
    try:
        chat_id = -1001831182787
        vip_chat = await context.bot.get_chat(chat_id)
        now = datetime.datetime.now()
        members = sql.db.get_active_clients(limit=10)
        for member in members:
            try:
                time.sleep(20)
                if member[3] < now:
                    mem = await vip_chat.get_member(member[0])
                    user = mem.user
                    if mem is not None:
                        try:
                            sql.db.update_client(member[0], active=0)
                            await context.bot.banChatMember(chat_id=chat_id, user_id=user.id)
                            await context.bot.unbanChatMember(chat_id=chat_id, user_id=user.id)
                            await context.bot.send_message(chat_id=TELEGRAM_SUPPORT_CHAT_ID,
                                                           text=bold(user.mention_html()) + " (#u" + str(
                                                               user.id) + ") subscription ended, for more details check the database",
                                                           parse_mode=telegram.constants.ParseMode.HTML)
                        except Exception as e:
                            print(e)
                            print(traceback.format_exc())
                elif (member[3] - timedelta(days=3)) < now and not member[5]:
                    mem = await context.bot.get_chat(member[0])
                    if mem is not None:
                        sql.db.update_client(member[0], dmed=1)
                        await context.bot.send_message(chat_id=member[0], text=html.escape(
                            f"Hello {mem.full_name}, your premium expires in 3days. Use /subscribe command to renew your subscription!"),
                            parse_mode=constants.ParseMode.HTML)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
    except Exception as e:
        print(e)
        print(traceback.format_exc())


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_chat.id == -1001778671844:
            buttons = [[KeyboardButton(text=button_text["how_it_works"])],
                       [KeyboardButton(text=button_text["prices"]), KeyboardButton(
                           text=button_text["how_to_pay"])],
                       [KeyboardButton(
                           text=button_text["vip_info"])],
                       [KeyboardButton(text=button_text["support"]),
                        KeyboardButton(text=button_text["free_channel_link"])]]
            reply_markup = ReplyKeyboardMarkup(buttons)
            await context.bot.send_photo(chat_id=update.effective_user.id, photo=pathlib.Path("logo.png"))
            await context.bot.send_message(chat_id=update.effective_user.id, text=welcome_message,
                                           reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.HTML)

    except Exception as error:
        print(traceback.format_exc())


def discord_bot():
    try:
        print("Run the Discord bot.")
        """Run the Discord bot."""
        global disBot

        disBot.run(token=disToken)
    except Exception as error:
        print(traceback.format_exc())
        try:
            disBot.run(token=disToken)
        except Exception as error:
            print(traceback.format_exc())


def telegram_bot() -> None:
    global application
    try:
        """Run the Telegram bot."""
        print("Run the Telegram bot.")
        # Create the Application and pass it your bot's token.

        application = Application.builder().token(token=token).concurrent_updates(128).connection_pool_size(
            50000000).pool_timeout(30).read_timeout(30).get_updates_pool_timeout(30).build()
        global bot

        bot = application.bot
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help))
        application.add_handler(CommandHandler("donate", donate))
        application.add_handler(CommandHandler("join", join))
        # application.add_handler(CommandHandler("code", code))
        application.add_handler(CommandHandler("subscribe", payment_method))
        application.add_handler(CommandHandler("addpremium", premiuma))
        application.add_handler(CommandHandler("addpremiump", premiumadd))
        application.add_handler(CommandHandler(
            "membershipstatus", membershipstatus))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(ConversationHandler(
            entry_points=[MessageHandler(filters=filters.ChatType.PRIVATE & ~ filters.COMMAND & ~ button_command_filter,
                                         callback=start_chat)],
            states={
                OnGoing: [
                    MessageHandler(filters=filters.ChatType.PRIVATE & ~ filters.COMMAND & ~ button_command_filter,
                                   callback=forward_to_chat)]
            },
            fallbacks=[],
            conversation_timeout=900,  # 15m timeout
            per_user=True,
            per_chat=True
        ))
        application.add_handler(
            MessageHandler(filters=filters.ChatType.PRIVATE & ~ filters.COMMAND & button_command_filter,
                           callback=forward_to_chat))
        application.add_handler(MessageHandler(filters.COMMAND, start))
        application.add_handler(MessageHandler(filters.Chat(
            TELEGRAM_SUPPORT_CHAT_ID) & filters.REPLY, forward_to_user))
        # application.add_handler(
        #     telegram.ext.ChatJoinRequestHandler(chat_join_request_callback))
        application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS, join_handler))
        job_queue = application.job_queue
        job_queue.run_repeating(callback=job, interval=3600)

        # Run the bot until the user presses Ctrl-C
        application.run_polling(timeout=30)

    except Exception as error:
        print(traceback.format_exc())
        try:
            application.run_polling(timeout=30)
        except Exception as error:
            print(traceback.format_exc())


app = Flask(__name__)


def np_signature_check(np_secret_key, np_x_signature, message):
    sorted_msg = json.dumps(message, separators=(',', ':'), sort_keys=True)
    digest = hmac.new(
        str(np_secret_key).encode(),
        sorted_msg.encode(),
        hashlib.sha512)
    signature = digest.hexdigest()
    if signature == np_x_signature:
        return True
    else:
        return False


@app.route('/ipn', methods=['POST'])
# Binance
# async def ipn():
#     message = request.json
#     id = request.args.get("id")
#     user_id = request.args.get("user_id")
#     plan = request.args.get("plan")
#     interaction_id = request.args.get("interaction_id")
#     mod_id = request.args.get("mod_id")
#     duration = request.args.get("duration")
#     if message["bizStatus"] == "PAY_SUCCESS":
#         if id == "ve_tg_subscription":
#             await give_premium(user_id, plan)
#         elif id == "ve_disc_subscription":
#             import sys
#             sys.path.append(os.path.abspath(os.curdir))
#             from PremiumManager import sql
#             sql.connect()
#             sql.addPremium(interaction_id, user_id,
#                             mod_id, duration)
#             user = disBot.get_user(int(user_id))
#             embed = discord.Embed()
#             embed.description = "Payment successfully received. Added premium plan for you with " + \
#                 str(duration) + " days duration"
#             # await disBot.loop.create_task(user.send(embed=embed))
#             asyncio.run_coroutine_threadsafe(
#                 user.send(embed=embed), disBot.loop)
#     return '{"returnCode":"SUCCESS","returnMessage":null}'
# NowPayments
async def ipn():
    payload = request.get_json()
    np_x_signature = request.headers.get('x-nowpayments-sig')
    np_secret_key = os.getenv("NP_SECRET_KEY")

    message = request.json

    # Compare the signed string with the x-nowpayments-sig header
    if np_signature_check(np_secret_key, np_x_signature, message):
        if message["payment_status"] == "finished":
            # await main.give_premium(u)
            if message["order_description"]:
                desc = "{" + message["order_description"] + "}"
                msg = json.loads(desc)
                if msg["id"] == "ve_tg_subscription":
                    await give_premium(msg["user_id"], msg["plan"])
                elif msg["id"] == "ve_disc_subscription":
                    import sys
                    sys.path.append(os.path.abspath(os.curdir))
                    from PremiumManager import sql
                    sql.connect()
                    sql.addPremium(msg["message_id"], msg["user_id"],
                                   msg["mod_id"], msg["duration"])

                    user = disBot.get_user(int(msg["user_id"]))

                    embed = discord.Embed()
                    embed.description = "Payment successfully received. Added premium plan for you with " + \
                        str(msg["duration"]) + " days duration"

                    # await disBot.loop.create_task(user.send(embed=embed))
                    asyncio.run_coroutine_threadsafe(
                        user.send(embed=embed), disBot.loop)
        return 'OK'
    else:
        # IPN signature is invalid, reject the request
        print("Invalid Signiture")
        return 'Invalid signature', 400


@app.route('/submit-connect', methods=['POST'])
async def submitConnect():
    secret_key = 'secretkey1234889128389398'

    message = request.json

    # Compare the secret key
    if message is not None and secret_key == message["secret_key"]:
        if message["payment_status"] == "finished":
            import sys
            sys.path.append(os.path.abspath(os.curdir))
            from PremiumManager import sql
            sql.connect()
            sql.addPremium(message["message_id"], message["disc_user_id"],
                           message["mod_id"], message["duration"])

            user = disBot.get_user(int(message["disc_user_id"]))

            embed = discord.Embed()
            embed.description = "Payment successfully received. Added premium plan for you with " + \
                str(message["duration"]) + " days duration"

            # await disBot.loop.create_task(user.send(embed=embed))
            asyncio.run_coroutine_threadsafe(
                user.send(embed=embed), disBot.loop)
    return "OK"


@app.route('/create-invite-link', methods=['POST'])
async def createInviteLink():
    try:
        secret_key = 'secretkey1234889128389398'

        message = request.json

        # Compare the secret key
        if message is not None and secret_key == message["secret_key"]:
            for i in range(5):
                try:
                    invite = await bot.create_chat_invite_link(chat_id=TELEGRAM_PREMIUM_CHAT_ID, creates_join_request=False, member_limit=1, name="Join Premium Channel Now! This link only valid for 1 people only!")
                    return jsonify({"status": "success", "invite_link": invite.invite_link})
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
        else:
            return 'Invalid signature', 400
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({"status": "failed"})


@app.route('/webhook/meeting', methods=['POST'])
async def webhook_meeting():
    try:
        secret_key = 'secretkey1234889128389398'

        message = request.json

        # Compare the secret key
        if message is not None and secret_key == message["secret_key"]:
            user = disBot.get_channel(1016345175225810995)

            embed = discord.Embed()
            embed.description = "One person has hopped on a call with you [here](" + \
                str(message["meeting_link"]) + \
                "). Please follow the link to create a google meeting room and add these emails into attendees list: " + \
                message['attendees']

            # await disBot.loop.create_task(user.send(embed=embed))
            asyncio.run_coroutine_threadsafe(
                user.send(embed=embed), disBot.loop)

            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "failed", "msg": "Invalid signature"}), 400
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({"status": "failed"})


def run_flask():
    app.run(debug=False, host='0.0.0.0', port=25921)


@disBot.event
async def on_ready():
    if not os.path.exists(os.path.abspath(
            os.curdir)+"/temp"):
        os.makedirs(os.path.abspath(
            os.curdir)+"/temp")
    print("Ready!")


@disBot.tree.command(name="discount_code", description="Owner and Supporters Only")
async def discountCode(interaction, discount_code: str = "", discount_percent: int = 85):
    if interaction.user.id in [906046683509583884, 566577469172351007] or discord.utils.get(interaction.guild.roles, id=993239960457052321) or discord.utils.get(interaction.guild.roles, id=993222522482991185):
        discount_code = sql.db.create_discount_code(
            discount_code, discount_percent)
        await interaction.response.send_message(f'Discount code created is : {discount_code}. Send this to your customer: {PAYMENT_URL}/?discount_code={discount_code}', delete_after=60, ephemeral=True)
    else:
        await interaction.response.send_message('You must be the owner or supporter to use this command!', delete_after=60, ephemeral=True)




@disBot.tree.command(name="list_subscriptions", description="Select subscription")
async def createSubscription(interaction):
    try:
        plans = sql.db.get_plans()
        view = discord.ui.View()
        style = discord.ButtonStyle.primary

        if plans is not None:
            for plan in plans:
                item = discord.ui.Button(
                    style=style,
                    custom_id=str(plan[0]),
                    disabled=False,
                    label=f"{plan[1]}:  ${plan[2]:g}/{plan[3]} {plan[4]}"
                )
                view.add_item(item=item)

        await interaction.response.send_message("List of all subscriptions!", view=view, delete_after=60, ephemeral=True)

        def convert_months_to_days(months):
            current_date = datetime.date.today()
            future_date = current_date + relativedelta(months=months)
            duration_in_days = (future_date - current_date).days
            return duration_in_days

        async def subscriptionsSelected(interaction):
            try:
                plan_id = interaction.data["custom_id"]
                plan = sql.db.get_plan(plan_id)
                if plan is not None:
                    days = 0
                    if plan[4] == "month":
                        days = convert_months_to_days(plan[3])
                    else:
                        days = plan[3]

                    # NowPayments
                    payment = nowpayments_api.create_payment(price=plan[2], ipn_callback_url=ipn_call_back_url,
                                                             order_description=f"{{\"id\": \"ve_disc_subscription\", \"interaction_id\":{interaction.id}, \"user_id\": {interaction.user.id}, \"mod_id\": {interaction.client.application_id}, \"duration\": {days}}}, \"channel_id\": {interaction.channel_id}, \"message_id\": {interaction.message.id}")

                    address = payment["pay_address"]

                    address_qrcode = qrcode.make(address)

                    with tempfile.TemporaryDirectory(dir=pathlib.Path().resolve()) as tmpdirname:
                        temp_dir = pathlib.Path(tmpdirname)

                    filename = temp_dir.name
                    address_qrcode.save(os.path.abspath(
                        os.curdir)+f"/temp/{filename}.png")

                    embed = discord.Embed()
                    embed.description = html.escape("Payment method: USDT TRC20") + f"\r\n\r\n{address}" + html.escape(
                        "\r\n\r\nSend ")+f"{str(round(payment['pay_amount'], 2))}"+html.escape(" USDT to the address above.\r\n\r\nYou can pay directly through the TRC20 Network. If you encounter any problems, please send a message below and it will be forwarded to our support team.\r\n\r\nWhen we receive payment, we will DM to you.")
                   
                    await interaction.response.edit_message(embed=embed, view=discord.ui.View(), attachments=[discord.File(os.path.abspath(os.curdir)+f"/temp/{filename}.png", filename="address_qrcode.png")])

                    os.remove(os.path.abspath(os.curdir) +
                              f"/temp/{filename}.png")

                    i = await disBot.wait_for("interaction", check=lambda i: i, timeout=45)
                    # await on_button_click(i, address)
                else:
                    await interaction.response.edit_message(content="Cannot find the subscription you have selected")
            except:
                print(traceback.format_exc())
                await interaction.response.edit_message(content="Error processing your request, please try again. If you are still getting this error, ask your administrator or support about this.")


        i = await disBot.wait_for("interaction", check=lambda i: i, timeout=45)

        await subscriptionsSelected(i)
    except:
        print(traceback.format_exc())

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    discord_thread = threading.Thread(target=discord_bot)
    # telegram_thread = threading.Thread(target=telegram_bot)

    flask_thread.start()
    discord_thread.start()
    # telegram_thread.start()

    telegram_bot()

    flask_thread.join()
    discord_thread.join()
    # telegram_thread.join()
