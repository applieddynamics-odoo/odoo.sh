odoo.define('adi_purchase_stock.FormController', function (require) {
    'use strict';
    
    const FormController = require('web.FormController');
    const Dialog = require('web.Dialog');

    FormController.include({
        _saveRecord(recordId, options) {
            if (this.modelName == 'purchase.order') {
                console.log(recordId || this.handle);
                var external_id = recordId || this.handle;
                var record = this.model.localData[external_id].data;
                var self = this;
                var sup = this._super;
                var params = arguments;
                return this._rpc({
                    model: 'purchase.order',
                    method: 'check_and_warn',
                    args: [record.id],
                }).then(function (should_warn) {
                    if (should_warn) {
                        return Dialog.confirm(self, 'The selected vendor has an on-time delivery rate below the current threshold. Please ensure there are no better alternatives for this order. Do you want to continue?', {
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