/**
 * Convert email select fields to select2 dropdowns
 */
function selectRecipient(toData = null, ccData = null, bccData = null) {
  // Get email select fields
  const $emailTo = $('#emailTo');
  const $emailCc = $('#emailCc');
  const $emailBcc = $('#emailBcc');

  // Check if the email select fields exist
  if ($emailTo.length === 0 && $emailCc.length === 0 && $emailBcc.length === 0) {
    return;
  }

  // Add contacts from the API to all three email select fields
  getContacts().then((response) => {
    $contacts = response.items;
    $contacts.forEach(function (contact) {
      // Append the contact to the email select fields
      $emailTo.append(`<option value="${contact.id}">${contact.name} &lt;${contact.email}&gt;</option>`);
      $emailCc.append(`<option value="${contact.id}">${contact.name} &lt;${contact.email}&gt;</option>`);
      $emailBcc.append(`<option value="${contact.id}">${contact.name} &lt;${contact.email}&gt;</option>`);
    });

    // Set the selected email addresses in the email select fields
    toData = toData || [];
    ccData = ccData || [];
    bccData = bccData || [];

    // Add the email addresses to the email select fields if they are not contacts
    if (toData.length != 0) {
      toData.forEach(function (value) {
        if (value.length == 1) {
          $emailTo.append(`<option value="${value}">${value}</option>`);
        } else if (value.length == 2) {
          // Select the contact if it exists
          getContact(value[0]).then((response) => {
            const contact = response;
            $emailTo.find(`option[value="${contact.id}"]`).prop('selected', true);
            $emailTo.trigger('change');
          }).catch((error) => {
            if (value[1] != null)
              $emailTo.append(`<option value="${value[1]}" selected>${value[1]}</option>`);
          });
        }
      });
    }

    if (ccData.length != 0) {
      ccData.forEach(function (value) {
        if (value.length == 1) {
          $emailCc.append(`<option value="${value}">${value}</option>`);
        } else if (value.length == 2) {
          // Select the contact if it exists
          getContact(value[0]).then((response) => {
            const contact = response;
            $emailCc.find(`option[value="${contact.id}"]`).prop('selected', true);
            $emailCc.trigger('change');
          }
          ).catch((error) => {
            if (value[1] != null)
              $emailCc.append(`<option value="${value[1]}" selected>${value[1]}</option>`);
          });
        }
      });
    }

    if (bccData.length != 0) {
      bccData.forEach(function (value) {
        if (value.length == 1) {
          $emailBcc.append(`<option value="${value}">${value}</option>`);
        } else if (value.length == 2) {
          // Select the contact if it exists
          getContact(value[0]).then((response) => {
            const contact = response;
            $emailBcc.find(`option[value="${contact.id}"]`).prop('selected', true);
            $emailBcc.trigger('change');
          }).catch((error) => {
            if (value[1] != null)
              $emailBcc.append(`<option value="${value[1]}" selected>${value[1]}</option>`);
          });
        }
      }
      );
    }

    // Set the selected email addresses in the email select fields
    $emailTo.val(toData).trigger('change');
    $emailCc.val(ccData).trigger('change');
    $emailBcc.val(bccData).trigger('change');

    // Create an object to store all email select fields
    const $emailList = { $emailTo, $emailCc, $emailBcc };


    // Initialize select2 dropdown for each email select field
    Object.values($emailList).forEach(function (email) {
      // Initialize select2 dropdown
      email.select2({
        // Allow multiple selections
        multiple: true,
        // Allow tags to be created
        tags: true,
        // Allow clearing the selection
        allowClear: true,
        // Placeholder text
        placeholder: 'Enter email address',
        // Custom template for creating a new tag
        createTag: function (params) {
          // Do not create a new tag if the input is not an email address
          const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (emailPattern.test(params.term)) {
            return {
              id: params.term,
              text: params.term,
              newOption: true
            };
          }
          return null;
        },
        // Custom template for displaying a text
        language: {
          noResults: function () {
            return 'Enter email address';
          },
          searching: function () {
            return 'Searching...';
          },
          inputTooShort: function () {
            return 'Enter email address';
          },
          errorLoading: function () {
            return 'Error loading results';
          },
          loadingMore: function () {
            return 'Loading more results';
          }
        }
      });
    });
  });
}

/**
 * Convert language tone select field to select2 dropdown
 */
function selectDropdowns(emailFrom = null, languageTone = null, emailLength = null) {
  // Get language tone select field and email length select field
  const $languageTone = $('#languageTone');
  const $emailLength = $('#emailLength');
  const $promptPreset = $('#promptPreset');
  const $emailFrom = $('#emailFrom');

  // Check if the select fields exist
  if ($languageTone.length === 0 && $emailLength.length === 0 && $promptPreset.length === 0) {
    return;
  }

  // Initialize select2 dropdown for language tone select field
  $languageTone.select2({
    tags: false,
  });
  // Initialize select2 dropdown for email length select field
  $emailLength.select2({
    tags: false,
  });
  // Initialize select2 dropdown for prompt preset select field
  $promptPreset.select2({
    tags: false,
    dropdownCssClass: "choose-prompt",
  });

  // Initialize select2 dropdown for email from select field
  $emailFrom.select2({
    tags: false,
    language: {
      noResults: function () {
        return 'Link an email account before generating an email.';
      },
    }
  });

  // Get linked accounts from the API
  getLinkedAccounts().then((response) => {
    const $accounts = response; // Get the linked accounts
    $emailFrom.empty(); // Clear the email from select field
    $emailFrom.append(`<option value="">Select an email account</option>`); // Add a default option
    $accounts.forEach(function (account) { // Append each account to the email from select field
      $emailFrom.append(`<option value="${account.id}" ${emailFrom == account.id ? 'selected' : ''}>${account.first_name + " " + account.last_name} &lt;${account.email}&gt;</option>`);
    });
  });

  // Set the default values for the select fields
  if (languageTone)
    $languageTone.val(languageTone).trigger('change');
  if (emailLength)
    $emailLength.val(emailLength).trigger('change');
}
/**
 * Chat input commands using Tribute.js
 */
