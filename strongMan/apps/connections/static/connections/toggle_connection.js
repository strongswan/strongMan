$(document).ready(function () {
    $("[id^=toggle_connection]").on('click', handler);
});

function handler(event) {
    event.preventDefault();
    var connectionId = this.id.value;
    $.ajax({ // create an AJAX call...
        data: $(this).serialize(), // get the form data
        type: 'POST', // GET or POST
        url: '/connections/toggle/' // the file to call
    });
    lock(connectionId, this.csrfmiddlewaretoken.value);
    return false;
}

function lock(connectionId, csrf) {
    $('#button_div' + connectionId).children().attr("disabled", "disabled");
    $('#spinner_place' + connectionId).append('<span id="spinner' + connectionId + '" class="glyphicon glyphicon-refresh spinning"></span>');
    $('#toggle_connection' + connectionId).off('click');
    setTimeout(function () {
        getState(connectionId, csrf)
    }, 1000);
}

function unlock(connectionId, csrf) {
    var spinnerName = '#spinner' + connectionId;
    $(spinnerName).remove(spinnerName);
    $('#button_div' + connectionId).children().removeAttr('disabled');
    $('#toggle_connection' + connectionId).on('click', handler);
}

function getState(connectionId, csrf) {
    $.ajax({ // create an AJAX call...
        data: {'csrfmiddlewaretoken': csrf},
        type: 'POST', // GET or POST
        url: '/connections/state/' + connectionId + '/', // the file to call
        success: function (response) { // on success..
            if (response.success) {
                switch (response.state) {
                    case 'CONNECTING':
                        setTimeout(function () {
                            getState(connectionId, csrf)
                        }, 1000);
                        break;
                    case 'ESTABLISHED':
                        $('#toggle_input' + response.id).bootstrapToggle('on');
                        unlock(response.id);
                        showConnectionInfoRow(response.id, csrf);
                        break;
                    default:
                        $('#toggle_input' + response.id).bootstrapToggle('off');
                        unlock(response.id);
                        hideConnectionInfoRow(response.id);
                        break;
                }
            } else {
                setAlert(response);
                unlock(response.id);
            }
        }
    });
}

function setAlert(response) {
    $('#alert_' + response.id).html('<div class="my_alert" role="alert" disabled="true">' +
        '<a class="close" data-dismiss="alert">&nbsp;×</a>' +
        '<strong>' + response.message + '</strong></div>');
}


function setConnectionInfo(connectionId, csrf) {
    $.ajax({
        data: {'csrfmiddlewaretoken': csrf, 'id': connectionId},
        type: 'POST',
        url: '/connections/info/',
        success: function (response) {
            if (response.success) {
                fillConnectionInfo(connectionId, response.child);
                setTimeout(function () {
                    setConnectionInfo(connectionId, csrf)
                }, 10000);
            }
        }
    });
}

function fillConnectionInfo(id, child) {
    $('#local-ts-' + id).text(child.local_ts);
    $('#remote-ts-' + id).text(child.remote_ts);
    $('#packets-in-' + id).text(child.packets_in);
    $('#packets-out-' + id).text(child.packets_out);
    $('#bytes-out-' + id).text(child.bytes_out);
    $('#bytes-in-' + id).text(child.bytes_in);
}

function showConnectionInfoRow(id, csrf) {
    setConnectionInfo(id, csrf);
    $('#connection-info-row-' + id).toggle(true);
    $('#connection-row-' + id).addClass("success");

}

function hideConnectionInfoRow(id) {
    $('#connection-info-row-' + id).toggle(false);
    $('#connection-row-' + id).removeClass("success");
}