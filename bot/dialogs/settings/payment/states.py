from aiogram.fsm.state import State, StatesGroup


class PaymentMenu(StatesGroup):
    main = State()
    choose_period = State()
    choose_method = State()
    monobank_payment = State()
    cryptobot_payment = State()
    success = State()
