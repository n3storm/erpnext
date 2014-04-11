// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Payment Period Based On Invoice Date"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: frappe._("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
		},
		{
			fieldname:"to_date",
			label: frappe._("To Date"),
			fieldtype: "Date",
			default: get_today()
		},
		{
			fieldname:"payment_type",
			label: frappe._("Payment Type"),
			fieldtype: "Select",
			options: "Incoming\nOutgoing",
			default: "Incoming"
		},
		{
			fieldname:"party",
			label: frappe._("Party"),
			fieldtype: "Link",
			options: "Party"
		},
		{
			fieldname:"company",
			label: frappe._("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("company")
		},
	]
}
