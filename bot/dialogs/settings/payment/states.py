from aiogram.fsm.state import State, StatesGroup

class PaymentMenu(StatesGroup):
    main = State()
    choose_package = State()
    choose_period = State()
    choose_method = State()
    card_payment = State() 
    crypto_payment = State()
    promo_code = State() 
    success = State()