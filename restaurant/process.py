import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from entities.entities import Order

def start():
    global session
    try:
        # Connecting to DB
        load_dotenv()
        engine = create_engine(os.getenv('path_to_database'))
        Session = sessionmaker(bind=engine)
        session = Session()
        # Start
        while True:
            # Getting "in progress" orders
            orders = session.query(Order).filter(Order.status == 'working').all()
            for order in orders:
                # Opening new session
                session_work = Session()
                order_work = session_work.query(Order).get(order.id)
                order_work.status = 'working'
                try:
                    session_work.commit()
                except SQLAlchemyError as error:
                    session_work.rollback()
                    raise error
                finally:
                    session_work.close()
                time.sleep(3)  # Delay
                # Opening new session
                session_complete = Session()
                order_complete = session_complete.query(Order).get(order.id)
                order_complete.status = 'done'
                try:
                    session_complete.commit()
                except SQLAlchemyError as error:
                    print("critical error")
                    session_complete.rollback()
                    raise error
                finally:
                    session_complete.close()
    except SQLAlchemyError as error:
        print("DB work exception:", error)
        if session:
            session.rollback()
    finally:
        if session:
            session.close()


start()
