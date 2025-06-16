from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure

from PySide6.QtCore import QSize, QCoreApplication, QDate
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(960, 800)
        MainWindow.setMinimumSize(QSize(480, 320))

        self.centralwidget = QWidget(MainWindow)
        self.gridLayout = QGridLayout(self.centralwidget)

        self.tabs = QTabWidget(self.centralwidget)

        self._init_home_tab()
        self._init_analytics_tab()
        self._init_tools_tab()
        self._init_settings_tab()

        self.gridLayout.addWidget(self.tabs, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)

    def _init_home_tab(self):
        self.tab_home = QWidget()
        layout = QHBoxLayout(self.tab_home)

        v_left = QVBoxLayout()
        self.table = QTableWidget(columnCount=4); self.table.setObjectName("table")
        for i, h in enumerate(("Дата", "Сумма", "Категория", "Описание")):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(h))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v_left.addWidget(self.table)

        h_bal = QHBoxLayout()
        self.lblBalanceTitle = QLabel("Текущий баланс:"); self.lblBalanceTitle.setObjectName("lblBalanceTitle")
        self.lblBalance = QLabel("0"); self.lblBalance.setObjectName("lblBalance")
        self.lblExpenseTitle = QLabel("Траты:"); self.lblExpenseTitle.setObjectName("lblExpenseTitle")
        self.lblExpense = QLabel("0"); self.lblExpense.setObjectName("lblExpense")
        self.lblIncomeTitle = QLabel("Доходы:"); self.lblIncomeTitle.setObjectName("lblIncomeTitle")
        self.lblIncome = QLabel("0"); self.lblIncome.setObjectName("lblIncome")
        for w in (self.lblBalanceTitle, self.lblBalance,
                  self.lblExpenseTitle, self.lblExpense,
                  self.lblIncomeTitle, self.lblIncome):
            h_bal.addWidget(w)
            if w in (self.lblBalance, self.lblExpense):
                h_bal.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        v_left.addLayout(h_bal)
        layout.addLayout(v_left)

        v_right = QVBoxLayout()
        self.grpNew = QGroupBox("Новая транзакция"); self.grpNew.setObjectName("grpNew")
        form = QFormLayout(self.grpNew); self.formNew = form

        self.cmbType = QComboBox(); self.cmbType.setObjectName("cmbType")
        self.cmbType.addItems(["Расход", "Доход"]); form.addRow("Тип:", self.cmbType)

        self.dateEdit = QDateEdit(); self.dateEdit.setObjectName("dateEdit")
        self.dateEdit.setDate(QDate.currentDate()); form.addRow("Дата:", self.dateEdit)

        self.spinAmount = QDoubleSpinBox(minimum=-1e8, maximum=1e9); self.spinAmount.setObjectName("spinAmount")
        form.addRow("Сумма:", self.spinAmount)

        h_cat = QHBoxLayout()
        self.cmbCategory = QComboBox(); self.cmbCategory.setObjectName("cmbCategory")
        self.btnAddCat = QPushButton("+"); self.btnAddCat.setObjectName("btnAddCat")
        self.btnAddCat.setFixedWidth(28)
        h_cat.addWidget(self.cmbCategory, 1); h_cat.addWidget(self.btnAddCat)
        self.lblCat = QLabel("Категория:"); self.lblCat.setObjectName("lblCat")
        form.addRow(self.lblCat, h_cat)

        self.lineNote = QLineEdit(); self.lineNote.setObjectName("lineNote")
        form.addRow("Описание:", self.lineNote)

        v_right.addWidget(self.grpNew)

        self.btnAdd = QPushButton("Добавить");
        self.btnAdd.setObjectName("btnAdd")
        self.btnDelete = QPushButton("Удалить");
        self.btnDelete.setObjectName("btnDelete")

        self.btnExport = QPushButton("Экспорт в Excel");
        self.btnExport.setObjectName("btnExport")

        v_right.addWidget(self.btnAdd)
        v_right.addWidget(self.btnDelete)
        v_right.addWidget(self.btnExport)

        v_right.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(v_right)
        self.tabs.addTab(self.tab_home, "Главная")

    def _init_analytics_tab(self):
        self.tab_analytics = QWidget()
        v = QVBoxLayout(self.tab_analytics)
        self.period_box = QComboBox(); self.period_box.setObjectName("period_box")
        self.period_box.addItems(["Последние 7 дней", "Месяц", "Год", "Весь период"])
        v.addWidget(self.period_box)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); scroll.setWidget(content)
        grid = QGridLayout(content)

        self.canvas_pie, self.canvas_bar = Canvas(Figure()), Canvas(Figure())
        self.canvas_line, self.canvas_donut = Canvas(Figure()), Canvas(Figure())
        for c in (self.canvas_pie, self.canvas_bar, self.canvas_line, self.canvas_donut):
            c.figure.subplots()

        titles = [
            ("grpPie", "Расходы по категориям (Pie)", self.canvas_pie),
            ("grpBar", "Доход / Расход по месяцам (Bar)", self.canvas_bar),
            ("grpLine", "Баланс со временем (Line)", self.canvas_line),
            ("grpDonut", "Доходы / Расходы (Donut)", self.canvas_donut),
        ]
        for idx, (name, title, canvas) in enumerate(titles):
            grp = QGroupBox(title); grp.setObjectName(name)
            setattr(self, name, grp)
            QVBoxLayout(grp).addWidget(canvas)
            grid.addWidget(grp, idx // 2, idx % 2)

        v.addWidget(scroll)
        self.tabs.addTab(self.tab_analytics, "Аналитика")

    def _init_tools_tab(self):
        self.tab_tools = QWidget()
        v = QVBoxLayout(self.tab_tools)

        self.grpConv = QGroupBox("Конвертер валют"); self.grpConv.setObjectName("grpConv")
        fC = QFormLayout(self.grpConv); self.formConv = fC
        self.spinConvAmount = QDoubleSpinBox(maximum=1e9); self.spinConvAmount.setObjectName("spinConvAmount")
        self.cmbCurFrom = QComboBox(); self.cmbCurFrom.setObjectName("cmbCurFrom")
        self.cmbCurTo = QComboBox(); self.cmbCurTo.setObjectName("cmbCurTo")
        self.cmbCurFrom.addItems(["RUB", "USD", "EUR"]); self.cmbCurTo.addItems(["RUB", "USD", "EUR"])
        self.btnConvert = QPushButton("Конвертировать"); self.btnConvert.setObjectName("btnConvert")
        self.lblConvResult = QLabel("—"); self.lblConvResult.setObjectName("lblConvResult")
        fC.addRow("Сумма:", self.spinConvAmount); fC.addRow("Из:", self.cmbCurFrom)
        fC.addRow("В:", self.cmbCurTo); fC.addRow(self.btnConvert, self.lblConvResult)
        v.addWidget(self.grpConv)

        self.grpCredit = QGroupBox("Калькулятор кредита"); self.grpCredit.setObjectName("grpCredit")
        fCr = QFormLayout(self.grpCredit); self.formCredit = fCr
        self.spinCreditSum = QDoubleSpinBox(maximum=1e9); self.spinCreditSum.setObjectName("spinCreditSum")
        self.spinCreditRate = QDoubleSpinBox(suffix=" %", maximum=100, decimals=2); self.spinCreditRate.setObjectName("spinCreditRate")
        self.spinCreditTerm = QSpinBox(suffix=" мес", maximum=480); self.spinCreditTerm.setObjectName("spinCreditTerm")
        self.btnCreditCalc = QPushButton("Рассчитать платёж"); self.btnCreditCalc.setObjectName("btnCreditCalc")
        self.lblCreditResult = QLabel("—"); self.lblCreditResult.setObjectName("lblCreditResult")
        fCr.addRow("Сумма кредита:", self.spinCreditSum)
        fCr.addRow("Ставка (% год):", self.spinCreditRate)
        fCr.addRow("Срок:", self.spinCreditTerm)
        fCr.addRow(self.btnCreditCalc, self.lblCreditResult)
        v.addWidget(self.grpCredit)

        self.grpDeposit = QGroupBox("Калькулятор вклада"); self.grpDeposit.setObjectName("grpDeposit")
        fD = QFormLayout(self.grpDeposit); self.formDeposit = fD
        self.spinDepInit = QDoubleSpinBox(maximum=1e9); self.spinDepInit.setObjectName("spinDepInit")
        self.spinDepRate = QDoubleSpinBox(suffix=" %", maximum=100, decimals=2); self.spinDepRate.setObjectName("spinDepRate")
        self.spinDepTerm = QSpinBox(suffix=" мес", maximum=480); self.spinDepTerm.setObjectName("spinDepTerm")
        self.spinDepMonthly = QDoubleSpinBox(prefix="+ ", maximum=1e9); self.spinDepMonthly.setObjectName("spinDepMonthly")
        self.chkDepCap = QCheckBox(""); self.chkDepCap.setObjectName("chkDepCap"); self.chkDepCap.setChecked(True)
        self.btnDepCalc = QPushButton("Рассчитать итог"); self.btnDepCalc.setObjectName("btnDepCalc")
        self.lblDepResult = QLabel("—"); self.lblDepResult.setObjectName("lblDepResult")
        fD.addRow("Начальная сумма:", self.spinDepInit)
        fD.addRow("Ставка (% год):", self.spinDepRate)
        fD.addRow("Срок:", self.spinDepTerm)
        fD.addRow("Ежемесячный взнос:", self.spinDepMonthly)
        fD.addRow("Капитализация:", self.chkDepCap)
        fD.addRow(self.btnDepCalc, self.lblDepResult)
        v.addWidget(self.grpDeposit)

        v.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.tabs.addTab(self.tab_tools, "Инструменты")

    def _init_settings_tab(self):
        self.tab_settings = QWidget()
        v = QVBoxLayout(self.tab_settings)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); scroll.setWidget(content)
        form = QFormLayout(content); self.formSettings = form

        self.cmbLang = QComboBox(); self.cmbLang.addItems(["Русский", "English"])
        self.cmbTheme = QComboBox(); self.cmbTheme.addItems(["Светлая", "Тёмная"])
        self.cmbDefCur = QComboBox(); self.cmbDefCur.addItems(["RUB", "USD", "EUR"])
        self.btnSaveSettings = QPushButton("Сохранить"); self.btnSaveSettings.setObjectName("btnSaveSettings")
        form.addRow("Язык:", self.cmbLang)
        form.addRow("Тема:", self.cmbTheme)
        form.addRow("Валюта по умолчанию:", self.cmbDefCur)
        form.addRow("", self.btnSaveSettings)

        v.addWidget(scroll)
        self.tabs.addTab(self.tab_settings, "Настройки")

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Управление финансами"))
