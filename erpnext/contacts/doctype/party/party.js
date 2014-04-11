// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'setup/doctype/contact_control/contact_control.js' %};

cur_frm.cscript.onload = function(doc, dt, dn) {
	cur_frm.cscript.load_defaults(doc, dt, dn);
}

cur_frm.cscript.load_defaults = function(doc, dt, dn) {
	doc = locals[doc.doctype][doc.name];
	if(!(doc.__islocal && doc.lead_name)) { return; }

	var fields_to_refresh = frappe.model.set_default_values(doc);
	if(fields_to_refresh) { refresh_many(fields_to_refresh); }
}

cur_frm.add_fetch('lead_name', 'company_name', 'party_name');
cur_frm.add_fetch('default_sales_partner','commission_rate','default_commission_rate');

cur_frm.cscript.refresh = function(doc, dt, dn) {
	cur_frm.cscript.setup_dashboard(doc);
	erpnext.hide_naming_series();

	if(doc.__islocal){
		hide_field(['address_html','contact_html']);
	}else{
		unhide_field(['address_html','contact_html']);
		// make lists
		cur_frm.cscript.make_address(doc, dt, dn);
		cur_frm.cscript.make_contact(doc, dt, dn);

		cur_frm.communication_view = new frappe.views.CommunicationList({
			parent: cur_frm.fields_dict.communication_html.wrapper,
			doc: doc,
		});
	}
}

cur_frm.cscript.setup_dashboard = function(doc) {
	cur_frm.dashboard.reset(doc);
	if(doc.__islocal)
		return;
	if (in_list(user_roles, "Accounts User") || in_list(user_roles, "Accounts Manager"))
		cur_frm.dashboard.set_headline('<span class="text-muted">'+ frappe._('Loading...')+ '</span>')

	cur_frm.dashboard.add_doctype_badge("Opportunity", "party");
	cur_frm.dashboard.add_doctype_badge("Quotation", "party");
	cur_frm.dashboard.add_doctype_badge("Sales Order", "party");
	cur_frm.dashboard.add_doctype_badge("Delivery Note", "party");
	cur_frm.dashboard.add_doctype_badge("Sales Invoice", "party");

	cur_frm.dashboard.add_doctype_badge("Supplier Quotation", "party");
	cur_frm.dashboard.add_doctype_badge("Purchase Order", "party");
	cur_frm.dashboard.add_doctype_badge("Purchase Receipt", "party");
	cur_frm.dashboard.add_doctype_badge("Purchase Invoice", "party");

	return frappe.call({
		type: "GET",
		method: "erpnext.contacts.doctype.party.party.get_dashboard_info",
		args: {
			party: cur_frm.doc.name
		},
		callback: function(r) {
			if (in_list(user_roles, "Accounts User") || in_list(user_roles, "Accounts Manager")) {
				cur_frm.dashboard.set_headline(
					frappe._("Total Billing This Year: ") + "<b>"
					+ format_currency(r.message.total_billing, erpnext.get_currency(cur_frm.doc.company))
					+ '</b> / <span class="text-muted">' + frappe._("Unpaid") + ": <b>"
					+ format_currency(r.message.total_unpaid, erpnext.get_currency(cur_frm.doc.company))
					+ '</b></span>');
			}
			cur_frm.dashboard.set_badge_count(r.message);
		}
	});
}

cur_frm.cscript.make_address = function() {
	if(!cur_frm.address_list) {
		cur_frm.address_list = new frappe.ui.Listing({
			parent: cur_frm.fields_dict['address_html'].wrapper,
			page_length: 5,
			new_doctype: "Address",
			get_query: function() {
				return "select name, address_type, address_line1, address_line2, city, state, country, pincode, fax, email_id, phone, is_primary_address, is_shipping_address from tabAddress where party='"+cur_frm.docname+"' and docstatus != 2 order by is_primary_address desc"
			},
			as_dict: 1,
			no_results_message: frappe._('No addresses created'),
			render_row: cur_frm.cscript.render_address_row,
		});
		// note: render_address_row is defined in contact_control.js
	}
	cur_frm.address_list.run();
}

cur_frm.cscript.make_contact = function() {
	if(!cur_frm.contact_list) {
		cur_frm.contact_list = new frappe.ui.Listing({
			parent: cur_frm.fields_dict['contact_html'].wrapper,
			page_length: 5,
			new_doctype: "Contact",
			get_query: function() {
				return "select name, first_name, last_name, email_id, phone, mobile_no, department, designation, is_primary_contact from tabContact where party='"+cur_frm.docname+"' and docstatus != 2 order by is_primary_contact desc"
			},
			as_dict: 1,
			no_results_message: frappe._('No contacts created'),
			render_row: cur_frm.cscript.render_contact_row,
		});
		// note: render_contact_row is defined in contact_control.js
	}
	cur_frm.contact_list.run();
}

cur_frm.fields_dict['party_group'].get_query = function(doc, dt, dn) {
	return{
		filters:{'allow_children': 'No'}
	}
}

cur_frm.fields_dict.lead_name.get_query = function(doc, cdt, cdn) {
	return{
		query: "erpnext.controllers.queries.lead_query"
	}
}

cur_frm.fields_dict['partner_target_details'].grid.get_field("item_group").get_query = function(doc, dt, dn) {
  return{
  	filters:{ 'allow_children': "No" }
  }
}

// -----------------------------------

frappe.provide("erpnext.utils");

erpnext.utils.get_party_details = function(frm, method, args) {
	if(!method) {
		method = "erpnext.contacts.doctype.party.party.get_party_details";
	}
	if(!args) {
		if(frm.doc.party) {
			args = {
				party: frm.doc.party,
				party_type: "Customer",
				price_list: frm.doc.selling_price_list
			};
		} else {
			args = {
				party: frm.doc.party,
				party_type: "Supplier",
				price_list: frm.doc.buying_price_list
			};
		}
	}
	args.currency = frm.doc.currency;
	args.company = frm.doc.company;
	frappe.call({
		method: method,
		args: args,
		callback: function(r) {
			if(r.message) {
				frm.updating_party_details = true;
				frm.set_value(r.message);
				frm.updating_party_details = false;
			}
		}
	});
}

erpnext.utils.get_address_display = function(frm, address_field, display_field) {
	if(frm.updating_party_details) return;
	if(!address_field) {
		if(frm.doc.party) {
			address_field = "party_address";
		} else if(frm.doc.party) {
			address_field = "party_address";
		} else return;
	}
	if(!display_field) display_field = "address_display";
	if(frm.doc[address_field]) {
		frappe.call({
			method: "erpnext.utilities.doctype.address.address.get_address_display",
			args: {"address_dict": frm.doc[address_field] },
			callback: function(r) {
				if(r.message)
					frm.set_value(display_field, r.message)
			}
		})
	}
}

erpnext.utils.get_contact_details = function(frm) {
	if(frm.updating_party_details) return;

	if(frm.doc["contact_person"]) {
		frappe.call({
			method: "erpnext.utilities.doctype.contact.contact.get_contact_details",
			args: {contact: frm.doc.contact_person },
			callback: function(r) {
				if(r.message)
					frm.set_value(r.message);
			}
		})
	}
}
