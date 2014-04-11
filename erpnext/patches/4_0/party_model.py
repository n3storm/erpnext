# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import scrub
from frappe.model import rename_field, get_doctype_module


def execute():
	party_fields_map = {
		"Customer": {
			"customer_name": "party_name",
			"customer_type": "party_type",
			"lead_name": "lead",
			"customer_group": "party_group",
			"customer_details": "party_details",
			"default_taxes_and_charges": "default_sales_taxes_and_charges"
		},
		"Supplier": {
			"supplier_name": "party_name",
			"supplier_type": "party_group",
			"supplier_details": "party_details",
			"default_taxes_and_charges": "default_purchase_taxes_and_charges"
		},
		"Sales Partner": {
			"partner_name": "party_name",
			"partner_type": "party_group",
			"distribution_id": "target_distribution",
			"partner_website": "website",
		}
	}

	# TODO: reload module conatcts
	for dt in ["party_group", "party"]:
		frappe.reload_doc("contacts", "doctype", dt)

	# TODO update property setters

	# update custom fields
	for d in frappe.db.sql("""select name, dt from `tabCustom Field`
		where dt in ('Customer', 'Supplier', 'Sales Partner')"""):
			cf = frappe.get_doc("Custom Field", d[0])
			cf.dt = "Party"
			if cf.insert_after in party_fields_map[d[1]]:
				cf.insert_after = party_fields_map[d[1]][cf.insert_after]

			if cf.depends_on and not cf.depends_on.startwith("eval"):
				if cf.depends_on in party_fields_map[d[1]]:
					cf.depends_on = party_fields_map[d[1]][cf.depends_on]

			cf.save()

	# update report dt
	frappe.db.sql("""update tabReport set ref_doctype='Party'
		where ref_doctype in ('Customer', 'Supplier', 'Sales Partner')
		and report_type in ('Query Report', 'Script Report')""")

	# Create party groups
	# based on customer groups
	for cg in frappe.db.sql("""select * from `tabCustomer Group` order by lft asc""", as_dict=True):
		create_party_group({
			"name": cg.name,
			"party_group_name": cg.customer_group_name,
			"parent_party_group": cg.parent_customer_group,
			"allow_children": cg.is_group,
			"default_price_list": cg.default_price_list
		})
	frappe.rename_doc("Party Group", "All Customer Groups", "All Party Groups")

	# based on supplier types
	create_party_group({
		"party_group_name": "Supplier Types",
		"parent_party_group": "",
		"allow_children": "Yes",
	})
	for st in frappe.db.sql("""select name from `tabSupplier Type`"""):
		create_party_group({
			"party_group_name": st[0],
			"parent_party_group": "Supplier Types",
			"allow_children": "No",
		})

	# based on partner types
	create_party_group({
		"party_group_name": "Partner Types",
		"parent_party_group": "",
		"allow_children": "Yes",
	})

	partner_types = frappe.get_meta("Sales Partner").get_options("partner_type").split("\n")
	for pt in partner_types:
		create_party_group({
			"party_group_name": pt,
			"parent_party_group": "Partner Types",
			"allow_children": "No",
		})

	# create party from customer, supplier and sales partner
	for dt, from_to in party_fields_map.items():
		from_doc = frappe.get_doc("DocType", dt)
		from_fields = from_doc.get_valid_columns()
		for d in frappe.db.sql("""select * from `tab%s`""" % dt, as_dict=True):
			party = frappe.new_doc("Party")
			for from_field in from_fields:
				to_field = from_to[from_field] if from_field in from_to.keys() else from_field
				if getattr(party, to_field, None):
					party[to_field] = d[from_field]

			party[scrub(dt)] = 1
			party.insert()

		child_tables = [t.options for t in from_doc.get_table_fields()]
		for child_table in child_tables:
			frappe.db.sql("""update `tab%s` set parenttype='Party' where parenttype=%s""" %
				(child_table, '%s'), (dt,))

	# update addresses and contacts
	for dt in ["Address", "Contact"]:
		frappe.reload_doc("utilities", "doctype", scrub(dt))
		frappe.db.sql("""update `tab%s` set party =
			CASE
				WHEN ifnull(customer, '')!='' THEN customer
				WHEN ifnull(supplier, '')!='' THEN supplier
				WHEN ifnull(sales_partner, '')!='' THEN sales_partner
				ELSE ''
			END""")

	frappe.delete_doc("Report", "Customer Account Head")
	frappe.delete_doc("Report", "Supplier Account Head")

	frappe.db.sql("""update tabAccount set warehouse = master_name where account_type = 'Warehouse'""")




