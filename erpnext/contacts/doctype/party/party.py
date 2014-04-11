# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.defaults import get_restrictions
from frappe.utils import add_days, flt, fmt_money
from erpnext.utilities.doctype.address.address import get_address_display
from erpnext.utilities.doctype.contact.contact import get_contact_details
from frappe.model.naming import make_autoname
from frappe import msgprint, _

from frappe.model.document import Document

class Party(Document):
	def autoname(self):
		if frappe.defaults.get_global_default('party_naming_by') == 'Party Name':
			self.name = self.party_name
		else:
			self.name = make_autoname(self.naming_series+'.#####')

	def validate(self):
		self.validate_mandatory()
		self.scrub_website()

	def on_update(self):
		self.validate_name_with_party_group()
		self.update_lead_status()
		self.create_address_contact_from_lead()

	def validate_mandatory(self):
		if frappe.defaults.get_global_default('party_naming_by') == 'Naming Series' \
			and not self.naming_series:
				frappe.throw(_("Series is mandatory"), frappe.MandatoryError)

	def scrub_website(self):
		if self.website and not self.website.startswith("http"):
			self.website = "http://" + self.website

	def validate_name_with_party_group(self):
		if frappe.db.exists("Party Group", self.name):
			frappe.throw(_("""A Party Group exists with same name,
				please change the Party name or rename the Party Group"""))

	def update_lead_status(self):
		if self.lead:
			frappe.db.set_value("Lead", self.lead, "status", "Converted")

	def create_address_contact_from_lead(self):
		if self.lead:
			if not frappe.db.get_value("Address", {"lead": self.lead, "party": self.party}):
				frappe.db.sql("""update tabAddress set party=%s where lead=%s""",
					(self.name, self.lead))

			lead = frappe.db.get_value("Lead", self.lead,
				["lead_name", "email_id", "phone", "mobile_no"], as_dict=True)
			c = frappe.get_doc('Contact')
			c.first_name = lead.lead_name
			c.email_id = lead.email_id
			c.phone = lead.phone
			c.mobile_no = lead.mobile_no
			c.party = self.name
			c.is_primary_contact = 1
			try:
				c.insert()
			except NameError, e:
				pass

	def get_page_title(self):
		"""for sales partner listing in website"""
		return self.partner_name


	def on_trash(self):
		self.delete_party_address()
		self.delete_party_contact()
		if self.lead:
			frappe.db.set_value("Lead", self.lead, "status", "Interested")

	def delete_party_address(self):
		addresses = frappe.db.sql("""select name, lead from `tabAddress` where party=%s""", self.name)

		for name, lead in addresses:
			if lead:
				frappe.db.set_value("Address", name, "party", None)
			else:
				frappe.db.sql("""delete from `tabAddress` where name=%s""", name)

	def delete_party_contact(self):
		for contact in frappe.db.sql_list("""select name from `tabContact` where party=%s""", self.name):
				frappe.delete_doc("Contact", contact)

	def after_rename(self, olddn, newdn, merge=False):
		frappe.db.sql("""update `tabAddress` set address_title=%s where address_title=%s and party=%s""",
			(newdn, olddn, newdn))

	def check_credit_limit(self, company, current_voucher_amount=None):
		credit_limit, credit_limit_from = self.get_credit_limit(company)
		outstanding_amount = self.get_outstanding_amount(current_voucher_amount)
		credit_controller = frappe.db.get_value('Accounts Settings', None, 'credit_controller')
		# If outstanding greater than credit limit and not authorized person raise exception
		if credit_limit > 0 and flt(outstanding_amount) > credit_limit \
				and credit_controller not in frappe.user.get_roles():
			frappe.throw("""Total Outstanding amount (%s) for <b>%s</b> can not be \
				greater than credit limit (%s). To change your credit limit settings, \
				please update in the <b>%s</b> master""" % (fmt_money(outstanding_amount),
				self.name, fmt_money(credit_limit), credit_limit_from))

	def get_credit_limit(self, company):
		credit_limit_from = 'Party'
		credit_limit = self.credit_limit

		if not credit_limit:
			credit_limit = frappe.db.get_value('Company', company, 'credit_limit')
			credit_limit_from = 'Company'

		return credit_limit, credit_limit_from

	def get_outstanding_amount(self, current_voucher_amount):
		outstanding_amount = flt(frappe.db.sql("""select sum(ifnull(debit, 0)) - sum(ifnull(credit, 0))
			from `tabGL Entry` where party = %s""", self.name)[0][0])
		if current_voucher_amount:
			outstanding_amount += flt(current_voucher_amount)

		return outstanding_amount

@frappe.whitelist()
def get_dashboard_info(party):
	if not frappe.has_permission("Party", "read", party):
		frappe.throw(_("No Permission"))

	out = {}
	for doctype in ["Opportunity", "Quotation", "Sales Order", "Delivery Note", "Sales Invoice",
		"Supplier Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice"]:
			out[doctype] = frappe.db.get_value(doctype,
				{"party": party, "docstatus": ["!=", 2] }, "count(*)")

	billing = frappe.db.sql("""select sum(grand_total), sum(outstanding_amount)
		from `tabSales Invoice` where party=%s and docstatus = 1""", party)

	out["total_sales_invoice_amount"] = billing[0][0]
	out["total_sales_invoice_outstanding"] = billing[0][1]

	billing = frappe.db.sql("""select sum(grand_total), sum(outstanding_amount)
		from `tabPurchase Invoice` where party=%s and docstatus = 1""", party)

	out["total_purchase_invoice_amount"] = billing[0][0]
	out["total_purchase_invoice_outstanding"] = billing[0][1]

	return out

