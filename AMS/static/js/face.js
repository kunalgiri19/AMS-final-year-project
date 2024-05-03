document.addEventListener('DOMContentLoaded', function () {
    const video = document.getElementById('video');

    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: {} })
            .then(function (stream) {
                video.srcObject = stream;

                // Periodically capture and recognize faces
                setInterval(captureAndRecognize, 5000);  // Adjust the interval as needed
            })
            .catch(function (err) {
                console.error("Error accessing webcam: ", err);
            });
    }

    function captureAndRecognize() {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');

        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataUrl = canvas.toDataURL('image/jpeg');

        // Send the captured image to the server for recognition
        fetch('/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageDataUrl }),
        })
            .then(response => response.json())
                .then(data => {
                    console.log(data);
                    if (data.status === 'success') {
                        alert(data.message);
                        window.location.href = data.redirect_url;
                    }
                })
            .catch(error => {
                console.error('Error capturing and recognizing face: ', error);
            });
    }
});

function showContent(id) {
    var elements = document.getElementsByClassName('container');
    for (var i = 0; i < elements.length; i++) {
      elements[i].style.display = 'none';
    }
    document.getElementById(id).style.display = 'block';
}

/* Login access */
// Add an event listener for the switch toggle
document.getElementById("faceRecognitionSwitch").addEventListener("change", function() {
    var accessGranted = this.checked;
    // Store the state in local storage
    localStorage.setItem('accessGranted', accessGranted);
    // Send AJAX request to update access status
    fetch('/toggle_access', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ accessGranted: accessGranted }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        if (!accessGranted) {
            // If access is denied, stop the camera
            stopCamera();
        }
    })
    .catch(error => {
        console.error('Error toggling access: ', error);
    });
});

// Function to stop the webcam stream
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(function(track) {
            track.stop();
        });
        stream = null; // Reset the stream variable
    }
}

// Check if access was previously granted and update the toggle button
document.addEventListener("DOMContentLoaded", function() {
    // Fetch the initial state from the server
    fetch('/check_access')
        .then(response => response.json())
        .then(data => {
            var accessGranted = data.accessGranted;
            if (accessGranted === true) {
                document.getElementById("faceRecognitionSwitch").checked = true;
            }
        })
        .catch(error => {
            console.error('Error fetching initial access state: ', error);
        });
});


function toggleDropdown(event) {
    var dropdownContent = document.getElementById("dropdownContent");
    dropdownContent.classList.toggle("show");
    event.stopPropagation(); // Prevent the click event from propagating to the window
}

// Close the dropdown menu if the user clicks outside of it
window.addEventListener("click", function (event) {
    var dropdownContent = document.getElementById("dropdownContent");
    var userDropdown = document.querySelector('.user-dropdown');
    if (!userDropdown.contains(event.target)) {
        // Check if the click is not within the dropdown or user-dropdown
        dropdownContent.classList.remove("show");
    }
});


//error box
    const errorBox = document.querySelector('.error');
    const errorTitle = document.querySelector('.error__title');
    const errorClose = document.querySelector('.error__close');
  
    errorClose.addEventListener('click', function () {
      errorBox.classList.remove('show'); // Remove the 'show' class to hide the error box
    });