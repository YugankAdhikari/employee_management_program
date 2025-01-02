$(document).ready(function() {
    // Check for saved theme preference in localStorage
    if (localStorage.getItem('theme') === 'dark') {
        $('body').addClass('dark-mode');
        $('#theme-toggle').text('☀️'); // Change text to sun icon
    }

    // Toggle theme on button click
    $('#theme-toggle').click(function() {
        $('body').toggleClass('dark-mode');
        if ($('body').hasClass('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            $(this).text('☀️'); // Change text to sun icon
        } else {
            localStorage.setItem('theme', 'light');
            $(this).text('🌙'); // Change text to moon icon
        }
    });
});