def create_party_group(args):
	party_group = frappe.new_doc("Party Group")
	for key in args:
		party_group[key] = args[key]
	party_group.insert()


def migrate_all_party_link_fields():
	fields_map = {
		"C-Form": {
			"customer": "party"
		},
		"POS Setting": {
			"customer": "party"
		},
		"C-Form": {
			"customer": "party"
		},
		"Sales Invoice": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Quotation": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Sales Order": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Delivery Note": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Sales Invoice Item": {
			"customer_item_code": "party_item_code",
		},
		"Quotation Item": {
			"customer_item_code": "party_item_code",
		},
		"Sales Order Item": {
			"customer_item_code": "party_item_code",
		},
		"Delivery Note Item": {
			"customer_item_code": "party_item_code",
		},
		"Project": {
			"customer": "party"
		},
		"Installation Note": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Customer Issue": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Maintenance Schedule": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address"
		},
		"Maintenance Visit": {
			"customer": "party",
			"customer_name": "party_name",
			"customer_group": "party_group",
			"customer_address": "party_address",
			"customer_feedback": "party_feedback"
		},
		"Lead": {
			"customer": "party"
		},
		"Support Ticket": {
			"customer": "party",
			"customer_name": "party_name"
		},
		"Supplier Quotation": {
			"supplier": "party",
			"supplier_name": "party_name",
			"supplier_address": "party_address",
		},
		"Purchase Order": {
			"supplier": "party",
			"supplier_name": "party_name",
			"supplier_address": "party_address",
		},
		"Purchase Invoice": {
			"supplier": "party",
			"supplier_name": "party_name",
			"supplier_address": "party_address",
		},
		"Purchase Receipt": {
			"supplier": "party",
			"supplier_name": "party_name",
			"supplier_address": "party_address",
		},
	}

	for dt, field_map in fields_map.items():
		for from_field, to_field in field_map.items():
			rename_field(dt, from_field, to_field)

		frappe.reload_doc(get_doctype_module(dt), "doctype", scrub(dt))


# to do
#------------------
# set party naming by
# Contact Control
# default receivable / payable account in company for exising and countrywise coa
 - delete all party accounts and convert receibale/payable group to ledger
# NOTE : All reports and print formats has been reloaded in "fields to be renamed" patch, hence not needed
# set party in gl entry and replace existing account with receivable/payable account
# Replace all existing customer/supplier account with receivable/payable account in all forms
# dealing with price list -  separate default price list ????
# Property setters
# reports made using Report builder based on customer, supplier and sales partner
# fix test record



# code replacement pending
#------------------
# party.js & party.py ---- get_party_details
# purchase analytics & sales analytics & report data map
# pos.js
# accounts receivable/payable report py
# shopping cart
# trends.py report
# customer acquisition and loyalty report
# print formats json


# country-wise coa
# --------------------
# make country-wise file for maintaining account properties
#	- Balance Sheet roots
#	- Profit and Loss roots
#	- default receivable account
#	- default payable account
#	- Stock asset group (create default warehouse account under this group)
# Enable/disable options in "Chart of Accounts"
# Make standard coa as per existing coa and always show in setup wizard
