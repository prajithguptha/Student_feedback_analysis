// Floating Window Interactive Logic
document.addEventListener('DOMContentLoaded', () => {
    const floatingToggleBtn = document.getElementById('floatingToggleBtn');
    const floatingWindow = document.getElementById('floatingWindow');
    const floatingCloseBtn = document.getElementById('floatingCloseBtn');
    const floatingMinimizeBtn = document.getElementById('floatingMinimizeBtn');
    const floatingHeader = document.getElementById('floatingHeader');
    const floatingBody = document.getElementById('floatingBody');
    const floatingBtnIcon = document.getElementById('floatingBtnIcon');

    let isOpen = false;
    let isMinimized = false;

    // Toggle Open/Close
    function toggleWindow() {
        isOpen = !isOpen;
        if (isOpen) {
            floatingWindow.classList.remove('hidden');
            floatingBtnIcon.classList.remove('fa-bolt');
            floatingBtnIcon.classList.add('fa-xmark');
        } else {
            floatingWindow.classList.add('hidden');
            floatingBtnIcon.classList.remove('fa-xmark');
            floatingBtnIcon.classList.add('fa-bolt');
        }
    }

    if (floatingToggleBtn) {
        floatingToggleBtn.addEventListener('click', toggleWindow);
    }

    if (floatingCloseBtn) {
        floatingCloseBtn.addEventListener('click', () => {
            isOpen = false;
            floatingWindow.classList.add('hidden');
            floatingBtnIcon.classList.remove('fa-xmark');
            floatingBtnIcon.classList.add('fa-bolt');
        });
    }

    // Minimize / Expand Body
    if (floatingMinimizeBtn) {
        floatingMinimizeBtn.addEventListener('click', () => {
            isMinimized = !isMinimized;
            if (isMinimized) {
                floatingBody.classList.add('hidden');
                document.getElementById('tabBtnStatus').parentElement.classList.add('hidden');
            } else {
                floatingBody.classList.remove('hidden');
                document.getElementById('tabBtnStatus').parentElement.classList.remove('hidden');
            }
        });
    }

    // Draggable Window functionality
    let isDragging = false;
    let currentX, currentY, initialX, initialY;
    let xOffset = 0, yOffset = 0;

    if (floatingHeader) {
        floatingHeader.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        // Touch support
        floatingHeader.addEventListener('touchstart', dragStart, { passive: false });
        document.addEventListener('touchmove', drag, { passive: false });
        document.addEventListener('touchend', dragEnd);
    }

    function dragStart(e) {
        if (e.type === 'touchstart') {
            initialX = e.touches[0].clientX - xOffset;
            initialY = e.touches[0].clientY - yOffset;
        } else {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
        }

        if (e.target === floatingHeader || floatingHeader.contains(e.target)) {
            if (e.target.tagName !== 'BUTTON' && e.target.parentElement.tagName !== 'BUTTON') {
                isDragging = true;
            }
        }
    }

    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            if (e.type === 'touchmove') {
                currentX = e.touches[0].clientX - initialX;
                currentY = e.touches[0].clientY - initialY;
            } else {
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
            }

            xOffset = currentX;
            yOffset = currentY;

            // Restrict bounds within viewport
            setTranslate(currentX, currentY, floatingWindow);
        }
    }

    function dragEnd() {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
    }

    function setTranslate(xPos, yPos, el) {
        el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
    }
});

// Switch Tab between Subject Status and Quick Help Desk
function switchFloatingTab(tabName) {
    const tabBtnStatus = document.getElementById('tabBtnStatus');
    const tabBtnHelp = document.getElementById('tabBtnHelp');
    const tabContentStatus = document.getElementById('tabContentStatus');
    const tabContentHelp = document.getElementById('tabContentHelp');

    if (tabName === 'status') {
        tabBtnStatus.className = "flex-1 py-2.5 px-3 border-b-2 border-indigo-600 text-indigo-600 bg-white transition flex items-center justify-center space-x-1.5 font-semibold";
        tabBtnHelp.className = "flex-1 py-2.5 px-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5";
        tabContentStatus.classList.remove('hidden');
        tabContentHelp.classList.add('hidden');
    } else {
        tabBtnHelp.className = "flex-1 py-2.5 px-3 border-b-2 border-indigo-600 text-indigo-600 bg-white transition flex items-center justify-center space-x-1.5 font-semibold";
        tabBtnStatus.className = "flex-1 py-2.5 px-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 transition flex items-center justify-center space-x-1.5";
        tabContentHelp.classList.remove('hidden');
        tabContentStatus.classList.add('hidden');
    }
}
