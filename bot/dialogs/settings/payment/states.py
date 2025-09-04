from aiogram.fsm.state import StatesGroup, State

class PaymentMenu(StatesGroup):
    main = State()
    choose_period = State()
    choose_method = State()
    monobank_payment = State()
    cryptobot_payment = State()
    success = State()
