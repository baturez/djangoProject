 $(document).ready(function() {
        $('#profilePictureForm').submit(function(event) {
            event.preventDefault(); // Prevent form submission

            let formData = new FormData(this);

            $.ajax({
                type: 'POST',
                url: "{% url 'upload_profile_picture' %}",
                data: formData,
                contentType: false, // Tell jQuery not to set contentType
                processData: false, // Tell jQuery not to process data
                success: function(response) {
                    if (response.success) {
                        $('.profile-img img').attr('src', response.url); // Update image source
                    } else {
                        alert(response.error_message);
                    }
                }
            });
        });
    });