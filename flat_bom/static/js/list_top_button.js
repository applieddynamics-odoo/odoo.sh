odoo.define('flat_bom.list_top_button', function(require) {
    "use strict";
    var list_controller = require('web.ListController');
    var list_view = require('web.ListView');
    var view_registry = require('web.view_registry');
    var tree_button = list_controller.extend({
        buttons_template: 'flat_bom_view.top_button',
        events: _.extend({}, list_controller.prototype.events, {}, {
            'click .open_wizard_action': '_OpenWizard',
}),
        _OpenWizard: function() {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model = 'test.wizard',
                name: 'Open Wizard',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: false,
            });
        }
    });
    var new_list_view = lsit_view.extend({
        config: _.extend({}, list_view.prototype.config, {
            Controller: tree_button,
        }),
    });
    view_registry.add('button_in_tree', new_list_view);
});
        }