function chatInputCommands() {
  // Get chat input field
  const $chatInput = $('#chatInput');
  // Initialize Tribute.js for chat input field
  var tribute = new Tribute({
    // Define the collection of commands and values
    collection: [
      {
        trigger: "/",  // Initial command trigger
        values: [
          { key: 'length', value: 'length' }, // Command and value
          { key: 'tone', value: 'tone' }, // Command and value
          { key: 'help', value: 'help' }, // Command and value
        ]
      },
      {
        // Trigger after typing '/length ' with a space after the command
        trigger: "length ",
        values: [
          { key: 'short', value: 'short' }, // Command and value
          { key: 'medium', value: 'medium' }, // Command and value
          { key: 'long', value: 'long' }, // Command and value
        ]
      },
      {
        // Trigger after typing '/tone ' with a space after the command
        trigger: "tone ",
        values: [
          { key: 'normal', value: 'normal' }, // Command and value
          { key: 'professional', value: 'professional' }, // Command and value
          { key: 'academic', value: 'academic' }, // Command and value
          { key: 'casual', value: 'casual' }, // Command and value
          { key: 'friendly', value: 'friendly' }, // Command and value
        ]
      }
    ]
  });
  // Attach Tribute.js to the chat input field
  tribute.attach($chatInput[0]);
}

/**
 * Form validation using Bootstrap
 */
function customPrompt() {
  // Get the prompt preset select field and instruction text area
  const $instruction = $('#instruction');
  const $promptPreset = $('#promptPreset');

  // Initialize select2 dropdown for prompt preset select field
  $promptPreset.on('select2:select', function (e) {
    preset = this.value; // Get the selected prompt preset
    // Custom prompt
    if (preset === 'custom')
      $instruction.val(''); // Clear the instruction text area
    // Meeting prompt
    if (preset === 'meeting')
      $instruction.val('Write an email requesting a meeting with the recipients to discuss [topic]. Suggest potential dates and times for the meeting.');

    // Leave request prompt
    else if (preset === 'leave_request')
      $instruction.val('Write an email requesting [number] day(s) of leave due to [reason]. Include the dates for the leave and express willingness to assist in any transition or pending tasks.');

    // Job application prompt
    else if (preset === 'job_application')
      $instruction.val('Write an email applying for the position of [position] at [company]. Highlight my [skills/qualifications] and express my interest in joining the team.');

    // Complaint prompt
    else if (preset === 'complaint')
      $instruction.val('Write an email to [company] to file a complaint about [issue]. Provide details and request a resolution or further assistance.');

    // Event invitation prompt
    else if (preset === 'event_invitation')
      $instruction.val('Write an email inviting [recipients] to attend [event name] on [date]. Provide details about the event and RSVP instructions.');

    // Resignation prompt
    else if (preset === 'resignation')
      $instruction.val('Write an email to formally resign from my position at [company] effective from [date]. Thank them for the opportunity and offer assistance during the transition.');

    // Feedback prompt
    else if (preset === 'feedback')
      $instruction.val('Write an email to provide feedback on [product/service/experience]. Highlight what was positive and offer suggestions for improvement where necessary.');

    // Thank you prompt
    else if (preset === 'thank_you')
      $instruction.val('Write an email thanking [recipient] for [reason]. Express appreciation for their help/support and mention how it was beneficial.');

    // Introduction prompt
    else if (preset === 'introduction')
      $instruction.val('Write an email introducing myself to [recipient]. Include information about my background, experience, and reason for reaching out.');
  });
}

/**
 * Start the email generation process
 */
function startEmail() {
  // Get the start email button and generated sections
  const $emailBtn = $('.startEmail');
  const $generateSection = $('#generatedSections');
  const $chatBot = $('#chatBot');

  // Check if the start email button exists
  if ($emailBtn.length === 0) {
    return;
  }

  // Remove the click event listener from the start email button
  $emailBtn.off('click');

  // Add a click event listener to the start email button
  $emailBtn.on('click', function () {
    // Get the number of linked accounts
    getLinkedAccounts().then((response) => {
      if (response.length === 0) {
        showFromQuestion();
        return;
      }
    });

    // Change the URL to the root URL
    history.pushState(null, null, '/dashboard');
    // Hide the the generated section if it is visible
    $generateSection.hide();

    $chatBot.hide(); // Hide the chat bot initially
    $chatBot.empty(); // Clear the chat bot content

    // Clear the generated sections
    $generateSection.empty();

    // Append and show the email generation form to the generated sections
    generateSection($generateSection);

    // Initialize select2 dropdowns
    selectRecipient();
    selectDropdowns();
    customPrompt();
    generateEmail();

    // Initialize form validation from main.js
    formValidation();
    enableBSTooltips();
    fromQuestion();

    // Scroll to the generated sections
    $('html, body').animate({
      scrollTop: $generateSection.offset().top
    }, 100);
  });
}

