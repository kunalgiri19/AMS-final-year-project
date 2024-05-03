/* Sidebar Expand*/
let btn = document.querySelector('#menubtn');
let sidebar = document.querySelector('.sidebar');
let navItems = document.querySelectorAll('.nav-item');

btn.addEventListener("click", function () {
    sidebar.classList.toggle('active');
    // Toggle display of nav items based on sidebar state
    navItems.forEach(item => {
        if (sidebar.classList.contains('active')) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
});


/* Toggle switch */
document.addEventListener("DOMContentLoaded", function () {
    const switchInput = document.getElementById("faceRecognitionSwitch");

    // Fetch the initial access status from the server and update the toggle switch
    fetch('/check_access')
        .then(response => response.json())
        .then(data => {
            var accessGranted = data.accessGranted;
            switchInput.checked = accessGranted;

            // Store switch state in local storage
            localStorage.setItem('accessGranted', accessGranted);
        })
        .catch(error => {
            console.error('Error fetching initial access state: ', error);
        });

    // Add event listener for switch toggle
    switchInput.addEventListener("change", function () {
        const accessGranted = this.checked;

        // Store switch state in local storage
        localStorage.setItem('accessGranted', accessGranted);

        // Update access status on the server
        fetch('/toggle_access', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ accessGranted }),
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
            })
            .catch(error => {
                console.error('Error toggling access: ', error);
            });
    });
});



/* Sidebar divs */

function showContent(id) {
    var elements = document.getElementsByClassName('container');
    for (var i = 0; i < elements.length; i++) {
        elements[i].style.display = 'none';
    }
    document.getElementById(id).style.display = 'block';
}

/* dropdown toggle profile */
function toggleDropdown(event) {
    var dropdownContent = document.getElementById("dropdownContent");
    dropdownContent.classList.toggle("show");
    event.stopPropagation(); // Prevent the click event from propagating to the window
}

// Close the dropdown menu if the user clicks outside of it
window.addEventListener("click", function (event) {
    var dropdownContent = document.getElementById("dropdownContent");
    var userDropdown = document.querySelector('.user-dropdown');
    if (!userDropdown.contains(event.target)) { // Close dropdown if the click is not within the user-dropdown
        dropdownContent.classList.remove("show");
    }
});

/* slideToggle */
$(document).ready(function () {

    // Toggle content slide
    $(".slidetoggle").click(function () {
        $(".content").slideToggle("slow");
    });
});



/* Filter */
function filterAttendance() {
    var filterStatus = document.getElementById("filterStatus").value;
    var filterName = document.getElementById("filterName").value;
    var filterDate = document.getElementById("filterDate").value;
    var rows = document.getElementsByClassName("attendance-row");

    for (var i = 0; i < rows.length; i++) {
        var name = rows[i].getElementsByTagName("td")[0].innerText; // Name is in the 1st column
        var date = rows[i].getElementsByTagName("td")[1].innerText; // Date is in the 2nd column
        var status = rows[i].getElementsByTagName("td")[3].innerText; // Status is in the 4th column
        
        var statusMatch = (filterStatus === "all" || status.toLowerCase() === filterStatus.toLowerCase());
        var nameMatch = (filterName === "all" || name === filterName);
        var dateMatch = (filterDate === "all" || date === filterDate);

        if (statusMatch && nameMatch && dateMatch) {
            rows[i].style.display = "";
        } else {
            rows[i].style.display = "none";
        }
    }
}

