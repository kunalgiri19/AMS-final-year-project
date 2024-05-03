document.addEventListener("DOMContentLoaded", function() {
  // Get the dropdown element
  var monthSelect = document.getElementById("month-select");

  // Check if the selected month is stored in localStorage
  var storedMonth = localStorage.getItem("selectedMonth");

  // Set the default selected month to the stored value or the current month if no value is stored
  var currentMonth = new Date().getMonth() + 1; // JavaScript months are zero-indexed
  monthSelect.value = storedMonth || currentMonth;

  // Add event listener to detect changes in the dropdown
  monthSelect.addEventListener("change", function() {
      // Get the selected month value
      var selectedMonth = this.value;

      // Store the selected month value in localStorage
      localStorage.setItem("selectedMonth", selectedMonth);

      // Redirect to the same page with the selected month as a query parameter
      window.location.href = "/user?month=" + selectedMonth;
  });
});


//lol
let btn = document.querySelector('#btn');
let sidebar = document.querySelector('.sidebar');
btn.addEventListener("click", function () {
  sidebar.classList.toggle('active');
});

function showContent(id) {
  var elements = document.getElementsByClassName('container');
  for (var i = 0; i < elements.length; i++) {
    elements[i].style.display = 'none';
  }
  document.getElementById(id).style.display = 'block';
}

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



/* Check_access */
document.addEventListener('DOMContentLoaded', function () {
  const errorBox = document.querySelector('.error');
  const errorTitle = document.querySelector('.error__title');
  const errorClose = document.querySelector('.error__close');
  const toggleButton = document.getElementById('toggleButton');

  errorClose.addEventListener('click', function () {
    errorBox.classList.remove('show'); // Remove the 'show' class to hide the error box
  });

  toggleButton.addEventListener('click', function () {
    // Check access status
    fetch('/check_access')
      .then(response => response.json())
      .then(data => {
        if (data.accessGranted === true) {
          // Access granted, redirect to face recognition page
          window.location.href = '/video';
        } else {
          // Access denied, show error message
          errorTitle.textContent = "Access to face recognition is disabled.";
          errorBox.classList.add('show');
        }
      })
      .catch(error => {
        console.error('Error checking access: ', error);
      });
  });
});

/* clock */
function startTime() {
  var today = new Date();
  var hr = today.getHours();
  var min = today.getMinutes();
  var sec = today.getSeconds();
  ap = (hr < 12) ? "<span>AM</span>" : "<span>PM</span>";
  hr = (hr == 0) ? 12 : hr;
  hr = (hr > 12) ? hr - 12 : hr;
  //Add a zero in front of numbers<10
  hr = checkTime(hr);
  min = checkTime(min);
  sec = checkTime(sec);
  document.getElementById("clock").innerHTML = hr + ":" + min + ":" + sec + " " + ap;

  var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var curWeekDay = days[today.getDay()];
  var curDay = today.getDate();
  var curMonth = months[today.getMonth()];
  var curYear = today.getFullYear();
  var date = curWeekDay + ", " + curDay + " " + curMonth + " " + curYear;
  document.getElementById("date").innerHTML = date;

  var time = setTimeout(function () { startTime() }, 500);
}
function checkTime(i) {
  if (i < 10) {
    i = "0" + i;
  }
  return i;
}
startTime();

/* attendance percentage */
fetch('/attendance_percentage')
.then(response => response.json())
.then(data => {
    const months = Object.keys(data.attendance_percentage);
    months.forEach(month => {
        const barContainer = document.getElementById(month.toLowerCase());
        const attendancePercentage = data.attendance_percentage[month];
        const bar = barContainer.querySelector('.bar');
        bar.style.height = `${attendancePercentage}%`;
    });
})
.catch(error => console.error('Error fetching attendance percentages:', error));

