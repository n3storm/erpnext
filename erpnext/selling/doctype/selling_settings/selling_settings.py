# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document

class SellingSettings(Document):

	def validate(self):
		for key in ["customer_group", "territory", "maintain_same_sales_rate",
			"editable_price_list_rate", "selling_price_list"]:
				frappe.db.set_default(key, self.get(key, ""))
