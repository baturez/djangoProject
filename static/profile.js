$(document).ready(function () {
    $('#profilePictureForm').submit(function (event) {
        event.preventDefault();

        let formData = new FormData(this);

        $.ajax({
            type: 'POST',
            url: "{% url 'upload_profile_picture' %}",
            data: formData,
            contentType: false,
            processData: false,
            success: function (response) {
                if (response.success) {
                    $('.profile-img img').attr('src', response.url);
                } else {
                    alert(response.error_message);
                }
            }
        });
    });
});


