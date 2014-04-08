# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr
from frappe.model.document import Document

class ContactsSettings(Document):
	def validate(self):
		from erpnext.setup.doctype.naming_series.naming_series import set_by_naming_series

		frappe.db.set_default("party_naming_by", cstr(self.party_naming_by))
		set_by_naming_series("Party", "party_name", cstr(self.party_naming_by)=="Naming Series",
			hide_name_field=False)
