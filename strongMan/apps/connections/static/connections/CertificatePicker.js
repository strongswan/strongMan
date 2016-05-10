CertificatePicker = function(certificateIdentPickerId, certificatePickerUrl, csrf_token){
    these = this;
    var certificateIdentPicker = $("#" + certificateIdentPickerId);
    if(!certificateIdentPicker.length){
        throw "certificateidentity_picker_id not found!"
    }
    var certificateSelect = certificateIdentPicker.find(".certificateselect");
    if(!certificateSelect.length){
        throw "certificateSelect not found!"
    }
    var identitySelect = certificateIdentPicker.find(".identityselect");
    if(!identitySelect.length){
        throw "identitySelect not found!"
    }
    var previousCertificateValue = null;
    var addCertificateModal = certificateIdentPicker.find(".modal");
    if(!addCertificateModal.length){
        throw "addCertificateModal not found!"
    }


    var addEventHandler = function(){
        // Adds the events to check if certificate has changed
        certificateSelect.mouseenter(function(){
            previousCertificateValue = certificateSelect.val()
        });
        certificateSelect.change(function(){
            var value = certificateSelect.val();
            if(value !== previousCertificateValue){
                previousCertificateValue = value;
                certificateSelectHasChanged(value);
            }
        });
        //Event for disappear modal.
        addCertificateModal.on('hidden.bs.modal', function () {
            these.refresh();
        });
    };

    var certificateSelectHasChanged = function(new_value){
        console.log("certificate_value_has_changed: " + new_value);
        these.refresh();
    };
    these.refresh = function(){
            $.ajax({
            type: 'POST',
            url: certificatePickerUrl,
            data: {
                csrfmiddlewaretoken: csrf_token,
                'certififcate_id': previousCertificateValue
            },
            success: function (data) {
                var newCertificateSelect = $('<div />').html(data).find('.certificateselect').html();
                var newIdentitySelect = $('<div />').html(data).find('.identityselect').html();
                var oldValue = identitySelect.val();
                certificateSelect.html(newCertificateSelect);
                identitySelect.html(newIdentitySelect);
                identitySelect.val(oldValue);
                identitySelect.prop('disabled', false);

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
