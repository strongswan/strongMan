jQuery(function($) {
    var $remove_btns = $('button.remove-btn');
    $remove_btns.each(function () {
        var $btn = $(this);
        var $form = $btn.closest('form');

        var $submitter = null;
        $form.submit(function (form) {
            if ($submitter && $submitter[0] == $btn[0] && $btn.hasClass('btn-default')) {
                $btn.removeClass('btn-default').addClass('btn-danger');
                $btn.find('.removebtn-text').text('Are you sure?');
                return false;
            } else {
                return true;
            }
        });
        $form.find('button[type=submit]').click(function () {
            $submitter = $(this);
        });
    });
});