/**
 * Retrieve the email generation form
 * @param {string} chatId - The chat ID to retrieve the email generation form
 */
function retrieveEmail($chatId) {
  const $generateSection = $('#generatedSections'); // Get the generated sections
  const $chatBot = $('#chatBot');  // Get the chat bot
  let $emailSent = false; // Email sent status

  if ($generateSection.length === 0) return;

  // Get the chat details from the API
  getChatDetails($chatId).then((response) => {
    $emailSent = response.is_sent; // Get the email sent status
    $emailFromId = response.oauth_id; // Get the email from ID

    console.log(`OAuth ID: ${$emailFromId}`);

    // Get the chat messages from the API
    getChat($chatId).then((response) => {
      const $chatData = response; // Get the chat data
      const $chatLength = $chatData.length; // Get the chat length
      if ($chatLength === 0) { // Check if the chat is empty
        toast('The chat was empty, and it has been deleted automatically.', 'info');
        deleteChat($chatId); // Delete the chat
        history.pushState(null, null, `/dashboard`); // Change the URL to the root URL
        chatHistory(); // Refresh the chat history
        return;
      }

      // Get the last contacts, email length, and language tone from the chat data
      let $lastContacts;
      let $first_instruction = $chatData[0].data.instruction;
      let $lastEmailLength;
      let $lastLanguageTone;

      // Loop through the chat data to get the last contacts, email length, and language tone
      for (let i = ($chatLength - 1); i >= 0; i--) {
        if ($chatData[i].data.contacts) {
          $lastContacts = $chatData[i].data.contacts;
          $lastEmailLength = $chatData[i].data.length;
          $lastLanguageTone = $chatData[i].data.language_tone;
          break;
        }
      }

      // Check if the last contacts, email length, and language tone exist
      const $contact_to = $lastContacts[0].to;
      const $contact_cc = $lastContacts[0].cc;
      const $contact_bcc = $lastContacts[0].bcc;

      // Hide the generated sections and chat bot
      $generateSection.hide();
      $chatBot.hide();
      $chatBot.empty();
      $generateSection.empty();

      // Append the email generation form to the generated sections
      generateSection($generateSection);

      // Get instruction and prompt preset fields
      const $instruction = $('#instruction');
      const $customPrompt = $('#promptPreset');


      // Get the contacts from the chat data
      $toData = contactToArray($contact_to);
      $ccData = contactToArray($contact_cc);
      $bccData = contactToArray($contact_bcc);

      let $length; // Email length

      // Set the email length based on the last email length
      if ($lastEmailLength.charAt(0).toLowerCase() === 's')
        $length = 'short';
      else if ($lastEmailLength.charAt(0).toLowerCase() === 'm')
        $length = 'medium';
      else if ($lastEmailLength.charAt(0).toLowerCase() === 'l')
        $length = 'long';
      else
        $length = 'medium';


      // Set the email length and language tone select fields
      selectRecipient($toData, $ccData, $bccData);
      selectDropdowns($emailFromId, $lastLanguageTone, $length);
      customPrompt();

      // Set the instruction field to the first instruction
      $instruction.val($first_instruction);
      $instruction.prop('disabled', true); // Disable the instruction field
      $generateBtn = $('#generateBtn'); // Get the generate email button
      $generateBtn.prop('disabled', true); // Disable the generate email button
      $customPrompt.prop('disabled', true); // Disable the prompt preset select field

      // Show the generated sections
      createChatBot($chatId, $emailSent);
      retrieveChat($chatData, $emailSent);

      formValidation();
      enableBSTooltips();
      fromQuestion();
    });
  }).catch((error) => {
    error_message = error.message ? error.message : "An error occurred";
    // Display an error message
    toast(error_message, "error");
  });
}

/**
 * Type writer effect for chat messages
 * @param {string} message - The message to type
 * @param {object} box - The message box to append the message
 * @param {object} chatBox - The chat box to scroll
 * @param {function} callback - The callback function to execute after typing the message
 */
function typeWriter(message, box, chatBox, callback) {
  let i = 0; // Index of the current character
  const typingSpeed = 1; // Typing speed in milliseconds

  // Type the message character by character
  function type() {
    // Check if there are more characters to type
    if (i < message.length) {
      let typed_message = ''; // Typed message so far
      let new_letter = message.charAt(i); // Get the next character to type

      // Append the new character to the typed message
      typed_message += new_letter;
      // Append the typed message to the chat box
      box.append(typed_message);
      // Scroll to the bottom of the chat box
      chatBox.scrollTop(chatBox[0].scrollHeight);
      i++; // Move to the next character
      setTimeout(() => requestAnimationFrame(type), typingSpeed); // Type the next character after a delay
    } else if (callback) {
      callback(); // Execute the callback function after typing the message
    }
  }
  type(); // Start typing the message
}

/**
 * Send a message to the chat box
 * @param {string} sender - The sender of the message
 * @param {string} message - The message to send
 */
