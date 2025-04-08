from aiogram_dialog import Window, Dialog
from aiogram.fsm.state import StatesGroup, State

class FlowSettingsMenu(StatesGroup):
    flow_settings = State()
    generation_frequency = State()
    character_limit = State()
    ad_block_settings = State()
    posts_in_flow = State()

    source_settings = State()
    add_source = State()
    add_source_type = State()             
    add_source_link = State()        
    select_source_to_edit = State()
    edit_source = State()          
    select_source_to_delete = State()