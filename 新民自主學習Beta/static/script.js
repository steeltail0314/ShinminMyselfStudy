document.addEventListener('DOMContentLoaded', function () {
    // 不再需要從 localStorage 取得暱稱，因為我們使用後端登入的使用者名稱

    var messageList = document.getElementById('messageList');
    var postInput = document.getElementById('postInput');
    var postButton = document.getElementById('postButton');

    function getMessages() {
        fetch('/posts')
            .then(response => response.text())
            .then(data => {
                messageList.innerHTML = data
                    .split('\u001e')
                    .filter(message => message.trim() !== '')
                    .map(message => {
                        var messageClass = message.includes('Admin') ? 'admin-message' : 'message';
                        return '<div class="' + messageClass + '"><p>' + message + '</p></div>';
                    })
                    .join('');
                messageList.scrollTop = messageList.scrollHeight;
            })
            .catch(error => console.error('Error fetching messages:', error));
    }

    postButton.addEventListener('click', function () {
        var message = postInput.value.trim();
        if (message !== '') {
            // 這裡不再手動加上暱稱，由後端來處理
            fetch('/post', {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/plain'
                },
                body: message  // 只傳送訊息內容
            })
                .then(response => {
                    if (response.ok) {
                        postInput.value = '';
                        getMessages();
                    } else {
                        console.error('Failed to send message');
                    }
                })
                .catch(error => console.error('Error posting message:', error));
        }
    });

    postInput.addEventListener('keyup', function (event) {
        if (event.key === 'Enter') {
            postButton.click();
        }
    });

    getMessages();
    setInterval(getMessages, 1000);
});