function sendMessage(sender, message) {
  // Get the chat box and create a new message box
  const $chatBox = $('#chatBox');
  const $messageBox = $(`<div class="message ${sender}-message"></div>`).hide();

  if ($chatBox.length === 0) return;

  // Display the message box
  $messageBox.fadeIn(500);
  // Append the message to the message box
  $chatBox.append($messageBox);

  // Check if the message is from the user
  if (sender === 'user') {
    // Type the message character by character
    $messageBox.append(message);
    // Scroll to the bottom of the chat box
    $chatBox.scrollTop($chatBox[0].scrollHeight);
  } else {
    // Type the message character by character
    typeWriter(message, $messageBox, $chatBox);
  }

  // Return the message box
  $chatBox.append($messageBox);

  // if the message is a command, execute the command
  if (message.startsWith('/')) {
    // Get the command and argument from the message
    const command = message.substring(1).split(' ')[0];
    const arg = message.substring(1).split(' ')[1];

    // The command is to set the email length
    if (command === 'length') {
      // Check if the argument is valid
      if (arg === 'short' || arg === 'medium' || arg === 'long') {
        // Set the email length to the argument
        $('#emailLength').val(arg).trigger('change');
        // Send a message to the chat box
        sendMessage('bot', `Email length set to: ${arg}`);
      } else {
        // Send an error message to the chat box
        sendMessage('bot', 'Invalid email length. Please select from: short, medium, or long.');
      }
      // The command is to set the language tone
    } else if (command === 'tone') {
      // Check if the argument is valid
      if (arg === 'normal' || arg === 'professional' || arg === 'academic' || arg === 'casual' || arg === 'friendly') {
        // Set the language tone to the argument
        $('#languageTone').val(arg).trigger('change');
        // Send a message to the chat box
        sendMessage('bot', `Language tone set to: ${arg}`);
      } else {
        // Send an error message to the chat box
        sendMessage('bot', 'Invalid language tone. Please select from: normal, professional, academic, casual, or friendly.');
      }
      // The command is to display the available commands
    } else if (command === 'help') {
      sendMessage('bot', 'Available commands:\n/length [short|medium|long]\n/tone [normal|professional|academic|casual|friendly]');
    } else {
      // Send an error message to the chat box
      sendMessage('bot', `Command not recognized: /${command}`);
    }
  }
}

/**
 * Create an email message
 * @param {string} subject - The subject of the email
 * @param {string} body - The body of the email
 */
function createEmail(subject, body, messageId, animate = true, emailSent = false) {
  // Get the chat box and create a new message box
  const $lastAction = $('.email-actions').last();
  $lastAction.remove();
  const $chatBox = $('#chatBox');
  const $messageBox = $(`<div class="message bot-message"></div>`).hide();
  // Create email subject, body, and actions
  const $emailSubject = $(`<div class="email-subject"></div>`);
  const $emailBody = $(`<div class="email-body"></div>`);
  const $emailActions = $(`
    <div class="email-actions">
      <input type="hidden" id="messageId" value="${messageId}">
      <button class="btn btn-primary px-4 py-2 sendEmail" ${emailSent ? 'disabled' : ''}>${emailSent ? 'Email Sent' : '<i class="bi bi-send-fill me-2"></i>Send Email'}</button>
    </div>
    `).hide();
  // Display the message box
  $messageBox.fadeIn(500);

  // Append the message to the message box
  $chatBox.append($messageBox);
  $messageBox.append($emailSubject);
  $messageBox.append($emailBody);
  $messageBox.append($emailActions);

  // Type the email subject and body character by character
  if (!animate) {
    // Append the email subject and body to the message box
    $emailSubject.append(subject.replace(/\n/g, ''));
    $emailBody.append(body);
    $emailActions.fadeIn(500);
    $chatBox.scrollTop($chatBox[0].scrollHeight);
    const $chatBot = $('#chatBot');
    window.scrollBy(0, $chatBot[0].scrollHeight);
  } else {
    typeWriter(subject, $emailSubject, $chatBox, () => {
      typeWriter(body, $emailBody, $chatBox, () => {
        $emailActions.fadeIn(500);
      });
    });
  }

  emailSend(); // Initialize the email send functionality
  if (!emailSent) emailSelection(); // Initialize the email selection functionality
}

/**
 * Initialize the chat functionality
 */
function sendChat() {
  // Get the chat input field and chat form
  const $chatInput = $('#chatInput');
  const $chatForm = $('#chatForm');
  const $chatBtn = $('#chatBtn');
  const $chatId = parseInt($('#chatId').val(), 10);

  if ($chatForm.length === 0) return;

  // Add a submit event listener to the chat form
  $chatForm.on('submit', function (e) {
    // Prevent the default form submission
    e.preventDefault();
    // Check if the chat input field is empty
    if (!$chatInput.val()) {
      toast('Please enter a message', 'error');
      return;
    } else if (!$chatInput.val().startsWith('/')) {
      $chatInput.prop('disabled', true);
      $chatBtn.html(`
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Generating...
      `);
      $chatBtn.prop('disabled', true);
    }

    // Get the chat message from the input field
    const $chatMessage = $chatInput.val();
    // Send the chat message to the chat box
    if ($chatMessage) {
      // Send the chat message to the chat box
      sendMessage('user', $chatMessage);
      $chatInput.val('');
      // Check if the chat message is a command
      if ($chatMessage.startsWith('/')) {
        return;
      }

      // Get the email details from the form
      const $emailTo = $('#emailTo').val();
      const $emailCc = $('#emailCc').val();
      const $emailBcc = $('#emailBcc').val();
      const $emailLength = $('#emailLength').val();
      const $languageTone = $('#languageTone').val();
      const $instruction = $chatMessage;

      const contacts = [
        {
          "to": $emailTo.map(function (value) {
            return !isNaN(value) ? { "id": Number(value) } : { "email": value };
          }),
          "cc": $emailCc.map(function (value) {
            return !isNaN(value) ? { "id": Number(value) } : { "email": value };
          }),
          "bcc": $emailBcc.map(function (value) {
            return !isNaN(value) ? { "id": Number(value) } : { "email": value };
          })
        }
      ];


      // Generate the email based on the chat message
      generateModifyEmail($chatId, contacts, $instruction, $languageTone, $emailLength).then((response) => {
        const $output = response.output;
        const $subject = $output.subject;
        const $email = $output.body;
        const $messageId = response.assistant_message_id;
        const $chatBot = $('#chatBot');
        createEmail($subject, $email, $messageId);
        window.scrollBy(0, $chatBot[0].scrollHeight);
        $chatInput.prop('disabled', false);
        $chatBtn.text('Send');
        $chatBtn.prop('disabled', false);
      }).catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
        sendMessage('bot', 'Error generating email. Please try again.');
        $chatInput.prop('disabled', false);
        $chatBtn.text('Send');
      });
    }
  });
}

