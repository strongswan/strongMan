function logger(csrf, logId) {
    logId = typeof logId !== 'undefined' ? logId : -1;
    $.ajax({
        data: {'csrfmiddlewaretoken': csrf, 'id': logId},
        type: 'POST',
        url: '/connections/log/',
        error: function (jqXHR, textStatus) {
            if (textStatus === 'timeout') {
                logger(csrf);
            }
        },
        success: function (response) {
            last_log = -1;
            for (var log in response.logs) {
                addRowToLog(response.logs[log]);
                last_log = response.logs[log].id;
            }
            logger(csrf, last_log);
        }
    });
}

function addRowToLog(log) {
    $('#log_table tbody').append('<tr class="child"><td class="timestamp">' + log.timestamp + '</td><td class="con_name">' + log.name + '</td><td><p>' + log.message + '</p></td></tr>');
    $('#log-content').scrollTop($('#log_table').height());
}

$(document).ready(function () {
    $('#log_panel').on('shown.bs.collapse', function () {
        $('#log-content').scrollTop($('#log_table').height());
    });
});


