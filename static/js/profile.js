function setGrAvatar() {
  const $avatar = $("#gravatarProfile");
  if (!$avatar.length) return;

  const cached = localStorage.getItem("gravatar_url");

  if (cached) {
    $avatar.html(`<img src="${cached}" class="rounded-circle" alt="Profile" width="128" draggable="false">`);
    return;
  }

  getProfile()
    .then((response) => {
      const first_name = response.first_name || "";
      const last_name = response.last_name || "";
      const email = response.email || "";
      const fullname = `${first_name} ${last_name}`.trim();

      const hash = md5(email.trim().toLowerCase());
      const avatarUrl = `https://www.gravatar.com/avatar/${hash}?d=https%3A%2F%2Fui-avatars.com%2Fapi%2F/${fullname}/128`;

      localStorage.setItem("gravatar_url", avatarUrl);
      $avatar.html(`<img src="${cached}" class="rounded-circle" alt="Profile" width="128" draggable="false">`);
    })
    .catch((error) => {
      toast(error.message || "An error occurred", "error");
    });
}

function editProfileFunction() {
  // Get the edit profile form
  const $editProfileForm = $("#editProfile");

  // Check if the form exists
  if ($editProfileForm.length === 0) return;

  // Get the graduation year input
  const $graduation_year_input = $("#graduation_year");

  // Set the minimum and maximum values for the graduation year input
  $graduation_year_input.attr("max", new Date().getFullYear() + 10);

  // Handle form submit
  $editProfileForm.on("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission
    // Get the form values
    const $first_name = $("#first_name").val(); // First name
    const $last_name = $("#last_name").val(); // Last name
    const $username = $("#username").val(); // Username
    const $phone_code = $("#phone_code").val(); // Phone code
    const $phone = $("#phone").val(); // Phone number
    const $company = $("#company").val(); // Company
    const $work_title = $("#Job").val();  // Job
    const $college = $("#college").val(); // College
    const $major = $("#major").val(); // Major
    const $graduation_year = $("#graduation_year").val(); // Graduation year
    const $btn = $("#editProfileBtn"); // Submit button

    // Disable the button
    $btn.prop("disabled", true);
    // Show loading state
    $btn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...`
    );

    // Create a data object
    const $data = {
      first_name: $first_name,
      last_name: $last_name,
      username: $username,
      phone_code: $phone_code,
      phone_number: $phone,
      company: $company,
      work_title: $work_title,
      college: $college,
      major: $major,
      graduation_year: $graduation_year,
    };

    // Update the profile
    updateProfile($data)
      .then((response) => {
        // Display a success message
        toast("Profile updated", "success");
        // Change profile details overviews
        data = response;
        $("#profileName").text(data.first_name + " " + data.last_name);
        $("#profileUsername").text("@" + data.username);
        $("#profileEmail").text(data.email);
        $("#profilePhone").text(data.phone_code + " " + data.phone_number);
        $("#profileCompany").text(data.company);
        $("#profileWork").text(data.work_title);
        $("#profileCollege").text(data.college);
        $("#profileMajor").text(data.major);
        $("#profileGraduation").text(data.graduation_year);
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Save Changes");
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Update");
      });
  });

  // Email verification
  verificationTimer();
  var $emailOriginal = $("#emailInput").val(); // Original email
  const $emailInput = $("#emailInput"); // Email input field
  const $changeEmailBtn = $("#changeEmailBtn"); // Change email button
  const $emailOTP = $("#emailOTP"); // Email OTP input field
  const $emailStatus = $("#emailStatus"); // Email status
  const $resendOTP = $("#resendOTP"); // Resend OTP button

  // Email change
  $emailInput.on("keyup", function () {
    const $email = $(this).val(); // Get the email value
    if ($email !== $emailOriginal) { // Check if the email is different from the original email
      $changeEmailBtn.prop("disabled", false); // Enable the change email button
      $changeEmailBtn.text("Change Email"); // Change the button text
      $changeEmailBtn.removeClass("d-none"); // Show the change email button
    } else {
      $changeEmailBtn.prop("disabled", true); // Disable the change email button
      $changeEmailBtn.text("Verified"); // Change the button text
    }
  });

  // Change email button
  $changeEmailBtn.on("click", function (e) {
    e.preventDefault(); // Prevent the default form submission
    const $email = $emailInput.val(); // Get the email value
    const timerEnd = localStorage.getItem("timerEnd"); // Get the timer end value
    if (timerEnd) { // Check if the timer end value exists
      const timeLeft = Math.ceil((timerEnd - Date.now()) / 1000); // Calculate the time left
      if (timeLeft > 0) { // Check if the time left is greater than 0
        // Display a warning message
        toast(
          `Please wait for ${timeLeft} seconds before updating your email again`,
          "warning"
        );
        return;
      }
    }
    $changeEmailBtn.prop("disabled", true); // Disable the change email button
    // Show loading state
    $changeEmailBtn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...`
    );

    updateEmail($email) // Update the email
      .then((response) => {
        // Display a success message
        toast(response.message, "success");

        // Set the timer for 60 seconds
        setVerificationTimer(60, $resendOTP);

        // Change Original Email
        $emailOriginal = $email;
        // Enable the OTP input field
        $emailOTP.removeClass("d-none");
        // Hide the change email button
        $changeEmailBtn.addClass("d-none");
        // Show the resend OTP button
        $resendOTP.removeClass("d-none");

        $emailStatus.text("Verify"); // Change the email status text
        $emailStatus.removeClass("text-success"); // Remove the success class
        $emailStatus.addClass("text-danger"); // Add the danger class
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        $changeEmailBtn.prop("disabled", false); // Enable the change email button
        $changeEmailBtn.text("Change Email"); // Change the button text
      });
  });

  $emailOTP.on("keyup", function () {
    const $code = $(this).val(); // Get the OTP code
    if ($code.length === 6) { // Check if the OTP code is 6 characters long
      verifyEmail($code) // Verify the email
        .then((response) => {
          toast(response.message, "success"); // Display a success message
          $emailOTP.addClass("d-none"); // Hide the OTP input field
          $emailStatus.text("Verified"); // Change the email status text
          $emailStatus.removeClass("text-danger"); // Remove the danger class
          $emailStatus.addClass("text-success"); // Add the success class
          $changeEmailBtn.removeClass("d-none"); // Show the change email button
          $changeEmailBtn.prop("disabled", true); // Disable the change email button
          $changeEmailBtn.text("Verified"); // Change the button text
          $resendOTP.addClass("d-none"); // Hide the resend OTP button
          $("#profileEmail").text($emailOriginal); // Change the profile email
        })
        .catch((error) => {
          error_message = error.message ? error.message : "An error occurred";
          // Display an error message
          toast(error_message, "error");
        });
    }
  });
}