/**
 * Create the chat bot interface
 * @param {string} message - The initial message to display
 */
function createChatBot(chat_id, emailSent = false) {
  // Get the chat bot element
  const $chatBot = $('#chatBot');
  $chatBot.hide(); // Hide the chat bot initially
  $chatBot.empty(); // Clear the chat bot content
  // Append the chat bot interface to the chat bot element
  $chatBot.append(`
    <div class="card email-card shadow rounded-4 border-0">
      <div class="card-body">
        <h5 class="card-title">Chat</h5>
        <!-- Chatbox -->
        <div class="chat-box" id="chatBox"></div>
          <form autocomplete="off" id="chatForm">
            <div class="input-group mt-4 mb-3 shadow-sm rounded-start">
              <input type="hidden" id="chatId" value="${chat_id}">

              <input type="text"
                    class="form-control border-end-0"
                    id="chatInput"
                    placeholder="Enter instructions or use / for commands"
                    aria-label="Chat Instructions"
                    aria-describedby="chatBtn"
                    ${emailSent ? 'disabled' : ''}>

              <button class="btn btn-primary px-4 d-flex align-items-center gap-2"
                      type="submit"
                      id="chatBtn"
                      ${emailSent ? 'disabled' : ''}>
                <i class="bi bi-send-fill"></i>
                <span id="chat-btn-text">Send</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `);
  sendChat(); // Initialize the chat functionality
  $chatBot.fadeIn(0); // Fade in the chat bot interface
  chatInputCommands(); // Initialize chat input commands
}

/**
 * Retrieve the chat
 * @param {array} messages - The chat messages to retrieve
 * @param {boolean} email_sent - The email sent status
 */
function retrieveChat(messages, email_sent) {
  // Loop through the chat messages
  messages.forEach(function (message) {
    const $chat_type = message.chat_type; // Get the chat type
    const $data = message.data ? message.data : message.output; // Get the chat data
    const $message_id = message.id; // Get the message ID
    // Check if the chat type is user
    if ($chat_type === 'user') {
      sendMessage('user', $data.instruction); // Send the user message to the chat box
    } else {
      createEmail($data.subject, $data.body, $message_id, false, email_sent); // Create the email message
    }
  });
}

/**
 * Generate the email generation form
 */
function generateEmail() {
  const $generateEmail = $('#generateEmail'); // Get the generate email form
  const $promptPreset = $('#promptPreset'); // Get the prompt preset select field
  const $emailPrompt = $('#instruction'); // Get the email prompt text area

  // Check if the generate email form exists
  if ($generateEmail.length === 0) return;

  // Add a submit event listener to the generate email form
  $generateEmail.on('submit', function (e) {
    e.preventDefault(); // Prevent the default form submission
    const $generateBtn = $('#generateBtn'); // Get the generate email button
    const $instruction = $('#instruction').val(); // Get the email prompt
    const $emailFrom = $('#emailFrom').val(); // Get the email from
    const $emailTo = $('#emailTo').val(); // Get the email to
    const $emailCc = $('#emailCc').val(); // Get the email cc
    const $emailBcc = $('#emailBcc').val(); // Get the email bcc
    const $emailLength = $('#emailLength').val(); // Get the email length
    const $languageTone = $('#languageTone').val(); // Get the language tone

    // Check if the email from is empty and not a number
    if ($emailFrom.length === 0 && !isNaN($emailFrom)) {
      toast('Please select one of your email addresses.', 'error');
      return;
    }

    // Check if the email to is empty
    const $emailFromId = Number($emailFrom);

    // Check if the email to is empty
    if ($instruction.length === 0 || $emailTo.length === 0) {
      toast('Please enter your prompt and select at least one recipient.', 'error');
      return;
    }

    $emailPrompt.prop('disabled', true); // Disable the email prompt text area
    $promptPreset.prop('disabled', true); // Disable the prompt preset select field
    $generateBtn.prop('disabled', true); // Disable the generate email button

    // Change the generate email button text to loading
    $generateBtn.html(`
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Generating Email...
    `);

    const extractEmail = (text) => {
      const match = text.match(/<([^>]+)>/); // Matches content within <>
      return match ? match[1] : text;       // Return email if found, otherwise the original text
    };

    // Create an object to store all email select fields
    const getContacts = (field, selector) => {
      return field.map((value) => {
        const text = selector.find(`option[value="${value}"]`).text();
        const email = extractEmail(text);
        if (!isNaN(value)) {
          return { id: Number(value), email: email };
        } else {
          return { email: value };
        }
      });
    };

    const contacts = [
      {
        to: getContacts($emailTo, $('#emailTo')),
        cc: getContacts($emailCc, $('#emailCc')),
        bcc: getContacts($emailBcc, $('#emailBcc'))
      }
    ];

    // Generate the email based on the prompt
    generateNewEmail(contacts, $instruction, $languageTone, $emailLength, $emailFromId).then((response) => {
      const $chat_id = response.chat_id; // Get the chat ID
      const $output = response.output; // Get the email output
      const $subject = $output.subject; // Get the email subject
      const $email = $output.body; // Get the email body
      const $messageId = response.assistant_message_id; // Get the message ID
      const $chatBot = $('#chatBot'); // Get the chat bot

      createChatBot($chat_id); // Create the chat bot interface
      sendMessage('user', $instruction); // Send the user message to the chat box

      createEmail($subject, $email, $messageId, true); // Create the email message
      toast('Email generated successfully.', 'success'); // Display a success toast message
      $generateBtn.text('Generate Email'); // Change the generate email button text
      chatHistory(); // Refresh the chat history
      window.scrollBy(0, $chatBot[0].scrollHeight); // Scroll to the chat bot
      history.pushState(null, null, `/dashboard?chat=${$chat_id}`); // Change the URL to the chat ID
    }).catch((error) => {
      error_message = error.message ? error.message : "An error occurred";
      // Display an error message
      toast(error_message, "error");
      $generateBtn.text('Generate Email'); // Change the generate email button text
      $emailPrompt.prop('disabled', false); // Enable the email prompt text area
      $promptPreset.prop('disabled', false); // Enable the prompt preset select field
      $generateBtn.prop('disabled', false); // Enable the generate email button
    });
  });
}

