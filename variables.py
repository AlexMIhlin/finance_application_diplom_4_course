DEFAULT_CURRENCY_RATES = {"RUB": 1, "USD": 92, "EUR": 100}

CURRENCY_SIGN = {"RUB": "₽", "USD": "$", "EUR": "€"}

LANG = {
    "ru": dict(
        tab_home="Главная", tab_analytics="Аналитика",
        tab_tools="Инструменты", tab_settings="Настройки",

        balance="Текущий баланс:", income="Доходы:", expense="Траты:",

        gb_new="Новая транзакция", gb_conv="Конвертер валют",
        gb_credit="Калькулятор кредита", gb_deposit="Калькулятор вклада",

        btn_add="Добавить", btn_del="Удалить",
        btn_add_cat="Новая категория",
        btn_convert="Конвертировать", btn_credit="Рассчитать платёж",
        btn_deposit="Рассчитать итог", btn_save="Сохранить",

        f_type="Тип:", f_date="Дата:", f_sum="Сумма:",
        f_cat="Категория:", f_note="Описание:",

        f_amount="Сумма:", f_from="Из:", f_to="В:",

        loan_sum="Сумма кредита:", loan_rate="Ставка (% год):",
        loan_term="Срок:",

        dep_init="Начальная сумма:", dep_rate="Ставка (% год):",
        dep_term="Срок:", dep_month="Ежемесячный взнос:",
        lbl_cap="Капитализация:",

        col_date="Дата", col_sum="Сумма",
        col_cat="Категория", col_note="Описание",

        periods=["Последние 7 дней", "Месяц", "Год", "Весь период"],

        g_pie="Расходы по категориям",
        g_bar="Доход / Расход по месяцам",
        g_line="Баланс со временем",
        g_donut="Доходы / Расходы",

        set_lang="Язык:", set_theme="Тема:",
        set_cur="Валюта по умолчанию:",

        note_title="Описание",
        msg_del="Удалить запись?",

        dlg_cat_title="Новая категория",
        dlg_cat_name="Название:",
        dlg_cat_type="Тип:",
        type_expense="Расход",
        type_income="Доход",
        btn_ok="ОК",
        btn_cancel="Отмена",

        btn_export="Экспорт в Excel",
    ),

    "en": dict(
        tab_home="Home", tab_analytics="Analytics",
        tab_tools="Tools", tab_settings="Settings",

        balance="Balance:", income="Income:", expense="Expense:",

        gb_new="New transaction", gb_conv="Currency converter",
        gb_credit="Loan calculator", gb_deposit="Deposit calculator",

        btn_add="Add", btn_del="Delete",
        btn_add_cat="New category",
        btn_convert="Convert", btn_credit="Calculate payment",
        btn_deposit="Calculate result", btn_save="Save",

        f_type="Type:", f_date="Date:", f_sum="Amount:",
        f_cat="Category:", f_note="Description:",

        f_amount="Amount:", f_from="From:", f_to="To:",

        loan_sum="Loan amount:", loan_rate="Rate (%/yr):",
        loan_term="Term:",

        dep_init="Initial amount:", dep_rate="Rate (%/yr):",
        dep_term="Term:", dep_month="Monthly add:",
        lbl_cap="Capitalization:",

        col_date="Date", col_sum="Amount",
        col_cat="Category", col_note="Note",

        periods=["Last 7 days", "Month", "Year", "All time"],

        g_pie="Expenses by category",
        g_bar="Income / Expense by month",
        g_line="Balance over time",
        g_donut="Income / Expense",

        set_lang="Language:", set_theme="Theme:",
        set_cur="Default currency:",

        note_title="Note",
        msg_del="Delete record?",

        dlg_cat_title="New category",
        dlg_cat_name="Name:",
        dlg_cat_type="Type:",
        type_expense="Expense",
        type_income="Income",
        btn_ok="OK",
        btn_cancel="Cancel",

        btn_export="Export to Excel",
    ),
}
