// Login function
function loginFunction() {
  // Get the login form
  const $loginForm = $("#loginForm");

  if ($loginForm.length === 0) return;

  // Handle form submit
  $loginForm.on("submit", function (e) {
    e.preventDefault();
    // Get the email and password values
    const $username = $("#username").val();
    const $password = $("#password").val();
    const $remember = $("#remember").is(":checked");
    const $btn = $("#loginBtn");

    // Disable the button
    $btn.prop("disabled", true);
    // Show loading state
    $btn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...`
    );

    authenticate($username, $password, $remember)
      .then((response) => {
        // Display a success message
        toast("Logged in", "success");
        // Redirect to the profile page
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1000);
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Login");
      });
  });
}

function logoutFunction() {
  const $logoutBtn = $("#logoutBtn");

  if ($logoutBtn.length === 0) return;

  $logoutBtn.on("click", function (e) {
    e.preventDefault();

    logout()
      .then((response) => {
        // Clear Gravatar cache
        localStorage.removeItem("gravatar_cache");

        // Display a success message
        toast(response.message, "success");

        // Redirect to login
        setTimeout(() => {
          window.location.href = "/login";
        }, 1000);
      })
      .catch((error) => {
        const error_message = error.message ? error.message : "An error occurred";
        toast(error_message, "error");
      });
  });
}

function registerFunction() {
  // Get the register form
  const $registerForm = $("#registerForm");

  if ($registerForm.length === 0) return;

  // Handle form submit
  $registerForm.on("submit", function (e) {
    e.preventDefault();
    // Get the form values
    const $first_name = $("#first_name").val();
    const $last_name = $("#last_name").val();
    const $email = $("#email").val();
    const $username = $("#username").val();
    const $password = $("#password").val();
    const $phone_code = $("#phone_code").val();
    const $phone = $("#phone").val();
    const $terms = $("#acceptTerms").is(":checked");
    const $privacy = $("#acceptPrivacy").is(":checked");
    const $btn = $("#registerBtn");

    // Disable the button
    $btn.prop("disabled", true);
    // Show loading state
    $btn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...`
    );
    register(
      $username,
      $email,
      $first_name,
      $last_name,
      $phone_code,
      $phone,
      $password,
      $terms,
      $privacy
    )
      .then((response) => {
        // Display a success message
        toast("Registered", "success");
        // Redirect to the login page
        setTimeout(() => {
          window.location.href = "/verify";
        }, 1000);
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Register");
      });
  });
}

