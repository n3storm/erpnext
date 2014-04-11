// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.cscript.refresh = function(doc, cdt, cdn) {
	cur_frm.cscript.set_root_readonly(doc);
}

cur_frm.cscript.set_root_readonly = function(doc) {
	// read-only for root party group
	if(!doc.parent_party_group) {
		cur_frm.set_read_only();
		cur_frm.set_intro(frappe._("This is a root party group and cannot be edited."));
	} else {
		cur_frm.set_intro(null);
	}
}

//get query select Party Group
cur_frm.fields_dict['parent_party_group'].get_query = function(doc,cdt,cdn) {
	return{
		searchfield:['name', 'parent_party_group'],
		filters: {
			'is_group': "Yes"
		}
	}
}
