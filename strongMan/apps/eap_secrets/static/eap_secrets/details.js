function removeBtnClicked(form) {
    jform = $(form);
    btn = jform.find('.remove-btn');
    if (btn.hasClass('btn-default')) {
        btn.removeClass('btn-default').addClass('btn-danger');
        btn.find('.removebtn-text').text('Are you sure?');
        return false;
    } else {
        return true;
    }
}
