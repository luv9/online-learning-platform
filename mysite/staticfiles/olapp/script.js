// script.js
document.addEventListener("DOMContentLoaded", function () {
    // Function to toggle the visibility of the description when the (i) button is clicked
    function toggleDescription(buttonId, descriptionId) {
      const button = document.getElementById(buttonId);
      const description = document.getElementById(descriptionId);
      button.addEventListener("click", function () {
        description.classList.toggle("hidden");
      });
    }
  
    // Call the function for the username (i) button
    toggleDescription("username-rules-btn", "username-rules");
  
    // Call the function for the password (i) button
    toggleDescription("password-rules-btn", "password-rules");
  });