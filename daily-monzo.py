# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import database
import pymonzo
import sys
import preferences
import os
from sqlalchemy import func
from config import get_config

session = database.OpenSession()
today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
last_sent_db = session.query(database.Saving.modified).filter(func.strftime('%Y-%m-%d', database.Saving.modified) == today).first()

if last_sent_db.modified.strftime('%Y-%m-%d') == today:
    session.close()
    sys.exit(0)

conf = get_config()

# Settings from config file
MINIMUM_BALANCE = conf.getint(section='settings', option='minimum_amount')
STEAL_FROM_COIN_JAR = conf.getboolean(section='settings', option='steal_from_coin_jar')

client = pymonzo.MonzoAPI()

accounts = [a for a in client.accounts() if a.closed is False]
account_id = accounts[0].id
balance = client.balance(account_id=accounts[0].id).balance

pots = client.pots()
coin_jar = [p for p in pots if p.name == 'Coin Jar'][0]

current_year = datetime.datetime.now().year
amount = session.query(database.Saving).filter(database.Saving.year == current_year)\
    .filter(database.Saving.paid == False)\
    .order_by(database.Saving.amount.asc()).limit(1).one()

test_balance = balance - MINIMUM_BALANCE - amount.amount

if STEAL_FROM_COIN_JAR and test_balance < 0:
    if coin_jar.balance >= abs(test_balance):
        coin_jar.withdraw(account_id=account_id, amount=abs(test_balance))
        balance = client.balance(account_id=accounts[0].id).balance
        test_balance = balance - MINIMUM_BALANCE - amount.amount


if test_balance < 0:
    d = preferences.get_config_dir(conf.get(section='saving', option='company'),
                                   conf.get(section='saving', option='app'))
    last_sent_file = os.path.join(d, 'last_sent')
    last_sent = None
    if os.path.isfile(last_sent_file):
        with open(last_sent_file, 'r') as f:
            last_sent = f.read()

    if today != last_sent:
        required_amount = MINIMUM_BALANCE + amount.amount
        params = {'title': conf.get(section='notification', option='title'),
                  'image_url': conf.get(section='notification', option='image_url'),
                  'body': conf.get(section='notification', option='body').format(pence=required_amount / 100.0)}
        client.feeditem(account_id=account_id, params=params)
        with open(last_sent_file, 'w') as f:
            f.write(today)

    session.close()
    sys.exit(1)

pots_name = 'Penny A Day Challenge'
penny_pot = None
for pot in pots:
    if pot.name == pots_name:
        penny_pot = pot
        break

if penny_pot is not None:
    amount.paid = True
    penny_pot.deposit(account_id=account_id, amount=amount.amount)
    print 'Transferred £{:.02f}'.format(amount.amount / 100.0)
    session.flush()
    session.commit()

session.close()
