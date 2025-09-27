from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

from aiogram.types import InlineKeyboardButton
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    Calendar,
    CalendarConfig,
    CalendarScope,
    CalendarScopeView,
    CalendarUserConfig,
)
from aiogram_dialog.widgets.text import Format, Text

EPOCH = date(1970, 1, 1)

CALLBACK_NEXT_MONTH = "+"
CALLBACK_PREV_MONTH = "-"
CALLBACK_NEXT_YEAR = "+Y"
CALLBACK_PREV_YEAR = "-Y"
CALLBACK_NEXT_YEARS_PAGE = "+YY"
CALLBACK_PREV_YEARS_PAGE = "-YY"
CALLBACK_SCOPE_MONTHS = "M"
CALLBACK_SCOPE_YEARS = "Y"

CALLBACK_PREFIX_MONTH = "MONTH"
CALLBACK_PREFIX_YEAR = "YEAR"

ZOOM_OUT_TEXT = Format("🔍")

PREV_YEARS_PAGE_TEXT = Format("<< {date:%Y}")
NEXT_YEARS_PAGE_TEXT = Format("{date:%Y} >>")
THIS_YEAR_TEXT = Format("[ {date:%Y} ]")
YEAR_TEXT = Format("{date:%Y}")
PREV_YEAR_TEXT = Format("<< {date:%Y}")
NEXT_YEAR_TEXT = Format("{date:%Y} >>")
MONTHS_HEADER_TEXT = Format("🗓 {date:%Y}")
THIS_MONTH_TEXT = Format("[ {date:%B} ]")
MONTH_TEXT = Format("{date:%B}")
DATE_TEXT = Format("{date:%d}")
TODAY_TEXT = Format("[ {date:%d} ]")

WEEK_DAY_TEXT = Format("{date:%a}")

PREV_MONTH_TEXT = Format("<< {date:%B %Y}")
NEXT_MONTH_TEXT = Format("{date:%B %Y} >>")
DAYS_HEADER_TEXT = Format("🗓 {date:%B %Y}")

BEARING_DATE = date(2018, 1, 1)


def empty_button():
    return InlineKeyboardButton(text=" ", callback_data="")


def raw_from_date(d: date) -> int:
    diff = d - EPOCH
    return int(diff.total_seconds())


def date_from_raw(raw_date: int) -> date:
    return EPOCH + timedelta(seconds=raw_date)


def month_begin(offset: date):
    return offset.replace(day=1)


def next_month_begin(offset: date):
    return month_begin(month_begin(offset) + timedelta(days=31))


def prev_month_begin(offset: date):
    return month_begin(month_begin(offset) - timedelta(days=1))


def get_today(tz: timezone):
    return datetime.now(tz).date()


CallbackGenerator = Callable[[str], str]