function resendCode() {
  verificationTimer();
  // Get the resend code button
  const $resendCodeBtn = $("#resendCode");

  if ($resendCodeBtn.length === 0) return;

  // Handle click event
  $resendCodeBtn.on("click", function (e) {
    e.preventDefault();

    $resendCodeBtn.prop("disabled", true);
    $resendCodeBtn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Resending...`
    );

    // Resend the verification code
    resendVerificationEmail()
      .then((response) => {
        toast(response, "success");
        setVerificationTimer(60, $resendCodeBtn);
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        $resendCodeBtn.prop("disabled", false);
        $resendCodeBtn.html("Resend code");
      });
  });
}

/**
 * Function to verify the digit code
 */
function digitVerification() {
  $(document).ready(function () {
    // Get all the input fields
    const $inputs = $(".code-input");

    if ($inputs.length === 0) return;

    // Handle keydown events
    $inputs.on("keydown", function (e) {
      // Get the current input field
      const $this = $(this);
      // Get the previous input field
      const $prev = $this.prev();

      // Handle backspace
      if (e.key === "Backspace" && $this.val() === "") {
        // Focus on the previous input field
        $prev.focus();
      }
    });

    // Handle paste events
    $inputs.on("paste", function (e) {
      // Prevent the default paste behavior
      e.preventDefault();
      // Get the current input field
      let $this = $(this);
      // Get the pasted content
      const paste = (e.originalEvent.clipboardData || e.clipboardData).getData(
        "text"
      );
      // Split the pasted content into an array
      const pasteArray = paste.split("");

      // Loop through the pasted content and fill inputs
      for (let i = 0; i < pasteArray.length; i++) {
        // Fill the input field
        $this.val(pasteArray[i]);
        // Move to the next input field
        $this = $this.next();

        // Stop if there are no more inputs
        if (!$this.length) {
          // Stop the loop
          break;
        }
      }
      // Focus on the last input field
      $inputs.last().focus();
    });

    // Handle input fields (auto move to next on input)
    $inputs.on("input", function () {
      // Get the current input field
      const $this = $(this);
      // Get the next input field
      const $next = $this.next();
      // Move to the next input field
      if ($this.val() !== "") {
        // Focus on the next input field
        $next.focus();
      }
    });

    // Handle focus event to auto-select text
    $inputs.on("focus", function () {
      // Select the input field text
      $(this).select();
    });
  });
}

function digitCode() {
  const $inputs = $(".code-input");

  if ($inputs.length === 0) return;

  let code = "";

  // Concatenate all the input values
  $inputs.each(function () {
    code += $(this).val();
  });

  if (code.length === 6 && !isNaN(code)) return code;

  // Clear the input fields
  $inputs.each(function () {
    $(this).val("");
  });

  // Focus on the first input field
  $inputs.first().focus();

  // Display an error message
  toast("invalid OTP", "error");

  // Return null if the code is invalid
  return null;
}

function verifyEmailFunction() {
  const $verifyForm = $("#verifyForm");

  if ($verifyForm.length === 0) return;

  const $submitBtn = $("#submitBtn");

  // Verify email
  $submitBtn.on("click", function (e) {
    e.preventDefault();
    // Get the code from the input fields
    const code = digitCode();

    verifyEmail(code)
      .then((response) => {
        // Display a success message
        toast("Email verified", "success");
        // Redirect to the profile page
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1000);
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
      });
  });
}

function changeEmail() {
  const $updateEmailBtn = $("#updateEmail");
  const $email = $("#email");

  $updateEmailBtn.on("click", function (e) {
    // Check if there's a timer in localStorage
    const timerEnd = localStorage.getItem("timerEnd");
    if (timerEnd) {
      const timeLeft = Math.ceil((timerEnd - Date.now()) / 1000);
      if (timeLeft > 0) {
        toast(
          `Please wait for ${timeLeft} seconds before updating your email`,
          "warning"
        );
        // Start the timer
        verificationTimer();
        return;
      }
    }

    Swal.fire({
      title: "Update Email",
      html: `Current email: <strong>${$email.text()}</strong>`,
      input: "email",
      inputLabel: "New Email",
      inputPlaceholder: "Enter your new email address",
      showCancelButton: true,
      confirmButtonText: "Update",
      showLoaderOnConfirm: true,
      preConfirm: async (email) => {
        Swal.showLoading();
        try {
          const response = await updateEmail(email);
          Swal.hideLoading();
          toast("Email has been updated.", "success");
          $email.text(email);

          setVerificationTimer(60, null);

          return response;
        } catch (error) {
          Swal.hideLoading();
          console.error("Error: " + error);
          Swal.showValidationMessage(`Error: ${error}`);
          error_message = error.message ? error.message : "An error occurred";
          // Display an error message
          toast(error_message, "error");
          throw new Error(error);
        }
      },
    });
  });
}

function chatHistory() {
  const $chatHistory = $("#chatHistory");

  if ($chatHistory.length === 0) return;

  getChatHistory(50, 1).then((response) => {
    chats = response.items;
    $chatHistory.empty();
    chats.forEach(function (chat) {
      $chatHistory.append(`
            <span class="nav-item d-flex align-items-center retrieveEmail">
                <button class="nav-link collapsed flex-fill" data-chat-sent="${chat.is_sent}" data-chat-id="${chat.id}">
                  <i class="bi bi-chat"></i>
                  <span>${chat.name}</span>
                </button>
                <button class="btn btn-link float-right" type="button"
                data-bs-toggle="dropdown" aria-expanded="false" data-chat-id="${chat.id}">
                <i class="bi bi-three-dots"></i>
              </button>
              <ul class="dropdown-menu dropdown-menu-end dropdown-menu-arrow" aria-labelledby="chatDropdown">
                <li><button class="dropdown-item chatRename">
                    <i class="bi bi-pencil"></i> Rename
                  </button></li>
                <li><button class="dropdown-item chatDelete">
                    <i class="bi bi-trash"></i> Delete
                  </button></li>
              </ul>
            </span>
      `);
    });
  });
}

function chatRename() {
  const $chatHistory = $("#chatHistory");

  $chatHistory.on("click", ".chatRename", function (e) {
    e.preventDefault();
    const $chatId = $(this).closest("span").find("button").data("chat-id");
    const $chatName = $(this).closest("span").find("span").text();
    const $chatNameInput = $(
      `<input type="text" class="form-control" value="${$chatName}">`
    );
    $(this).closest("span").find("span").replaceWith($chatNameInput);
    $chatNameInput.focus();
    $chatNameInput.on("blur keypress", function (e) {
      if (e.type === "blur" || (e.type === "keypress" && e.which === 13)) {
        const $newChatName = $chatNameInput.val();
        updateChat($chatId, $newChatName)
          .then((response) => {
            toast("Chat renamed successfully.", "success");
            $(this).replaceWith(`<span>${$newChatName}</span>`);
            chatHistory();
          })
          .catch((error) => {
            toast("Error renaming chat. Please try again.", "error");
            $(this).replaceWith(`<span>${$chatName}</span>`);
          });
      }
    });
  });
}

function chatDelete() {
  const $chatHistory = $("#chatHistory");

  $chatHistory.on("click", ".chatDelete", function (e) {
    e.preventDefault();
    const $chatSpan = $(this).closest("span");
    const $chatId = $(this).closest("span").find("button").data("chat-id");

    Swal.fire({
      title: "Are you sure?",
      text: "You will not be able to recover this chat!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it!",
      cancelButtonText: "No, keep it",
    }).then((result) => {
      if (result.isConfirmed) {
        deleteChat($chatId)
          .then((response) => {
            toast("Chat deleted successfully.", "success");
            // If the chat is open, clear the chat box
            if ($("#chatId").val() == $chatId) {
              $("#chatBot").empty();
              $("#generatedSections").empty();
            }
            $chatSpan.remove();
          })
          .catch((error) => {
            toast("Error deleting chat. Please try again.", "error");
          });
      }
    });
  });
}

function openChat() {
  const $chatHistory = $("#chatHistory");
  const $generateSection = $("#generatedSections");

  $chatHistory.on("click", ".nav-link", function (e) {
    e.preventDefault();
    const $clickedChat = $(this).closest("span");
    const $clickedLink = $clickedChat.find("button");

    if ($clickedLink.find("input").length > 0) {
      return;
    }
    let $chatId = $(this).data("chat-id");

    if ($generateSection.length > 0) {
      history.pushState(null, null, `/dashboard?chat=${$chatId}`);
      retrieveEmail($chatId);
    } else {
      window.location.href = `/dashboard?chat=${$chatId}`;
    }
  });
}

function checkChat() {
  // Check if the chat ID is in the URL and if the chat section exists
  const $chatId = new URLSearchParams(window.location.search).get("chat");
  const $generateSection = $("#generatedSections");
  if ($chatId && $generateSection.length > 0) {
    retrieveEmail($chatId);
  }
}

function setNewPassword() {
  const $resetForm = $("#resetForm");

  if ($resetForm.length === 0) return;
  // Start and check the timer
  verificationTimer();

  // Send OTP
  const $sendOTPBtn = $("#sendOTP");

  $sendOTPBtn.on("click", function (e) {
    e.preventDefault();
    const $email = $("#email").val();
    $sendOTPBtn.prop("disabled", true);
    $sendOTPBtn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...`
    );
    resetPasswordOTP($email)
      .then((response) => {
        toast(response, "success");
        setVerificationTimer(60, $sendOTPBtn);
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        $sendOTPBtn.prop("disabled", false);
        $sendOTPBtn.text("Send OTP");
      });
  });

  // Reset password
  const $submitBtn = $("#submitBtn");
  $submitBtn.on("click", function (e) {
    const code = digitCode();
    if (!code) return;

    const $email = $("#email").val();
    const $newPassword = $("#newPassword").val();
    const $confirmPassword = $("#confirmPassword").val();

    $submitBtn.prop("disabled", true);
    $submitBtn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Resetting...`
    );

    resetPassword($email, code, $newPassword, $confirmPassword)
      .then((response) => {
        toast(response, "success");
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1000);
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        $submitBtn.prop("disabled", false);
        $submitBtn.text("Reset Password");
      });
  });
}

function contactToArray(contact) {
  let $contactArray = [];
  if (Array.isArray(contact)) {
    contact.forEach(function (value) {
      if (value.id) {
        $contactArray.push([value.id, value.email]);
      } else {
        $contactArray.push([value.email]);
      }
    });
  }
  return $contactArray;
}

function chatHistoryInit() {
  // Chat history
  chatHistory(); // Initialize chat history
  chatRename(); // Initialize chat rename
  chatDelete(); // Initialize chat delete
  openChat(); // Initialize chat open
  checkChat(); // Check if chat ID is in URL
}

// Initialize all functions
function functionInit() {
  // Login
  $(loginFunction);
  // Register
  $(registerFunction);
  // Logout
  $(logoutFunction);
  // Update email
  $(changeEmail);
  // Send password OTP
  $(setNewPassword);
  // Verify email
  $(verifyEmailFunction);
  // Verify digit code
  $(digitVerification);
  $(chatHistoryInit);
}

$(functionInit);
