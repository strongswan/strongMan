function logger(csrf, logId) {
    logId = typeof logId !== 'undefined' ? logId : -1;
    $.ajax({ // create an AJAX call...
        data: {'csrfmiddlewaretoken': csrf, 'id':logId},
        type: 'POST', // GET or POST
        url: '/connections/log/', // the file to call
        success: function (response) { // on success..
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