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
    event.preventDefault();  // Prevent the default form submission

    const form = event.target;
    const commentContent = form.comment_content.value;  // Get the content of the comment

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value  // CSRF token
        },
        body: JSON.stringify({
            post_id: postId,
            comment_content: commentContent
        })
    })
    .then(response => response.json())  // Parse the response as JSON
    .then(data => {
        if (data.success) {
            const commentsSection = document.getElementById('comments-' + postId);

            // Append the new comment to the bottom of the comment section
            commentsSection.insertAdjacentHTML('beforeend', `
                <div class="comment">
                    <strong>${data.commenter}</strong>: ${data.comment_content}
                    <small>${new Date().toLocaleString()}</small>
                </div>
            `);

            form.reset();  // Reset the form after submission
        } else {
            alert(data.error_message || 'Failed to add comment.');  // Show an error if something goes wrong
        }
    })
    .catch(error => {
        console.error('Error:', error);  // Handle any errors that may occur during the fetch
        alert('An error occurred while adding your comment.');
    });
}


currentStoryIndex = 0;
stories = [
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


let chatSocket = null;
let selectedFriend = null;
let notificationButton = document.querySelector('.toggle-chat-btn');

// Arkadaş seçimi işlevi
function selectFriend(friendUsername) {
    selectedFriend = friendUsername;
    document.getElementById("selected-friend-name").textContent = `Sohbet - ${friendUsername}`;
    document.getElementById("chat-section").style.display = "block";

    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = "";  // Clear previous messages

    if (chatSocket) chatSocket.close();  // Close previous WebSocket connection

    const yourUsername = getUsernameFromSession();  // Get the logged-in user's username
    const groupName = `chat_${[yourUsername, selectedFriend].sort().join('_')}`;

    // Send request to mark all previous messages as unread in the backend (MongoDB)

    // Establish a new WebSocket connection
    chatSocket = new WebSocket(`wss://${window.location.host}/ws/chat/${groupName}/`);

    chatSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        displayMessage(data);
    };

    chatSocket.onclose = function () {
        console.error("WebSocket connection closed.");
    };

    fetchMessages(friendUsername, chatMessages);  // Fetch old messages
    markMessagesAsRead(yourUsername, friendUsername);
}
function markMessagesAsRead(sender, recipient) {
    // Backend'e mesajları okundu olarak işaretlemesi için bir istek gönder
    fetch(`/mark_messages_as_read/${sender}/${recipient}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ sender: sender, recipient: recipient })
});
}
// Send a request to the backend to mark all messages as unread

function displayMessage(data) {
    const chatMessages = document.getElementById("chat-messages");
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    const senderElement = document.createElement("strong");
    const yourUsername = getUsernameFromSession();  // Kullanıcı adını al

    if (data.sender === yourUsername) {
        senderElement.textContent = `You: `;
        senderElement.classList.add("sender");
    } else {
        senderElement.textContent = `${data.sender}: `;
        senderElement.classList.add("receiver");
    }

    messageElement.appendChild(senderElement);
    const messageText = document.createElement("span");
    messageText.textContent = data.message || '';
    messageElement.appendChild(messageText);

    if (data.file_name && data.file_data) {
        addFileToMessage(messageElement, data);
    }

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Yeni mesaj alındığında butonu değiştirme
    if (selectedFriend !== data.sender) {
        notificationButton.classList.add("new-message");  // Butona stil ekle
        notificationButton.textContent = "🔔 Yeni Mesaj";  // Butonun üzerine bildirim simgesi ekle
    }
}
document.addEventListener('DOMContentLoaded', function () {


    // Mesaj geldiğinde çalışır
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === 'message') {
            // Yeni mesaj göstergesini görünür yap
            const indicator = document.getElementById('new-message-indicator');
            if (indicator) {
                indicator.style.display = 'inline'; // Görünür yap
            }
        }
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket kapandı.');
    };

    // Yeni mesaj göstergesini temizleme işlevi
    window.clearNewMessageNotification = function () {
        const indicator = document.getElementById('new-message-indicator');
        if (indicator) {
            indicator.style.display = 'none'; // Gizle
        }
    };
});
function checkNewMessages() {
    fetch('/check-new-messages/')
        .then(response => {
            console.log('Response:', response);
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(`Server error: ${errorData.error}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Data:', data);
            if (data.new_message) {
                document.getElementById("new-message-indicator").style.display = "inline-block";
            }
        })
        .catch(error => console.error('Error checking new messages:', error));
}

