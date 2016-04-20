$(document).ready(function () {
    $('#toggle_connection').click(function (event) { // catch the form's submit event
        event.preventDefault();
        console.log($(this).serialize());
        $.ajax({ // create an AJAX call...
            data: $(this).serialize(), // get the form data
            type: 'POST', // GET or POST
            url: '/connections/toggle/', // the file to call
            success: function (response) { // on success..
                if (response.success) {
                    var toggle = '#toggle_input' + response.id;
                    $(toggle).bootstrapToggle('toggle');
                } else {
                    var alert_name = '#alert_' + response.id;
                    $(alert_name).html('<div class="btn alert alert-danger" role="alert">' +
                        '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
                        '<span class="sr-only">Error: </span>' + response.message +
                        '</div>');
                }
            }
        });
        return false;
    });
});


