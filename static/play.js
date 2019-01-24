// hints popover
$(function() {
    $('[data-toggle="popover"]').popover()
})

var q = $('#question').data("value");

// answer validation
$('form[id=answer]').submit(function(event) {
    if ($("input:first").val() === q) {
        $("#validate").text("Well done!").show();
        return;
    }

    $("#validate").text("Try again!").show();
    event.preventDefault();
});

// main page random words animation
// oryginal by Amit Rogye https://codepen.io/cooljockey/pen/uyeHz
$(document).ready(function() {
    animateDiv('.a');
    animateDiv('.b');
    animateDiv('.c');
    animateDiv('.d');
    animateDiv('.e');
});

function makeNewPosition() {
    var h = $(window).height() - 50;
    var w = $(window).width() - 50;

    var nh = Math.floor(Math.random() * h);
    var nw = Math.floor(Math.random() * w);

    return [nh, nw];

}

function animateDiv(myclass) {
    var newq = makeNewPosition();
    $(myclass).animate({ top: newq[0], left: newq[1] }, 10000, function() {
        animateDiv(myclass);
    });

}