$(function() {
    window.sock = new WebSocket('ws://l:7999/ws/');
    sock.onopen = function() {
        console.log('open');
    };
    sock.onmessage = function(e) {
        console.log('message', e.data);
        console.log(Date.now())
    };
    sock.onclose = function() {
        console.log('close');
    };
    $('form').submit(function(e) {
        e.preventDefault();
        console.log(Date.now())
        sock.send($('input').val())
        $('input').val('')
    })
})
