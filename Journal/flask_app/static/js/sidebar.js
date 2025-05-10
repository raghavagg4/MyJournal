document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('close-sidebar');
    const openButton = document.getElementById('open-sidebar');
    const sidebar = document.getElementById('sidebar-panel');
    const contentPanel = document.getElementById('content-panel');

    function toggleSidebar(isHidden) {
        if (isHidden) {
            sidebar.style.display = 'none';
            openButton.style.display = 'flex';
            contentPanel.style.flex = '1';
            contentPanel.style.maxWidth = '100%';
        } else {
            sidebar.style.display = 'flex';
            openButton.style.display = 'none';
            contentPanel.style.flex = '1';
            contentPanel.style.maxWidth = 'none';
        }
    }

    if (toggleButton && openButton && sidebar && contentPanel) {
        toggleButton.addEventListener('click', function() {
            toggleSidebar(true);
        });

        openButton.addEventListener('click', function() {
            toggleSidebar(false);
        });
    }
});
