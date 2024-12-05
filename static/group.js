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

