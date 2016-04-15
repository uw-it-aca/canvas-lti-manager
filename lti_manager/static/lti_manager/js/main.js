/*jslint browser: true, plusplus: true, regexp: true */
/*global $, jQuery, Handlebars, moment */

(function ($) {
    "use strict";

    $.ajaxSetup({
        headers: { "X-CSRFToken": $('input[name="csrfmiddlewaretoken"]').val() }
    });

    function draw_error(xhr) {
        var json;
        try {
            json = $.parseJSON(xhr.responseText);
            console.log('admin service error:' + json.error);
        } catch (e) {
            console.log('Unknown admin service error');
        }
    }

    function gather_form_data() {
        var data = {
            'name': $('#et-name-input').val(),
            'account_id': $('#et-account-input').val(),
            'config': $('#et-config-input').val(),
        };

        return {'external_tool': data};
    }

    function add_external_tool() {
        var json_data = gather_form_data();
        $.ajax({
            url: '/lti_manager/api/v1/external_tool/',
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify(json_data), 
            success: load_external_tools,
            error: draw_error
        });
    }

    function draw_add_external_tool() {
        var tpl = Handlebars.compile($('#tool-editor').html()),
            data = {};

        $('#external-tool-editor').html(tpl(data)).modal({
            backdrop: 'static',
            show: true
        });
        $('.save-btn').click(add_external_tool);
    }

    function draw_external_tools(data) {
        var tpl = Handlebars.compile($('#tool-table-row').html());

        $('#external-tools-table tbody').html(tpl(data));
        $('#external-tools-table').dataTable({
            'aaSorting': [[ 0, 'asc' ]],
            'bPaginate': false,
            'searching': false,
            'bScrollCollapse': true
        });
        $('.add-external-tool-btn').click(draw_add_external_tool);
    }

    function load_external_tools() {
        $.ajax({
            url: '/lti_manager/api/v1/external_tools',
            type: 'GET',
            dataType: 'json',
            success: draw_external_tools,
            error: draw_error
        });
    }

    $(document).ready(function () {
        load_external_tools();
    });
}(jQuery));
