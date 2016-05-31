var doCertificateRefresh = $.Event('certRefresh'); //Event for all certificate selects. Gets called when a certificate could be uploaded.


CertificatePicker = function (certificateIdentPickerId, certificatePickerUrl, csrf_token) {
    var these = this;
    var $_ = function (selector, base) {
        if (typeof base !== "undefined") {
            element = base.find(selector);
        } else {
            var element = $(selector);
        }
        if (!element.length) {
            throw select + " not found!"
        }
        return element;
    };
    var certificateIdentPicker = $_("#" + certificateIdentPickerId);
    var certificateSelect = $_(".certificateselect", certificateIdentPicker);
    var identitySelect = $_(".identityselect", certificateIdentPicker);
    var previousCertificateValue = certificateSelect.val();
    var addCertificateModal = $_(".modal", certificateIdentPicker);


    var addEventHandler = function () {
        // Adds the events to check if certificate has changed
        certificateSelect.mouseenter(function () {
            previousCertificateValue = certificateSelect.val()
        });
        certificateSelect.change(function () {
            var value = certificateSelect.val();
            if (value !== previousCertificateValue) {
                previousCertificateValue = value;
                certificateSelectHasChanged(value);
            }
        });
        //Event for disappear modal.
        addCertificateModal.on('hidden.bs.modal', function () {
            these.refresh();
        });

        //Event when certificates has to be refreshed
        $(window).on('certRefresh', refreshMe);

    };
    these.refresh = function () {
        $(window).trigger(doCertificateRefresh);
    };

    var certificateSelectHasChanged = function (new_value) {
        these.refresh();
    };

    var refreshMe = function () {
        $.ajax({
                type: 'POST',
                url: certificatePickerUrl,
                data: {
                    csrfmiddlewaretoken: csrf_token,
                    'certififcate_id': previousCertificateValue
                },
                success: function (data) {
                    //Replace bootstrap selects with new rendered selects
                    var newCertificateSelect = $('<div />').html(data).find('.certificateselect').html();
                    var newIdentitySelect = $('<div />').html(data).find('.identityselect').html();
                    var oldValue = identitySelect.val();
                    certificateSelect.html(newCertificateSelect);
                    identitySelect.html(newIdentitySelect);
                    identitySelect.val(oldValue);
                    if (certificateSelect.val() != -1) {
                        identitySelect.prop('disabled', false);
                    }


                    $('.selectpicker').selectpicker('refresh');
                },
                error: function (data) {
                    throw data;
                }

            }
        );
    };

    addEventHandler();
};


CaPicker = function (caPickerId, caPickerUrl, csrf_token) {
    var these = this;
    var $_ = function (selector, base) {
        if (typeof base !== "undefined") {
            element = base.find(selector);
        } else {
            var element = $(selector);
        }
        if (!element.length) {
            throw select + " not found!"
        }
        return element;
    };
    var caPicker = $_("#" + caPickerId);
    var caSelect = $_(".selectpicker", caPicker);
    var addCertificateModal = $_(".modal", caPicker);
    var isServerIdentityCheckbox = $_(".is_server_identity", caPicker);
    var identityPicker = $_(".identity_picker", caPicker);
    var identityInput = $_("input", identityPicker);


    var addEventHandler = function () {
        //Event for disappear modal.
        addCertificateModal.on('hidden.bs.modal', function () {
            these.refresh();
        });
        isServerIdentityCheckbox.change(function () {
            checkIdentityDisable();
        });
        $(document).ready(function () {
            checkIdentityDisable();
        });

        //Event when certificates has to be refreshed
        $(window).on('certRefresh', refreshMe);

    };

    var checkIdentityDisable = function () {
        var checked = isServerIdentityCheckbox.is(':checked');
        identityInput.prop('disabled', checked);
        if (checked) {
            identityPicker.hide();
        } else {
            identityPicker.show();
        }
    };

    var certificateSelectHasChanged = function (new_value) {
        these.refresh();
    };
    these.refresh = function () {
        //Call global certificate refresh
        $(window).trigger(doCertificateRefresh);
    };
    var refreshMe = function () {
        $.ajax({
                type: 'POST',
                url: caPickerUrl,
                data: {
                    csrfmiddlewaretoken: csrf_token
                },
                success: function (data) {
                    //Replace bootstrap selects with new rendered selects
                    var newCertificateSelect = $('<div />').html(data).find('.selectpicker').html();
                    var oldValue = caSelect.val();
                    caSelect.html(newCertificateSelect);
                    caSelect.val(oldValue);

                    $('.selectpicker').selectpicker('refresh');
                },
                error: function (data) {
                    throw data;
                }

            }
        );
    };

    addEventHandler();
};

CaAuto = function (caPickerId) {
    var these = this;
    var $_ = function (selector, base) {
        if (typeof base !== "undefined") {
            element = base.find(selector);
        } else {
            var element = $(selector);
        }
        if (!element.length) {
            throw selector + " not found!"
        }
        return element;
    };
    var caPicker = $_("#" + caPickerId);
    var caPickerRow = $_(".ca_picker", caPicker);
    var caSelectPicker = $_(".selectpicker", caPickerRow);
    var caAutoCheckbox = $_("#certificate_ca_auto", caPicker);


    var addEventHandler = function () {
        caAutoCheckbox.change(function () {
            refresh();
        });
        $(document).ready(function () {
            refresh();
        });
    };

    var refresh = function () {
        var checked = caAutoCheckbox.is(':checked');
        if (checked) {
            caPickerRow.hide();
            caSelectPicker.prop('disabled', true);
        } else {
            caPickerRow.show();
            caSelectPicker.prop('disabled', false);
            console.log(caSelectPicker.prop('disabled'));
        }
        caSelectPicker.selectpicker('refresh');
    };
    addEventHandler();
};

