// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// searches for enabled users
frappe.provide("erpnext.queries");
$.extend(erpnext.queries, {
	user: function() {
		return { query: "frappe.core.doctype.user.user.user_query" };
	},

	lead: function() {
		return { query: "erpnext.controllers.queries.lead_query" };
	},

	customer: function() {
		return { query: "erpnext.controllers.queries.customer_query" };
	},

	supplier: function() {
		return { query: "erpnext.controllers.queries.supplier_query" };
	},

	account: function() {
		return { query: "erpnext.controllers.queries.account_query" };
	},

	item: function() {
		return { query: "erpnext.controllers.queries.item_query" };
	},

	bom: function() {
		return { query: "erpnext.controllers.queries.bom" };
	},

	task: function() {
		return { query: "erpnext.projects.utils.query_task" };
	},

	party_filter: function(doc) {
		if(!doc.party) {
			frappe.throw(frappe._("Please specify a") + " " +
				frappe._(frappe.meta.get_label(doc.doctype, "party", doc.name)));
		}

		return { filters: { party: doc.party } };
	},

	party_filter: function(doc) {
		if(!doc.party) {
			frappe.throw(frappe._("Please specify a") + " " +
				frappe._(frappe.meta.get_label(doc.doctype, "party", doc.name)));
		}

		return { filters: { party: doc.party } };
	},

	lead_filter: function(doc) {
		if(!doc.lead) {
			frappe.throw(frappe._("Please specify a") + " " +
				frappe._(frappe.meta.get_label(doc.doctype, "lead", doc.name)));
		}

		return { filters: { lead: doc.lead } };
	},

	not_a_group_filter: function() {
		return { filters: { is_group: "No" } };
	},
});
