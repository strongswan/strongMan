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
    logger(connectionId, this.csrfmiddlewaretoken.value);
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
                        break;
                    default:
                        $('#toggle_input' + response.id).bootstrapToggle('off');
                        unlock(response.id);
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

function logger(connectionId, csrf) {
    $.ajax({ // create an AJAX call...
        data: {'csrfmiddlewaretoken': csrf},
        type: 'POST', // GET or POST
        url: '/connections/log/' + connectionId + '/', // the file to call
        success: function (response) { // on success..
            if (response.has_log) {
                if (response.level == "1") {
                    setTimeout(function () {
                        logger(connectionId, csrf)
                    }, 200);
                }
                addRowToLog(response)
            } else {
                setTimeout(function () {
                    logger(connectionId, csrf)
                }, 1000);
            }
        }
    });
}

function addRowToLog(log) {
    $('#log_table tbody').append('<tr class="child"><td>' + log.timestamp + '</td><td>' + log.name + '</td><td>' + log.message + '</td></tr>');
    $('#div-table-content').scrollTop($('#log_table').height());
}