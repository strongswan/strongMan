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
        url: '/server_connections/toggle/',
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

function stateLoaded(connectionId) {
    $('#toggle_input' + connectionId).prop('checked', true).change();
    $('#button_div' + connectionId).find('.toggle-on').text("Loaded");
    $('#button_div' + connectionId).find('.toggle-on').attr("class", "btn btn-success toggle-on");
    $('#button_div' + connectionId).find('.toggle').attr("class", 'toggle btn btn-success');
}

function stateUnloaded(connectionId) {
    $('#toggle_input' + connectionId).prop('checked', false).change();
    $('#button_div' + connectionId).find('.toggle-off').text("Unloaded");
    $('#toggle_connection' + connectionId).prop('checked', false).change();
    $('#button_div' + connectionId).find('.toggle').attr("class", 'toggle btn btn-default off');
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
        url: '/server_connections/state/' + connectionId + '/',
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
                    case 'LOADED':
                        stateLoaded(response.id);
                        showConnectionInfoRow(response.id, csrf);
                        break;
                    case 'UNLOADED':
                        stateUnloaded(response.id);
                        hideConnectionInfoRow(response.id, csrf);
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
        url: '/server_connections/info/',
        success: function (response) {
            if (response.success) {
                fillConnectionInfo(connectionId, response.child);
            }
            setTimeout(function () {
                setConnectionInfo(connectionId, csrf)
            }, 10000);
        }
    });
}