/**
 * Send an email
 */
function emailSend() {
  const $sendBtn = $('.sendEmail');
  const $generatedSections = $('#generatedSections');
  const $chatBot = $('#chatBot');
  const $chatId = parseInt($('#chatId').val());

  $sendBtn.on('click', function () {
    const $emailFrom = $('#emailFrom').val();
    if (!$emailFrom) {
      toast('Please select an email account.', 'error');
      return;
    }

    const $emailSubject = $('.email-subject').last().text();
    const $emailBody = $('.email-body').last().text();
    const $emailTo = $('#emailTo').val();
    const $emailCc = $('#emailCc').val();
    const $emailBcc = $('#emailBcc').val();

    if (!$emailTo || $emailTo.length === 0) {
      toast('Please select at least one recipient.', 'error');
      return;
    }

    const $bodyHtml = $('.email-body').last().html();
    const $emailFooter = `<hr class="email-template-hr"><p class="email-template-footer">Generated with <a href="https://daryandev.com" target="_blank">DaryanDev - Easy-Email</a></p>`;
    const $emailTemplate = `
      <h5>${$emailSubject}</h5>
      <div class="email-template-body">
        <div style="text-align: left; color: #555; font-size: 14px; font-family: Arial, sans-serif;">
          ${$bodyHtml}
        </div>
        ${$emailFooter}
      </div>`;

    Swal.fire({
      title: 'Preview Email',
      html: $emailTemplate,
      width: 800,
      showCancelButton: true,
      confirmButtonText: '<i class="bi bi-send-fill me-2"></i>Send Email',
      cancelButtonText: '<i class="bi bi-x-lg me-2"></i> Cancel',
      customClass: {
        confirmButton: 'btn btn-primary px-4',
        cancelButton: 'btn px-4 text-white',
        popup: 'rounded-4 shadow'
      }
    }).then((result) => {
      if (!result.isConfirmed) return;

      $sendBtn.prop('disabled', true).html(`
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Sending Email...
      `);

      const formatRecipients = (list) => {
        return (list || []).map(value => !isNaN(value) ? { id: Number(value) } : { email: value });
      };

      const contacts = [{
        to: formatRecipients($emailTo),
        cc: formatRecipients($emailCc),
        bcc: formatRecipients($emailBcc)
      }];

      sendEmail($chatId, contacts, $emailSubject, $emailBody, $emailFrom).then(() => {
        toast('Email sent successfully.', 'success');
        $generatedSections.empty();
        $chatBot.empty();

        $generatedSections.append(`
          <div class="card shadow-sm border-0 rounded-4">
            <div class="card-body text-center py-5">
              <i class="bi bi-check-circle-fill text-success fs-1 mb-3"></i>
              <h5 class="card-title fw-bold">Email Sent</h5>
              <p class="card-text text-muted mb-4">Your email has been sent successfully.</p>
              <button class="btn btn-primary px-4 py-2 startEmail">
                <i class="bi bi-arrow-repeat me-2"></i> Start Over
              </button>
            </div>
          </div>
        `).fadeIn(500);

        startEmail();

      }).catch((error) => {
        const message = error.message || "An error occurred";
        toast(message, "error");
        sendMessage('bot', message);
        $sendBtn.html('<i class="bi bi-send-fill"></i> Send Email').prop('disabled', false);
      });
    });
  });
}


/**
 * Account linking helper function
 */
function fromQuestion() {
  const $fromQuestion = $('#fromQuestion'); // Get the from question icon

  // Add a click event listener to the from question icon
  $fromQuestion.on('click', function () {
    showFromQuestion(); // Show the from question dialog
  });
}

/**
 * Show the from question dialog
 */
