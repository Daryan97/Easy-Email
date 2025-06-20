// Used to make API calls to the backend server
// Test Server: https://diyariai.daryandev.com/api
// Local Server: http://localhost:5000/api
API_URL = `https://${window.location.hostname}/api`; // Default API URL

if (window.location.hostname === 'localhost') {
    API_URL = 'http://localhost:5000/api';
}


const CSRF_TOKEN = getCookie('csrf_access_token');

function authenticate(username, password, remember = false) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/user/auth`,
            contentType: 'application/json',
            data: JSON.stringify({
                username: username,
                password: password,
                remember: remember
            }),
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function logout() {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'DELETE',
            url: `${API_URL}/user/auth`,
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                reject('Unknown error occurred.');
            }
        });
    });
}

function register(username, email, first_name, last_name, phone_code, phone_number, password, terms, privacy) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/user`,
            contentType: 'application/json',
            data: JSON.stringify({
                username: username,
                email: email,
                first_name: first_name,
                last_name: last_name,
                phone_number: phone_number,
                phone_code: phone_code,
                password: password,
                terms: terms,
                privacy: privacy
            }),
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                if (response) {
                    resolve(response);
                }
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function getProfile(user_id = null) {
    return new Promise((resolve, reject) => {
        let request_url = `${API_URL}/user` + (user_id ? `/${user_id}` : '/profile');
        $.ajax({
            type: 'GET',
            url: request_url,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function updateProfile(data) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/user/profile`,
            contentType: 'application/json',
            data: JSON.stringify(data),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                if (response) {
                    resolve(response);
                }
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function updatePassword(current_password, new_password, confirm_password) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/user/profile`,
            contentType: 'application/json',
            data: JSON.stringify({
                new_password: new_password,
                current_password: current_password,
                confirm_password: confirm_password
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                if (response) {
                    resolve(response);
                }
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function resendVerificationEmail() {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/user/verify/send`,
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                if (response) {
                    resolve(response.message);
                }
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function verifyEmail(otp) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/user/verify`,
            contentType: 'application/json',
            data: JSON.stringify({ otp: otp }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                if (response) {
                    resolve(response);
                }
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function updateEmail(email) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/user/email`,
            contentType: 'application/json',
            data: JSON.stringify({ email: email }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function getContacts(per_page = 10, page = 1) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/contact?per_page=${per_page}&page=${page}`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function getContact(contact_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/contact/${contact_id}`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function addContact(contact) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/contact`,
            contentType: 'application/json',
            data: JSON.stringify(contact),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function updateContact(contact_id, contact) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/contact/${contact_id}`,
            contentType: 'application/json',
            data: JSON.stringify(contact),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function deleteContact(contact_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'DELETE',
            url: `${API_URL}/contact/${contact_id}`,
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function generateNewEmail(contacts, instruction, languageTone, length, oauth_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/chat/generate`,
            contentType: 'application/json',
            data: JSON.stringify({
                contacts: contacts,
                instruction: instruction,
                language_tone: languageTone,
                length: length,
                oauth_id: oauth_id
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function generateModifyEmail(chat_id, contacts, instruction, languageTone, length) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/chat/generate`,
            contentType: 'application/json',
            data: JSON.stringify({
                chat_id: chat_id,
                contacts: contacts,
                instruction: instruction,
                language_tone: languageTone,
                length: length
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function sendEmail(chatId, contacts, subject, body, oauthId) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/chat/send`,
            contentType: 'application/json',
            data: JSON.stringify({
                chat_id: chatId,
                contacts: contacts,
                subject: subject,
                body: body,
                oauth_id: oauthId
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let message = xhr.responseJSON || 'Unknown error occurred.';
                reject(message);
            }
        });
    });
}

function getChatHistory(per_page = 10, page = 1) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/chat?per_page=${per_page}&page=${page}`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function updateChat(chat_id, name) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/chat/${chat_id}`,
            contentType: 'application/json',
            data: JSON.stringify({ name: name }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function deleteChat(chat_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'DELETE',
            url: `${API_URL}/chat/${chat_id}`,
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function getChat(chat_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/chat/${chat_id}/messages`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function getChatDetails(chat_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/chat/${chat_id}`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function getLinkedAccounts() {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/link`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function deleteLink(id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'DELETE',
            url: `${API_URL}/link/${id}`,
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function refreshLink(id, service) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/link/${service}/${id}`,
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function resetPasswordOTP(email) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/user/password`,
            contentType: 'application/json',
            data: JSON.stringify({ email: email }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response.message);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function resetPassword(email, otp, new_password, confirm_password) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/user/password`,
            contentType: 'application/json',
            data: JSON.stringify({
                email: email,
                otp: otp,
                new_password: new_password,
                confirm_password: confirm_password
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response.message);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function paraphrase(text, message_id, selectedType, position) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/chat/paraphrase/${message_id}`,
            contentType: 'application/json',
            data: JSON.stringify({
                text: text,
                type: selectedType,
                position: position
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },

            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function updateParaphrase(message_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'PUT',
            url: `${API_URL}/chat/paraphrase/${message_id}`,
            contentType: 'application/json',
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },

            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function getLinkedAccountFolders(service, id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/link/${service}/${id}/folder`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function getInboxMessages(service, id, folder, max_result = 10, query = null, next_page = null) {
    return new Promise((resolve, reject) => {
        let url = `${API_URL}/link/${service}/${id}`;

        const data = {
            folder_name: folder || 'inbox',
            max_result: max_result || 10
        };

        if (query) data.query = query;
        if (next_page) data.next_page = next_page;

        $.ajax({
            type: 'POST',
            url: url,
            contentType: 'application/json',
            data: JSON.stringify(data),
            xhrFields: {
            withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
            resolve(response);
            },
            error: function (xhr) {
            let error = xhr.responseJSON || 'Unknown error occurred.';
            reject(error);
            }
        });
    });
}

function getInboxMessage(service, id, message_id) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/link/${service}/${id}/message/${message_id}`,
            xhrFields: {
                withCredentials: true
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function messageAction(service, id, message_id, action) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/link/${service}/${id}/message/${message_id}/${action}`,
            contentType: 'application/json',
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function replyInboxMessage(service, id, message_id, body) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/link/${service}/${id}/message/${message_id}/reply`,
            contentType: 'application/json',
            data: JSON.stringify({ body: body }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },
            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}

function generateSmartReply(subject, body, sender, instruction, oauthId) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'POST',
            url: `${API_URL}/chat/reply`,
            contentType: 'application/json',
            data: JSON.stringify({
                subject: subject,
                body: body,
                sender: sender,
                oauth_id: oauthId,
                instruction: instruction
            }),
            xhrFields: {
                withCredentials: true
            },
            headers: {
                'X-CSRF-Token': CSRF_TOKEN
            },

            success: function (response) {
                resolve(response);
            },
            error: function (xhr) {
                let error = xhr.responseJSON || 'Unknown error occurred.';
                reject(error);
            }
        });
    });
}