  // CORS Proxy URL to bypass CORS policy
  const cors_proxy = 'https://corsproxy.io/';

/**
 * Function to display a toast message
 * @param {string} message - The message to display
 * @param {string} icon - The icon to display in the toast message
 * @param {number} duration - The duration to display the toast message
*/
function toast(message, icon = 'info', duration = 2000) {
  // Toast default configuration options
  const toast = Swal.mixin({
    // SweetAlert2 type of toast
    toast: true,
    // Position of the toast message
    position: 'top-end',
    // Has an animation
    animation: true,
    // don't show a close button
    showConfirmButton: false,
    // Timer to close the toast message
    timer: duration,
    // Show a progress bar
    timerProgressBar: true,
    // Custom class for the toast message
    didOpen: (toast) => {
      // Pause the timer when the mouse enters the toast
      toast.addEventListener('mouseenter', Swal.stopTimer)
      // Resume the timer when the mouse leaves the toast
      toast.addEventListener('mouseleave', Swal.resumeTimer)
      // Close the toast when clicked
      toast.addEventListener('click', Swal.close)
    }
  });

  // Display the toast message
  toast.fire({
    // The icon to display in the toast message
    icon: icon,
    // The title of the toast message
    title: message
  });
}

/**
 * Function to load the calling codes for the phone number country code
 */
function loadCallingCodes() {
  // Get the country select dropdown element
  const $country_dropdown = $('#phone_code');
  $country_dropdown.append(`<option value="">Select Country</option>`);
  // Countries API URL
  const countries_api = 'https://www.apicountries.com/countries';
  // Encode the countries API URL
  const encoded_url = encodeURIComponent(countries_api);

  // Fetch the countries API data
  $.ajax({
    url: `${cors_proxy}?url=${encoded_url}`,
    type: 'GET',
    // on success, add the countries to the dropdown
    success: function (data) {
      data.forEach((country) => {
        const $option = $(`<option></option>`);
        $option.val(`+${country.callingCodes[0]}`);
        $option.text(`${country.name} (+${country.callingCodes[0]})`);
        $country_dropdown.append($option);
      });
      $phone_code_data = $country_dropdown.data('user-code');
      if ($phone_code_data) {
        $country_dropdown.val($phone_code_data);
      }
    },
    // on error, add the default country to the dropdown
    error: function (error) {
      const $option = $(`<option></option>`);
      $option.val('+964');
      $option.text(`Iraq (+964)`);
      $country_dropdown.append($option);

      // Log the error to the console
      console.error('Fetch Error: ', error);
    }
  });
}

// Function to start the timer
function verificationTimer() {
  const $updateEmailBtn = $('#updateEmail');
  const $resendCodeBtn = $('#resendCode');
  const $sendOTPBtn = $('#sendOTP');
  const $resendOTP = $('#resendOTP');

  // Check if there's a timer in localStorage
  const timerEnd = localStorage.getItem('timerEnd');
  if (timerEnd) {
    let timeLeft = Math.ceil((timerEnd - Date.now()) / 1000);
    if (timeLeft > 0) {
      // Disable the button
      $resendCodeBtn.prop('disabled', true);
      $sendOTPBtn.prop('disabled', true);
      const timer = setInterval(() => {
        // Update the button text
        $resendCodeBtn.text(`Resend code in ${timeLeft} seconds`);
        $sendOTPBtn.text(`${timeLeft} seconds`);
        $resendOTP.text(`${timeLeft}`);
        // Decrement the time left
        timeLeft--;

        // If the time left is less than 0
        if (timeLeft < 0) {
          // Clear the timer
          clearInterval(timer);
          // Enable the button
          $resendCodeBtn.prop('disabled', false);
          // Reset the button text
          $resendCodeBtn.text('Resend code');
          $updateEmailBtn.prop('disabled', false);
          // Reset the button text
          $sendOTPBtn.text('Send OTP');
          $sendOTPBtn.prop('disabled', false);
          $resendOTP.prop('disabled', false);
          $resendOTP.text('Resend');
          // Remove the timer from localStorage
          localStorage.removeItem('timerEnd');
        }
      }, 1000);
    }
  }
}

// Function to set the timer
function setVerificationTimer(duration, button) {
      // Set the timer end time
      const timeLeft = duration;
      const timerEnd = Date.now() + timeLeft * 1000;
      localStorage.setItem('timerEnd', timerEnd);

      if (button != null)
        button.prop('disabled', true);

      // Start the timer
      verificationTimer();
}

// Sidebar toggle
function sideBarToggle() {
  // Get the sidebar toggle button
  const $sidebarToggle = $('.toggle-sidebar-btn');

  if (!$sidebarToggle.length) {
    return;
  }

  // Get the body element
  const $body = $('body');
  // Handle click event
  $sidebarToggle.on('click', function (e) {
    // Toggle the sidebar class
    $body.toggleClass('toggle-sidebar');
  });
}

// Scroll to top button
function scrollListener() {
  // Get the scroll to top button
  const $scrollBtn = $('.back-to-top');

  if (!$scrollBtn.length) {
    return;
  }

  // Handle scroll event
  $(window).on('scroll', function () {
    // If the scroll is greater than 100, show the button else hide it
    if ($(this).scrollTop() > 100) {
      $scrollBtn.toggleClass('active', true);
    } else {
      $scrollBtn.toggleClass('active', false);
    }
  });

  // Handle click event to scroll to top
  $scrollBtn.on('click', function (e) {
    // Prevent the default behavior
    e.preventDefault();
    // Scroll to the top of the page
    $('html, body').animate({ scrollTop: 0 }, 0);
  });
}

// Form validation
function formValidation() {
  const $needsValidation = $('.needs-validation');

  if (!$needsValidation.length) {
    return;
  }

  $needsValidation.each(function () {
    $(this).on('submit', function (e) {
      if (this.checkValidity() === false) {
        e.preventDefault();
        e.stopPropagation();
      }

      $(this).addClass('was-validated');
    });
  });
}

// Enable Bootstrap tooltips
function enableBSTooltips() {
  // Enable Bootstrap tooltips
  $('[data-bs-toggle-tt="tooltip"]').tooltip();

  // Enable Bootstrap Tooltips with HTML
  $('[data-bs-toggle-tt="tooltip-html"]').tooltip({
    html: true,
    // Prevent hiding on hover
    trigger: 'manual'
  }).on('mouseenter', function () {
    const _this = this;
    $(this).tooltip('show');
    $('.tooltip').on('mouseleave', function () {
      $(_this).tooltip('hide');
    });
  }).on('mouseleave', function () {
    const _this = this;
    setTimeout(function () {
      if (!$('.tooltip:hover').length) {
        $(_this).tooltip('hide');
      }
    }, 1500);
  });
}

function goBack() {
  window.history.back();
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Initialize the app
function init() {
  // Load the calling codes
  $(loadCallingCodes);
  // Update email
  $(changeEmail);
  // Sidebar toggle
  $(sideBarToggle);
  // Scroll listener
  $(scrollListener);
  // Resend code
  $(resendCode);
  // Form validation
  $(formValidation);
  // Enable Bootstrap tooltips
  $(enableBSTooltips);
}

// Initialize the app
$(init);