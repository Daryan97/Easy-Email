function selectInboxDropdowns() {
    const $inboxSection = $('#inboxSection');

    if ($inboxSection.length === 0) return;
    const $selectInbox = $('<select id="selectInbox"></select>');
    $inboxSection.append($selectInbox);
    getLinkedAccounts().then((linkedAccounts) => {
        $selectInbox.append('<option value="" disabled selected>Select Inbox</option>');
        linkedAccounts.forEach((account) => {
            $selectInbox.append(`<option value="${account.id}" data-service="${account.service}">${account.email}</option>`);
        });
    });

    $selectInbox.select2({
        tags: false,
        dropdownAutoWidth: true,
        selectAutoWidth: false,
        width: '150px',
    });

    $selectInbox.on('change', function () {
        const accountId = $(this).val();
        const service = $(this).find(':selected').data('service');

        $selectInbox.attr('disabled', true);

        $(createInbox(service, accountId));
    });
}

let page_tracker = [];
let next_page_tracker = null;

function createInbox($service, $id) {
    const $inboxTabs = $('#inboxTabs');
    const $inboxContent = $('#inboxContent');

    if (!$inboxTabs.length || !$inboxContent.length) return;

    // Clear previous inbox and show loading
    $inboxTabs.html(`
    <div class="text-center py-3">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  `);
    $inboxContent.html(`
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  `);

    // Fetch folders
    getLinkedAccountFolders($service, $id).then((folders) => {
        $inboxTabs.empty();

        if (!folders.length) {
            $inboxTabs.html('<div class="text-center text-muted">No folders found.</div>');
            return;
        }

        // Sort with "Inbox" first
        const sortedFolders = folders
            .filter(f => !(f.isHidden || f.messageCount === 0 || f.name.startsWith('Category_')))
            .sort((a, b) => {
                if (a.name.toLowerCase() === 'inbox') return -1;
                if (b.name.toLowerCase() === 'inbox') return 1;
                return a.name.localeCompare(b.name);
            });

        if (!sortedFolders.length) {
            $inboxTabs.html('<div class="text-center text-muted">No visible folders.</div>');
            return;
        }

        const $ul = $('<ul class="nav nav-tabs inbox-tabs gap-1"></ul>');
        let isFirst = true;

        sortedFolders.forEach(folder => {
            const folderName = folder.name;
            const unread = folder.unreadCount;
            const isActive = isFirst ? 'active' : '';
            const ariaSelected = isFirst ? 'true' : 'false';

            const $tab = $(`
        <li class="nav-item" role="presentation">
          <button class="nav-link ${isActive}" type="button"
            data-bs-toggle="tab"
            data-bs-target="#${folderName}"
            data-folder="${folderName}"
            aria-selected="${ariaSelected}">
            ${folderName}
            ${unread > 0 ? `<span class="badge bg-primary ms-2">${unread}</span>` : ''}
          </button>
        </li>
      `);

            $ul.append($tab);
            isFirst = false;
        });

        // Append tabs
        $inboxTabs.append($ul);

        // Load first folder
        const firstFolder = sortedFolders[0].name;
        getMessages($service, $id, firstFolder);

        // Event binding
        $inboxTabs.off('click').on('click', '.nav-link', function () {
            const folderName = $(this).data('folder');
            $('#searchEmailInput').val('');
            getMessages($service, $id, folderName);
            refreshTabs();
            page_tracker = [];
            next_page_tracker = null;
        });

    }).catch((error) => {
        const message = error.message || 'An error occurred';
        toast(message, 'error');
        $inboxTabs.empty();
        $inboxContent.empty();
        $('#selectInbox').attr('disabled', false);
    });
}

function changePage() {
    const $inboxPages = $('#inboxPages');

    if (!$inboxPages.length) return;

    const $inboxSection = $('#inboxSection');
    const $inboxTabs = $('#inboxTabs');
    const inboxId = $inboxSection.find('#selectInbox').val();
    const service = $inboxSection.find('#selectInbox').find(':selected').data('service');
    const folderName = $inboxTabs.find('.nav-link.active').data('bs-target').replace('#', '');

    $inboxPages.empty();

    if (next_page_tracker) {
        $inboxPages.append(`
            <li class="page-item w-100 text-center mt-3">
                <button class="btn btn-outline-primary px-4 py-2 fw-semibold rounded-pill shadow-sm" data-page="next">
                <i class="bi bi-arrow-down-circle me-2"></i> Load More
                </button>
            </li>
            `);

    }

    $next = $inboxPages.find('[data-page="next"]');

    $next.off('click');

    $next.on('click', function () {
        getMessages(service, inboxId, folderName, next_page_tracker, null, 10);
        page_tracker.push(next_page_tracker);
    });
}

