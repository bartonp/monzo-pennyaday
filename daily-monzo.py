# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import database
import pymonzo
import sys
import preferences
import os
from sqlalchemy import func

MINIMUM_BALANCE = 500
STEAL_FROM_COIN_JAR = True

client = pymonzo.MonzoAPI()
session = database.OpenSession()

accounts = [a for a in client.accounts() if a.closed is False]
account_id = accounts[0].id

balance = accounts[0].balance().balance
pots = client.pots()

coin_jar = [p for p in pots if p.name == 'Coin Jar'][0]
test_balance = balance - MINIMUM_BALANCE
current_year = datetime.datetime.now().year

amount = session.query(database.Saving).filter(database.Saving.year == current_year)\
    .filter(database.Saving.paid == False)\
    .order_by(database.Saving.amount.asc()).limit(1).one()

test_balance = balance - MINIMUM_BALANCE - amount.amount

if STEAL_FROM_COIN_JAR and test_balance < 0:
    if coin_jar.balance >= abs(test_balance):
        coin_jar.withdraw(account_id=account_id, amount=abs(test_balance))
        balance = accounts[0].balance().balance
        test_balance = balance - MINIMUM_BALANCE - amount.amount

today = datetime.datetime.utcnow().strftime('%Y-%m-%d')

if test_balance < 0:

    d = preferences.get_config_dir('bartonp', 'saving')
    last_sent_file = os.path.join(d, 'last_sent')
    last_sent = None
    if os.path.isfile(last_sent_file):
        with open(last_sent_file, 'r') as f:
            last_sent = f.read()

    if today != last_sent:
        required_amount = MINIMUM_BALANCE + amount.amount
        client.feeditem(account_id=account_id, params={'title': 'Minimum not met for Penny a Day Challenge',
                                                       'image_url': 'http://i.imgur.com/6RTnUwK.gif',
                                                       'body': 'You need at least £{:.02f} to run penny a day'.format(required_amount / 100.0)})
        with open(last_sent_file, 'w') as f:
            f.write(today)

    sys.exit(1)

last_sent_db = session.query(database.Saving.modified).filter(func.strftime('%Y-%m-%d', database.Saving.modified) == today).first()

if last_sent_db.modified.strftime('%Y-%m-%d') != today:
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