// Her 5 saniyede bir yeni mesaj kontrolü yap
setInterval(checkNewMessages, 10000);
function clearNewMessageNotification() {
    const notificationIndicator = document.getElementById('new-message-indicator');
    notificationIndicator.style.display = 'none';
}



// Function to send the mark_as_read signal via WebSocket

function getUsernameFromSession() {
    return document.getElementById("username").dataset.username;
}
function reconnectWebSocket() {
    const newUsername = getUsernameFromSession();  // Get the updated username
    // Reconnect WebSocket with new username (assuming 'selectedFriend' is set)
    if (selectedFriend) {
        const groupName = `chat_${[newUsername, selectedFriend].sort().join('_')}`;
        chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${groupName}/`);
        chatSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            displayMessage(data);
        };
    }
}
window.addEventListener('load', function () {
    const newUsername = getUsernameFromSession();  // Get the updated username after page reload
    if (newUsername) {
        reconnectWebSocket();  // Reconnect the WebSocket with the new username
    }
});
// WebSocket mesajı geldiğinde
chatSocket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    displayMessage(data); // Gelen mesajı ekle
};

// Dosya bilgilerini mesaja ekle
function addFileToMessage(messageElement, data) {
    const fileData = data.file_data;  // Hata kaynağı düzeltiliyor
    const fileName = data.file_name;
    const fileSize = (data.file_size / 1024).toFixed(2);  // KB boyutu
    const fileInfoText = `Dosya: ${fileName} (${fileSize} KB)`;

    const downloadButton = document.createElement("button");
    downloadButton.textContent = "İndir";
    downloadButton.classList.add("btn", "btn-success", "btn-sm");
    downloadButton.style.marginLeft = "10px";

    downloadButton.onclick = function () {
        // Dosyayı indir
        const link = document.createElement("a");
        link.href = `data:application/octet-stream;base64,${fileData}`;
        link.download = fileName;
        link.click();  // Dosya indirme işlemini başlat

        // WebSocket üzerinden dosya indirildiğini bildiren mesaj gönder
        chatSocket.send(JSON.stringify({
            type: 'file_downloaded',
            file_name: fileName
        }));

        // Bildirim göster
        alert(`Dosya indirildi ve MongoDB'den silinmesi için işaretlendi: ${fileName}`);
    };

    messageElement.appendChild(document.createTextNode(fileInfoText));
    messageElement.appendChild(downloadButton);
}