def get_party_list(doctype, txt, searchfield, start, page_len, filters):
	if frappe.db.get_default("party_naming_by") == "Party Name":
		fields = ["name", "party_type", "party_group", "territory"]
	else:
		fields = ["name", "party_name", "party_type", "party_group", "territory"]

	return frappe.db.sql("""select %s from `tabParty` where docstatus < 2
		and (%s like %s or party_name like %s) order by
		case when name like %s then 0 else 1 end,
		case when party_name like %s then 0 else 1 end,
		name, party_name limit %s, %s""" %
		(", ".join(fields), searchfield, "%s", "%s", "%s", "%s", "%s", "%s"),
		("%%%s%%" % txt, "%%%s%%" % txt, "%%%s%%" % txt, "%%%s%%" % txt, start, page_len))

@frappe.whitelist()
def get_party_details(party=None, account=None, party_type="Customer", company=None,
	posting_date=None, price_list=None, currency=None):

	return _get_party_details(party, account, party_type, company, posting_date, price_list, currency)

def _get_party_details(party=None, account=None, party_type="Customer", company=None,
	posting_date=None, price_list=None, currency=None, ignore_permissions=False):
	out = frappe._dict(set_account_and_due_date(party, account, party_type, company, posting_date))

	party = out[party_type.lower()]

	if not ignore_permissions and not frappe.has_permission(party_type, "read", party):
		frappe.throw("Not Permitted", frappe.PermissionError)

	party = frappe.get_doc(party_type, party)

	set_address_details(out, party, party_type)
	set_contact_details(out, party, party_type)
	set_other_values(out, party, party_type)
	set_price_list(out, party, party_type, price_list)

	if not out.get("currency"):
		out["currency"] = currency

	# sales team
	if party_type=="Customer":
		out["sales_team"] = [{
			"sales_person": d.sales_person,
			"sales_designation": d.sales_designation
		} for d in party.get("sales_team")]

	return out

def set_address_details(out, party, party_type):
	billing_address_field = "party_address" if party_type == "Lead" \
		else party_type.lower() + "_address"
	out[billing_address_field] = frappe.db.get_value("Address",
		{party_type.lower(): party.name, "is_primary_address":1}, "name")

	# address display
	out.address_display = get_address_display(out[billing_address_field])

	# shipping address
	if party_type in ["Customer", "Lead"]:
		out.shipping_address_name = frappe.db.get_value("Address",
			{party_type.lower(): party.name, "is_shipping_address":1}, "name")
		out.shipping_address = get_address_display(out["shipping_address_name"])

def set_contact_details(out, party, party_type):
	out.contact_person = frappe.db.get_value("Contact",
		{party_type.lower(): party.name, "is_primary_contact":1}, "name")

	out.update(get_contact_details(out.contact_person))

def set_other_values(out, party, party_type):
	for f in ["party_name", "party_group", "territory"]:
		out[f] = party.get(f)

	# fields prepended with default in Customer doctype
	for f in ['currency', 'taxes_and_charges'] \
		+ (['sales_partner', 'commission_rate'] if party_type=="Customer" else []):
		if party.get("default_" + f):
			out[f] = party.get("default_" + f)

def set_price_list(out, party, party_type, given_price_list):
	# price list
	price_list = get_restrictions().get("Price List")
	if isinstance(price_list, list):
		price_list = None

	if not price_list:
		price_list = party.default_price_list

	if not price_list and party_type=="Customer":
		price_list =  frappe.db.get_value("Customer Group",
			party.party_group, "default_price_list")

	if not price_list:
		price_list = given_price_list

	if price_list:
		out.price_list_currency = frappe.db.get_value("Price List", price_list, "currency")

	out["selling_price_list" if party.doctype=="Customer" else "buying_price_list"] = price_list


def set_account_and_due_date(party, account, party_type, company, posting_date):
	if not posting_date:
		# not an invoice
		return {
			party_type.lower(): party
		}

	if party:
		account = get_party_account(company, party, party_type)

	account_fieldname = "debit_to" if party_type=="Customer" else "credit_to"

	out = {
		party_type.lower(): party,
		account_fieldname : account,
		"due_date": get_due_date(posting_date, party, company)
	}
	return out

def get_party_account(company, party, party_type):
	if not company:
		frappe.throw(_("Please select company first."))
	else:
		field = "default_receivable_account" if party_type=="Customer" else "default_payable_account"
		return frappe.db.get_value("Company", company, field)

def get_due_date(posting_date, party, company):
	"""Set Due Date = Posting Date + Credit Days"""
	due_date = None
	if posting_date:
		credit_days = 0
		if party:
			credit_days = frappe.db.get_value("Party", party, "credit_days")
		if company and not credit_days:
			credit_days = frappe.db.get_value("Company", company, "credit_days")

		due_date = add_days(posting_date, credit_days) if credit_days else posting_date

	return due_date
