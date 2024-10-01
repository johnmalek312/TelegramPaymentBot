from datetime import timedelta, datetime

import mysql.connector
import traceback
import string
import random
import os
from dotenv import load_dotenv


def convert_date(unit: str):
    if unit.lower() == "day" or unit.lower() == "days":
        return 1
    elif unit.lower() == "week" or unit.lower() == "weeks":
        return 7
    elif unit.lower() == "month" or unit.lower() == "months":
        return 30
    elif unit.lower() == "year" or unit.lower() == "years":
        return 366
    else:
        return 1


class Myself:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.connected = False
        self.connect()
        self.f = '%Y-%m-%d %H:%M:%S'

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=3306
            )
            self.cursor = self.connection.cursor()
            self.connected = True
            print("Connected to MySQL database.")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to connect to MySQL database: {}".format(error))

    def create_plan(self, title, price, duration, unit="days", active=True):
        try:
            if not self.connected:
                self.connect()
            sql = "INSERT INTO plans (title, price, duration, unit, active) VALUES ( %s, %s, %s, %s, %s)"
            val = (title, price, duration, unit, active)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record inserted.")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to insert record into plans table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_plans(self):
        try:
            if not self.connected:
                self.connect()
            self.cursor.execute("SELECT * FROM plans")
            myresult = self.cursor.fetchall()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from plans table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_activeplans(self):
        try:
            if not self.connected:
                self.connect()
            self.cursor.execute("SELECT * FROM plans WHERE active = 1")
            myresult = self.cursor.fetchall()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from plans table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_plan(self, id):
        try:
            if not self.connected:
                self.connect()
            self.cursor.execute(f"SELECT * FROM plans WHERE id = {id}")
            myresult = self.cursor.fetchone()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from plans table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def update_plan(self, id, title=None, price=None, duration=None, unit="days", active=True):
        try:
            if not self.connected:
                self.connect()
            sql = "UPDATE plans SET "
            vals = []
            if title is not None:
                sql += "title = %s, "
                vals.append(title)
            if price is not None:
                sql += "price = %s, "
                vals.append(price)
            if duration is not None:
                sql += "duration = %s, "
                vals.append(duration)
            if unit is not None:
                sql += "unit = %s, "
                vals.append(unit)
            if active is not None:
                sql += "active = %s, "
                vals.append(active)
            sql = sql[:-2] + " WHERE id = %s"
            vals.append(id)
            val = tuple(vals)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record(s) affected.")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to update record in plans table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def insert_or_update_payment(self, user_id, payment_address):
        try:
            print("SELECT * FROM payments WHERE user_id = %s", (user_id,))
            print("INSERT INTO payments (user_id, payment_address) VALUES (%s, %s)",
                                    (user_id, payment_address))
            print("UPDATE payments SET payment_address = %s WHERE user_id = %s",
                                    (payment_address, user_id))
            self.cursor.execute("SELECT * FROM payments WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            if result is None:
                self.cursor.execute("INSERT INTO payments (user_id, payment_address) VALUES (%s, %s)",
                                    (user_id, payment_address))
            else:
                self.cursor.execute("UPDATE payments SET payment_address = %s WHERE user_id = %s",
                                    (payment_address, user_id))
            self.connection.commit()
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to update record in payments table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_payment(self, user_id=None):
        try:
            self.cursor.execute("SELECT * FROM payments WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to insert record into tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_payments(self):
        try:
            self.cursor.execute("SELECT * FROM payments")
            results = self.cursor.fetchall()
            return results
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to insert record into tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def create_client(self, user_id, duration, plan=0, active=True, dmed=True):
        try:
            client = self.get_client(user_id)
            if client is not None:
                raise Exception("Error: Client already exists, can't create another client.")
            if not self.connected:
                self.connect()
            sql = "INSERT INTO tgclients (user_id, purchase_date, duration, expiration_date, active, dmed, plan) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            val = (user_id, datetime.now().strftime(self.f), duration,
                   (datetime.now() + timedelta(days=duration)).strftime(self.f), active, dmed, plan)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record inserted.")
            select_sql = "SELECT * FROM tgclients WHERE user_id = %s"
            select_val = (user_id,)
            self.cursor.execute(select_sql, select_val)
            inserted_row = self.cursor.fetchone()
            return inserted_row
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to insert record into tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_clients(self):
        try:
            if not self.connected:
                self.connect()
            self.cursor.execute("SELECT * FROM tgclients")
            myresult = self.cursor.fetchall()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()
    def get_active_clients(self, limit=None):
        try:
            if not self.connected:
                self.connect()
            query = "SELECT * FROM tgclients WHERE active = 1"
            if limit is not None:
                query += " LIMIT %s"
                self.cursor.execute(query, (limit,))
            else:
                self.cursor.execute(query)
            myresult = self.cursor.fetchall()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()
    def get_client(self, user_id):
        try:
            myresult = None
            if not self.connected:
                self.connect()
            self.cursor.execute(f"SELECT * FROM tgclients WHERE user_id = {user_id}")
            myresult = self.cursor.fetchone()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def is_client_premium(self, user_id) -> bool:
        try:
            if not self.connected:
                self.connect()
            self.cursor.execute(f"SELECT * FROM tgclients WHERE user_id = {user_id} AND active = 1")
            myresult = self.cursor.fetchone()
            if myresult is not None:
                return True
            else:
                return False
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()
            return False

    def update_client(self, user_id, purchase_date=None, duration=None, expiration_date=None, active=None,
                      dmed=None, plan=None):
        try:
            if not self.connected:
                self.connect()
            sql = "UPDATE tgclients SET "
            vals = []
            if purchase_date is not None:
                sql += "purchase_date = %s, "
                vals.append(purchase_date)
            if duration is not None:
                sql += "duration = %s, "
                vals.append(duration)
            if expiration_date is not None:
                sql += "expiration_date = %s, "
                vals.append(expiration_date)
            if active is not None:
                sql += "active = %s, "
                vals.append(active)
            if dmed is not None:
                sql += "dmed = %s, "
                vals.append(dmed)
            if plan is not None:
                sql += "plan = %s, "
                vals.append(plan)
            sql = sql[:-2] + " WHERE user_id = %s"
            vals.append(user_id)
            val = tuple(vals)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record(s) affected.")
            select_sql = "SELECT * FROM tgclients WHERE user_id = %s"
            select_val = (user_id,)
            self.cursor.execute(select_sql, select_val)
            inserted_row = self.cursor.fetchone()
            return inserted_row
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to update record in tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_client_formatted_expiration_date(self, user_id):
        query = f"SELECT CONCAT(DATE_FORMAT(expiration_date, '%d %b \\'%y, %H:%i'),' (UTC) (', \
                 DATEDIFF(expiration_date, NOW()), ' months, ', \
                 MOD(DATEDIFF(expiration_date, NOW()), 30), ' days left)') AS formatted_expiration_date \
                 FROM tgclients WHERE user_id = {user_id}"
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            if result:
                return result
            else:
                return None
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to execute query: {}".format(error))
        return None

    def get_clients_formatted_expiration_date(self):
        query = f"SELECT CONCAT(DATE_FORMAT(expiration_date, '%d %b \\'%y, %H:%i'),' (UTC) (', \
                 DATEDIFF(expiration_date, NOW()), ' months, ', \
                 MOD(DATEDIFF(expiration_date, NOW()), 30), ' days left)') AS formatted_expiration_date \
                 FROM tgclients"
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            if result:
                return result
            else:
                return None
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to execute query: {}".format(error))
        return None

    def add_premium_client(self, user_id, duration, unit="days"):
        dom = duration * convert_date(unit)
        client = self.get_client(user_id)
        if client is not None:
            if client[3] > client[1]:
                client = self.update_client(user_id, expiration_date=(client[3] + timedelta(duration)).strftime(self.f),
                                            duration=client[2] + dom)
            else:
                client = self.update_client(user_id, purchase_date=datetime.now().strftime(self.f),
                                            expiration_date=(datetime.now() + timedelta(duration)).strftime(self.f),
                                            duration=client[2] + dom)
        else:
            client = self.create_client(user_id, duration)
        return client

    def add_plan_client(self, user_id, plan_id):
        plan = self.get_plan(plan_id)
        unit = plan[4]
        duration = plan[3]
        dom = duration * convert_date(unit)
        client = self.get_client(user_id)
        if client is not None:
            if client[3] > client[1]:
                client = self.update_client(user_id, expiration_date=(client[3] + timedelta(dom)).strftime(self.f),
                                            duration=client[2] + dom, plan=plan_id)
            else:
                client = self.update_client(user_id, purchase_date=datetime.now().strftime(self.f),
                                            expiration_date=(datetime.now() + timedelta(dom)).strftime(self.f),
                                            duration=client[2] + dom, plan=plan_id)
        else:
            client = self.create_client(user_id, dom, plan=plan_id)
        return client

    def delete_client(self, user_id):
        try:
            if not self.connected:
                self.connect()
            sql = "DELETE FROM tgclients WHERE user_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record(s) deleted.")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to delete record from tgclients table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def upsert_lang(self, user_id, language):
        try:
            if not self.connected:
                self.connect()
            sql = "INSERT INTO lang (user_id, language) VALUES (%s, %s) ON DUPLICATE KEY UPDATE language = VALUES(language)"
            val = (user_id, language)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record upserted.")
            return self.get_lang(user_id=user_id)
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to upsert record in lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def delete_lang(self, user_id):
        try:
            if not self.connected:
                self.connect()
            sql = "DELETE FROM lang WHERE user_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record(s) deleted.")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to delete record from lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_langs(self):
        try:
            if not self.connected:
                self.connect()
            self.cursor.execute("SELECT * FROM lang")
            myresult = self.cursor.fetchall()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve records from lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_lang(self, user_id):
        try:
            if not self.connected:
                self.connect()
            sql = "SELECT * FROM lang WHERE user_id = %s"
            val = (user_id,)
            self.cursor.execute(sql, val)
            myresult = self.cursor.fetchone()
            return myresult
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve record from lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def add_chat(self, chat_id):
        try:
            sql = "INSERT INTO chats (chat_id) VALUES (%s)"
            values = (chat_id,)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print(f"{self.cursor.rowcount} row(s) added")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve record from lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def delete_chat(self, chat_id):
        try:
            sql = "DELETE FROM chats WHERE chat_id = %s"
            values = (chat_id,)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print(f"{self.cursor.rowcount} row(s) deleted")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve record from lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_chats(self):
        try:
            sql = "SELECT chat_id FROM chats"
            self.cursor.execute(sql)
            a = self.cursor.fetchall()
            if a is not None:
                return [item[0] for item in a]
            else:
                return []
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve record from lang table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def get_user_plan_by_sid(self, sid):
        try:
            sql = f"SELECT plan FROM user_session WHERE sid = '{sid}'"
            self.cursor.execute(sql)
            a = self.cursor.fetchall()
            if a is not None and len(a) > 0:
                return a[0]
            else:
                return []
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to retrieve record from user_session table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def update_tg_user_id_by_user_code(self, sid, telegram_user_id):
        try:
            if not self.connected:
                self.connect()
            values = (telegram_user_id, sid,)

            # Delete all old rows
            self.cursor.execute("UPDATE user_session SET telegram_user_id = %s WHERE sid = %s", values)
            self.connection.commit()

            print(f"{self.cursor.rowcount} row(s) updated")
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to update record from user_session table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

    def create_discount_code(self, discount_code="", discount_percent=0.85) -> str:
        try:
            if not self.connected:
                self.connect()
            sql = "INSERT INTO discount_codes (code, percent) VALUES (%s, %s)"
            if discount_code == "":
                discount_code = generate_random_string(18)

            val = (discount_code,discount_percent,)

            self.cursor.execute(sql, val)
            self.connection.commit()
            print(self.cursor.rowcount, "record inserted.")

            return discount_code
        except Exception as error:
            print(traceback.format_exc())
            print("Failed to insert record into discount_codes table: {}".format(error))
            self.connected = False
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                print("MySQL connection is closed")
            self.connect()

def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

db = Myself(
    host=db_host,
    database=db_name,
    user=db_user,
    password=db_password
)