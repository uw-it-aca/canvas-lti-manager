/*jslint browser: true, plusplus: true, regexp: true */
/*global $, jQuery, Handlebars, moment */

(function ($) {
    "use strict";

    function draw_error(xhr) {
        var json;
        try {
            json = $.parseJSON(xhr.responseText);
            console.log('admin service error:' + json.error);
        } catch (e) {
            console.log('Unknown admin service error');
        }
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
    }

    function load_external_tools() {
        $.ajax({
            url: '/lti_manager/api/v1/external_tools',
            dataType: 'json',
            success: draw_external_tools,
            error: draw_error
        });
    }

    $(document).ready(function () {
        load_external_tools();
    });
}(jQuery));