function fetchMessages(friendUsername, chatMessages) {
    fetch('/fetch_messages?friend=' + friendUsername)
    .then(response => response.json())
    .then(data => {
        if (data.messages) {
            // Eski mesajları temizle
            chatMessages.innerHTML = '';

            // Mesajları tersten ekleyerek en alta ekleyelim
            data.messages.forEach(msg => {
                const messageElement = document.createElement("div");
                messageElement.className = "message";

                // Gönderenin ismini mavi yapalım (Eğer mesajı biz göndermişsek)
                const senderElement = document.createElement("strong");

                const yourUsername = document.getElementById("username").dataset.username; // Kullanıcının ismini al

                if (msg.sender === yourUsername) {
                    // Eğer bu mesaj senin gönderdiğin bir mesaj ise
                    senderElement.textContent = `You: `;
                    senderElement.classList.add("sender"); // Kendi ismini mavi yapmak için
                } else {
                    // Eğer mesaj karşı taraftan geldiyse
                    senderElement.textContent = `${msg.sender}: `;
                    senderElement.classList.add("receiver"); // Karşıdaki göndereni yeşil yapmak için
                }

                messageElement.appendChild(senderElement);

                // Mesajın metnini ekleyelim
                const messageText = document.createElement("span");
                messageText.textContent = msg.text || '';
                messageElement.appendChild(messageText);

                // Dosya varsa, dosyayı ekle
                if (msg.file_name && msg.file_data) {
                    addFileToMessage(messageElement, msg);  // Dosyayı ekle
                }

                // Yeni mesajı en alta ekleyelim
                chatMessages.appendChild(messageElement);
            });

            // Mesajları ekledikten sonra, mesajı en altta tutmak için kaydırma
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    })
    .catch(error => console.error('Mesajları çekerken hata oluştu:', error));
}

// Dosya seçimi işlevi
function handleFileSelect(event) {
    const fileInput = event.target;
    const file = fileInput.files[0];

    if (file) {
        // Dosya Bilgilerini Göster
        document.getElementById('file-name').innerText = file.name;
        document.getElementById('file-info').style.display = 'block';

        // İlerleme Çubuğu Sıfırla
        const progressBar = document.getElementById('progress-bar');
        progressBar.style.width = '0%';
        document.getElementById('upload-progress').style.display = 'block';
    }
}

// Dosya seçimini temizle
function clearFile() {
    // Dosya Girdisini Temizle
    const fileInput = document.getElementById('file-input');
    fileInput.value = '';
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('upload-progress').style.display = 'none';
}

function simulateUploadProgress() {
    const progressBar = document.getElementById('progress-bar');
    let progress = 0;

    // İlerleme Simülasyonu
    const interval = setInterval(() => {
        progress += 10;
        progressBar.style.width = `${progress}%`;

        if (progress >= 100) {
            clearInterval(interval);
            alert('Dosya başarıyla yüklendi!');
        }
    }, 300);
}
document.getElementById('file-input').addEventListener('change', () => {
    simulateUploadProgress();
});

// Mesaj gönderme işlevi
function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const messageContent = messageInput.value.trim();
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];
    const yourUsername = document.getElementById("username").dataset.username;

    if ((messageContent || file) && chatSocket && selectedFriend) {
        // Geçici "gönderiliyor..." mesajını ekleme
        const chatMessages = document.getElementById("chat-messages");
        const tempMessage = document.createElement("div");
        tempMessage.className = "message temp-message";
        tempMessage.textContent = "gönderiliyor...";  // Geçici mesaj
        chatMessages.appendChild(tempMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;  // Otomatik kaydırma

        // WebSocket üzerinden mesaj gönderme
        if (file) {
            sendFileMessage(file, messageContent, yourUsername);
        } else {
            sendTextMessage(messageContent, yourUsername, tempMessage);
        }

        // Giriş alanlarını sıfırlama
        messageInput.value = "";
    } else {
        alert("Mesaj veya dosya göndermek için lütfen bir içerik seçin.");
    }
}

// Metin mesajı gönderme (dosya olmayan)
function sendTextMessage(messageContent, yourUsername, tempMessage) {
    try {
        chatSocket.send(JSON.stringify({
            message: messageContent,
            recipient: selectedFriend,
            sender: yourUsername
        }));

        // Gelen mesaj ile geçici mesajı güncelleme
        chatSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.message) {
                // Geçici mesajı kaldır, gerçek mesajı ekle
                tempMessage.remove();  // Geçici mesajı sil
                displayMessage(data);  // Gerçek mesajı ekle
            }
        };

    } catch (error) {
        console.error("Metin mesajı gönderme hatası:", error);
        alert("Mesaj gönderilemedi. Bağlantınızı kontrol edin.");
    }
}

// Dosya içeren mesaj gönderme
function sendFileMessage(file, messageContent, yourUsername) {
    const fileReader = new FileReader();

    fileReader.onload = function (event) {
        const fileData = event.target.result.split(',')[1];  // Base64 verisi

        // WebSocket üzerinden dosya mesajını gönder
        chatSocket.send(JSON.stringify({
            message: messageContent || '',
            recipient: selectedFriend,
            sender: yourUsername,
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            fileData: fileData
        }));

        // Dosya girişini sıfırla
        document.getElementById("file-input").value = "";  // Dosya seçimini sıfırla
    };

    fileReader.readAsDataURL(file);
}











function toggleChat() {
    var chatBar = document.getElementById("chat-bar");
    var indicator = document.getElementById("new-message-indicator");
    var chatsection = document.getElementById("chat-section")
    if (chatBar.style.display === "none") {
        chatBar.style.display = "block"; // Open the chat bar
        indicator.style.display = "none"; // Hide the notification
        chatsection.style.display = "none";
    } else {
        chatBar.style.display = "none"; // Close the chat bar

        // Close WebSocket connection when chat bar is closed
        if (chatSocket) {
            chatSocket.close();
            chatSocket = null;  // Reset WebSocket connection
            console.log("WebSocket connection closed.");
        }
    }
}