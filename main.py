# -*- coding: utf-8 -*-

import os
import datetime, time
import sqlite3
import csv
import db, connect_TCP, log_unit, const
import threading, queue

import modbus_tk.defines as cst

import telebot
from telebot import types

bot = telebot.TeleBot(const.TOKEN)

############ Инициализируем базы данных
db.init_db()
db.init_db_passing()
db.init_db_log()


#######################################

class User:
    def __init__(self, id):
        self.id = id
        self.code = None
        self.password = None


user = User(None)

qe = queue.Queue()
t1 = threading.Thread(target=log_unit.logging, args=[qe])
t1.start()


def _init_propusk():
    query = """SELECT userid,  first_name, last_name, username, pass, datareg FROM users;"""
    otvet = {}
    rez = db.get_record(query, "")
    one_result = rez.fetchall()
    # one_result[0]
    if one_result.__len__() > 0:
        i = 0
        for i in range(0, one_result.__len__()):
            # one_result[i] = one_result[i] + (False, 0)
            otvet[str(one_result[i][0])] = {"userid": one_result[i][0], "first_name": one_result[i][1],
                                            "last_name": one_result[i][2], "username": one_result[i][3],
                                            "pass": one_result[i][4], "datareg": one_result[i][5], "active": True}
            # otvet = {**otvet, }
            i += 1
    else:
        pass
    return otvet

    #
    # fillter_tuples = list(itertools.takewhile(lambda x: x[0] == 'C#', list_of_tuples))


#

isauthorized = _init_propusk()


######################################################################################### Проверка пароля
def inputpass(message, schet):
    if schet == 1:
        suffix = ' (попробуй 123)'
    elif schet == 2:
        suffix = ' (qwerty однозначно)'
    else:
        suffix = ""
    bot.send_message(message.from_user.id, "Попытка №" + str(schet + 1) + suffix)
    msg = bot.reply_to(message, """Введите пароль:""")
    bot.register_next_step_handler(msg, verifypass, schet)


def verifypass(message, schet):
    if message.text == str(isauthorized[str(message.from_user.id)]["pass"]):
        bot.send_message(message.from_user.id, "Небось угадал.")
        # globals()['isauthorized'] = True
        isauthorized[str(message.from_user.id)]["active"] = True
        mainmenu(message)
    else:
        schet = schet + 1
        if schet <= 2:
            inputpass(message, schet)
        else:
            bot.send_message(message.from_user.id, "Вы какой то подозрительный.")
            bot.clear_step_handler_by_chat_id(chat_id=message.from_user.id)


######################################################################################### Проверка пароля


def makeCSV(data):
    try:
        with open("temp.csv", mode="w", encoding="cp1251") as w_file:
            names = ["id", "dt", "tempatm", "temptributary", "tempreturn", "condition", "alarm"]
            file_writer = csv.DictWriter(w_file, delimiter=";", lineterminator="\r", fieldnames=names)
            file_writer.writeheader()
            for rec in data:
                file_writer.writerow(
                    {"id": rec[0], "dt": rec[1], "tempatm": '"' + str(rec[2]) + '"',
                     "temptributary": '"' + str(rec[3]) + '"', "tempreturn": '"' + str(rec[4]) + '"',
                     "condition": bool(rec[5]), "alarm": rec[6]})

            return w_file
    except Exception as err:
        pass


@bot.message_handler(commands=['help'])  # стартовая команда
def help(message):
    # bot.send_message(message.from_user.id, 'Бог в помощь.')
    bot.reply_to(message, "Бог тебе в помощь.")
    # bot.send_message(message.from_user.id,
    #                  """/off - завершение, перезагрузка компьютера бота\n/offbot - завершение работы бота.""")
    # bot.send_message(message.from_user.id, "/offbot - завершение работы бота.")