function changePassword() {
  const $changePasswordForm = $("#changePassword"); // Get the change password form

  // Check if the form exists
  if ($changePasswordForm.length === 0) return;

  // Handle form submit
  $changePasswordForm.on("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission
    // Get the form values
    const $current_password = $("#currentPassword").val();
    const $new_password = $("#newPassword").val();
    const $confirm_password = $("#confirmPassword").val();
    const $btn = $("#changePasswordBtn");

    // Disable the button
    $btn.prop("disabled", true);
    // Show loading state
    $btn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Changing...`
    );

    // Update the password
    updatePassword($current_password, $new_password, $confirm_password)
      .then((response) => {
        // Display a success message
        toast("Password changed", "success"); // Display a success message
        // Reset the form
        $changePasswordForm.trigger("reset");
        // Enable the button
        $btn.prop("disabled", false); // Enable the button
        // Reset the button text
        $btn.html("Change Password"); // Reset the button text
      })
      .catch((error) => {
        if (!error.errors && error.message) {
          error_message = error.message ? error.message : "An error occurred";
          // Display an error message
          toast(error_message, "error");
        } else {
          toast("Password must be at least 8 characters.", "error"); // Display an error message
        }
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Change");
      });
  });
}

function getContactsList(page = 1) {
  // Get the contacts list
  const $contactsList = $("#contactsList").find("tbody"); // Contacts list
  const $contactsNav = $("#contactsNav"); // Contacts navigation
  const per_page = 10; // Number of contacts per page

  // Check if the contacts list exists
  if ($contactsList.length === 0) return;

  // Get the contacts
  getContacts(per_page, page)
    .then((response) => {
      const $contacts = response.items; // Contacts
      const $total = response.total; // Total number of contacts
      const $page = response.page; // Current page
      const $total_pages = response.pages; // Total number of pages

      $contactsList.empty(); // Empty the contacts list
      $contactsNav.empty(); // Empty the contacts navigation
      if ($contacts.length === 0) {
        $contactsList.empty(); // Empty the contacts list
        // Display a message if no contacts are found
        $contactsList.append(`
          <tr>
            <td colspan="3" class="text-center">No contacts found</td>
          </tr>
        `);
        return;
      }

      // Display the contacts
      $contacts.forEach((contact) => {
        // Append the contact to the contacts list
        $contactsList.append(`
          <tr data-contact-id="${contact.id}">
            <td>${contact.name}</td>
            <td><a href="mailto:${contact.email}">${contact.email}</a></td>
            <td>
              <div class="dropdown">
                <button class="btn btn-link dropdown-toggle float-right" type="button" id="dropdownMenuButton"
                  data-bs-toggle="dropdown" aria-expanded="false">
                  Actions
                </button>
                <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                  <li><button class="dropdown-item contactView">
                      <i class="bi bi-eye"></i> View
                    </button></li>
                  <li><button class="dropdown-item contactEdit">
                      <i class="bi bi-pencil"></i> Edit
                    </button></li>
                  <li><button class="dropdown-item contactDelete">
                      <i class="bi bi-trash"></i> Delete
                    </button></li>
                </ul>
              </div>
            </td>
          </tr>
        `);
      });

      // Add page number to contactsNav data attribute
      $contactsNav.attr("data-page", $page);
      // Create the pagination
      $contactsNav.html(`
        <li class="page-item ${$page === 1 ? "disabled" : ""}">
          <button class="page-link" tabindex="-1" data-page="${$page - 1
        }">Previous</button>
        </li>
        ${Array.from({ length: $total_pages }, (_, i) => i + 1)
          .map(
            (page) => `
          <li class="page-item ${$page === page ? "active" : ""}">
            <button class="page-link" data-page="${page}">${page}</button>
          </li>
        `
          )
          .join("")}
        <li class="page-item ${$page === $total_pages ? "disabled" : ""}">
          <button class="page-link" data-page="${$page + 1}">Next</button>
        </li>
      `);

      // Initialize the contact actions
      contactViewCard();
      contactEditCard();
      contactDeleteNotification();
    })
    .catch((error) => {
      error_message = error.message ? error.message : "An error occurred";
      // Display an error message
      toast(error_message, "error");
    });
}

function contactPagination() {
  const $contactsNav = $("#contactsNav"); // Contacts navigation

  $contactsNav.on("click", ".page-link", function (e) { // Handle pagination click
    e.preventDefault(); // Prevent the default form submission
    const $page = $(this).data("page"); // Get the page number
    getContactsList($page); // Get the contacts list
  });
}

function addContactFunction() {
  // Get the add contact form
  const $addContactForm = $("#addContact"); // Add contact form

  if ($addContactForm.length === 0) return; // Check if the form exists

  // Handle form submit
  $addContactForm.on("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission
    // Get the form values
    const $name = $("#name").val();
    const $email = $("#email").val();
    const $phone_code = $("#phone_code").val();
    const $phone = $("#phone").val();
    const $company = $("#company").val();
    const $work_title = $("#work_title").val();
    const $college = $("#college").val();
    const $major = $("#major").val();
    const $btn = $("#addContactBtn");

    // Disable the button
    $btn.prop("disabled", true);
    // Show loading state
    $btn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...`
    );

    // Create a data object with the form values
    const $data = {
      ...($name && { name: $name }),
      ...($email && { email: $email }),
      ...($phone && $phone_code && { phone_code: $phone_code }),
      ...($phone && $phone_code && { phone_number: $phone }),
      ...($company && { company: $company }),
      ...($work_title && { work_title: $work_title }),
      ...($college && { college: $college }),
      ...($major && { major: $major }),
    };

    addContact($data)
      .then((response) => {
        // Display a success message
        toast("Contact added", "success"); // Display a success message
        $page_number = $("#contactsNav").data("page"); // Get the page number
        // Get the contacts list
        getContactsList($page_number); // Get the contacts list
        // Close the contact card
        closeContactCard(); // Close the contact card
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Add");
      });
  });
}

