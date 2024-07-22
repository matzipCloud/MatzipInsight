document.querySelectorAll('.sort-buttons button').forEach(button => {
    button.addEventListener('click', function() {
        document.querySelectorAll('.sort-buttons button').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
    });
});