# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint

def execute(filters=None):
	if not filters: filters ={}

	days_since_last_order = filters.get("days_since_last_order")
	if cint(days_since_last_order) <= 0:
		frappe.msgprint("Please mention positive value in 'Days Since Last Order' field",raise_exception=1)

	columns = get_columns()
	parties = get_so_details()

	data = []
	for party in parties:
		if cint(party[8]) >= cint(days_since_last_order):
			party.insert(7,get_last_so_amt(party[0]))
			data.append(party)
	return columns, data

def get_so_details():
	return frappe.db.sql("""select
			party.name,
			party.party_name,
			party.territory,
			party.party_group,
			count(distinct(so.name)) as 'num_of_order',
			sum(net_total) as 'total_order_value',
			sum(if(so.status = "Stopped",
				so.net_total * so.per_delivered/100,
				so.net_total)) as 'total_order_considered',
			max(so.transaction_date) as 'last_sales_order_date',
			DATEDIFF(CURDATE(), max(so.transaction_date)) as 'days_since_last_order'
		from `tabParty` party, `tabSales Order` so
		where party.name = so.party and so.docstatus = 1
		group by party.name
		order by 'days_since_last_order' desc """,as_list=1)

def get_last_so_amt(party):
	res =  frappe.db.sql("""select net_total from `tabSales Order`
		where party ='%(party)s' and docstatus = 1 order by transaction_date desc
		limit 1""" % {'party':party})

	return res and res[0][0] or 0

def get_columns():
	return [
		"Customer (Party):Link/Party:120",
		"Customer Name:Data:120",
		"Territory::120",
		"Customer Group::120",
		"Number of Order::120",
		"Total Order Value:Currency:120",
		"Total Order Considered:Currency:160",
		"Last Order Amount:Currency:160",
		"Last Sales Order Date:Date:160",
		"Days Since Last Order::160"
	]
