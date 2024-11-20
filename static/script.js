document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("loginButton").addEventListener("click", function(event) {
        event.preventDefault();
        validateForm();
    });
});

function validateForm() {
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;
    
    // Kullanıcı adı ve şifre boş mu kontrolü
    if (username === "" || password === "") {
        alert("Kullanıcı adı ve şifre alanları doldurulmalıdır.");
    } else {
        // Formu sunucuya gönder
        document.querySelector('.login-form').submit();
    }
}

if (document.querySelector('.alert.alert-danger')) {
    alert("Kullanıcı adı veya şifre hatalı!");
}