function showFromQuestion() {
  // Display the from question dialog
  Swal.fire({
    icon: 'info',
    title: '<strong>Link Your Email Account</strong>',
    html: `
    <div class="text-start">
      <p>
        To continue using <span class="fw-bold text-primary">Easy-Email</span>, you must authorize access to your email account.
        This is required to <strong>generate</strong> and <strong>send emails</strong> on your behalf.
      </p>
    </div>
  `,
    showCancelButton: true,
    confirmButtonText: '<i class="bi bi-link-45deg me-2"></i> Link Account',
    cancelButtonText: '<i class="bi bi-x-lg me-2"></i> Cancel',
    buttonsStyling: false,
    customClass: {
      popup: 'rounded-4 shadow border-0',
      confirmButton: 'btn btn-primary px-4 me-2',
      cancelButton: 'btn btn-danger px-4 text-white'
    }
  }).then((result) => {
    if (result.isConfirmed) {
      window.location.href = '/profile/link';
    }
  });
}

/**
 * Initialize the email generation process
 * @param {object} section - The section to append the email generation form
 */
function generateSection(section) {
  section.append(`
    <div class="card email-card shadow rounded-4 border-0">
      <div class="card-body">
        <h5 class="card-title">Generate Email</h5>
        <div class="card-text">
          <form class="needs-validation" autocomplete="off" id="generateEmail" novalidate>
            <div class="row">
              <div class="col-12">
                <div class="form-group mb-3 has-validation">
                  <label for="emailFrom">
                  From
                  <span class="text-danger">*</span>
                  <i class="bi bi-patch-question-fill" id="fromQuestion" data-bs-toggle-tt="tooltip-html" data-bs-title="Link your account at <a href='/profile/link'>/profile/link</a>"></i>
                  </label>
                  <select class="form-control" id="emailFrom" required>
                  </select>
                  <div class="invalid-feedback">Please select one of your email addresses.</div>
                </div>
                <div class="form-group mb-3 has-validation">
                  <label for="emailTo">To<span class="text-danger">*</span></label>
                  <select class="form-control" id="emailTo" multiple="multiple" required>
                  </select>
                  <div class="invalid-feedback">Please select at least one recipient.</div>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-12 mb-3 text-center">
                <a class="btn btn-sm btn-outline-secondary" data-bs-toggle="collapse" href="#advanced" role="button" aria-expanded="false" aria-controls="advanced">
                  <i class="bi bi-sliders me-1"></i> Advanced
                </a>
              </div>
            </div>
            <div class="row collapse" id="advanced">
              <div class="col-6 mb-3">
                <div class="form-group mb-3">
                  <label for="emailCc">Cc</label>
                  <select class="form-control" id="emailCc" multiple="multiple">
                  </select>
                </div>
              </div>
              <div class="col-6 mb-3">
                <div class="form-group">
                  <label for="emailBcc">Bcc</label>
                  <select class="form-control" id="emailBcc" multiple="multiple">
                  </select>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-6 mb-3">
                <div class="form-group">
                  <label for="languageTone">Language Tone</label>
                  <select class="form-control" id="languageTone">
                    <option value="normal">🙂 Normal</option>
                    <option value="professional">👨‍💼 Professional</option>
                    <option value="academic">👩‍🎓 Academic</option>
                    <option value="casual">😎 Casual</option>
                    <option value="friendly">😊 Friendly</option>
                  </select>
                </div>
              </div>
              <div class="col-6 mb-3">
                <div class="form-group">
                  <label for="emailLength">Email Length:</label>
                  <select class="form-control" id="emailLength" name="emailLength">
                    <option value="short">Short</option>
                    <option value="medium">Medium</option>
                    <option value="long">Long</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-12 mb-3">
                <label for="instruction" class="form-label">Prompt<span class="text-danger">*</span></label>
                <div class="input-group has-validation" id="emailCustomPrompt">
                  <div class="input-group-prepend">
                    <select class="form-select" id="promptPreset">
                      <option value="custom">Custom</option>
                      <option value="meeting">Meeting</option>
                      <option value="leave_request">Leave Request</option>
                      <option value="job_application">Job Application</option>
                      <option value="complaint">Complaint</option>
                      <option value="event_invitation">Event Invitation</option>
                      <option value="resignation">Resignation</option>
                      <option value="feedback">Feedback</option>
                      <option value="thank_you">Thank You</option>
                      <option value="introduction">Introduction</option>
                    </select>
                  </div>
                  <textarea type="text" name="instruction" class="form-control" id="instruction"
                    placeholder="Write me an email about..." required></textarea>
                  <div class="invalid-feedback">Please enter your instruction.</div>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                <div class="form-group text-center">
                  <button type="submit" class="btn btn-primary" id="generateBtn">
                      <span id="generate-btn-text">
                        <i class="bi bi-stars"></i> Generate Email
                      </span>
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
`).fadeIn(500);
}

/**
 * When selecting a word, sentence, or paragraph show the context menu
 */
