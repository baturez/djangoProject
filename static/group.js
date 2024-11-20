function searchGroups() {
        const input = document.getElementById('searchGroup').value.toLowerCase();
        const groupItems = document.querySelectorAll('#groupList li');

        groupItems.forEach(item => {
            const groupName = item.textContent.toLowerCase();
            if (groupName.includes(input)) {
                item.style.display = 'list-item';
            } else {
                item.style.display = 'none';
            }
        });
    }

let lastGroupTimestamp = null;
let currentGroupId = null;

function toggleGroupChat(groupId) {
    const groupChatBar = document.getElementById('group-chat-bar');
    currentGroupId = groupId;

    if (groupChatBar.style.display === 'none') {
        groupChatBar.style.display = 'block';
        longPollGroup();
    } else {
        groupChatBar.style.display = 'none';
        lastGroupTimestamp = null;
    }
}
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
function sendGroupMessage() {
    const messageInput = document.getElementById('group-message-input');
    const message = messageInput.value;

    if (currentGroupId && message) {

        fetch('/send-group-message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                group_id: currentGroupId,
                text: message,
            }),
        }).then(response => {
            if (response.ok) {

                displaySentMessage({
                    sender: 'You',
                    text: message,
                    timestamp: new Date().toISOString()
                });

                messageInput.value = '';
            }
        }).catch(error => {
            console.error('Error sending message:', error);
        });
    } else {
        console.warn('Group ID or message is invalid.');
    }
}
function displaySentMessage(message) {
    const groupChatMessages = document.getElementById('group-chat-messages');
    const messageElement = document.createElement('div');
    messageElement.textContent = `${message.sender}: ${message.text}`;
    groupChatMessages.appendChild(messageElement);
}

function displayGroupMessages(messages) {
    const groupChatMessages = document.getElementById('group-chat-messages');
    messages.forEach(message => {
        const messageElement = document.createElement('div');
        messageElement.textContent = `${message.sender}: ${message.text}`;
        groupChatMessages.appendChild(messageElement);
    });
}

function longPollGroup() {
    if (!currentGroupId) return;

    fetch(`/fetch-group-messages/?group_id=${currentGroupId}&last_timestamp=${lastGroupTimestamp || 'null'}`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response was not ok');
        })
        .then(data => {
            if (data.messages.length) {
                lastGroupTimestamp = data.messages[data.messages.length - 1].timestamp;
                displayGroupMessages(data.messages);
            }
            longPollGroup();
        })
        .catch(error => {
            console.error('Error fetching messages:', error);
            setTimeout(longPollGroup, 2000);
        });
}

