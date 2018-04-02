from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy import event
from datetime import datetime, timedelta
import preferences
import os
from config import get_config


config = get_config()
p = preferences.get_config_dir(config.get(section='saving', option='company'),
                               config.get(section='saving', option='app'))
sqlite_path = os.path.join(p, 'penny_a_day_monzo.sqlite')
engine = create_engine('sqlite:///{}'.format(sqlite_path))

__OpenSession = scoped_session(sessionmaker(bind=engine))
def OpenSession():
    session = __OpenSession()
    session.commit()
    return session

Base = declarative_base(bind=engine)

def updateModifiedTime(mapper, connection, target):
    target.modified = datetime.utcnow()

def updateCreatedTime(mapper, connection, target):
    target.created = datetime.utcnow()


class Saving(Base):
    __tablename__ = "saving"
    __table_args__ = {'sqlite_autoincrement': True}

    pk_id = Column(INTEGER, primary_key=True)
    created = Column(DATETIME, default=datetime.utcnow())
    modified = Column(DATETIME, default=datetime.utcnow())

    amount = Column(INTEGER, nullable=False)
    year = Column(INTEGER, nullable=False)
    paid = Column(BOOLEAN, default=False, nullable=False)

event.listen(Saving, 'before_update', updateModifiedTime, propagate=True)
event.listen(Saving, 'before_insert', updateCreatedTime, propagate=False)

Base.metadata.create_all()

def initialise_db():

    year = datetime.now().year

    init_session = OpenSession()

    if init_session.query(Saving).filter(Saving.year == year).first() is None:
        start = datetime.strptime('{}-01-01'.format(year), '%Y-%m-%d')
        end = start + timedelta(days=364)

        if end.strftime('%m-%d') == '12-31':
            days = 365
        else:
            days = 366

        for penny in xrange(1, days+1):
            if init_session.query(Saving).filter(Saving.amount == penny).filter(Saving.year == year).first() is None:
                t = Saving()
                t.amount = penny
                t.year = year
                init_session.add(t)

        init_session.flush()
        init_session.commit()

initialise_db()
