$(function () {
    $('form').change(function () {
        $.ajax({
            type: "POST",
            url: "/connections/toggle/",
            data: data,
        });
    })
});