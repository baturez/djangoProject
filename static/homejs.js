

function toggleComments(postId) {
    const commentsSection = document.getElementById('comments-' + postId);
    commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
}
function submitReply(event, postId, commentId) {
    event.preventDefault();
    const form = event.target;
    const replyContent = form.reply_content.value;

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            post_id: postId,
            comment_id: commentId,
            reply_content: replyContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentDiv = form.closest('.comment');
            const repliesDiv = commentDiv.querySelector('.replies');
            repliesDiv.insertAdjacentHTML('beforeend', `
                <div class="reply">
                    <strong>${data.replier}</strong>: ${data.reply_content}
                    <small>${new Date().toLocaleString()}</small>
                </div>
            `);
            form.reset();
        } else {
            alert(data.error_message || 'Failed to add reply.');
        }
    });
}
function submitComment(event, postId) {
    event.preventDefault();
    const form = event.target;
    const commentContent = form.comment_content.value;

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            post_id: postId,
            comment_content: commentContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentsSection = document.getElementById('comments-' + postId);
            commentsSection.insertAdjacentHTML('beforeend', `
                <div class="comment">
                    <strong>${data.commenter}</strong>: ${data.comment_content}
                    <small>${new Date().toLocaleString()}</small>
                </div>
            `);
            form.reset();
        } else {
            alert(data.error_message || 'Failed to add comment.');
        }
    });
}

let currentStoryIndex = 0;
const stories = [
    'https://picsum.photos/200/300',
    'https://picsum.photos/200/300?1',
    'https://picsum.photos/200/300?2',
];

function showLargeStory(index) {
    currentStoryIndex = index;
    const largeStoryContainer = document.getElementById('largeStoryContainer');
    const largeStoryImage = document.getElementById('largeStoryImage');

    largeStoryImage.src = stories[currentStoryIndex];
    largeStoryContainer.style.display = 'flex';
}

function closeLargeStory() {
    const largeStoryContainer = document.getElementById('largeStoryContainer');
    largeStoryContainer.style.display = 'none';
}

function nextStory(event) {
    event.stopPropagation();
    currentStoryIndex++;
    if (currentStoryIndex >= stories.length) {
        currentStoryIndex = 0;
    }
    const largeStoryImage = document.getElementById('largeStoryImage');
    largeStoryImage.src = stories[currentStoryIndex];
}



let selectedFriend = null;
let lastMessageTimestamp = null;
function selectFriend(friendUsername) {
    selectedFriend = friendUsername;
    document.getElementById("selected-friend-name").textContent = `Sohbet - ${friendUsername}`;
    document.getElementById("chat-section").style.display = "block";
    fetchMessages();
}

function fetchMessages() {
    if (selectedFriend) {
        fetch(`/fetch_messages/?friend=${selectedFriend}`)
            .then(response => response.json())
            .then(data => {
                const chatMessages = document.getElementById("chat-messages");
                chatMessages.innerHTML = '';

                data.messages.forEach(message => {
                    const messageElement = document.createElement("div");
                    messageElement.className = "message";
                    messageElement.textContent = `${message.sender}: ${message.text}`;
                    chatMessages.appendChild(messageElement);
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;

                setTimeout(fetchMessages, 500);
            })
            .catch(error => {
                console.error("Error fetching messages:", error);
                setTimeout(fetchMessages, 2000);
            });
    }
}

function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const messageContent = messageInput.value.trim();

    if (messageContent && selectedFriend) {
        fetch(`/send_message/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}"
            },
            body: JSON.stringify({ message: messageContent, recipient: selectedFriend })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                messageInput.value = "";

                fetchMessages();
            } else {
                console.error("Message sending failed:", data.error);
            }
        })
        .catch(error => console.error("Error sending message:", error));
    }
}
let pollingInterval;
let isChatOpen = false;
function toggleChat() {
    const chatBar = document.getElementById('chat-bar');
    const isVisible = chatBar.style.display === 'block';

    if (!isVisible) {
        chatBar.style.display = 'block';
        isChatOpen = true;
        fetchMessages();
        pollingInterval = setInterval(fetchMessages, 2000);
    } else {
        chatBar.style.display = 'none';
        isChatOpen = false;
        clearInterval(pollingInterval);
    }
}


document.getElementById('send-button').addEventListener('click', sendMessage);