function fillConnectionInfo(id, child) {
    generate_entries(id, Object.keys(child).length, child);
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

function generate_entries(id, rows, child) {
    sas = document.getElementById("connection-" + id + "-sas");

    $("#connection-" + id + "-sas tr").remove();

    for (var i = 0; i < rows; i++) {
        id = child[i].uniqueid;
        var row = document.createElement("tr");

        var cell_uniqueid = document.createElement("td");
        var uniqueid = document.createTextNode(id);
        cell_uniqueid.appendChild(uniqueid);
        row.appendChild(cell_uniqueid);

        var cell_remote_host = document.createElement("td");
        var remote_host = document.createTextNode(child[i].remote_host);
        cell_remote_host.appendChild(remote_host);
        row.appendChild(cell_remote_host);

        var cell_remote_id = document.createElement("td");
        var remote_id = document.createTextNode(child[i].remote_id);
        cell_remote_id.appendChild(remote_id);
        row.appendChild(cell_remote_id);

        var cell_button = document.createElement("td");

        var form = document.createElement("form");
        form.id = "delete_sa_form_" + id;
        form.action = "/server_connections/delete_sa/";

        var csrf_token = document.createElement("input");
        csrf_token.name = "csrfmiddlewaretoken";
        csrf_token.value = getCookie('csrftoken');
        csrf_token.type = "hidden";
        form.appendChild(csrf_token);

        var sa_id = document.createElement("input");
        sa_id.name = "sa_id";
        sa_id.value = id;
        sa_id.type = "hidden";
        form.appendChild(sa_id);

        var div = document.createElement("div");
        div.id = "delete_sa_" + id;

        var delete_button = document.createElement("button");
        delete_button.type = 'button';
        delete_button.className = 'btn btn-danger';
        delete_button.innerHTML = "delete";

        div.appendChild(delete_button);
        form.appendChild(sa_id);
        form.appendChild(div);
        cell_button.appendChild(form);
        row.appendChild(cell_button);
       
        sas.appendChild(row);

        // CHILD SAS
        child_sas = child[i].child_sas;
        nr_of_childs = Object.keys(child_sas).length;

        var child_sas_row = document.createElement("tr");
        child_sas_row.id = "child-sas" + id;

        var cell_child_sas = document.createElement("td");
        cell_child_sas.colSpan = "4";

        var table = document.createElement("table");
        table.className = "table-hover table-condensed table-responsive";
        table.style = "width: 100%";

        var child_sas_header_row = document.createElement("thead");

        var h_cell_remote_ts = document.createElement("th");
        var h_remote_ts = document.createTextNode("remote ts");
        h_cell_remote_ts.appendChild(h_remote_ts);
        child_sas_header_row.appendChild(h_cell_remote_ts);
        var h_cell_local_ts = document.createElement("th");
        var h_local_ts = document.createTextNode("local ts");
        h_cell_local_ts.appendChild(h_local_ts);
        child_sas_header_row.appendChild(h_cell_local_ts);
        var h_cell_bytes_in = document.createElement("th");
        var h_bytes_in = document.createTextNode("bytes in");
        h_cell_bytes_in.appendChild(h_bytes_in);
        child_sas_header_row.appendChild(h_cell_bytes_in);
        var h_cell_bytes_out = document.createElement("th");
        var h_bytes_out = document.createTextNode("bytes out");
        h_cell_bytes_out.appendChild(h_bytes_out);
        child_sas_header_row.appendChild(h_cell_bytes_out);
        var h_cell_packets_in = document.createElement("th");
        var h_packets_in = document.createTextNode("packets in");
        h_cell_packets_in.appendChild(h_packets_in);
        child_sas_header_row.appendChild(h_cell_packets_in);
        var h_cell_packets_out = document.createElement("th");
        var h_packets_out = document.createTextNode("packets out");
        h_cell_packets_out.appendChild(h_packets_out);
        child_sas_header_row.appendChild(h_cell_packets_out);
        var h_cell_delete_button = document.createElement("th");
        child_sas_header_row.appendChild(h_cell_delete_button);

        table.appendChild(child_sas_header_row);

        for (var n = 0; n < nr_of_childs; n++) {
            var child_sa = child_sas[n];

            var child_row = document.createElement("tr");

            var cell_remote_ts = document.createElement("td");
            var remote_ts = document.createTextNode(child_sa.remote_ts);
            cell_remote_ts.appendChild(remote_ts);
            child_row.appendChild(cell_remote_ts);

            var cell_local_ts = document.createElement("td");
            var local_ts = document.createTextNode(child_sa.local_ts);
            cell_local_ts.appendChild(local_ts);
            child_row.appendChild(cell_local_ts);

            var cell_bytes_in = document.createElement("td");
            var bytes_in = document.createTextNode(child_sa.bytes_in);
            cell_bytes_in.appendChild(bytes_in);
            child_row.appendChild(cell_bytes_in);

            var cell_bytes_out = document.createElement("td");
            var bytes_out = document.createTextNode(child_sa.bytes_out);
            cell_bytes_out.appendChild(bytes_out);
            child_row.appendChild(cell_bytes_out);

            var cell_packets_in = document.createElement("td");
            var packets_in = document.createTextNode(child_sa.packets_in);
            cell_packets_in.appendChild(packets_in);
            child_row.appendChild(cell_packets_in);

            var cell_packets_out = document.createElement("td");
            var packets_out = document.createTextNode(child_sa.packets_out);
            cell_packets_out.appendChild(packets_out);
            child_row.appendChild(cell_packets_out);

            var cell_button_child_sa = document.createElement("td");

            var form_child_sa = document.createElement("form");
            form_child_sa.id = "delete_sa_form_" + id;
            form_child_sa.action = "/server_connections/delete_sa/";

            var csrf_token_child_sas = document.createElement("input");
            csrf_token_child_sas.name = "csrfmiddlewaretoken";
            csrf_token_child_sas.value = getCookie('csrftoken');
            csrf_token_child_sas.type = "hidden";
            form_child_sa.appendChild(csrf_token_child_sas);

            var child_sa_id = document.createElement("input");
            child_sa_id.name = "sa_id";
            child_sa_id.value = id;
            child_sa_id.type = "hidden";
            form_child_sa.appendChild(child_sa_id);

            var div_child_sa = document.createElement("div");
            div_child_sa.id = "delete_child_sa_" + id;

            var delete_child_sa_button = document.createElement("button");
            delete_child_sa_button.type = 'button';
            delete_child_sa_button.className = 'btn btn-danger';
            delete_child_sa_button.innerHTML = "delete";

            div_child_sa.appendChild(delete_child_sa_button);
            form_child_sa.appendChild(child_sa_id);
            form_child_sa.appendChild(div_child_sa);
            cell_button_child_sa.appendChild(form_child_sa);
            child_row.appendChild(cell_button_child_sa);

            table.appendChild(child_row);
        }

        cell_child_sas.appendChild(table);

        child_sas_row.appendChild(cell_child_sas);

        sas.appendChild(child_sas_row);
    }
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length,c.length);
        }
    }
    return "";
}