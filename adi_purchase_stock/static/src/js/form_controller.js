odoo.define('adi_purchase_stock.FormController', function (require) {
    'use strict';
    
    const FormController = require('web.FormController');
    const Dialog = require('web.Dialog');

    const confirm = function (owner, message, options) {
        var buttons = [
            {
                text: "YES",
                classes: 'btn-primary',
                close: true,
                click: options && options.confirm_callback,
            },
            {
                text: "NO",
                close: true,
                click: options && options.cancel_callback
            }
        ];
        return new Dialog(owner, _.extend({
            size: 'medium',
            buttons: buttons,
            $content: $('<main/>', {
                role: 'alert',
                text: message,
            }),
            title: "Confirmation",
            onForceClose: options && (options.onForceClose || options.cancel_callback),
        }, options)).open({shouldFocusButtons:true});
    };

    FormController.include({
        _saveRecord(recordId, options) {
            if (this.modelName == 'purchase.order' && !options.stayInEdit) {
                var external_id = recordId || this.handle;
                var record = this.model.localData[external_id];
                var self = this;
                var sup = this._super;
                var params = arguments;
                var changes = record._changes || {};
                var vendor = changes.partner_id || record.data.partner_id;
                return this._rpc({
                    model: 'res.partner',
                    method: 'should_warn',
                    args: [this.model.localData[vendor].data.id],
                }).then(function (should_warn) {
                    if (should_warn) {
                        return confirm(self, 'The selected vendor has an on-time delivery rate below the current threshold. Please ensure there are no better alternatives for this order. Do you want to continue?', {
                            confirm_callback: () => sup.apply(self, params),
                        });
                    } else {
                        return sup.apply(self, params);
                    }
                })
            } else {
                return this._super.apply(this, arguments);
            }
        },
    });
});