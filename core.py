from __future__ import annotations

import sys
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from ui import Ui_MainWindow
from dataBase import DataBase
from dataLoad import SettingsManager, export_to_excel
from exchange import RateProvider
from variables import CURRENCY_SIGN, LANG

logger = logging.getLogger(__name__)


class CategoryDialog(QDialog):
    def __init__(self, L: dict[str, str], income: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(L["dlg_cat_title"])

        v = QVBoxLayout(self)

        v.addWidget(QLabel(L["dlg_cat_name"]))
        self.edName = QLineEdit(self)
        v.addWidget(self.edName)

        v.addWidget(QLabel(L["dlg_cat_type"]))
        self.cmbType = QComboBox(self)
        self.cmbType.addItems([L["type_expense"], L["type_income"]])
        self.cmbType.setCurrentIndex(1 if income else 0)
        v.addWidget(self.cmbType)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        bb.button(QDialogButtonBox.Ok).setText(L.get("btn_ok", "OK"))
        bb.button(QDialogButtonBox.Cancel).setText(L.get("btn_cancel", "Cancel"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

class FinanceCore:
    def __init__(self, db: DataBase) -> None:
        self.db = db
        self.settings = SettingsManager()
        self.fx = RateProvider()

        self.user_id = self.db.ensure_default_user()
        self.account_id = self.db.ensure_default_account(self.user_id)
        self._ensure_categories()

    def add(self, date: QDate, amount_rub: float, cat: int, income: bool, note: str = ""):
        self.db.add_operation(
            self.account_id,
            1 if income else 0,
            abs(amount_rub),
            cat,
            datetime.combine(date.toPython(), datetime.min.time()),
            note,
        )

    def delete(self, op_id: int) -> None:
        self.db.delete_operation(op_id)

    def ops(self):
        return self.db.list_operations(self.account_id)

    def balance(self) -> float:
        return self.db.get_account_balance(self.account_id) / 100

    def totals(self) -> tuple[float, float]:
        inc = exp = 0
        for o in self.ops():
            v = o["amount"] / 100
            inc += v if o["type"] else 0
            exp += v if not o["type"] else 0
        return inc, exp

    def _ensure_categories(self):
        if self.db.get_categories(self.user_id):
            return
        for n in ("Еда", "Транспорт", "Развлечения"):
            self.db.add_category(self.user_id, n, 0)
        for n in ("Зарплата", "Подарок"):
            self.db.add_category(self.user_id, n, 1)

    def cats(self, income: bool):
        cat_type = 1 if income else 0
        return [
            (c["id"], c["name"]) for c in self.db.get_categories(self.user_id, cat_type)
        ]

    def stats(self, days: int | None):
        ops = sorted(self.ops(), key=lambda o: o["date"])
        if days is not None:
            border = datetime.now() - timedelta(days=days)
            ops = [o for o in ops if datetime.fromisoformat(o["date"]) >= border]

        pie, inc, exp = defaultdict(float), defaultdict(float), defaultdict(float)
        bal = 0
        line: list[tuple[datetime, float]] = []

        for o in ops:
            sign = 1 if o["type"] else -1
            v = sign * o["amount"] / 100
            dt = datetime.fromisoformat(o["date"])

            bal += v
            line.append((dt, bal))

            m = dt.strftime("%Y-%m")
            (inc if o["type"] else exp)[m] += abs(v)

            if not o["type"]:
                pie[o["category_name"] or "—"] += abs(v)

        return pie, inc, exp, line

    def cv(self, amount: float, frm: str, to: str) -> float:
        return amount * self.fx[frm] / self.fx[to]

    def credit(self, p, r, n):
        return (
            0
            if n == 0
            else (
                p
                * ((r / 12 / 100) * (1 + r / 12 / 100) ** n)
                / (((1 + r / 12 / 100) ** n) - 1)
                if r
                else p / n
            )
        )

    def deposit(self, i, r, n, m, cap=True):
        if n == 0:
            return i
        if cap:
            s = i
            r = r / 12 / 100
            for _ in range(n):
                s = (s + m) * (1 + r)
            return round(s, 2)
        return round(i + i * r / 100 * (n / 12) + m * n, 2)

class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.core = FinanceCore(DataBase())
        self.conf = self.core.settings.all()
        self.k = self.core.fx[self.conf["currency"]]

        self._apply_lang()
        self._apply_theme()
        self._sync_settings_ui()

        self._type_changed()
        self._fill_table()
        self._ind()
        self._sig()

    def _money(self, r: float) -> str:
        return f"{r / self.k:,.2f} {CURRENCY_SIGN[self.conf['currency']]}"

    def _sync_settings_ui(self):
        self.ui.cmbLang.setCurrentIndex(0 if self.conf["lang"] == "ru" else 1)
        self.ui.cmbTheme.setCurrentIndex(0 if self.conf["theme"] == "light" else 1)
        self.ui.cmbDefCur.setCurrentText(self.conf["currency"])

    def _apply_lang(self):
        L = LANG[self.conf["lang"]]

        self.ui.tabs.setTabText(0, L["tab_home"])
        self.ui.tabs.setTabText(1, L["tab_analytics"])
        self.ui.tabs.setTabText(2, L["tab_tools"])
        self.ui.tabs.setTabText(3, L["tab_settings"])

        self.ui.lblBalanceTitle.setText(L["balance"])
        self.ui.lblIncomeTitle.setText(L["income"])
        self.ui.lblExpenseTitle.setText(L["expense"])

        self.ui.grpNew.setTitle(L["gb_new"])
        self.ui.grpConv.setTitle(L["gb_conv"])
        self.ui.grpCredit.setTitle(L["gb_credit"])
        self.ui.grpDeposit.setTitle(L["gb_deposit"])

        self.ui.btnAdd.setText(L["btn_add"])
        self.ui.btnDelete.setText(L["btn_del"])
        self.ui.btnAddCat.setText(L["btn_add_cat"])
        self.ui.btnExport.setText(L["btn_export"])
        self.ui.btnConvert.setText(L["btn_convert"])
        self.ui.btnCreditCalc.setText(L["btn_credit"])
        self.ui.btnDepCalc.setText(L["btn_deposit"])
        self.ui.btnSaveSettings.setText(L["btn_save"])

        self.ui.formNew.labelForField(self.ui.cmbType).setText(L["f_type"])
        self.ui.formNew.labelForField(self.ui.dateEdit).setText(L["f_date"])
        self.ui.formNew.labelForField(self.ui.spinAmount).setText(L["f_sum"])
        self.ui.lblCat.setText(L["f_cat"])
        self.ui.formNew.labelForField(self.ui.lineNote).setText(L["f_note"])

        self.ui.formConv.labelForField(self.ui.spinConvAmount).setText(L["f_amount"])
        self.ui.formConv.labelForField(self.ui.cmbCurFrom).setText(L["f_from"])
        self.ui.formConv.labelForField(self.ui.cmbCurTo).setText(L["f_to"])

        self.ui.formCredit.labelForField(self.ui.spinCreditSum).setText(L["loan_sum"])
        self.ui.formCredit.labelForField(self.ui.spinCreditRate).setText(L["loan_rate"])
        self.ui.formCredit.labelForField(self.ui.spinCreditTerm).setText(L["loan_term"])

        self.ui.formDeposit.labelForField(self.ui.spinDepInit).setText(L["dep_init"])
        self.ui.formDeposit.labelForField(self.ui.spinDepRate).setText(L["dep_rate"])
        self.ui.formDeposit.labelForField(self.ui.spinDepTerm).setText(L["dep_term"])
        self.ui.formDeposit.labelForField(self.ui.spinDepMonthly).setText(L["dep_month"])
        self.ui.formDeposit.labelForField(self.ui.chkDepCap).setText(L["lbl_cap"])

        for i, h in enumerate((L["col_date"], L["col_sum"], L["col_cat"], L["col_note"])):
            self.ui.table.horizontalHeaderItem(i).setText(h)

        self.ui.grpPie.setTitle(L["g_pie"])
        self.ui.grpBar.setTitle(L["g_bar"])
        self.ui.grpLine.setTitle(L["g_line"])
        self.ui.grpDonut.setTitle(L["g_donut"])

        self.ui.period_box.blockSignals(True)
        self.ui.period_box.clear()
        self.ui.period_box.addItems(L["periods"])
        self.ui.period_box.blockSignals(False)

        self.ui.formSettings.labelForField(self.ui.cmbLang).setText(L["set_lang"])
        self.ui.formSettings.labelForField(self.ui.cmbTheme).setText(L["set_theme"])
        self.ui.formSettings.labelForField(self.ui.cmbDefCur).setText(L["set_cur"])

        self._note_title   = L["note_title"]
        self._msg_del      = L["msg_del"]
        self._msg_no_data  = L.get("msg_no_data",  "No data")
        self._msg_saved    = L.get("msg_saved",    "File saved")
        self._msg_err_save = L.get("msg_err_save", "Save error")
        self._L = L

    def _apply_theme(self):
        qss = Path(__file__).parent / f"styles/{self.conf['theme']}.qss"
        QApplication.instance().setStyleSheet(qss.read_text(encoding="utf-8"))

    def _is_income(self) -> bool:
        return self.ui.cmbType.currentIndex() == 1

    def _type_changed(self):
        if self._is_income():
            self.ui.spinAmount.setRange(0, 1e9)
            if self.ui.spinAmount.value() < 0:
                self.ui.spinAmount.setValue(abs(self.ui.spinAmount.value()))
        else:
            self.ui.spinAmount.setRange(-1e9, 0)
            if self.ui.spinAmount.value() > 0:
                self.ui.spinAmount.setValue(-abs(self.ui.spinAmount.value()))
        self._fill_cats()

    def _fill_cats(self):
        self.ui.cmbCategory.clear()
        for cid, name in self.core.cats(self._is_income()):
            self.ui.cmbCategory.addItem(name, cid)

    def _add_category(self):
        dlg = CategoryDialog(self._L, self._is_income(), self)
        if dlg.exec() != QDialog.Accepted:
            return
        name = dlg.edName.text().strip()
        if not name:
            return
        income = dlg.cmbType.currentIndex() == 1
        self.core.db.add_category(self.core.user_id, name, 1 if income else 0)
        if income == self._is_income():
            self._fill_cats()

    def _fill_table(self):
        tab = self.ui.table
        ops = self.core.ops()
        tab.clearContents()
        tab.setRowCount(len(ops))
        for r, o in enumerate(ops):
            dt_text = datetime.fromisoformat(o["date"]).strftime("%d.%m.%Y")
            sign = 1 if o["type"] else -1
            value = sign * o["amount"] / 100
            items = [
                QTableWidgetItem(dt_text),
                QTableWidgetItem(self._money(value)),
                QTableWidgetItem(o["category_name"] or "—"),
                QTableWidgetItem(o["note"] or ""),
            ]
            for c, it in enumerate(items):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                tab.setItem(r, c, it)
            tab.item(r, 0).setData(Qt.UserRole, o["id"])

    def _ind(self):
        bal = self.core.balance()
        inc, exp = self.core.totals()
        self.ui.lblBalance.setText(self._money(bal))
        self.ui.lblIncome.setText(self._money(inc))
        self.ui.lblExpense.setText(self._money(exp))

    def _export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, self._L["btn_export"], "operations.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return

        rows = []
        for r in range(self.ui.table.rowCount()):
            rows.append(
                {
                    self._L["col_date"]: self.ui.table.item(r, 0).text(),
                    self._L["col_sum"]: self.ui.table.item(r, 1).text(),
                    self._L["col_cat"]: self.ui.table.item(r, 2).text(),
                    self._L["col_note"]: self.ui.table.item(r, 3).text(),
                }
            )

        if not rows:
            QMessageBox.information(self, "", self._msg_no_data)
            return

        try:
            export_to_excel(rows, path)
            QMessageBox.information(self, "", self._msg_saved)
        except Exception as e:
            logger.exception("Save Excel error")
            QMessageBox.critical(self, "Error", f"{self._msg_err_save}\n{e}")

    def _sig(self):
        u = self.ui
        u.btnAdd.clicked.connect(self._add)
        u.btnDelete.clicked.connect(self._del)
        u.btnAddCat.clicked.connect(self._add_category)
        u.btnExport.clicked.connect(self._export_excel)
        u.cmbType.currentIndexChanged.connect(self._type_changed)
        u.table.cellDoubleClicked.connect(self._show_note)

        u.btnConvert.clicked.connect(self._conv)
        u.btnCreditCalc.clicked.connect(self._loan)
        u.btnDepCalc.clicked.connect(self._dep)

        u.btnSaveSettings.clicked.connect(self._save)

        u.period_box.currentIndexChanged.connect(self._charts)
        u.tabs.currentChanged.connect(
            lambda i: self._charts()
            if u.tabs.widget(i) is u.tab_analytics
            else None
        )

    def _add(self):
        raw_amt = abs(self.ui.spinAmount.value())
        if raw_amt == 0:
            return

        amount_rub = self.core.cv(raw_amt, self.conf["currency"], "RUB")

        self.core.add(
            self.ui.dateEdit.date(),
            amount_rub,
            self.ui.cmbCategory.currentData(),
            self._is_income(),
            self.ui.lineNote.text(),
        )
        self._fill_table()
        self._ind()
        self._charts()
        self.ui.spinAmount.setValue(0)
        self.ui.lineNote.clear()

    def _del(self):
        row = self.ui.table.currentRow()
        if row == -1:
            return
        if QMessageBox.question(self, "", self._msg_del) == QMessageBox.Yes:
            self.core.delete(self.ui.table.item(row, 0).data(Qt.UserRole))
            self._fill_table()
            self._ind()
            self._charts()

    def _show_note(self, row: int, col: int):
        if col != 3:
            return
        item = self.ui.table.item(row, col)
        if item and item.text().strip():
            QMessageBox.information(self, self._note_title, item.text(), QMessageBox.Ok)

    def _conv(self):
        a = self.ui.spinConvAmount.value()
        res = self.core.cv(
            a, self.ui.cmbCurFrom.currentText(), self.ui.cmbCurTo.currentText()
        )
        self.ui.lblConvResult.setText(
            f"{res:,.2f} {CURRENCY_SIGN[self.ui.cmbCurTo.currentText()]}"
        )

    def _loan(self):
        pay = self.core.credit(
            self.ui.spinCreditSum.value(),
            self.ui.spinCreditRate.value(),
            self.ui.spinCreditTerm.value(),
        )
        self.ui.lblCreditResult.setText(self._money(pay))

    def _dep(self):
        tot = self.core.deposit(
            self.ui.spinDepInit.value(),
            self.ui.spinDepRate.value(),
            self.ui.spinDepTerm.value(),
            self.ui.spinDepMonthly.value(),
            self.ui.chkDepCap.isChecked(),
        )
        self.ui.lblDepResult.setText(self._money(tot))

    def _save(self):
        lang = "ru" if self.ui.cmbLang.currentIndex() == 0 else "en"
        theme = "light" if self.ui.cmbTheme.currentIndex() == 0 else "dark"
        cur = self.ui.cmbDefCur.currentText()
        for k, v in (("lang", lang), ("theme", theme), ("currency", cur)):
            self.core.settings.set(k, v)
            self.conf[k] = v
        self.core.settings.sync()
        self.k = self.core.fx[cur]
        self._apply_lang()
        self._apply_theme()
        self._sync_settings_ui()
        self._fill_table()
        self._ind()
        self._charts()

    def _charts(self):
        if self.ui.tabs.currentWidget() is not self.ui.tab_analytics:
            return
        dmap = {0: 7, 1: 30, 2: 365, 3: None}
        pie, inc, exp, ln = self.core.stats(dmap[self.ui.period_box.currentIndex()])
        k = self.k

        ax = self.ui.canvas_pie.figure.axes[0]
        ax.clear()
        if pie:
            ax.pie([v / k for v in pie.values()], labels=pie.keys(), autopct="%1.1f%%")
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        self.ui.canvas_pie.figure.tight_layout()
        self.ui.canvas_pie.draw()

        ax = self.ui.canvas_bar.figure.axes[0]
        ax.clear()
        months = sorted(set(inc) | set(exp))
        if months:
            idx = range(len(months))
            iv = [inc.get(m, 0) / k for m in months]
            ev = [exp.get(m, 0) / k for m in months]
            ax.bar(idx, iv, width=0.4, label="Inc")
            ax.bar(idx, ev, width=0.4, bottom=iv, color="#D86969", label="Exp")
            sameY = all(m.startswith(datetime.now().strftime("%Y")) for m in months)
            ax.set_xticks(idx)
            ax.set_xticklabels(
                [m[5:] if sameY else m for m in months], rotation=45, ha="right"
            )
            ax.set_xlim(-0.5, len(months) - 0.5)
            ax.legend()
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        self.ui.canvas_bar.figure.tight_layout()
        self.ui.canvas_bar.draw()

        ax = self.ui.canvas_line.figure.axes[0]
        ax.clear()
        if ln:
            dt, b = zip(*ln)
            ax.plot(dt, [x / k for x in b], marker=".")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
            if dt[0] == dt[-1]:
                ax.set_xlim(dt[0] - timedelta(days=1), dt[0] + timedelta(days=1))
            else:
                ax.set_xlim(dt[0], dt[-1])
            ax.figure.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        self.ui.canvas_line.figure.tight_layout()
        self.ui.canvas_line.draw()

        ax = self.ui.canvas_donut.figure.axes[0]
        ax.clear()
        inc_total, exp_total = sum(inc.values()), sum(exp.values())
        if inc_total or exp_total:
            labels = [
                self._L["income"].rstrip(":"),
                self._L["expense"].rstrip(":"),
            ]
            ax.pie(
                [inc_total / k, exp_total / k],
                labels=labels,
                wedgeprops=dict(width=0.4),
                autopct="%1.1f%%",
            )
            ax.set(aspect="equal")
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
        self.ui.canvas_donut.figure.tight_layout()
        self.ui.canvas_donut.draw()


def run_app():
    app = QApplication(sys.argv)
    app.setStyleSheet((Path(__file__).parent / "styles/light.qss").read_text())
    w = FinanceApp()
    w.show()
    sys.exit(app.exec())