function searchEmails() {
    const $searchInput = $('#searchEmailInput');
    const $searchButton = $('#searchEmailBtn');

    if (!$searchInput.length || !$searchButton.length) return;

    $searchButton.on('click', function () {
        const $inboxSection = $('#inboxSection');
        const $inboxTabs = $('#inboxTabs');
        const inboxId = $inboxSection.find('#selectInbox').val();
        const service = $inboxSection.find('#selectInbox').find(':selected').data('service');
        const folderName = $inboxTabs.find('.nav-link.active').data('bs-target').replace('#', '');
        const query = $searchInput.val();

        getMessages(service, inboxId, folderName, null, query, 10);
    });

    $searchInput.on('keypress', function (e) {
        if (e.which === 13) {
            const $inboxSection = $('#inboxSection');
            const $inboxTabs = $('#inboxTabs');
            const inboxId = $inboxSection.find('#selectInbox').val();
            const service = $inboxSection.find('#selectInbox').find(':selected').data('service');
            const folderName = $inboxTabs.find('.nav-link.active').data('bs-target').replace('#', '');
            const query = $searchInput.val();

            getMessages(service, inboxId, folderName, null, query, 10);
        }
    });
}

function getMessages($service, $id, $folderName, $next_page = null, $query = null, $max_results = 10) {
    const $inboxContent = $('#inboxContent');

    if (!$inboxContent.length) return;

    const $inboxTabs = $('#inboxTabs');
    const $inboxSection = $('#selectInbox');
    const $emailSearchInput = $('#searchEmailInput');
    const $emailSearchButton = $('#searchEmailBtn');
    const $nextPage = $('#inboxPages');

    $inboxTabs.find('.nav-link').attr('disabled', true);
    $inboxSection.attr('disabled', true);
    $emailSearchInput.attr('disabled', true);
    $emailSearchButton.attr('disabled', true);

    if (!$next_page) {
        $inboxContent.empty();
        $nextPage.empty();
        $inboxContent.append(`<div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div></div>`);
    } else {
        $nextPage.find('[data-page="next"]')
            .attr('disabled', true)
            .html(`<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`);
    }

    getInboxMessages($service, $id, $folderName, $max_results, $query, $next_page).then((messages) => {
        $nextPage.empty();

        if (!messages || !messages.messages.length) {
            if (!$next_page) {
                $inboxContent.empty();
                $inboxContent.append('<div class="text-center">No messages found.</div>');
            }
            $inboxTabs.find('.nav-link').attr('disabled', false);
            $inboxSection.attr('disabled', false);
            $emailSearchInput.attr('disabled', false);
            $emailSearchButton.attr('disabled', false);
            return;
        }

        const $messages = messages.messages;
        const $nextPageVal = messages.next_page;

        let $messageList = $inboxContent.find('.message-list');
        if (!$messageList.length) {
            $messageList = $('<div class="message-list"></div>');
            $inboxContent.empty().append($messageList);
        }

        function getDateCategory(date) {
            const today = new Date();
            const diffDays = Math.floor((today - date) / (1000 * 60 * 60 * 24));

            if (diffDays === 0) return "Today";
            if (diffDays === 1) return "Yesterday";
            if (diffDays < 7) return "Last 7 Days";
            if (diffDays < 30) return "Last 30 Days";
            if (diffDays < 60) return "Last 60 Days";
            if (diffDays < 90) return "Last 90 Days";
            if (diffDays < 180) return "Last 180 Days";
            if (diffDays < 365) return "Last 365 Days";
            return "Older";
        }

        let lastCategory = null;

        $messages.forEach((message) => {
            const $messageData = message.message;
            const $messageId = message.id;
            const $from = $messageData.from ? $messageData.from.replace(/</g, '&lt;').replace(/>/g, '&gt;') : 'No Sender';
            const $subject = $messageData.subject ? $messageData.subject.replace(/</g, '&lt;').replace(/>/g, '&gt;') : 'No Subject';
            const $dateStr = $messageData.date;
            const $isRead = $messageData.isRead;
            const $attachments = $messageData.attachments;

            const $date = new Date($dateStr);
            const currentCategory = getDateCategory($date);

            if (currentCategory !== lastCategory) {
                $messageList.append(`<div class="text-muted fw-semibold border-bottom pb-1 mt-4 mb-2">${currentCategory}</div>`);
                lastCategory = currentCategory;
            }

            const isUnreadClass = !$isRead ? 'fw-bold border-start border-4 border-primary bg-light unread' : '';
            const attachmentIcon = $attachments.length > 0
                ? `<i class="bi bi-paperclip text-muted me-2" title="${$attachments.length} attachment${$attachments.length > 1 ? 's' : ''}"></i>`
                : '';

            $messageList.append(`
              <div class="card mb-2 mt-2 shadow-sm email-row ${isUnreadClass}" data-id="${$messageId}" data-read="${$isRead}">
                <div class="card-body d-flex align-items-center justify-content-between">
                  <div class="form-check me-3">
                  </div>
                  <div class="flex-grow-1 me-3" style="min-width: 0;">
                    <div class="d-flex justify-content-between align-items-center">
                      <div class="text-truncate" style="max-width: 60%;">
                        ${!$isRead ? `<b>${$from}</b>` : $from}
                      </div>
                      <small class="text-muted text-nowrap">${$date.toDateString()} ${$date.toLocaleTimeString()}</small>
                    </div>
                    <div class="text-truncate mt-1">
                      ${!$isRead ? `<b>${$subject}</b>` : $subject} ${attachmentIcon}
                    </div>
                  </div>
                  <div class="text-end">
                    <button type="button" class="btn btn-sm btn-outline-danger deleteMessage" title="Delete Message">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            `);
        });

        next_page_tracker = $nextPageVal;
        $(changePage);

        // if ($next_page) {
        //     $('html, body').animate({ scrollTop: $('#inboxPages').offset().top }, 400);
        // }

        $('.email-row').off('click').on('click', function () {
            const $emailRow = $(this);
            const $emailId = $emailRow.data('id');
            const $isRead = $emailRow.data('read');
            if (!$isRead) {
                messageAction($service, $id, $emailId, 'read').then(() => {
                    refreshTabs();
                }).catch((error) => {
                    toast(error.message || "An error occurred", "error");
                });
            }
            getMessage($service, $id, $emailId);
        });

        $('.deleteMessage').off('click').on('click', function (e) {
            e.stopPropagation();

            Swal.fire({
                title: '<i class="bi bi-trash text-danger me-2"></i> Confirm Deletion',
                html: `
      <div class="text-muted">
        This action will <b>permanently delete</b> the selected message.<br>
        <small>This cannot be undone.</small>
      </div>
    `,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: '<i class="bi bi-check-circle-fill me-1"></i> Yes, Delete',
                cancelButtonText: '<i class="bi bi-x-circle-fill me-1"></i> Cancel',
                customClass: {
                    confirmButton: 'btn btn-danger',
                    cancelButton: 'btn ms-2 btn-secondary bg-secondary',
                },
                buttonsStyling: false,
                focusCancel: true,
            }).then((result) => {
                if (result.isConfirmed) {
                    const $emailRow = $(this).closest('.email-row');
                    const $emailId = $emailRow.data('id');

                    const $prevRow = $emailRow.prev();
                    const $nextRow = $emailRow.next();

                    const $prevRowCategory = $prevRow.hasClass('text-muted');
                    const $nextRowCategory = $nextRow.hasClass('text-muted');

                    messageAction($service, $id, $emailId, 'delete').then((data) => {
                        if (data.message === 'Message deleted successfully.') {
                            Swal.fire({
                                icon: 'success',
                                title: 'Deleted!',
                                text: 'The message was removed.',
                                timer: 1500,
                                showConfirmButton: false
                            });

                            if ($prevRowCategory && $nextRowCategory) {
                                $prevRow.remove();
                            }

                            if ($prevRow.hasClass('text-muted') && $nextRow.hasClass('text-muted')) {
                                $prevRow.remove();
                            }

                            $emailRow.remove();
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Oops!',
                                text: 'Something went wrong while deleting the message.',
                            });
                        }
                    }).catch((error) => {
                        toast(error.message || "An error occurred", "error");
                    });
                }
            });
        });


        $inboxTabs.find('.nav-link').attr('disabled', false);
        $inboxSection.attr('disabled', false);
        $emailSearchInput.attr('disabled', false);
        $emailSearchButton.attr('disabled', false);

        $(enableBSTooltips);
    });
}