@bot.message_handler(commands=['start'])  # стартовая команда
def start(message):
    # Зарегистрируем проходящего
    dt = datetime.datetime.now()
    db.add_record_passing([message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                           message.from_user.username, dt])
    #############################
    if isauthorized.get(str(message.from_user.id)) == None or isauthorized.__len__() == 0:
        registration(message)
    elif isauthorized[str(message.from_user.id)]["active"] is True:
        bot.send_message(message.from_user.id, "Вы авторизованны.")
        mainmenu(message)
        return
    else:
        schet = 0
        inputpass(message, schet)

    # data = checkregistration(message)
    # if isauthorized.__len__() == 0:
    #     registration(message)

    # if isauthorized[message.from_user.id] is True:
    #     mainmenu(message)


########################################################################### Регистрация

@bot.message_handler(commands=['reg'])  # команда
def registration(message):
    # if globals()["isauthorized"] is True:
    #     bot.send_message(message.from_user.id, "Вы уже авторизованы.")
    #     return
    bot.reply_to(message, "{who}\nНеобходима регистрация.".format(who=message.from_user.first_name))
    try:
        chat_id = message.from_user.id
        name = message.text
        # user = User(message.from_user.id)
        # user_dict[chat_id] = user
        bot.send_message(message.from_user.id, 'Начнём регистацию.')
        msg = bot.send_message(message.from_user.id, 'Введите ключ проекта')
        bot.register_next_step_handler(msg, process_code_step, user)
    except Exception as e:
        bot.reply_to(message, 'Опаньки(oooops)')


def process_code_step(message, user):
    try:
        chat_id = message.from_user.id
        # id = message.text
        # user = User(message.from_user.id)
        # user.code = message.text
        if message.text != '369':
            bot.send_message(message.from_user.id, "Неправильный ключ. Обратитесь к Буратино.")
            return
        msg = bot.reply_to(message, 'Введите пароль?')
        bot.register_next_step_handler(msg, process_pass_step, user)
    except Exception as e:
        bot.reply_to(message, 'Опаньки(oooops')


def process_pass_step(message, user):
    try:
        chat_id = message.from_user.id
        name = message.text
        user.password = message.text
        db.add_record([message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                       message.from_user.username, user.password, datetime.datetime.now()])

        isauthorized[str(message.from_user.id)] = {"userid": message.from_user.id,
                                                   "first_name": message.from_user.first_name,
                                                   "last_name": message.from_user.last_name,
                                                   "username": message.from_user.username,
                                                   "pass": user.password, "datareg": datetime.datetime.now(),
                                                   "active": True}
        # bot.register_next_step_handler(msg, process_age_step)
        # globals()["isauthorized"] = _init_propusk()
    except Exception as e:
        bot.reply_to(message, 'Опаньки(oooops')


########################################################################### Регистрация


def setdevice(message, reg, decimal):
    # if message.text != 'Главное меню' and message.text != 'Помощь' and message.text != 'Задать выход устройства':
    #     num = int(NumOutput[6:]) - 1
    #     SetOutput(message, 16, num, 1, [int(message.text)])

    try:
        if connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_REGISTERS, reg,
                                  int(float(message.text.replace(",", ".")) * 10 if decimal is False else int(
                                      message.text))) is True:
            if connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_COILS, 1540, 1) is True:
                # time.sleep(0.1)
                connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_COILS, 1540, 0)

            bot.send_message(message.from_user.id, "Установлено.")
            # bot.clear_step_handler_by_chat_id(chat_id=message.from_user.id)
        return True
    except Exception as err:
        bot.send_message(message.from_user.id, "Не установлено.")
        return False

    # mainmenu(message)


def setdeviceAF(message, step):
    # try:
    if step == 1:
        reg = 3072
    elif step == 2:
        reg = 3073
    rez = connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_REGISTERS, reg, int(message.text))
    if rez is False:
        bot.send_message(message.from_user.id, "Нет подключения.")
        mainmenu(message)
    else:
        bot.clear_step_handler_by_chat_id(chat_id=message.from_user.id)
        if step == 1:
            msg = bot.send_message(message.from_user.id, "Введите значение AF2 (menu->next пропустить):")
            step = 2
            bot.register_next_step_handler(msg, setdeviceAF, step)
        else:
            bot.send_message(message.from_user.id, " Изменения внесенны.")
            mainmenu(message)


