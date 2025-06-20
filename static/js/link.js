function linkedAccounts() {
    const $linkList = $('#link-list');

    if (!$linkList.length) {
        return;
    }

    $linkList.empty();
    $linkList.append(`<div class="text-center">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div></div>`);

    getLinkedAccounts().then((data) => {
        $linkList.empty();
        if (!data.length) {
            $linkList.append('<div class="text-center">No linked accounts.</div>');
            return;
        }
        data.forEach((account) => {
            const service_logo = `https://logo.clearbit.com/${account.service}.com`;

            $linkList.append(`
            <div class="row d-flex m-2 align-items-center justify-content-center" >
              <div class="col-md-2 col-12 text-center mb-4">
                <img src="${service_logo}" width="48" draggable="false">
              </div>
              <div class="col-md-6 col-8 d-flex flex-column">
                <h5>${account.first_name} ${account.last_name}</h5>
                <h5>${account.email}</h5>
                <p class="text-muted mb-0">${account.service.charAt(0).toUpperCase() + account.service.slice(1)}</p>
              </div>
              <div class="col-md-4 col-4 text-end">
                <button type="button" class="btn btn-danger unlinkBtn" data-ac-id="${account.id}">
                <i class="bi bi-link-45deg"></i>
                Unlink
                </button>
              </div>
              </div>`);
            //   if not last element, add a line
            if (data.indexOf(account) !== data.length - 1) {
                $linkList.append('<hr>');
            }
        });
        $(unlinkAccount);
    });
}

function unlinkAccount() {
    const $unlinkBtn = $('.unlinkBtn');

    if (!$unlinkBtn.length) {
        return;
    }

    $unlinkBtn.on('click', function () {
        const id = $(this).data('ac-id');

        Swal.fire({
            title: `Unlink Account`,
            text: `Are you sure you want to unlink this account?`,
            icon: 'question',
            showCancelButton: true,
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Unlink',
            cancelButtonText: 'Cancel',
        }).then((result) => {
            if (result.isConfirmed) {
                deleteLink(id).then((data) => {
                    if (data.message === 'Acount unlinked successfully.') {
                        Swal.fire({
                            title: 'Unlinked!',
                            text: 'Acount unlinked successfully',
                            icon: 'success',
                        });
                        $(linkedAccounts);
                    } else {
                        Swal.fire({
                            title: 'Error!',
                            text: 'An error occurred while unlinking account.',
                            icon: 'error',
                        });
                    }
                });
            }
        });
    });
}

function linkAccount() {
    const $linkBtn = $('#linkAccount');

    $linkBtn.on('click', function () {
        Swal.fire({
            title: `Link Account`,
            html: `
            <div class="d-flex flex-column">
                <a href="/link/google" class="btn mb-2 btn-link-account">
                    <img src="https://logo.clearbit.com/google.com" width="16" draggable="false">
                    <span>Link Google Account</span>
                </a>
                <a href="/link/microsoft" class="btn mb-2 btn-link-account">
                    <img src="https://logo.clearbit.com/microsoft.com" width="16" draggable="false">
                    <span>Link Microsoft Account</span>
                </a>
                <button class="btn mb-2 btn-link-account">
                    <span>Manual Configuration</span>
                </button>
            </div>
            `,
            showCancelButton: false,
            showCloseButton: true,
            showConfirmButton: false,
        });
    });
}

function init() {
    $(linkedAccounts);
    $(linkAccount);
}

$(init);