function unlockInboxUI() {
    $('#inboxTabs .nav-link').attr('disabled', false);
    $('#selectInbox').attr('disabled', false);
    $('#searchEmailInput').attr('disabled', false);
    $('#searchEmailBtn').attr('disabled', false);
}


function refreshTabs() {

    const $inboxTabs = $('#inboxTabs');

    if (!$inboxTabs.length) return;
    const $activeTab = $('#inboxTabs').find('.nav-link.active');

    const $ul = $('<ul class="nav nav-tabs"></ul>');

    $inboxTabs.find('.nav-link').attr('disabled', true);
    const $inboxSection = $('#inboxSection');
    const $id = $inboxSection.find('#selectInbox').val();
    const $service = $inboxSection.find('#selectInbox').find(':selected').data('service');

    getLinkedAccountFolders($service, $id).then((folders) => {
        $inboxTabs.empty();
        const sortedFolders = folders.sort((a, b) => {
            if (a.name.toLowerCase() === 'inbox') return -1;
            if (b.name.toLowerCase() === 'inbox') return 1;
            return 0;
        });

        sortedFolders.forEach((folder) => {
            const $folderName = folder.name;
            const $unreadCount = folder.unreadCount;
            const $isHidden = folder.isHidden || folder.messageCount === 0 || folder.name.startsWith('Category_');
            if ($isHidden) return;

            const activeClass = $folderName === $activeTab.data('folder') ? 'active' : '';
            const ariaSelected = $folderName === $activeTab.data('folder') ? 'true' : 'false';

            $ul.append(`<li class="nav-item">
                <button class="nav-link ${activeClass}" id="nav-profile-tab" data-bs-toggle="tab" data-bs-target="#${$folderName}"
                  type="button" role="tab" data-folder="${$folderName}" aria-controls="${$folderName}" aria-selected="${ariaSelected}">
                  <div>${$folderName}</div> ${`<span class="badge bg-primary">${$unreadCount}</span>`}
                </button>
              </li>`);
        });

        $inboxTabs.append($ul);
    }).catch((error) => {
        error_message = error.message ? error.message : "An error occurred";
        // Display an error message
        toast(error_message, "error");
    });
}

