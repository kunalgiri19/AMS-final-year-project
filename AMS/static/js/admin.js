
/* Sidebar */
let btn = document.querySelector('#btn');
let sidebar = document.querySelector('.sidebar');
btn.addEventListener("click", function () {
  sidebar.classList.toggle('active');
});

/* Sidebar divs */
const currentUrl = window.location.href;
const sidebarLinks = document.querySelectorAll('.sidebar ul li a');
sidebarLinks.forEach(link => {
  const href = link.getAttribute('href');
  if (currentUrl.includes(href)) {
    link.parentNode.classList.add('active');
  }
});

function showContent(id) {
  var elements = document.getElementsByClassName('container');
  for (var i = 0; i < elements.length; i++) {
    elements[i].style.display = 'none';
  }
  document.getElementById(id).style.display = 'block';
}

/* slideToggle */
$(document).ready(function () {

  // Toggle content slide
  $(".slidetoggle").click(function () {
    $(".content").slideToggle("slow");
  });
});

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