function editContactFunction() {
  // Get the edit contact form
  const $editContactForm = $("#editContact");

  if ($editContactForm.length === 0) return; // Check if the form exists

  // Handle form submit
  $editContactForm.on("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission
    // Get the form values
    const $id = $("#id").val();
    const $name = $("#name").val();
    const $email = $("#email").val();
    const $phone_code = $("#phone_code").val();
    const $phone = $("#phone").val();
    const $company = $("#company").val();
    const $work_title = $("#work_title").val();
    const $college = $("#college").val();
    const $major = $("#major").val();
    const $btn = $("#editContactBtn");

    // Disable the button
    $btn.prop("disabled", true);
    // Show loading state
    $btn.html(
      `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...`
    );

    // Create a data object with the form values
    const $data = {
      name: $name,
      email: $email,
      phone_code: $phone_code || "",
      phone_number: $phone || "",
      company: $company || "",
      work_title: $work_title || "",
      college: $college || "",
      major: $major || "",
    };

    // Update the contact
    updateContact($id, $data)
      .then((response) => {
        // Display a success message
        toast("Contact updated", "success");
        $page_number = $("#contactsNav").data("page");
        // Get the contacts list
        getContactsList($page_number);
        // Close the contact card
        closeContactCard();
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        // Enable the button
        $btn.prop("disabled", false);
        // Reset the button text
        $btn.html("Save");
      });
  });
}

