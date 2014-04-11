# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from erpnext.accounts.report.accounts_receivable.accounts_receivable import get_ageing_data

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns()
	entries = get_entries(filters)
	invoice_posting_date_map = get_invoice_posting_date_map(filters)
	against_date = ""
	outstanding_amount = 0.0

	data = []
	for d in entries:
		if d.against_voucher:
			against_date = d.against_voucher and invoice_posting_date_map[d.against_voucher] or ""
			outstanding_amount = d.debit or -1*d.credit
		else:
			against_date = d.against_invoice and invoice_posting_date_map[d.against_invoice] or ""
			outstanding_amount = d.credit or -1*d.debit

		row = [d.name, d.account, d.posting_date, d.against_voucher or d.against_invoice,
			against_date, d.debit, d.credit, d.cheque_no, d.cheque_date, d.remark]

		if d.against_voucher or d.against_invoice:
			row += get_ageing_data(d.posting_date, against_date, outstanding_amount)
		else:
			row += ["", "", "", "", ""]

		data.append(row)

	return columns, data

def get_columns():
	return ["Journal Voucher:Link/Journal Voucher:140", "Party:Link/Party:140",
		"Account:Link/Account:140",
		"Posting Date:Date:100", "Against Invoice:Link/Purchase Invoice:130",
		"Against Invoice Posting Date:Date:130", "Debit:Currency:120", "Credit:Currency:120",
		"Reference No::100", "Reference Date:Date:100", "Remarks::150", "Age:Int:40",
		"0-30:Currency:100", "30-60:Currency:100", "60-90:Currency:100", "90-Above:Currency:100"
	]

def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " and company = '%s'" % filters["company"].replace("'", "\'")

	parties = []

	if filters.get("party"):
		parties = [filters["party"]]
	else:
		if filters.get("payment_type") == "Incoming":
			cond = " and ifnull(customer, 0)=1"
		else:
			cond = " and ifnull(supplier, 0)=1"

		parties = frappe.db.sql_list("""select name from `tabParty`
			where docstatus < 2 %s""" % cond)


	if parties:
		conditions += " and jvd.party in (%s)" % (", ".join(['%s']*len(parties)))

	if filters.get("from_date"): conditions += " and jv.posting_date >= '%s'" % filters["from_date"]
	if filters.get("to_date"): conditions += " and jv.posting_date <= '%s'" % filters["to_date"]

	return conditions, parties

def get_entries(filters):
	conditions, parties = get_conditions(filters)
	entries =  frappe.db.sql("""select jv.name, jvd.account, jvd.party, jv.posting_date,
		jvd.against_voucher, jvd.against_invoice, jvd.debit, jvd.credit,
		jv.cheque_no, jv.cheque_date, jv.remark
		from `tabJournal Voucher Detail` jvd, `tabJournal Voucher` jv
		where jvd.parent = jv.name and jv.docstatus=1 %s order by jv.name DESC""" %
		(conditions), tuple(parties), as_dict=1)

	return entries

def get_invoice_posting_date_map(filters):
	invoice_posting_date_map = {}
	if filters.get("payment_type") == "Incoming":
		for t in frappe.db.sql("""select name, posting_date from `tabSales Invoice`"""):
			invoice_posting_date_map[t[0]] = t[1]
	else:
		for t in frappe.db.sql("""select name, posting_date from `tabPurchase Invoice`"""):
			invoice_posting_date_map[t[0]] = t[1]

	return invoice_posting_date_map