function getMessage($service, $id, $emailId) {
    const $inboxContent = $('#inboxContent');
    if (!$inboxContent.length || !$emailId || !$service || !$id) return;

    const $inboxPages = $('#inboxPages');
    $inboxPages.empty();
    $inboxContent.empty().append(`
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>`);

    getInboxMessage($service, $id, $emailId).then((email) => {
        const $emailBody = email.body || 'No content';
        const $emailSubject = email.subject || 'No subject';
        const $emailDateStr = email.date || 'Unknown date';
        const $emailDate = new Date($emailDateStr);
        const $emailAttachments = email.attachments || [];

        const parseAddress = (address) => {
            if (!address) return { name: 'Unknown', email: '' };
            const parts = address.split(' <');
            return {
                name: parts[0],
                email: parts[1] ? parts[1].replace('>', '') : parts[0]
            };
        };

        const from = parseAddress(email.from);
        const to = parseAddress(email.to);
        const cc = email.cc ? parseAddress(email.cc) : null;
        const bcc = email.bcc ? parseAddress(email.bcc) : null;

        const displayNameEmail = (obj) => {
            if (!obj) return '';
            if (obj.name === obj.email) {
                return `<span class="text-dark" id="fromEmail">${obj.email}</span>`;
            } else {
                return `<span class="text-dark" id="fromName">${obj.name}</span><br><small class="text-muted" id="fromEmail">${obj.email}</small>`;
            }
        };

        const $emailContent = `
          <div class="card">
        <div class="card-body">
          <div class="email-head-subject mb-4">
            <div id="emailId" class="d-none">${$emailId}</div>
            <div class="form-floating">
              <input type="text" class="form-control" id="emailSubject" value="${$emailSubject}" readonly>
              <label for="emailSubject">Subject</label>
            </div>
          </div>

          <div class="row mb-3">
            <div class="col-md-6">
              <div class="mb-2">
            <div class="fw-semibold mb-1">From:</div>
            <div class="text-break">
              ${displayNameEmail(from)}
            </div>
              </div>
              <div class="mb-2">
            <div class="fw-semibold mb-1">To:</div>
            <div class="text-break">
              ${displayNameEmail(to)}
            </div>
              </div>
              ${cc ? `
              <div class="mb-2">
            <div class="fw-semibold mb-1">CC:</div>
            <div class="text-break">
              ${displayNameEmail(cc)}
            </div>
              </div>` : ''}
              ${bcc ? `
              <div class="mb-2">
            <div class="fw-semibold mb-1">BCC:</div>
            <div class="text-break">
              ${displayNameEmail(bcc)}
            </div>
              </div>` : ''}
            </div>
            <div class="col-md-6 text-md-end mt-3 mt-md-0">
              <div class="email-date text-muted small">
            <i class="bi bi-calendar3 me-1"></i>${$emailDate.toDateString()}<br>
            <i class="bi bi-clock me-1"></i>${$emailDate.toLocaleTimeString()}
              </div>
            </div>
          </div>

          <hr>

          <div class="email-body mb-4">
            <iframe id="emailContentIframe" style="width: 100%; height: 750px; border: 1px solid #dee2e6; border-radius: .5rem;" class="shadow-sm"></iframe>
          </div>

          ${$emailAttachments.length > 0 ? `
            <div class="email-attachments mb-4">
              <h6 class="fw-bold">Attachments</h6>
              <ul class="list-group list-group-flush">
            ${$emailAttachments.map((attachment) => `
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <div><i class="bi bi-paperclip me-2"></i>${attachment.filename}</div>
                <div>
                  <span class="text-muted small me-3">${attachment.size} KB</span>
                  <button class="btn btn-sm btn-outline-primary">Download</button>
                </div>
              </li>`).join('')}
              </ul>
            </div><hr>` : ''}

        <div class="email-head-subject mt-4">
        <div class="d-flex flex-wrap align-items-center gap-3">
            <button class="btn btn-primary rounded-pill px-4 shadow-sm d-flex align-items-center" id="smartReply">
            <i class="bi bi-lightbulb me-2 fs-5"></i>
            <span class="fw-semibold">Smart Reply</span>
            </button>

            <button class="btn btn-secondary rounded-pill px-4 shadow-sm d-flex align-items-center" id="replyEmail">
            <i class="bi bi-reply me-2 fs-5"></i>
            <span class="fw-semibold">Write a Reply</span>
            </button>
        </div>
        </div>
        <div class="container mt-3" id="generatereplyEmail"></div>
          </div>`;

        $inboxContent.empty().append($emailContent);

        const $emailContentIframe = $('#emailContentIframe');
        $emailContentIframe.contents().find('html').html($emailBody);
        $emailContentIframe.contents().find('a').attr('target', '_blank');

        replyEmail();
    });

    copyMenu();
}