def mainmenu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("Текущее состояние объекта")
    btn2 = types.KeyboardButton("Лог")
    btn3 = types.KeyboardButton("Уставки")
    # btn3 = types.KeyboardButton('Изменение уставки температуры')
    # btn4 = types.KeyboardButton('Изменение скорости вентилятора')
    btn4 = types.KeyboardButton('Вкл/Выкл')
    # btn5 = types.KeyboardButton('Лог')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.from_user.id, "Выберите действие?", reply_markup=markup)


def _setpoints(message):
    setpoints = connect_TCP.read_unit(1, cst.READ_HOLDING_REGISTERS, 3072, 15)
    if setpoints is None:
        bot.send_message(message.from_user.id, "Не удалось прочитать уставки.")
    # Прочитаем из pr22 в pr12 если уставки нулевые
    elif setpoints[0] + setpoints[1] + setpoints[2] + setpoints[3] + setpoints[4] + setpoints[5] + setpoints[6] + setpoints[7] + setpoints[8] + setpoints[9] + setpoints[10] + setpoints[11] + setpoints[12] + setpoints[13] + setpoints[14] == 0:
        if connect_TCP.read_unit(1, cst.WRITE_MULTIPLE_COILS, 1539, 1) is True:
            connect_TCP.read_unit(1, cst.WRITE_MULTIPLE_COILS, 1539, 0)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='AF1-Норм.темп.притока=' + str(setpoints[0] / 10), callback_data=1))
        markup.add(types.InlineKeyboardButton(text='AF2-Аварийная низкая темп.притока=' + str(setpoints[1] / 10),
                                              callback_data=2))
        markup.add(types.InlineKeyboardButton(text='AF3-Низкая темп.обратки=' + str(setpoints[2] / 10),
                                              callback_data=3))
        markup.add(types.InlineKeyboardButton(text='AF4-Скорость вентиляторов 0-100.0=' + str(setpoints[3] / 10),
                                              callback_data=4))
        markup.add(types.InlineKeyboardButton(
            text='AF5-Прогрев емп. обратки=' + str(setpoints[4] / 10), callback_data=5))
        markup.add(
            types.InlineKeyboardButton(text='AF6-Мин.проц.откр.3-х ход.крана',
                                       callback_data=6))
        markup.add(types.InlineKeyboardButton(
            text='AF7-Время открытия возд.заслонки=' + str(setpoints[6]), callback_data=7))
        markup.add(
            types.InlineKeyboardButton(text='AF8-Выбор номера PID=' + str(setpoints[7]), callback_data=8))
        markup.add(types.InlineKeyboardButton(text='AF9-Постоянное Значение, не изменяется=' + str(setpoints[8]),
                                              callback_data=9))
        markup.add(types.InlineKeyboardButton(
            text='AF10-Темп.отключ.насоса при простое=' + str(
                setpoints[9] / 10), callback_data=10))
        markup.add(types.InlineKeyboardButton(
            text='AF11-Темп. открытия контура простоя=' + str(
                setpoints[10] / 10), callback_data=11))
        markup.add(types.InlineKeyboardButton(text='AF12-Аварийная темп.обратки=' + str(setpoints[11] / 10),
                                              callback_data=12))
        markup.add(types.InlineKeyboardButton(
            text='AF13-Время задержки вкл.ПИД=' + str(setpoints[12]),
            callback_data=13))
        markup.add(types.InlineKeyboardButton(text='Главное меню', callback_data=14))
        bot.send_message(message.from_user.id, message.text, reply_markup=markup)


