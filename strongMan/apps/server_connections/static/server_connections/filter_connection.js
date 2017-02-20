$(document).ready(function() {

    function rememberVisible (obj) {
        obj.removeClass('notVisible');
        if(obj.css('display') == 'none') {
            obj.addClass('notVisible');
        }
    }

    function triggerAllFilter () {
        $('#remoteTsFilter').trigger('click');
        $('#localTsFilter').trigger('click');
        $('#remoteHostFilter').trigger('click');
        $('#remoteIdFilter').trigger('click');
    }

    function initAllFilter (){
        $('.child-sa-table').filterTable({
            inputSelector: $('#remoteTsFilter'),
            ignoreColumns: [1,2,3,4,5,6],
            minRows: 0,
            highlightClass: 'child-alt1',
            visibleClass: 'visible1',
            callback: function(term, table) {
                if (term.length>0) {
                    table.find('tr').not('.visible1').parent().closest('tr').hide().prev().hide();
                    table.find('.visible1.visible2').parent().closest('tr').prev('.visible3.visible4').show().next().show();
                } else {
                    table.find('.visible2').parent().closest('tr').prev('.visible3.visible4').show().next().show();
                }
            }
        }).filterTable({
            inputSelector: $('#localTsFilter'),
            ignoreColumns: [0,2,3,4,5,6],
            minRows: 0,
            highlightClass: 'child-alt2',
            visibleClass: 'visible2',
            callback: function(term, table) {
                if (term.length>0) {
                    table.find('tr').not('.visible2').parent().closest('tr').hide().prev().hide();
                    table.find('.visible2.visible1').parent().closest('tr').prev('.visible3.visible4').show().next().show();
                } else {
                    table.find('.visible1').parent().closest('tr').prev('.visible3.visible4').show().next().show();
                }
            }
        });
        $('.sa-table').filterTable({
            inputSelector: $('#remoteHostFilter'),
            ignoreColumns: [1,2],
            ignoreClass: 'child-sa-cell',
            highlightClass: 'alt1',
            visibleClass: 'visible3',
            minRows: 0,
            callback: function(term, table) {
                table.find('.notVisible').hide();
                table.children('tbody').children().not('.visible3.visible4').hide();
                table.find('tbody').children('.visible3.visible4').next().show().find('tr').show();
                if ( $('#remoteTsFilter').val().length>0 ) {
                    table.find('.child-sa-table').find("tr:not(.visible1)").parent().closest('tr').hide().prev().hide();
                }
                if ( $('#localTsFilter').val().length>0 ) {
                    table.find('.child-sa-table').find("tr:not(.visible2)").parent().closest('tr').hide().prev().hide();
                }
            }
        }).filterTable({
            inputSelector: $('#remoteIdFilter'),
            ignoreColumns: [0,2],
            ignoreClass: 'child-sa-cell',
            highlightClass: 'alt2',
            visibleClass: 'visible4',
            minRows: 0,
            callback: function(term, table) {
                table.find('.notVisible').hide();
                table.children('tbody').children().not('.visible3.visible4').hide();
                table.find('tbody').children('.visible3.visible4').next().show().find('tr').show();
                if ( $('#remoteTsFilter').val().length>0 ) {
                    table.find('.child-sa-table').find("tr:not(.visible1)").parent().closest('tr').hide().prev().hide();
                }
                if ( $('#localTsFilter').val().length>0 ) {
                    table.find('.child-sa-table').find("tr:not(.visible2)").parent().closest('tr').hide().prev().hide();
                }
            }
        });
    }

    function startFilter () {
        initAllFilter();
        triggerAllFilter();
        $('#remoteHostFilter, #remoteIdFilter, #remoteTsFilter, #localTsFilter').unbind();
    }

    $('.connection-info-row').each(function() {
        var that = $(this);
        rememberVisible(that);
        $(document).bind("ajaxComplete", function(){
            rememberVisible(that);
        });
    });

    $('#filter-btn').on("click", function(){
        $('#filter-active-status').val('1');
        startFilter();
    });

    $('#filter-clear').on("click", function(){
        $('#remoteHostFilter, #remoteIdFilter, #remoteTsFilter, #localTsFilter').val('');
        startFilter();
        $('#filter-active-status').val('0');
    });
});