document.addEventListener('DOMContentLoaded', function () {
    const nicknameInput = document.getElementById('nicknameInput');
    const enterChatButton = document.getElementById('enterChatButton');

    enterChatButton.addEventListener('click', function () {
        const nickname = nicknameInput.value.trim();

        if (nickname) {
            localStorage.setItem('nickname', nickname);  // 將暱稱儲存到 localStorage
            window.location.href = '/chat';  // 重定向到聊天室
        } else {
            alert("請輸入有效的暱稱");
        }
    });
});