def _vkl(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Вкл.', callback_data="Вкл"))
    markup.add(types.InlineKeyboardButton(text='Выкл', callback_data="Выкл"))
    markup.add(types.InlineKeyboardButton(text='Отмена', callback_data=14))
    bot.send_message(message.from_user.id, message.text, reply_markup=markup)


#
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    # bot.answer_callback_query(callback_query_id=call.id, text='Поехали')
    answer = "<>"
    select = call.data
    # message = call.data[1]
    if select == '1':
        msg = bot.send_message(call.from_user.id, "Введите значение температуры притока:")
        bot.register_next_step_handler(msg, setdevice, reg=3072, decimal=False)
        bot.answer_callback_query(callback_query_id=call.id, text='Отбой')
        # answer = "Введите значение температуры притока:"
    elif select == '2':
        msg = bot.send_message(call.from_user.id, "Введите значение -Аварийная низкая температура притока:")
        bot.register_next_step_handler(msg, setdevice, reg=3073, decimal=False)
        # answer =
    elif select == '3':
        msg = bot.send_message(call.from_user.id, "Введите значение Аварийная низкая температура обратки:")
        bot.register_next_step_handler(msg, setdevice, reg=3074, decimal=False)
        # answer =
    elif select == '4':
        msg = bot.send_message(call.from_user.id, "Введите значение Скорость вентиляторов:")
        bot.register_next_step_handler(msg, setdevice, reg=3075, decimal=False)
        # answer =
    elif select == '5':
        msg = bot.send_message(call.from_user.id, "Введите значение Темп.обратки прогрев перед вкл.вент.")
        bot.register_next_step_handler(msg, setdevice, reg=3076, decimal=False)
        # answer =
    elif select == '6':
        pass
    elif select == '7':
        msg = bot.send_message(call.from_user.id, "Введите значение Значение времени открытия воздушной заслонки")
        bot.register_next_step_handler(msg, setdevice, reg=3078, decimal=True)
        # answer =
    elif select == '8':
        msg = bot.send_message(call.from_user.id, "Введите значение Выбор номера типа PID")
        bot.register_next_step_handler(msg, setdevice, reg=3079, decimal=True)
        # answer =
    elif select == '9':
        # Не изменяется
        pass
    elif select == '10':
        msg = bot.send_message(call.from_user.id,
                               "Введите темп.уличного воздуха отключения насоса при неработающей вент.установке")
        bot.register_next_step_handler(msg, setdevice, reg=3081, decimal=False)
        # answer =
    elif select == '11':
        msg = bot.send_message(call.from_user.id,
                               "Введите значение внешней темп.открытия контура теплообменника во время простоя вент.установки")
        bot.register_next_step_handler(msg, setdevice, reg=3082, decimal=False)
        # answer =
    elif select == '12':
        msg = bot.send_message(call.from_user.id, "Введите значение АВАРИЙНАЯ ТЕМПЕРАТУРА ОБРАТКИ")
        bot.register_next_step_handler(msg, setdevice, reg=3083, decimal=False)
        # answer =
    elif select == '13':
        msg = bot.send_message(call.from_user.id,
                               "Введите значение времени задержки перед вкл.ПИД после пуска вентилятора")
        bot.register_next_step_handler(msg, setdevice, reg=3084, decimal=True)
        # answer =
    elif select == '14':
        # msg = bot.send_message(call.from_user.id, "И это всё")
        bot.answer_callback_query(callback_query_id=call.id, text='Отбой')
        answer = 'Выберите действие'
    elif select == 'Вкл':
        if connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_COILS, 1536, 1) is True:
            connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_COILS, 1536, 0)
            otvet = "Включено"
        else:
            otvet = "Ошибка включения"
        bot.answer_callback_query(callback_query_id=call.id, text=otvet)
        # answer = 'Включено'
    elif select == 'Выкл':
        if connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_COILS, 1537, 1) is True:
            connect_TCP.write_unit(1, cst.WRITE_MULTIPLE_COILS, 1537, 0)
            otvet = "Выключено"
        else:
            otvet = "Ошибка выключения"
        bot.answer_callback_query(callback_query_id=call.id, text=otvet)
        # answer = 'Выключено'

    # bot.send_message(call.message.chat.id, answer)

    # bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=answer,
                          reply_markup=None)
    # mainmenu(message)


