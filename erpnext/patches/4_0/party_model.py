# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import scrub

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

	# update property setters
	# How to update db schema based on ps?

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
		frappe.db.sql("""update `tab%s` set party = CASE
			WHEN ifnull(customer, '')!='' THEN customer
			WHEN ifnull(supplier, '')!='' THEN supplier
			WHEN ifnull(sales_partner, '')!='' THEN sales_partner
			ELSE ''
		END""")

def create_party_group(args):
	party_group = frappe.new_doc("Party Group")
	for key in args:
		party_group[key] = args[key]
	party_group.insert()
