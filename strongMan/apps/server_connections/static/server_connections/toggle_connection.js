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
    var button = $('#button_div' + connectionId);
    button.find('.toggle-on').text("On");
    button.find('.toggle-on').attr("class", "btn btn-success toggle-on");
    button.find('.toggle').attr("class", 'toggle btn btn-success');
}

function stateDown(connectionId) {
    $('#toggle_input' + connectionId).prop('checked', false).change();
    var button = $('#button_div' + connectionId);
    button.find('.toggle-off').text("Off");
    $('#toggle_connection' + connectionId).prop('checked', false).change();
    button.find('.toggle').attr("class", 'toggle btn btn-default off');
}

function stateConnecting(connectionId) {
    var button = $('#button_div' + connectionId);
    button.find('.toggle-on').text("");
    button.find('.toggle-on').append("<i class='glyphicon glyphicon-refresh spinning'></i>");
    button.find('.toggle-on').attr("class", "btn btn-warning toggle-on");
    button.find('.toggle').attr("class", 'toggle btn btn-warning');
    $('#toggle_input' + connectionId).prop('checked', true).change();
    lock(connectionId);
}

function stateLoaded(connectionId) {
    var button = $('#button_div' + connectionId);
    button.find('.toggle-on').text("Loaded");
    button.find('.toggle-on').attr("class", "btn btn-success toggle-on");
    button.find('.toggle').attr("class", 'toggle btn btn-success');
    $('#toggle_input' + connectionId).prop('checked', true).change();
}

function stateUnloaded(connectionId) {
    var button = $('#button_div' + connectionId);
    button.find('.toggle-off').text("Unloaded");
    $('#toggle_connection' + connectionId).prop('checked', false).change();
    button.find('.toggle').attr("class", 'toggle btn btn-default off');
    $('#toggle_input' + connectionId).prop('checked', false).change();
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
    var alert = $('#alert_' + response.id);
    alert.popover({title: "Warning!", content: response.message, placement: "left", trigger: 'focus', container: 'body'});
    alert.popover('show');
}

function setConnectionInfo(connectionId, csrf) {
    $.ajax({
        data: {'csrfmiddlewaretoken': csrf, 'id': connectionId},
        type: 'POST',
        url: '/server_connections/info/',
        success: function (response) {
            if (response.success && $('#filter-active-status').val()==="0") {
                fillConnectionInfo(connectionId, response.child);
            }
            setTimeout(function () {
                setConnectionInfo(connectionId, csrf)
            }, 10000);
        }
    });
}

function fillConnectionInfo(id, child) {
    fillInfos(id, Object.keys(child).length, child);
}

function showConnectionInfoRow(id, csrf) {
    setConnectionInfo(id, csrf);
    $('#connection-info-row-' + id).toggle(true);
    $('#connection-row-' + id).addClass("success");
    var btn = $('#collapse-btn-' + id);
    var btn_text = btn.children().slice(0);
    if (btn_text.hasClass("glyphicon-chevron-right")) {
        btn_text.removeClass("glyphicon-chevron-right");
        btn_text.addClass("glyphicon-chevron-down");
    }
}

function hideConnectionInfoRow(id) {
    $('#connection-info-row-' + id).toggle(false);
    $('#connection-row-' + id).removeClass("success");
    var btn = $('#collapse-btn-' + id);
    var btn_text = btn.children().slice(0);
    if (btn_text.hasClass("glyphicon-chevron-down")) {
        btn_text.removeClass("glyphicon-chevron-down");
        btn_text.addClass("glyphicon-chevron-right");
    }
}

function toggleConnectionInfoRow(id) {
    var row = $('#connection-info-row-' + id);
    var btn = $('#collapse-btn-' + id);
    var btn_text = btn.children().slice(0);
    if (btn_text.hasClass("glyphicon-chevron-right")) {
        btn_text.removeClass("glyphicon-chevron-right");
        btn_text.addClass("glyphicon-chevron-down");
    } else {
        btn_text.removeClass("glyphicon-chevron-down");
        btn_text.addClass("glyphicon-chevron-right");
    }
    row.toggle();
}