#####################################################################
######################################################################
######################################################################
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    # Если сообщение старее 10 минут появления то ну его в Вукоебано
    # DTNow = datetime.datetime.now().replace(microsecond=0)
    # DTReg = datetime.datetime.fromtimestamp(message.json['date'])
    # s = (DTNow - DTReg).seconds
    # if s > 600:
    #     return
    # else:
    #     pass
    ##############

    #    Получим из потока данные
    n = qe.get()
    #   Проверим нааврийные уставки
    if n[4] is True:
        if n[0][1] <= n[2][1]:
            bot.send_message(isauthorized['1494201864']['userid'], 'Аварийная температура приточной вентиляции' +
                             '\n Установленно=' + str(n[2][1]) +
                             '\n Текущее значение=' + str(n[0][1]) +
                             '\n Зарегестрировано' + str(n[3]))
            # for bola in isauthorized:

            # bot.send_message(bola, 'Аварийная температура приточной вентиляции' +
            #                  '\n Установленно = ' + str(n[2][1] / 10) +
            #                  '\n Текущее значение = ' + str(n[0][1] / 10) +
            #                  '\n Зарегестрировано = ' + str(n[3]))
            # pass
        elif n[0][2] <= n[2][2]:
            for bola in isauthorized:
                bot.send_message(bola, 'Аварийная температура обратки' +
                                 '\n Установленно = ' + str(n[2][2] / 10) +
                                 '\n Текущее значение = ' + str(n[0][2] / 10) +
                                 '\n Зарегестрировано = ' + str(n[3]))

    #####################################

    # list(filter(lambda x: x[4] == 123, isauthorized))[0]
    if isauthorized.get(str(message.from_user.id)) == None or isauthorized.__len__() == 0:
        dt = datetime.datetime.now()
        db.add_record_passing([message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.username, dt])
        registration(message)
    elif isauthorized[str(message.from_user.id)]["active"] is True:
        pass

    if message.text == 'Главное меню':
        mainmenu(message)
    elif message.text == 'Текущее состояние объекта':
        try:
            paket = connect_TCP.read_unit(1, cst.READ_HOLDING_REGISTERS, 3137, 3)
            if paket[0] == None:
                tempatm = '0'
            else:
                tempatm = str((65536 - paket[0]) * (-1) if paket[0] > 65000 else paket[0]/10)
            temptributary = paket[1]
            tempreturn = paket[2]
            # tempatm = connect_TCP.read_unit(1, cst.HOLDING_REGISTERS, 3137, 1)
            # temptributary = connect_TCP.read_unit(1, cst.HOLDING_REGISTERS, 3138, 1)
            # tempreturn = connect_TCP.read_unit(1, cst.HOLDING_REGISTERS, 3139, 1)
            vkl = connect_TCP.read_unit(1, cst.READ_COILS, 1538, 1)
            bot.send_message(message.from_user.id, 'Cостояние оборудования : ' + ('ВКЛ.' if vkl[0] is 1 else 'ВЫКЛ.') +
                             '\n---------------------' +
                             '\nТемпература атмосферы = ' + str('0' if tempatm == None else str(tempatm / 10)) +
                             '\nТемпература притока = ' + str(
                '0' if temptributary == None else str(temptributary / 10)) +
                             '\nТемпература обратки = ' + str('0' if tempreturn == None else str(tempreturn / 10)) +
                             '\n---------------------')

        except Exception as err:
            bot.send_message(message.from_user.id, "Ошибка чтения состояния:")
        _vkl(message)

    elif message.text == 'Вкл/Выкл':
        _vkl(message)
    elif message.text == 'Изменение скорости вентилятора':
        pass
    elif message.text == 'Уставки':
        _setpoints(message)

    elif message.text == "Вкл/выкл":
        pass
    elif message.text == "Лог":
        conn = sqlite3.connect("log.db")
        cur = conn.cursor()

        query = """SELECT id, dt, tempatm, temptributary, tempreturn, condition, alarm FROM log order by dt desc LIMIT 2600"""
        # param = {"userid": message.from_user.id, "first_name": message.from_user.first_name}
        rez = cur.execute(query)
        one_result = rez.fetchall()
        buf = makeCSV(one_result)
        file = open(buf.name, 'rb')
        bot.send_document(message.from_user.id, file)

    else:
        bot.reply_to(message, "Ничего не понял.")
        mainmenu(message)


bot.polling(none_stop=True, interval=0)  # обязательная для работы бота часть
