var currentmode;


function loadCurrentMode(){
    var element = document.getElementById('mode-switcher');
    currentmode = getCookie("currentmode");
    var currentmodeWasNull = false;
    if (currentmode === null) {
        setCookie('currentmode',"",-1);
        setCookie('currentmode', 'server', 100);
        currentmode = 'server';
        currentmodeWasNull = true;
    }

    if (currentmode === 'server') {
        $(".server-mode").removeClass("visible-mode invisible-mode").addClass("visible-mode");
        $(".client-mode").removeClass("visible-mode invisible-mode").addClass("invisible-mode");
        element.innerHTML = 'Switch to Client mode';
    }
    else {
        $(".server-mode").removeClass("visible-mode invisible-mode").addClass("invisible-mode");
        $(".client-mode").removeClass("visible-mode invisible-mode").addClass("visible-mode");
        element.innerHTML = 'Switch to Server mode';
    }
    if(currentmodeWasNull){
        $(".one-time-alert").removeClass("hide-after-switch");
    }
    else{
        $(".one-time-alert").removeClass("hide-after-switch").addClass("hide-after-switch");
    }
}


function toggle_navbar_visibility() {

    var element = document.getElementById('mode-switcher');
    currentmode = getCookie("currentmode");

    if(currentmode === 'server'){
        $(".server-mode").removeClass("visible-mode invisible-mode").addClass("invisible-mode");
        $(".client-mode").removeClass("visible-mode invisible-mode").addClass("visible-mode");


        element.innerHTML = 'Switch to Server mode';
        setCookie('currentmode',"",-1);
        setCookie('currentmode', 'client', 100);
    }
    else {
        $(".server-mode").removeClass("visible-mode invisible-mode").addClass("visible-mode");
        $(".client-mode").removeClass("visible-mode invisible-mode").addClass("invisible-mode");
        element.innerHTML = 'Switch to Client mode';
        setCookie('currentmode',"",-1);
        setCookie('currentmode', 'server', 100);
    }
}
function setCookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}