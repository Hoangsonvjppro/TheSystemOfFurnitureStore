/**
 * File: components.js
 * Mục đích: Xử lý việc nhúng và quản lý các components trong ứng dụng
 */

/**
 * Hàm nhúng một component HTML vào một container
 * @param {string} containerId - ID của phần tử sẽ chứa component
 * @param {string} componentPath - Đường dẫn tới file component
 * @param {Function} callback - Hàm callback tùy chọn được gọi sau khi component được tải
 */
async function loadComponent(containerId, componentPath, callback) {
    try {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Không tìm thấy container với ID: ${containerId}`);
        }

        // Tìm đường dẫn gốc dựa trên trang hiện tại
        const isRootPage = window.location.pathname.endsWith('/') || 
                          window.location.pathname.endsWith('index.html');
        
        // Điều chỉnh đường dẫn dựa trên vị trí của trang hiện tại
        const adjustedPath = isRootPage ? `components/${componentPath}` : `../components/${componentPath}`;

        const response = await fetch(adjustedPath);
        if (!response.ok) {
            throw new Error(`Không thể tải component từ ${adjustedPath}`);
        }
        
        const html = await response.text();
        container.innerHTML = html;
        
        // Gọi callback nếu được cung cấp
        if (typeof callback === 'function') {
            callback();
        }
        
        return true;
    } catch (error) {
        console.error('Lỗi khi tải component:', error);
        document.getElementById(containerId).innerHTML = 
            `<div class="p-4 text-red-600">
                Lỗi khi tải component: ${error.message}
            </div>`;
        return false;
    }
}

/**
 * Hàm tải tất cả các component phổ biến (navbar, footer, v.v.)
 */
async function loadCommonComponents() {
    await loadComponent('navbar-container', 'Navbar.html', initNavbarFunctions);
    await loadComponent('footer-container', 'Footer.html');
}

/**
 * Khởi tạo các chức năng cho Navbar sau khi được tải
 */
function initNavbarFunctions() {
    // Xử lý button mobile menu
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Xử lý user menu dropdown
    const userMenuButton = document.getElementById('user-menu-button');
    const userDropdown = document.querySelector('.user-dropdown');
    
    if (userMenuButton && userDropdown) {
        userMenuButton.addEventListener('click', function() {
            userDropdown.classList.toggle('hidden');
        });
        
        // Đóng dropdown khi click ra ngoài
        document.addEventListener('click', function(event) {
            if (!userMenuButton.contains(event.target) && !userDropdown.contains(event.target)) {
                userDropdown.classList.add('hidden');
            }
        });
    }
}

// Tự động tải các component khi DOM đã sẵn sàng
document.addEventListener('DOMContentLoaded', loadCommonComponents); 