function openContactCard() {
  const $contacts = $("#contactsCol"); // Contacts column
  const $contactPr = $("#contactPr"); // Contact profile

  if ($contacts.length === 0) return; // Check if the contacts column exists

  $contacts.removeClass("col-md-12"); // Remove the col-md-12 class
  $contacts.addClass("col-md-8"); // Add the col-md-8 class
  $contactPr.removeClass("d-none"); // Remove the d-none class
}

function closeContactCard() {
  const $contacts = $("#contactsCol"); // Contacts column
  const $contactPr = $("#contactPr"); // Contact profile

  if ($contacts.length === 0) return; // Check if the contacts column exists

  $contacts.removeClass("col-md-8"); // Remove the col-md-8 class
  $contacts.addClass("col-md-12"); // Add the col-md-12 class
  $contactPr.addClass("d-none"); // Add the d-none class
}

function closeContactCardBtn() {
  const $closeBtn = $("#closePr"); // Close button

  if ($closeBtn.length === 0) return; // Check if the close button exists

  $closeBtn.click(function () {
    closeContactCard(); // Close the contact card
  });
}

function contactAddCard() {
  const $contactBody = $("#contactBody"); // Contact body
  const $contactTitle = $("#contactTitle"); // Contact title
  const $addBtn = $("#addContact"); // Add contact button

  if ($addBtn.length === 0) return; // Check if the add contact button exists

  $addBtn.click(function () {
    $contactTitle.text("Add Contact"); // Set the contact title
    $contactBody.empty(); // Empty the contact body
    $contactBody.append(`
                <form id="addContact">
                    <h5 class="card-title">Profile</h5>
                    <label for="name">Name</label>
                    <input type="text" id="name" name="name" class="form-control" placeholder="Full name" required>
                    <label class="mt-2" for="email">Email</label>
                    <input type="email" id="email" name="email" class="form-control" placeholder="Email" required>
                    <label class="mt-2" for="phone">Phone</label>
                    <div class="input-group">
                        <div class="input-group-prepend">
                            <select class="form-select" id="phone_code" name="phone_code">
                            </select>
                        </div>
                        <input type="tel" name="phone" class="form-control" id="phone" placeholder="Phone number">
                    </div>
                    <h5 class="card-title mt-3">Company</h5>
                    <label for="company">Company</label>
                    <input type="text" id="company" name="company" class="form-control" placeholder="Company">
                    <label class="mt-2" for="work_title">Work Title</label>
                    <input type="text" id="work_title" name="work_title" class="form-control" placeholder="Work Title">
                    <h5 class="card-title mt-3">Education</h5>
                    <label for="college">College</label>
                    <input type="text" id="college" class="form-control" placeholder="College">
                    <label class="mt-2" for="major">Major</label>
                    <input type="text" id="major" class="form-control" placeholder="Major">
                    <div class="text-center">
                        <button type="submit" id="addContactBtn" class="btn btn-primary mt-3 text-center">Add</button>
                    </div>
              </form>
        `);
    loadCallingCodes(); // Load calling codes
    addContactFunction(); // Add contact function
    openContactCard(); // Open contact card
  });
}