function emailSelection() {
  const $lastBotMessage = $('.bot-message').last();
  const $emailElements = $lastBotMessage.find('.email-body, .email-subject');

  // Destroy previous listeners
  $emailElements.off('mouseup');
  $lastBotMessage.off('mousedown', '.textSelection button');

  // Clear any existing text selection
  window.getSelection().removeAllRanges();

  // Remove text selection dropdown when clicking outside
  $(document).on('mousedown', function (e) {
    if (!$(e.target).closest('.textSelection').length) {
      $('.textSelection').remove();
    }
  });

  $emailElements.on('mouseup', function (e) {
    // Get the selected text
    const selection = window.getSelection();
    const $selectedText = selection.toString();

    const $range = window.getSelection().getRangeAt(0);

    const $toPosition = $range.endOffset;
    const $fromPosition = $range.startOffset;


    // Remove any existing dropdown before creating a new one
    $('.textSelection').remove();

    // Check if position is valid
    if ($toPosition === $fromPosition) return;

    // Check if the selected text goes beyond the email body or subject
    if (!this.contains($range.startContainer) || !this.contains($range.endContainer)) return;

    // Check if the selected text is not empty
    if ($selectedText) {
      // Get the selected text range and position
      const $range = selection.getRangeAt(0);
      const $rect = $range.getBoundingClientRect();
      const $top = $rect.top + window.scrollY + 20;
      const $left = $rect.left + window.scrollX;

      // Remove spaces from the start and end of the selected text
      const hasLeadingSpace = $selectedText.startsWith(' ');
      const hasTrailingSpace = $selectedText.endsWith(' ');
      const hasLeadingNewline = $selectedText.startsWith('\n');
      const hasTrailingNewline = $selectedText.endsWith('\n');
      const trimmedSelectedText = $selectedText.trim();
      const textType = $(this).hasClass('email-body') ? 'body' : 'subject';

      // Create the dropdown
      const $newDropdown = $(`
        <div class="dropdown-menu show textSelection shadow rounded-4 border-0" data-selected-type="${textType}" data-selected-text="${trimmedSelectedText}" data-leading-space="${hasLeadingSpace}" data-trailing-space="${hasTrailingSpace}" data-leading-newline="${hasLeadingNewline}" data-trailing-newline="${hasTrailingNewline}" style="top: ${$top}px; left: ${$left}px;">
          <h6 class="dropdown-header">Selected Text</h6>
          <button class="dropdown-item" id="copyText">
            <i class="bi bi-clipboard"></i> Copy
          </button>
          <button class="dropdown-item" id="paraphraseText">
            <i class="bi bi-pencil"></i> Paraphrase
          </button>
        </div>
      `);

      // Append and show the dropdown
      $('body').append($newDropdown);
      $newDropdown.hide().fadeIn(200); // Use fadeIn for smoother appearance
    }
  });

  // Prevent default behavior for buttons in the dropdown
  $lastBotMessage.on('mousedown', '.textSelection button', function (e) {
    e.preventDefault(); // Prevent text selection when clicking the buttons
  });

  // Destroy pervious copy and text selection listeners
  $(document).off('click', '#copyText');
  $(document).off('click', '#paraphraseText');

  // When copying the selected text
  $(document).on('click', '#copyText', function () {
    const $selectedText = $('.textSelection').data('selected-text');
    navigator.clipboard.writeText($selectedText);
    toast('Text copied to clipboard.', 'success');
    $('.textSelection').remove();
  });

  // When paraphrasing the selected text
  $(document).on('click', '#paraphraseText', function () {
    const $selectedText = $('.textSelection').data('selected-text');
    const $selectedType = $('.textSelection').data('selected-type');
    const $message_id = $('#messageId').val();

    $(this).prop('disabled', true);
    $(this).html(`
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Paraphrasing...
    `);

    let $fromPosition;
    let $toPosition;

    if ($selectedType === 'body') {
      $fromPosition = $lastBotMessage.find('.email-body').text().indexOf($selectedText);
      $toPosition = $fromPosition + $selectedText.length;
    } else {
      $fromPosition = $lastBotMessage.find('.email-subject').text().indexOf($selectedText);
      $toPosition = $fromPosition + $selectedText.length;
    }


    // Check if the selected text has leading or trailing spaces or newlines
    const $leadingSpace = $('.textSelection').data('leading-space');
    const $trailingSpace = $('.textSelection').data('trailing-space');
    const $leadingNewline = $('.textSelection').data('leading-newline');
    const $trailingNewline = $('.textSelection').data('trailing-newline');


    const $position = {
      'to': $toPosition,
      'from': $fromPosition,
      'leadingSpace': $leadingSpace,
      'trailingSpace': $trailingSpace,
      'leadingNewline': $leadingNewline,
      'trailingNewline': $trailingNewline
    }

    paraphrase($selectedText, $message_id, $selectedType, $position).then((response) => {
      let $newText = response.paraphrase;

      // Show confirmation dialog
      Swal.fire({
        title: 'Paraphrase',
        html: `
          <mark class="paraphrase-text text-remove">${$selectedText}</mark>
          <p class="text-separator">will be replaced with</p>
          <mark class="paraphrase-text text-add">${$newText}</mark>
        `,
        showCancelButton: true,
        confirmButtonText: 'Replace',
        cancelButtonText: 'Cancel'
      }).then((result) => {
        updateParaphrase($message_id).then((response) => {
          const $subject = response.subject;
          const $email = response.body;

          // Update the email subject and body
          $('.email-subject').last().text($subject);
          $('.email-body').last().html($email);
        }).catch((error) => {
          error_message = error.message ? error.message : "An error occurred";
          // Display an error message
          toast(error_message, "error");
        });
      });

      // Remove the dropdown
      $('.textSelection').remove();
    }).catch((error) => {
      error_message = error.message ? error.message : "An error occurred";
      // Display an error message
      toast(error_message, "error");
    });
  });
}

/**
 * Initialize the email generation process
 */
function emailInit() {
  $(startEmail); // Start the email generation process
}

$(emailInit); // Initialize all functions