function replyEmail() {
    const $generateReplyEmail = $('#generatereplyEmail');

    if (!$generateReplyEmail.length) return;
    $generateReplyEmail.empty();

    const $replyEmail = $('#replyEmail');

    $replyEmail.off('click');

    $replyEmail.on('click', function () {
        createReplyEmail();
    });

    smartReply();
}

function smartReply() {
    const $smartReply = $('#smartReply');
    if (!$smartReply.length) return;

    $smartReply.off('click');

    $smartReply.on('click', function () {
        Swal.fire({
            title: '<i class="bi bi-lightbulb-fill text-warning me-2"></i> Smart Reply',
            input: 'textarea',
            inputLabel: 'Enter your instruction:',
            inputPlaceholder: 'Type your instruction here...',
            inputAttributes: {
                'aria-label': 'Smart reply instruction',
                'style': 'resize: none;',
                'id': 'smartInstruction'
            },
            showCancelButton: true,
            confirmButtonText: '<i class="bi bi-robot me-1"></i> Generate',
            cancelButtonText: '<i class="bi bi-x-circle-fill me-1"></i> Cancel',
            customClass: {
                confirmButton: 'btn btn-primary',
                cancelButton: 'btn ms-2 btn-secondary bg-secondary'
            },
            buttonsStyling: false,
            showLoaderOnConfirm: true,
            inputValidator: (value) => {
                if (!value) {
                    return 'Instructions are required!';
                }
            },
            preConfirm: (instruction) => {
                const $emailSubject = $('#emailSubject').val();
                const $iframe = $('#emailContentIframe').contents();
                const $emailBody = $iframe.find('html').html();
                let $emailSender;
                const $fromName = $('#fromName').text().trim();
                const $fromEmail = $('#fromEmail').text().trim();
                if ($fromName && $fromEmail && $fromName !== $fromEmail) {
                    $emailSender = `${$fromName} <${$fromEmail}>`;
                } else {
                    $emailSender = $fromEmail;
                }
                const $oauthId = Number($('#selectInbox').val());

                return generateSmartReply($emailSubject, $emailBody, $emailSender, instruction, $oauthId)
                    .then((data) => {
                        return data.reply;
                    })
                    .catch((error) => {
                        Swal.showValidationMessage(`Request failed: ${error.message || error}`);
                    });
            },
            allowOutsideClick: () => !Swal.isLoading()
        }).then((result) => {
            if (result.isConfirmed) {
                createReplyEmail(result.value);
                toast('Smart reply generated successfully.', 'success');
            }
        });
    });
}