function contactViewCard() {
  const $viewBtn = $(".contactView"); // View contact button
  const $contactBody = $("#contactBody"); // Contact body
  const $contactTitle = $("#contactTitle"); // Contact title

  if ($viewBtn.length === 0) return; // Check if the view contact button exists

  $viewBtn.click(function (e) {
    e.preventDefault(); // Prevent the default form submission
    const $contactId = $(this).closest("tr").data("contact-id"); // Get the contact ID

    getContact($contactId) // Get the contact
      .then((response) => {
        $contactTitle.text("View Contact"); // Set the contact title
        $contactBody.empty(); // Empty the contact body
        data = response; // Set the data

        // Append the contact details to the contact body
        $contactBody.append(`
              <form id="contactInfo">
                  <h5 class="card-title">Profile</h5>
                  <label for="name">Name</label>
                  <input type="text" id="name" name="name" class="form-control" value="${data.name
          }" disabled>
                  <label class="mt-2" for="email">Email</label>
                  <input type="email" id="email" name="email" class="form-control" value="${data.email
          }" disabled>
                  <label class="mt-2" for="phone">Phone</label>
                  <input type="text" id="phone" name="phone_number" class="form-control" value="${data.phone_code + data.phone_number || ""
          }"
                    disabled>
                  <h5 class="card-title mt-3">Company</h5>
                  <label for="company">Company</label>
                  <input type="text" id="company" name="company" class="form-control" value="${data.company || ""
          }" disabled>
                  <label class="mt-2" for="work_title">Work Title</label>
                  <input type="text" id="work_title" name="work_title" class="form-control" value="${data.work_title || ""
          }"
                    disabled>
                  <h5 class="card-title mt-3">Education</h5>
                  <label for="college">College</label>
                  <input type="text" id="college" class="form-control" value="${data.college || ""
          }" disabled>
                  <label class="mt-2" for="major">Major</label>
                  <input type="text" id="major" class="form-control" value="${data.major || ""
          }" disabled>
              </form>
          `);
        openContactCard();
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
      });
  });
}

function contactEditCard() {
  const $editBtn = $(".contactEdit");
  const $contactBody = $("#contactBody");
  const $contactTitle = $("#contactTitle");

  if ($editBtn.length === 0) return;

  $editBtn.click(function () {
    const $contactId = $(this).closest("tr").data("contact-id");

    getContact($contactId)
      .then((response) => {
        $contactTitle.text("Edit Contact");
        $contactBody.empty();
        data = response;
        $contactBody.append(`
            <form id="editContact">
                <input type="hidden" id="id" value="${$contactId}">
                <h5 class="card-title">Profile</h5>
                <label for="name">Name</label>
                <input type="text" id="name" name="name" class="form-control" value="${data.name
          }">
                <label class="mt-2" for="email">Email</label>
                <input type="email" id="email" name="email" class="form-control" value="${data.email
          }">
                <label class="mt-2" for="phone">Phone</label>
                <div class="input-group">
                    <div class="input-group-prepend">
                        <select class="form-select" id="phone_code" data-user-code="${data.phone_code || ""
          }" name="phone_code">
                        </select>
                    </div>
                    <input type="tel" name="phone" class="form-control" id="phone" placeholder="Phone number" value="${data.phone_number || ""
          }">
                </div>
                <h5 class="card-title">Company</h5>
                <label for="company">Company</label>
                <input type="text" id="company" name="company" class="form-control" value="${data.company || ""
          }">
                <label class="mt-2" for="work_title">Work Title</label>
                <input type="text" id="work_title" name="work_title" class="form-control" value="${data.work_title || ""
          }">
                <h5 class="card-title">Education</h5>
                <label for="college">College</label>
                <input type="text" id="college" class="form-control" value="${data.college || ""
          }">
                <label class="mt-2" for="major">Major</label>
                <input type="text" id="major" class="form-control" value="${data.major || ""
          }">
                <div class="text-center">
                    <button type="submit" id="editContactBtn" class="btn btn-primary mt-3 text-center">Save</button>
                </div>
            </form>
        `);
        loadCallingCodes();
        openContactCard();
        editContactFunction();
      })
      .catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
      });
  });
}

function contactDeleteNotification() {
  const $deleteBtn = $(".contactDelete");

  if ($deleteBtn.length === 0) return;

  $deleteBtn.click(function () {
    const $contactRow = $(this).closest("tr");
    const $contactId = $contactRow.data("contact-id");

    Swal.fire({
      title: "Are you sure?",
      text: "You will not be able to recover this contact.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Delete",
    }).then((result) => {
      if (result.isConfirmed) {
        deleteContact($contactId)
          .then((response) => {
            // Display a success message
            toast("Contact deleted", "success");
            // Get the page number
            $page_number = $("#contactsNav").data("page");
            // Get the contacts list
            getContactsList($page_number);
            closeContactCard();
          })
          .catch((error) => {
            // Display an error message
            error_message = error.message ? error.message : "An error occurred";
            // Display an error message
            toast(error_message, "error");
          });
      }
    });
  });
}

function profileInit() {
  $(setGrAvatar); // Set Gravatar
  $(editProfileFunction); // Edit profile
  $(changePassword); // Change password
  $(getContactsList(1)); // Get contacts list
  $(contactPagination); // Pagination for contacts
  $(contactAddCard); // Add contact card
  $(closeContactCardBtn); // Close contact card
}

$(profileInit);