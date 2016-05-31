$(document).ready(function () {
    $("[id^=toggle_connection]").on('click', handler);
});

function handler(event) {
    event.preventDefault();
    var connectionId = this.id.value;
    var csrf = this.csrfmiddlewaretoken.value;
    $.ajax({
        data: $(this).serialize(),
        type: 'POST',
        url: '/connections/toggle/',
        success: function (response) {
            if (!response.success) {
                setAlert(response);
                stateDown(response.id);
            }
        }
    });
    stateConnecting(connectionId);
    setTimeout(function () {
        getState(connectionId, csrf)
    }, 900);
    return false;
}


function stateEstablished(connectionId) {
    $('#toggle_input' + connectionId).prop('checked', true).change();
    $('#button_div' + connectionId).find('.toggle-on').text("On");
    $('#button_div' + connectionId).find('.toggle-on').attr("class", "btn btn-success toggle-on");
    $('#button_div' + connectionId).find('.toggle').attr("class", 'toggle btn btn-success');
}

function stateDown(connectionId) {
    $('#toggle_input' + connectionId).prop('checked', false).change();
    $('#button_div' + connectionId).find('.toggle-off').text("Off");
    $('#toggle_connection' + connectionId).prop('checked', false).change();
    $('#button_div' + connectionId).find('.toggle').attr("class", 'toggle btn btn-default off');
}

function stateConnecting(connectionId) {
    $('#toggle_input' + connectionId).prop('checked', true).change();
    $('#button_div' + connectionId).find('.toggle-on').text("");
    $('#button_div' + connectionId).find('.toggle-on').append("<i class='glyphicon glyphicon-refresh spinning'></i>");
    $('#button_div' + connectionId).find('.toggle-on').attr("class", "btn btn-warning toggle-on");
    $('#button_div' + connectionId).find('.toggle').attr("class", 'toggle btn btn-warning');
    lock(connectionId);
}

function lock(connectionId) {
    $('#toggle_connection' + connectionId).unbind('click');
    setTimeout(function () {
        unlock(connectionId)
    }, 1000);
}

function unlock(connectionId) {
    $('#toggle_connection' + connectionId).on('click', handler);
}


function getState(connectionId, csrf) {
    $.ajax({
        data: {'csrfmiddlewaretoken': csrf},
        type: 'POST',
        url: '/connections/state/' + connectionId + '/',
        success: function (response) {
            if (response.success) {
                switch (response.state) {
                    case 'CONNECTING':
                        stateConnecting(response.id);
                        hideConnectionInfoRow(response.id);
                        setTimeout(function () {
                            getState(connectionId, csrf)
                        }, 900);
                        break;
                    case 'ESTABLISHED':
                        stateEstablished(response.id);
                        showConnectionInfoRow(response.id, csrf);
                        break;
                    default:
                        stateDown(response.id);
                        hideConnectionInfoRow(response.id);
                        break;
                }
            } else {
                setAlert(response);
                stateDown(response.id);
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