function createReplyEmail(content = '') {
    const $generateReplyEmail = $('#generatereplyEmail');

    if (!$generateReplyEmail.length) return;

    $generateReplyEmail.empty();

    const $emailSubject = $('#emailSubject').val();

    $generateReplyEmail.append(`<div class="card">
    <div class="card-body">
        <div class="email-head">
            <div class="email-head-subject">
                <div class="row p-3">
                    <div class="form-group">
                        <div class="form-floating">
                            <input type="text" class="form-control" id="replySubject" value="Re: ${$emailSubject.trim()}">
                            <label for="replySubject">Subject</label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="email-body p-3">
            <div id="replyContent" rows="10"></div>
        </div>
        <div class="email-head-subject p-3">
            <div class="title d-flex align-items-center justify-content-end">
                <div class="icons icons d-flex justify-content-start">
                    <button class="btn btn-primary m-1" id="sendReplyEmail">
                        <i class="bi bi-reply"></i>
                        <span>Send Reply</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>`);


    const toolbarOptions = [
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],

        [{ 'font': [] }],
        [{ 'align': [] }],

        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        ['link', 'image'],

        [{ 'list': 'ordered' }, { 'list': 'bullet' }, { 'list': 'check' }],
        [{ 'indent': '-1' }, { 'indent': '+1' }],
        [{ 'direction': 'rtl' }],

        ['clean']
    ];

    const $replyQuill = new Quill('#replyContent', {
        theme: 'snow',
        modules: {
            toolbar: toolbarOptions,
        },
        placeholder: 'Compose your reply here...',
    });

    if (content) {
        // Change the text to HTML, each new line is a new paragraph
        const lines = content.split('\n');
        const htmlLines = lines.map((line) => `<p>${line}</p>`);
        const htmlContent = htmlLines.join('');
        $replyQuill.root.innerHTML = htmlContent;
    }

    $(sendReplyEmail);
}

function sendReplyEmail() {
    const $sendReplyEmail = $('#sendReplyEmail');

    if (!$sendReplyEmail.length) return;

    $sendReplyEmail.off('click');

    $sendReplyEmail.on('click', function () {
        const $emailId = $('#emailId').text();
        const $replyContent = $('#replyContent').find('.ql-editor').html();
        const $replySubject = $('#replySubject').val().trim();
        const $textLength = $replyContent.replace(/<[^>]*>?/gm, '').trim().length;

        if ($textLength === 0) {
            toast('Reply content cannot be empty.', 'error');
            return;
        }

        const $inboxSection = $('#inboxSection');
        const $id = $inboxSection.find('#selectInbox').val();
        const $service = $inboxSection.find('#selectInbox').find(':selected').data('service');

        $sendReplyEmail.attr('disabled', true);
        $sendReplyEmail.html(`<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...`);

        replyInboxMessage($service, $id, $emailId, $replyContent, $replySubject).then((data) => {
            const $response = data.message;
            toast($response, 'success');

            const $generateReplyEmail = $('#generatereplyEmail');
            $generateReplyEmail.empty();
        }).catch((error) => {
            error_message = error.message ? error.message : "An error occurred";
            // Display an error message
            toast(error_message, "error");
            $sendReplyEmail.attr('disabled', false);
            $sendReplyEmail.html(`<i class="bi bi-reply"></i> Send`);
        });
    });
}

function copyMenu() {
    $(document).on('click', '.dropdown-menu button', function () {
        const $button = $(this);
        const $text = $button.find('span').last().text();
        copyToClipboard($text);
    });


    $(document).on('click', '#copyDate', function () {
        const date = $(this).find('span').eq(0).text();
        if (date) copyToClipboard(date.trim());
    });

}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
            .then(() => toast("Text copied to clipboard.", "success"))
            .catch(err => toast("Failed to copy text to clipboard.", "error"));
    } else {
        toast("Clipboard access is not available.", "error");
    }
}

function init() {
    $(selectInboxDropdowns);
    $(searchEmails);
}

$(init);