function fillInfos(conn_id, rows, child) {
    var sas = document.getElementById("connection-" + conn_id + "-sas");

    $("#connection-" + conn_id + "-sas tr").remove();

    for (var i = 0; i < rows; i++) {
        var id = child[i].uniqueid;

        var row = document.createElement("tr");

        var cell_remote_host = document.createElement("td");
        var remote_host = document.createTextNode(child[i].remote_host);
        cell_remote_host.appendChild(remote_host);
        row.appendChild(cell_remote_host);

        var cell_remote_id = document.createElement("td");
        var remote_id = document.createTextNode(child[i].remote_id);
        cell_remote_id.appendChild(remote_id);
        row.appendChild(cell_remote_id);

        var cell_button_terminate_sa = document.createElement("td");

        var form_terminate_sa = document.createElement("form");
        form_terminate_sa.id = id;
        form_terminate_sa.method = "POST";
        form_terminate_sa.action = "/server_connections/terminate_sa/";
        form_terminate_sa.className = "pull-right inline-class";
        form_terminate_sa.setAttribute("onSubmit", "return button_terminate_sa_clicked(this)");

        var csrf_token = document.createElement("input");
        csrf_token.name = "csrfmiddlewaretoken";
        csrf_token.value = getCookie('csrftoken');
        csrf_token.type = "hidden";
        form_terminate_sa.appendChild(csrf_token);

        var sa_id = document.createElement("input");
        sa_id.name = "sa_id";
        sa_id.value = id;
        sa_id.type = "hidden";
        form_terminate_sa.appendChild(sa_id);

        var connection_id = document.createElement("input");
        connection_id.name = "conn_id";
        connection_id.value = conn_id;
        connection_id.type = "hidden";
        form_terminate_sa.appendChild(connection_id);

        var span_terminate_sa = document.createElement("span");
        span_terminate_sa.title = "Terminate SA";

        var button_terminate_sa = document.createElement("button");
        button_terminate_sa.type = "submit";
        button_terminate_sa.className = "btn btn-default btn-sm";
        button_terminate_sa.id = "btn_terminate_sa_" + id;

        var glyphicon_remove = document.createElement("span");
        glyphicon_remove.className = "glyphicon glyphicon-remove";
        button_terminate_sa.appendChild(glyphicon_remove);

        var button_terminate_sa_text = document.createElement("span");
        button_terminate_sa_text.id = "btn_terminate_sa_text";
        button_terminate_sa.appendChild(button_terminate_sa_text);

        span_terminate_sa.appendChild(button_terminate_sa);
        form_terminate_sa.appendChild(span_terminate_sa);
        cell_button_terminate_sa.appendChild(form_terminate_sa);
        row.appendChild(cell_button_terminate_sa);
       

        //sa_scroll.appendChild(row);
        sas.appendChild(row);

        // CHILD SAS
        var child_sas = child[i].child_sas;
        var nr_of_children = Object.keys(child_sas).length;

        if (nr_of_children > 0) {

            var child_sas_row = document.createElement("tr");
            child_sas_row.id = "child_sas" + id;

            var cell_child_sas = document.createElement("td");
            cell_child_sas.className = "child-sa-cell";
            cell_child_sas.colSpan = "3";
            cell_child_sas.style = "padding-left: 34px; background-color: #dadfe8;";

            var table = document.createElement("table");
            table.className = "table-hover table-condensed table-responsive child-sa-table";
            table.style = "width: 100%;";

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
            var h_cell_install_time = document.createElement("th");
            var h_install_time = document.createTextNode("install time");
            h_cell_install_time.appendChild(h_install_time);
            child_sas_header_row.appendChild(h_cell_install_time);
            var h_cell_terminate_button = document.createElement("th");
            child_sas_header_row.appendChild(h_cell_terminate_button);

            table.appendChild(child_sas_header_row);


            var child_sas_body_row = document.createElement("tbody");

            for (var n = 0; n < nr_of_children; n++) {
                var child_sa = child_sas[n];

                var child_id = child_sa.uniqueid;

                var child_row = document.createElement("tr");

                var cell_remote_ts = document.createElement("td");
                cell_remote_ts.className = "child-sa-cell";
                var remote_ts = document.createTextNode(child_sa.remote_ts);
                cell_remote_ts.appendChild(remote_ts);
                child_row.appendChild(cell_remote_ts);

                var cell_local_ts = document.createElement("td");
                cell_local_ts.className = "child-sa-cell";
                var local_ts = document.createTextNode(child_sa.local_ts);
                cell_local_ts.appendChild(local_ts);
                child_row.appendChild(cell_local_ts);

                var cell_bytes_in = document.createElement("td");
                cell_bytes_in.className = "child-sa-cell";
                var bytes_in = document.createTextNode(child_sa.bytes_in);
                cell_bytes_in.appendChild(bytes_in);
                child_row.appendChild(cell_bytes_in);

                var cell_bytes_out = document.createElement("td");
                cell_bytes_out.className = "child-sa-cell";
                var bytes_out = document.createTextNode(child_sa.bytes_out);
                cell_bytes_out.appendChild(bytes_out);
                child_row.appendChild(cell_bytes_out);

                var cell_packets_in = document.createElement("td");
                cell_packets_in.className = "child-sa-cell";
                var packets_in = document.createTextNode(child_sa.packets_in);
                cell_packets_in.appendChild(packets_in);
                child_row.appendChild(cell_packets_in);

                var cell_packets_out = document.createElement("td");
                cell_packets_out.className = "child-sa-cell";
                var packets_out = document.createTextNode(child_sa.packets_out);
                cell_packets_out.appendChild(packets_out);
                child_row.appendChild(cell_packets_out);

                var cell_install_time = document.createElement("td");
                cell_install_time.className = "child-sa-cell";
                var install_time_seconds = child_sa.install_time;
                var time_stamp = new Date().getTime() - install_time_seconds * 1000;
                var time = new Date(time_stamp);

                var install_time = document.createTextNode(time.toLocaleTimeString());
                cell_install_time.appendChild(install_time);
                child_row.appendChild(cell_install_time);

                var cell_button_terminate_child_sa = document.createElement("td");
                cell_button_terminate_child_sa.className = "child-sa-cell";

                var form_terminate_child_sa = document.createElement("form");
                form_terminate_child_sa.id = child_id;
                form_terminate_child_sa.method = "POST";
                form_terminate_child_sa.action = "/server_connections/terminate_sa/";
                form_terminate_child_sa.className = "pull-right inline-class";
                form_terminate_child_sa.setAttribute("onSubmit", "return button_terminate_child_sa_clicked(this)");

                var csrf_token_child_sa = document.createElement("input");
                csrf_token_child_sa.name = "csrfmiddlewaretoken";
                csrf_token_child_sa.value = getCookie('csrftoken');
                csrf_token_child_sa.type = "hidden";
                form_terminate_child_sa.appendChild(csrf_token_child_sa);

                var child_sa_id = document.createElement("input");
                child_sa_id.name = "child_sa_id";
                child_sa_id.value = child_id;
                child_sa_id.type = "hidden";
                form_terminate_child_sa.appendChild(child_sa_id);

                var connection_id_child_sa = document.createElement("input");
                connection_id_child_sa.name = "conn_id";
                connection_id_child_sa.value = conn_id;
                connection_id_child_sa.type = "hidden";
                form_terminate_child_sa.appendChild(connection_id_child_sa);

                var span_terminate_child_sa = document.createElement("span");
                span_terminate_child_sa.title = "Terminate Child SA";

                var button_terminate_child_sa = document.createElement("button");
                button_terminate_child_sa.type = "submit";
                button_terminate_child_sa.className = "btn btn-default btn-sm";
                button_terminate_child_sa.id = "btn_terminate_child_sa_" + child_id;

                var glyphicon_remove_child_sa = document.createElement("span");
                glyphicon_remove_child_sa.className = "glyphicon glyphicon-remove";
                button_terminate_child_sa.appendChild(glyphicon_remove_child_sa);

                var button_terminate_child_sa_text = document.createElement("span");
                button_terminate_child_sa_text.id = "btn_terminate_child_sa_text";
                button_terminate_child_sa.appendChild(button_terminate_child_sa_text);

                span_terminate_child_sa.appendChild(button_terminate_child_sa);
                form_terminate_child_sa.appendChild(span_terminate_child_sa);
                cell_button_terminate_child_sa.appendChild(form_terminate_child_sa);
                child_row.appendChild(cell_button_terminate_child_sa);

                child_sas_body_row.appendChild(child_row);
                table.appendChild(child_sas_body_row);
            }
            cell_child_sas.appendChild(table);
            child_sas_row.appendChild(cell_child_sas);
            sas.appendChild(child_sas_row);
        }
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

button_terminate_sa_clicked = function button_terminate_sa_clicked(form) {
    var btn = $("#btn_terminate_sa_" + form.id);
    if (btn.hasClass('btn-default')) {
        btn.removeClass('btn-default').addClass('btn-danger');
        btn.children('#btn_terminate_sa_text').text(' terminate');
        return false;
    } else {
        return true;
    }
};

button_terminate_child_sa_clicked = function button_terminate_child_sa_clicked(form) {
    var btn = $("#btn_terminate_child_sa_" + form.id);
    if (btn.hasClass('btn-default')) {
        btn.removeClass('btn-default').addClass('btn-danger');
        btn.children('#btn_terminate_child_sa_text').text(' terminate');
        return false;
    } else {
        return true;
    }
};