class UkrainianCalendarDaysView(CalendarScopeView):
    def __init__(
        self,
        callback_generator: CallbackGenerator,
        date_text: Text = DATE_TEXT,
        today_text: Text = TODAY_TEXT,
        weekday_text: Text = None,
        header_text: Text = None,
        zoom_out_text: Text = ZOOM_OUT_TEXT,
        next_month_text: Text = None,
        prev_month_text: Text = None,
    ):
        self.zoom_out_text = zoom_out_text
        self.callback_generator = callback_generator
        self.date_text = date_text
        self.today_text = today_text
        self.weekday_text = weekday_text

        self.ukrainian_months = {
            1: "Січень",
            2: "Лютий",
            3: "Березень",
            4: "Квітень",
            5: "Травень",
            6: "Червень",
            7: "Липень",
            8: "Серпень",
            9: "Вересень",
            10: "Жовтень",
            11: "Листопад",
            12: "Грудень",
        }

        self.ukrainian_weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

    async def _render_date_button(
        self,
        selected_date: date,
        today: date,
        data: dict,
        manager: DialogManager,
    ) -> InlineKeyboardButton:
        current_data = {
            "date": selected_date,
            "data": data,
        }
        if selected_date == today:
            text = self.today_text
        else:
            text = self.date_text

        raw_date = raw_from_date(selected_date)

        return InlineKeyboardButton(
            text=await text.render_text(current_data, manager),
            callback_data=self.callback_generator(str(raw_date)),
        )

    async def _render_days(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        keyboard = []
        start_date = offset.replace(day=1)
        min_date = max(config.min_date, start_date)
        days_since_week_start = start_date.weekday() - config.firstweekday
        if days_since_week_start < 0:
            days_since_week_start += 7
        start_date -= timedelta(days=days_since_week_start)
        end_date = next_month_begin(offset) - timedelta(days=1)
        max_date = min(config.max_date, end_date)
        days_since_week_start = end_date.weekday() - config.firstweekday
        days_till_week_end = (6 - days_since_week_start) % 7
        end_date += timedelta(days=days_till_week_end)

        today = get_today(config.timezone)
        for offset in range(0, (end_date - start_date).days, 7):
            row = []
            for row_offset in range(7):
                days_offset = timedelta(days=(offset + row_offset))
                current_date = start_date + days_offset
                if min_date <= current_date <= max_date:
                    row.append(
                        await self._render_date_button(
                            current_date,
                            today,
                            data,
                            manager,
                        )
                    )
                else:
                    row.append(empty_button())
            keyboard.append(row)
        return keyboard

    async def _render_week_header(
        self,
        config: CalendarConfig,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        header = []
        for i in range(7):
            day_index = (config.firstweekday + i) % 7
            header.append(
                InlineKeyboardButton(
                    text=self.ukrainian_weekdays[day_index],
                    callback_data="",
                )
            )
        return header

    async def _render_header(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        month_name = self.ukrainian_months.get(offset.month, f"Місяць {offset.month}")
        header_text = f"🗓 {month_name} {offset.year}"

        return [
            InlineKeyboardButton(
                text=header_text,
                callback_data=self.callback_generator(CALLBACK_SCOPE_MONTHS),
            )
        ]

    async def _render_pager(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        prev_end = month_begin(offset) - timedelta(1)
        prev_begin = month_begin(prev_end)
        next_begin = next_month_begin(offset)

        if prev_end < config.min_date and next_begin > config.max_date:
            return []

        prev_month_name = self.ukrainian_months.get(
            prev_begin.month, f"Місяць {prev_begin.month}"
        )
        next_month_name = self.ukrainian_months.get(
            next_begin.month, f"Місяць {next_begin.month}"
        )

        if prev_end < config.min_date:
            prev_button = empty_button()
        else:
            prev_button = InlineKeyboardButton(
                text=f"<< {prev_month_name} {prev_begin.year}",
                callback_data=self.callback_generator(CALLBACK_PREV_MONTH),
            )

        zoom_button = InlineKeyboardButton(
            text="🔍",
            callback_data=self.callback_generator(CALLBACK_SCOPE_MONTHS),
        )

        if next_begin > config.max_date:
            next_button = empty_button()
        else:
            next_button = InlineKeyboardButton(
                text=f"{next_month_name} {next_begin.year} >>",
                callback_data=self.callback_generator(CALLBACK_NEXT_MONTH),
            )

        return [prev_button, zoom_button, next_button]

    async def render(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        return [
            await self._render_header(config, offset, data, manager),
            await self._render_week_header(config, data, manager),
            *await self._render_days(config, offset, data, manager),
            await self._render_pager(config, offset, data, manager),
        ]


class UkrainianCalendarMonthView(CalendarScopeView):
    def __init__(
        self,
        callback_generator: CallbackGenerator,
        month_text: Text = None,
        this_month_text: Text = None,
        header_text: Text = MONTHS_HEADER_TEXT,
        zoom_out_text: Text = ZOOM_OUT_TEXT,
        next_year_text: Text = NEXT_YEAR_TEXT,
        prev_year_text: Text = PREV_YEAR_TEXT,
    ):
        self.callback_generator = callback_generator
        self.month_text = month_text
        self.this_month_text = this_month_text
        self.header_text = header_text
        self.zoom_out_text = zoom_out_text
        self.next_year_text = next_year_text
        self.prev_year_text = prev_year_text

        self.ukrainian_months = {
            1: "Січень",
            2: "Лютий",
            3: "Березень",
            4: "Квітень",
            5: "Травень",
            6: "Червень",
            7: "Липень",
            8: "Серпень",
            9: "Вересень",
            10: "Жовтень",
            11: "Листопад",
            12: "Грудень",
        }

    async def _render_pager(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        curr_year = offset.year
        next_year = curr_year + 1
        prev_year = curr_year - 1

        if curr_year not in range(config.min_date.year, config.max_date.year + 1):
            return []

        if prev_year < config.min_date.year:
            prev_button = empty_button()
        else:
            prev_button = InlineKeyboardButton(
                text=f"<< {prev_year}",
                callback_data=self.callback_generator(CALLBACK_PREV_YEAR),
            )

        if next_year > config.max_date.year:
            next_button = empty_button()
        else:
            next_button = InlineKeyboardButton(
                text=f"{next_year} >>",
                callback_data=self.callback_generator(CALLBACK_NEXT_YEAR),
            )

        zoom_button = InlineKeyboardButton(
            text="🔍",
            callback_data=self.callback_generator(CALLBACK_SCOPE_YEARS),
        )

        return [prev_button, zoom_button, next_button]

    def _is_month_allowed(
        self, config: CalendarConfig, offset: date, month: int
    ) -> bool:
        start = date(offset.year, month, 1)
        end = next_month_begin(start) - timedelta(days=1)
        return end >= config.min_date and start <= config.max_date

    async def _render_month_button(
        self,
        month: int,
        this_month: int,
        data: dict,
        offset: date,
        config: CalendarConfig,
        manager: DialogManager,
    ) -> InlineKeyboardButton:
        if not self._is_month_allowed(config, offset, month):
            return empty_button()

        month_name = self.ukrainian_months.get(month, f"Місяць {month}")

        if month == this_month:
            button_text = f"[ {month_name} ]"
        else:
            button_text = month_name

        return InlineKeyboardButton(
            text=button_text,
            callback_data=self.callback_generator(f"{CALLBACK_PREFIX_MONTH}{month}"),
        )

    async def _render_months(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        keyboard = []
        today = get_today(config.timezone)
        this_month = today.month if offset.year == today.year else -1

        for row in range(0, 12, config.month_columns):
            keyboard_row = []
            for column in range(config.month_columns):
                month = row + column + 1
                if month <= 12:
                    keyboard_row.append(
                        await self._render_month_button(
                            month,
                            this_month,
                            data,
                            offset,
                            config,
                            manager,
                        )
                    )
            if keyboard_row:
                keyboard.append(keyboard_row)
        return keyboard

    async def _render_header(
        self, config, offset, data, manager
    ) -> list[InlineKeyboardButton]:
        return [
            InlineKeyboardButton(
                text=f"🗓 {offset.year}",
                callback_data=self.callback_generator(CALLBACK_SCOPE_YEARS),
            )
        ]

    async def render(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        return [
            await self._render_header(config, offset, data, manager),
            *await self._render_months(config, offset, data, manager),
            await self._render_pager(config, offset, data, manager),
        ]


class UkrainianCalendarYearsView(CalendarScopeView):
    def __init__(
        self,
        callback_generator: CallbackGenerator,
        year_text: Text = None,
        this_year_text: Text = None,
        next_page_text: Text = None,
        prev_page_text: Text = None,
    ):
        self.callback_generator = callback_generator

    async def _render_pager(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        curr_year = offset.year
        next_year = curr_year + config.years_per_page
        prev_year = curr_year - config.years_per_page

        if curr_year <= config.min_date.year:
            prev_button = empty_button()
        else:
            prev_button = InlineKeyboardButton(
                text=f"<< {prev_year}",
                callback_data=self.callback_generator(CALLBACK_PREV_YEARS_PAGE),
            )

        if next_year > config.max_date.year:
            next_button = empty_button()
        else:
            next_button = InlineKeyboardButton(
                text=f"{next_year} >>",
                callback_data=self.callback_generator(CALLBACK_NEXT_YEARS_PAGE),
            )

        if prev_button == next_button == empty_button():
            return []
        return [prev_button, next_button]

    def _is_year_allowed(self, config: CalendarConfig, year: int) -> bool:
        return config.min_date.year <= year <= config.max_date.year

    async def _render_year_button(
        self,
        year: int,
        this_year: int,
        data: dict,
        config: CalendarConfig,
        manager: DialogManager,
    ) -> InlineKeyboardButton:
        if not self._is_year_allowed(config, year):
            return empty_button()

        if year == this_year:
            button_text = f"[ {year} ]"
        else:
            button_text = str(year)

        return InlineKeyboardButton(
            text=button_text,
            callback_data=self.callback_generator(f"{CALLBACK_PREFIX_YEAR}{year}"),
        )

    async def _render_years(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        keyboard = []
        this_year = get_today(config.timezone).year
        years_columns = config.years_columns
        years_per_page = config.years_per_page

        for row in range(0, years_per_page, years_columns):
            keyboard_row = []
            for column in range(years_columns):
                curr_year = offset.year + row + column
                keyboard_row.append(
                    await self._render_year_button(
                        curr_year,
                        this_year,
                        data,
                        config,
                        manager,
                    )
                )
            keyboard.append(keyboard_row)
        return keyboard

    async def render(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        return [
            *await self._render_years(config, offset, data, manager),
            await self._render_pager(config, offset, data, manager),
        ]


class UkrainianCalendar(Calendar):
    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        return {
            CalendarScope.DAYS: UkrainianCalendarDaysView(self._item_callback_data),
            CalendarScope.MONTHS: UkrainianCalendarMonthView(self._item_callback_data),
            CalendarScope.YEARS: UkrainianCalendarYearsView(self._item_callback_data),
        }

    async def _get_user_config(
        self,
        data: dict,
        manager: DialogManager,
    ) -> CalendarUserConfig:
        return CalendarUserConfig(firstweekday=0)
