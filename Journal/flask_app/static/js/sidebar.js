document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('close-sidebar');
    const openButton = document.getElementById('open-sidebar');
    const openButtonContainer = document.getElementById('open-sidebar-container');
    const sidebar = document.getElementById('sidebar-panel');
    const contentPanel = document.getElementById('content-panel');

    function toggleSidebar(isHidden) {
        if (isHidden) {
            sidebar.style.display = 'none';
            openButtonContainer.style.display = 'block';
            contentPanel.style.flex = '1';
            contentPanel.style.maxWidth = '100%';
        } else {
            sidebar.style.display = 'flex';
            openButtonContainer.style.display = 'none';
            contentPanel.style.flex = '1';
            contentPanel.style.maxWidth = 'none';
        }
    }

    if (toggleButton && openButton && sidebar && contentPanel) {
        // Set initial state
        sidebar.style.display = 'flex';
        openButtonContainer.style.display = 'none';

        toggleButton.addEventListener('click', function() {
            toggleSidebar(true);
        });

        openButton.addEventListener('click', function() {
            toggleSidebar(false);
        });
    }
});
