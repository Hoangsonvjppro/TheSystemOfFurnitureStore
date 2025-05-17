/**
 * Nội Thất Cao Cấp - Main JavaScript
 * Xử lý tải components và các chức năng chính
 */

// Cấu hình API
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
const AUTH_TOKEN_KEY = 'auth_token';
const AUTH_REFRESH_KEY = 'auth_refresh';
const USER_INFO_KEY = 'user_info';

// DOM Elements Cache
const navbarContainer = document.getElementById('navbar-container');
const contentContainer = document.getElementById('content-container');
const footerContainer = document.getElementById('footer-container');

// Khởi tạo giỏ hàng
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// Đếm số lượng sản phẩm trong giỏ hàng
function updateCartCount() {
    const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
    const cartCountElements = document.querySelectorAll('.cart-count');
    cartCountElements.forEach(element => {
        element.textContent = cartCount;
    });
}

// Quản lý Authentication
const Auth = {
    // Lưu token vào localStorage
    setAuthToken: function(token, refreshToken, user) {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
        localStorage.setItem(AUTH_REFRESH_KEY, refreshToken);
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
    },
    
    // Lấy token từ localStorage
    getAuthToken: function() {
        return localStorage.getItem(AUTH_TOKEN_KEY);
    },
    
    // Lấy refresh token từ localStorage
    getRefreshToken: function() {
        return localStorage.getItem(AUTH_REFRESH_KEY);
    },
    
    // Lấy thông tin user
    getUserInfo: function() {
        const userStr = localStorage.getItem(USER_INFO_KEY);
        return userStr ? JSON.parse(userStr) : null;
    },
    
    // Xóa token (logout)
    clearAuth: function() {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(AUTH_REFRESH_KEY);
        localStorage.removeItem(USER_INFO_KEY);
    },
    
    // Kiểm tra đã đăng nhập hay chưa
    isAuthenticated: function() {
        return !!this.getAuthToken();
    },
    
    // Lấy role của người dùng
    getUserRole: function() {
        const user = this.getUserInfo();
        return user ? user.role : null;
    },
    
    // Kiểm tra nếu user là admin
    isAdmin: function() {
        return this.getUserRole() === 'ADMIN';
    },

    // Kiểm tra nếu user là manager
    isManager: function() {
        return this.getUserRole() === 'MANAGER';
    },

    // Kiểm tra nếu user là sales
    isSalesStaff: function() {
        return this.getUserRole() === 'SALES_STAFF';
    },

    // Kiểm tra nếu user là inventory
    isInventoryStaff: function() {
        return this.getUserRole() === 'INVENTORY_STAFF';
    },
    
    // Kiểm tra nếu user là staff (bất kỳ loại nào)
    isStaff: function() {
        const role = this.getUserRole();
        return role === 'ADMIN' || role === 'MANAGER' || 
               role === 'SALES_STAFF' || role === 'INVENTORY_STAFF';
    }
};

// Tải các components
async function loadComponents() {
    try {
        // Tải Navbar
        const navbarResponse = await fetch('./components/Navbar.html');
        const navbarHtml = await navbarResponse.text();
        if (navbarContainer) {
            navbarContainer.innerHTML = navbarHtml;
        }

        // Tải Footer
        const footerResponse = await fetch('./components/Footer.html');
        const footerHtml = await footerResponse.text();
        if (footerContainer) {
            footerContainer.innerHTML = footerHtml;
        }

        // Sau khi tải xong components
        initializeComponents();
        
    } catch (error) {
        console.error('Error loading components:', error);
    }
}

// Khởi tạo các components sau khi tải
function initializeComponents() {
    // Xử lý mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Cập nhật số sản phẩm trong giỏ hàng
    updateCartCount();
    
    // Cập nhật UI dựa trên trạng thái đăng nhập
    updateAuthUI();
}

// Cập nhật UI dựa trên trạng thái đăng nhập
function updateAuthUI() {
    const loginButtons = document.querySelectorAll('.login-button');
    const logoutButtons = document.querySelectorAll('.logout-button');
    const userInfoElements = document.querySelectorAll('.user-info');
    const adminLinks = document.querySelectorAll('.admin-link');
    const staffLinks = document.querySelectorAll('.staff-link');
    
    if (Auth.isAuthenticated()) {
        // Nếu đã đăng nhập
        const user = Auth.getUserInfo();
        
        // Ẩn nút đăng nhập, hiện nút đăng xuất
        loginButtons.forEach(btn => btn.classList.add('hidden'));
        logoutButtons.forEach(btn => {
            btn.classList.remove('hidden');
            btn.addEventListener('click', handleLogout);
        });
        
        // Hiển thị thông tin người dùng
        userInfoElements.forEach(el => {
            el.classList.remove('hidden');
            el.textContent = user.full_name || user.username;
        });
        
        // Hiển thị link admin nếu là admin
        if (Auth.isAdmin()) {
            adminLinks.forEach(link => link.classList.remove('hidden'));
        }
        
        // Hiển thị link dành cho nhân viên
        if (Auth.isStaff()) {
            staffLinks.forEach(link => link.classList.remove('hidden'));
        }
    } else {
        // Nếu chưa đăng nhập
        loginButtons.forEach(btn => btn.classList.remove('hidden'));
        logoutButtons.forEach(btn => btn.classList.add('hidden'));
        userInfoElements.forEach(el => el.classList.add('hidden'));
        adminLinks.forEach(link => link.classList.add('hidden'));
        staffLinks.forEach(link => link.classList.add('hidden'));
    }
}

// Xử lý đăng xuất
async function handleLogout() {
    try {
        // Gọi API logout
        await fetchAPI('/users/logout/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getAuthToken()}`
            }
        });
        
        // Xóa token và thông tin người dùng
        Auth.clearAuth();
        
        // Cập nhật UI
        updateAuthUI();
        
        // Chuyển về trang chủ
        window.location.href = '/';
        
    } catch (error) {
        console.error('Logout error:', error);
        // Xóa token và thông tin người dùng bất kể lỗi
        Auth.clearAuth();
        window.location.href = '/';
    }
}

// Xử lý thêm vào giỏ hàng
function addToCart(productId, quantity = 1) {
    // Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        // Nếu đã có, tăng số lượng
        existingItem.quantity += quantity;
    } else {
        // Nếu chưa có, thêm mới
        cart.push({
            id: productId,
            quantity: quantity
        });
    }
    
    // Lưu giỏ hàng vào localStorage
    localStorage.setItem('cart', JSON.stringify(cart));
    
    // Cập nhật số lượng hiển thị
    updateCartCount();
    
    // Hiển thị thông báo
    showNotification('Đã thêm sản phẩm vào giỏ hàng!');
}

// Hiển thị thông báo
function showNotification(message, type = 'success', duration = 3000) {
    // Tạo element thông báo
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white z-50 transform transition-transform duration-300 translate-y-full`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Thêm vào body
    document.body.appendChild(notification);
    
    // Hiển thị notification với animation
    setTimeout(() => {
        notification.classList.remove('translate-y-full');
    }, 10);
    
    // Xóa notification sau khoảng thời gian
    setTimeout(() => {
        notification.classList.add('translate-y-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
}

// Tải component ProductCard
async function loadProductCard(product) {
    try {
        const response = await fetch('./components/ProductCard.html');
        let template = await response.text();
        
        // Tạo một hàm để render template
        const render = (template, data) => {
            return template.replace(/\${(.*?)}/g, (_, key) => {
                return eval(`(${key})`);
            });
        };
        
        // Render dữ liệu vào template
        const rendered = render(template, { product });
        
        return rendered;
    } catch (error) {
        console.error('Error loading product card:', error);
        return '';
    }
}

// Fetch API helper
async function fetchAPI(endpoint, options = {}) {
    try {
        // Thêm token vào header nếu đã đăng nhập
        let headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (Auth.isAuthenticated() && !endpoint.includes('/token/')) {
            headers['Authorization'] = `Bearer ${Auth.getAuthToken()}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });
        
        // Nếu token hết hạn, thử refresh token
        if (response.status === 401 && Auth.getRefreshToken()) {
            const refreshResponse = await fetch(`${API_BASE_URL}/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: Auth.getRefreshToken() })
            });
            
            if (refreshResponse.ok) {
                const data = await refreshResponse.json();
                
                // Cập nhật token mới
                const user = Auth.getUserInfo();
                Auth.setAuthToken(data.access, Auth.getRefreshToken(), user);
                
                // Thử lại request ban đầu với token mới
                headers['Authorization'] = `Bearer ${data.access}`;
                const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
                    ...options,
                    headers
                });
                
                if (!retryResponse.ok) {
                    throw new Error(`API request failed: ${retryResponse.status}`);
                }
                
                return await retryResponse.json();
            } else {
                // Refresh token không hợp lệ, đăng xuất
                Auth.clearAuth();
                window.location.href = '/pages/login.html';
                throw new Error('Session expired. Please login again.');
            }
        }
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Tải dữ liệu trang hiện tại dựa trên pathname
function loadCurrentPage() {
    const pathname = window.location.pathname;
    
    // Xóa nội dung container
    if (contentContainer) {
        contentContainer.innerHTML = '<div class="flex justify-center p-8"><div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div></div>';
    }
    
    // Dựa vào path để load trang tương ứng
    if (pathname === '/' || pathname.includes('index.html')) {
        loadHomePage();
    } else if (pathname.includes('product_list.html')) {
        loadProductListPage();
    } else if (pathname.includes('product_detail.html')) {
        const urlParams = new URLSearchParams(window.location.search);
        const productId = urlParams.get('id');
        loadProductDetailPage(productId);
    } else if (pathname.includes('cart.html')) {
        loadCartPage();
    } else if (pathname.includes('checkout.html')) {
        loadCheckoutPage();
    } else if (pathname.includes('order_confirmation.html')) {
        loadOrderConfirmationPage();
    }
}

// Khởi tạo khi trang tải xong
document.addEventListener('DOMContentLoaded', function() {
    // Tải components
    loadComponents();
    
    // Load trang hiện tại
    loadCurrentPage();
    
    // Redirect to login if attempting to access restricted pages
    const pathname = window.location.pathname;
    const restrictedPages = [
        'checkout.html',
        'user_orders.html',
        'admin_dashboard.html',
        'inventory_dashboard.html',
        'sales_dashboard.html'
    ];
    
    // Nếu đang truy cập trang cần đăng nhập nhưng chưa đăng nhập
    const needsLogin = restrictedPages.some(page => pathname.includes(page));
    if (needsLogin && !Auth.isAuthenticated()) {
        window.location.href = '/pages/login.html?redirect=' + encodeURIComponent(pathname);
    }
    
    // Nếu đang truy cập trang admin nhưng không phải admin
    if (pathname.includes('admin_dashboard.html') && !Auth.isAdmin()) {
        window.location.href = '/';
    }
    
    // Nếu đang truy cập trang inventory nhưng không phải inventory staff
    if (pathname.includes('inventory_dashboard.html') && 
        !(Auth.isInventoryStaff() || Auth.isAdmin() || Auth.isManager())) {
        window.location.href = '/';
    }
    
    // Nếu đang truy cập trang sales nhưng không phải sales staff
    if (pathname.includes('sales_dashboard.html') && 
        !(Auth.isSalesStaff() || Auth.isAdmin() || Auth.isManager())) {
        window.location.href = '/';
    }
});

// Dữ liệu mẫu để test (sẽ thay bằng API)
const sampleProducts = [
    {
        id: 1,
        name: "Ghế sofa góc Scandinavian",
        price: 15990000,
        original_price: 18990000,
        discount_percentage: 15,
        image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=2070&auto=format&fit=crop",
        category: "Phòng khách",
        rating: 4.5,
        review_count: 12
    },
    {
        id: 2,
        name: "Bàn ăn gỗ sồi",
        price: 8990000,
        image: "https://images.unsplash.com/photo-1577140917170-285929fb55b7?q=80&w=2787&auto=format&fit=crop",
        category: "Phòng ăn",
        rating: 5,
        review_count: 8
    },
    {
        id: 3,
        name: "Giường ngủ bọc nỉ",
        price: 12490000,
        original_price: 13990000,
        discount_percentage: 10,
        image: "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=2940&auto=format&fit=crop",
        category: "Phòng ngủ",
        rating: 4.8,
        review_count: 15
    },
    {
        id: 4,
        name: "Tủ quần áo hiện đại",
        price: 9990000,
        image: "https://images.unsplash.com/photo-1631510083806-5730437ea72c?q=80&w=2874&auto=format&fit=crop",
        category: "Phòng ngủ",
        rating: 4.2,
        review_count: 6
    },
    {
        id: 5,
        name: "Kệ tivi gỗ công nghiệp",
        price: 5990000,
        image: "https://images.unsplash.com/photo-1581539250439-c96689b516dd?q=80&w=1965&auto=format&fit=crop",
        category: "Phòng khách",
        rating: 4.3,
        review_count: 9
    },
    {
        id: 6,
        name: "Bàn làm việc thông minh",
        price: 4590000,
        original_price: 5990000,
        discount_percentage: 23,
        image: "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?q=80&w=2798&auto=format&fit=crop",
        category: "Phòng làm việc",
        rating: 4.7,
        review_count: 14
    },
    {
        id: 7,
        name: "Ghế văn phòng cao cấp",
        price: 3290000,
        image: "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?q=80&w=2000&auto=format&fit=crop",
        category: "Phòng làm việc",
        rating: 4.6,
        review_count: 11
    },
    {
        id: 8,
        name: "Đèn trang trí phòng khách",
        price: 1990000,
        image: "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?q=80&w=2070&auto=format&fit=crop",
        category: "Phòng khách",
        rating: 4.4,
        review_count: 7
    },
    {
        id: 9,
        name: "Tủ bếp thông minh",
        price: 18990000,
        original_price: 22990000,
        discount_percentage: 17,
        image: "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?q=80&w=2070&auto=format&fit=crop",
        category: "Phòng bếp",
        rating: 4.9,
        review_count: 18
    },
    {
        id: 10,
        name: "Bộ bàn ghế phòng ăn",
        price: 14990000,
        image: "https://images.unsplash.com/photo-1615066390971-03eସ4506145?q=80&w=2071&auto=format&fit=crop",
        category: "Phòng ăn",
        rating: 4.7,
        review_count: 13
    },
    {
        id: 11,
        name: "Kệ sách đa năng",
        price: 3990000,
        image: "https://images.unsplash.com/photo-1594620302200-9a762244a156?q=80&w=2048&auto=format&fit=crop",
        category: "Phòng làm việc",
        rating: 4.5,
        review_count: 10
    },
    {
        id: 12,
        name: "Tủ lạnh mini văn phòng",
        price: 2990000,
        image: "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?q=80&w=2070&auto=format&fit=crop",
        category: "Phòng bếp",
        rating: 4.2,
        review_count: 5
    }
];

// Danh mục sản phẩm mẫu
const sampleCategories = [
    { id: 1, name: "Phòng khách", slug: "phong-khach", count: 3 },
    { id: 2, name: "Phòng ngủ", slug: "phong-ngu", count: 2 },
    { id: 3, name: "Phòng bếp", slug: "phong-bep", count: 2 },
    { id: 4, name: "Phòng làm việc", slug: "phong-lam-viec", count: 3 },
    { id: 5, name: "Phòng ăn", slug: "phong-an", count: 2 }
];

// Khai báo các hàm tải trang
async function loadHomePage() {
    console.log('Loading home page...');
    
    try {
        // Tải nội dung trang home
        const response = await fetch('./pages/home.html');
        const html = await response.text();
        
        if (contentContainer) {
            contentContainer.innerHTML = html;
            
            // Xử lý dữ liệu sản phẩm sau khi tải trang
            loadHomePageData();
        }
    } catch (error) {
        console.error('Error loading home page:', error);
        if (contentContainer) {
            contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
        }
    }
}

// Tải dữ liệu cho trang Home
async function loadHomePageData() {
    try {
        // 1. Tải sản phẩm nổi bật
        let featuredProducts = [];
        try {
            // Thử lấy từ API
            featuredProducts = await fetchAPI('/products/products/?featured=true&limit=4');
        } catch (error) {
            console.warn('Failed to fetch from API, using sample data:', error);
            // Fallback to sample data
            featuredProducts = sampleProducts;
        }
        
        // 2. Tải sản phẩm mới
        let newProducts = [];
        try {
            // Thử lấy từ API
            newProducts = await fetchAPI('/products/products/?ordering=-created_at&limit=4');
        } catch (error) {
            console.warn('Failed to fetch from API, using sample data:', error);
            // Fallback to sample data
            newProducts = [...sampleProducts].reverse();
        }
        
        // 3. Render sản phẩm nổi bật
        const featuredContainer = document.getElementById('featured-products');
        if (featuredContainer) {
            featuredContainer.innerHTML = '';
            
            for (const product of featuredProducts) {
                const card = document.createElement('div');
                card.innerHTML = await loadProductCard(product);
                featuredContainer.appendChild(card);
            }
        }
        
        // 4. Render sản phẩm mới
        const newProductsContainer = document.getElementById('new-products');
        if (newProductsContainer) {
            newProductsContainer.innerHTML = '';
            
            for (const product of newProducts) {
                const card = document.createElement('div');
                card.innerHTML = await loadProductCard(product);
                newProductsContainer.appendChild(card);
            }
        }
        
    } catch (error) {
        console.error('Error loading home page data:', error);
    }
}

async function loadProductListPage() {
    console.log('Loading product list page...');
    
    try {
        // Tải nội dung trang product list
        const response = fetch('./pages/product_list.html')
            .then(response => response.text())
            .then(html => {
                if (contentContainer) {
                    contentContainer.innerHTML = html;
                    
                    // Khởi tạo các biến và state cho trang danh sách sản phẩm
                    let currentPage = 1;
                    let productsPerPage = 12;
                    let currentView = 'grid-3';
                    let totalProducts = 0;
                    let filteredProducts = [];
                    let categories = [];
                    
                    // Khởi tạo filter state
                    let filterState = {
                        category: null,
                        priceRange: { min: 0, max: 50000000 },
                        rating: null,
                        availability: { in_stock: false, on_sale: false },
                        sort: 'featured',
                        search: ''
                    };
                    
                    // Lấy thông số từ URL (nếu có)
                    const urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.has('category')) {
                        filterState.category = urlParams.get('category');
                    }
                    if (urlParams.has('sort')) {
                        filterState.sort = urlParams.get('sort');
                        document.getElementById('sort-by').value = filterState.sort;
                    }
                    
                    // Tải dữ liệu danh mục và sản phẩm
                    loadProductData();
                    
                    // Xử lý các sự kiện
                    initEvents();
                    
                    // Tải dữ liệu sản phẩm từ API hoặc sử dụng dữ liệu mẫu
                    async function loadProductData() {
                        try {
                            // Tải danh mục sản phẩm
                            try {
                                // Thử lấy danh mục từ API
                                categories = await fetchAPI('/products/categories/');
                            } catch (error) {
                                console.warn('Không thể tải danh mục từ API, sử dụng dữ liệu mẫu:', error);
                                // Sử dụng danh mục mẫu
                                categories = [
                                    { id: 1, name: "Phòng khách", slug: "phong-khach", count: 3 },
                                    { id: 2, name: "Phòng ngủ", slug: "phong-ngu", count: 2 },
                                    { id: 3, name: "Phòng bếp", slug: "phong-bep", count: 2 },
                                    { id: 4, name: "Phòng làm việc", slug: "phong-lam-viec", count: 3 },
                                    { id: 5, name: "Phòng ăn", slug: "phong-an", count: 2 }
                                ];
                            }
                            
                            // Render danh mục
                            renderCategories();
                            
                            // Tải sản phẩm
                            try {
                                // Chuẩn bị query params dựa trên filter
                                const params = new URLSearchParams();
                                
                                if (filterState.category) {
                                    params.append('category', filterState.category);
                                }
                                if (filterState.sort === 'newest') {
                                    params.append('ordering', '-created_at');
                                } else if (filterState.sort === 'price_asc') {
                                    params.append('ordering', 'price');
                                } else if (filterState.sort === 'price_desc') {
                                    params.append('ordering', '-price');
                                } else if (filterState.sort === 'rating') {
                                    params.append('ordering', '-rating');
                                }
                                
                                // Thử lấy sản phẩm từ API
                                const products = await fetchAPI(`/products/products/?${params.toString()}`);
                                filteredProducts = products.results || products;
                                totalProducts = products.count || filteredProducts.length;
                            } catch (error) {
                                console.warn('Không thể tải sản phẩm từ API, sử dụng dữ liệu mẫu:', error);
                                // Lọc dữ liệu mẫu theo filter state
                                filteredProducts = filterSampleProducts();
                                totalProducts = filteredProducts.length;
                            }
                            
                            // Cập nhật UI
                            renderProducts();
                            updatePagination();
                            document.getElementById('product-count').textContent = totalProducts;
                            
                        } catch (error) {
                            console.error('Lỗi khi tải dữ liệu sản phẩm:', error);
                            showError('Có lỗi xảy ra khi tải dữ liệu sản phẩm. Vui lòng thử lại sau.');
                        }
                    }
                    
                    // Lọc sản phẩm mẫu dựa trên filter state
                    function filterSampleProducts() {
                        let filtered = [...sampleProducts];
                        
                        // Lọc theo danh mục
                        if (filterState.category) {
                            const category = categories.find(c => c.slug === filterState.category);
                            if (category) {
                                filtered = filtered.filter(p => p.category === category.name);
                            }
                        }
                        
                        // Lọc theo đánh giá
                        if (filterState.rating) {
                            filtered = filtered.filter(p => p.rating >= filterState.rating);
                        }
                        
                        // Lọc theo giá
                        filtered = filtered.filter(p => 
                            p.price >= filterState.priceRange.min && 
                            p.price <= filterState.priceRange.max
                        );
                        
                        // Lọc theo tình trạng giảm giá
                        if (filterState.availability.on_sale) {
                            filtered = filtered.filter(p => p.discount_percentage);
                        }
                        
                        // Sắp xếp
                        switch(filterState.sort) {
                            case 'newest':
                                filtered.sort((a, b) => b.id - a.id);
                                break;
                            case 'price_asc':
                                filtered.sort((a, b) => a.price - b.price);
                                break;
                            case 'price_desc':
                                filtered.sort((a, b) => b.price - a.price);
                                break;
                            case 'rating':
                                filtered.sort((a, b) => b.rating - a.rating);
                                break;
                        }
                        
                        return filtered;
                    }
                    
                    // Render sản phẩm
                    async function renderProducts() {
                        const productGrid = document.getElementById('product-grid');
                        productGrid.innerHTML = '';
                        
                        // Tính toán sản phẩm cho trang hiện tại
                        const startIndex = (currentPage - 1) * productsPerPage;
                        const endIndex = Math.min(startIndex + productsPerPage, filteredProducts.length);
                        const productsToShow = filteredProducts.slice(startIndex, endIndex);
                        
                        // Cập nhật layout dựa trên view
                        updateGridView();
                        
                        if (productsToShow.length === 0) {
                            document.getElementById('no-results').classList.remove('hidden');
                            productGrid.classList.add('hidden');
                        } else {
                            document.getElementById('no-results').classList.add('hidden');
                            productGrid.classList.remove('hidden');
                            
                            // Render từng sản phẩm
                            for (const product of productsToShow) {
                                const productCard = document.createElement('div');
                                productCard.innerHTML = await loadProductCard(product);
                                productGrid.appendChild(productCard);
                            }
                        }
                    }
                    
                    // Cập nhật layout grid dựa trên view
                    function updateGridView() {
                        const productGrid = document.getElementById('product-grid');
                        
                        // Xóa tất cả class grid hiện tại
                        productGrid.className = 'grid gap-6';
                        
                        // Thêm class mới dựa trên view
                        switch(currentView) {
                            case 'grid-2':
                                productGrid.classList.add('grid-cols-1', 'md:grid-cols-2');
                                break;
                            case 'list':
                                productGrid.classList.add('grid-cols-1');
                                break;
                            case 'grid-3':
                            default:
                                productGrid.classList.add('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
                                break;
                        }
                    }
                    
                    // Cập nhật phân trang
                    function updatePagination() {
                        const totalPages = Math.ceil(totalProducts / productsPerPage);
                        const pageNumbers = document.getElementById('page-numbers');
                        
                        // Xóa các nút trang cũ
                        pageNumbers.innerHTML = '';
                        
                        // Cập nhật nút prev/next
                        document.getElementById('prev-page').disabled = currentPage <= 1;
                        document.getElementById('next-page').disabled = currentPage >= totalPages;
                        
                        // Tạo các nút số trang
                        let startPage = Math.max(1, currentPage - 2);
                        let endPage = Math.min(totalPages, startPage + 4);
                        
                        if (endPage - startPage < 4) {
                            startPage = Math.max(1, endPage - 4);
                        }
                        
                        // Hiển thị trang đầu
                        if (startPage > 1) {
                            addPageButton(1);
                            if (startPage > 2) {
                                addPageButton('...', true);
                            }
                        }
                        
                        // Hiển thị các trang giữa
                        for (let i = startPage; i <= endPage; i++) {
                            addPageButton(i);
                        }
                        
                        // Hiển thị trang cuối
                        if (endPage < totalPages) {
                            if (endPage < totalPages - 1) {
                                addPageButton('...', true);
                            }
                            addPageButton(totalPages);
                        }
                        
                        // Thêm nút trang
                        function addPageButton(pageNum, isEllipsis = false) {
                            const button = document.createElement('button');
                            button.textContent = pageNum;
                            button.className = `pagination-btn px-3 py-2 border-r border-gray-300 ${
                                isEllipsis ? 'text-gray-400' : 'text-gray-500 hover:bg-gray-100'
                            }`;
                            
                            if (pageNum === currentPage && !isEllipsis) {
                                button.classList.add('current-page');
                            }
                            
                            if (!isEllipsis) {
                                button.addEventListener('click', () => {
                                    currentPage = pageNum;
                                    renderProducts();
                                    updatePagination();
                                    window.scrollTo({top: 0, behavior: 'smooth'});
                                });
                            }
                            
                            pageNumbers.appendChild(button);
                        }
                    }
                    
                    // Render danh mục
                    function renderCategories() {
                        const categoryFilters = document.getElementById('category-filters');
                        categoryFilters.innerHTML = '';
                        
                        // Thêm tùy chọn "Tất cả"
                        const allLabel = document.createElement('label');
                        allLabel.className = 'flex items-center justify-between cursor-pointer py-1';
                        allLabel.innerHTML = `
                            <span class="flex items-center">
                                <input type="radio" name="category" class="form-radio text-primary-600 h-4 w-4" 
                                    ${filterState.category === null ? 'checked' : ''} data-category="all">
                                <span class="ml-2 text-sm ${filterState.category === null ? 'text-primary-600 font-medium' : 'text-gray-700'}">
                                    Tất cả sản phẩm
                                </span>
                            </span>
                            <span class="text-xs text-gray-500">(${totalProducts})</span>
                        `;
                        categoryFilters.appendChild(allLabel);
                        
                        // Thêm các danh mục
                        categories.forEach(category => {
                            const label = document.createElement('label');
                            label.className = 'flex items-center justify-between cursor-pointer py-1';
                            label.innerHTML = `
                                <span class="flex items-center">
                                    <input type="radio" name="category" class="form-radio text-primary-600 h-4 w-4" 
                                        ${filterState.category === category.slug ? 'checked' : ''} data-category="${category.slug}">
                                    <span class="ml-2 text-sm ${filterState.category === category.slug ? 'text-primary-600 font-medium' : 'text-gray-700'}">
                                        ${category.name}
                                    </span>
                                </span>
                                <span class="text-xs text-gray-500">(${category.count})</span>
                            `;
                            categoryFilters.appendChild(label);
                        });
                    }
                    
                    // Khởi tạo sự kiện
                    function initEvents() {
                        // Xử lý chọn danh mục
                        document.getElementById('category-filters').addEventListener('change', (e) => {
                            if (e.target.tagName === 'INPUT' && e.target.type === 'radio') {
                                if (e.target.dataset.category === 'all') {
                                    filterState.category = null;
                                } else {
                                    filterState.category = e.target.dataset.category;
                                }
                                currentPage = 1;
                                loadProductData();
                            }
                        });
                        
                        // Xử lý sắp xếp
                        document.getElementById('sort-by').addEventListener('change', (e) => {
                            filterState.sort = e.target.value;
                            currentPage = 1;
                            loadProductData();
                        });
                        
                        // Xử lý số sản phẩm mỗi trang
                        document.getElementById('per-page').addEventListener('change', (e) => {
                            productsPerPage = parseInt(e.target.value);
                            currentPage = 1;
                            renderProducts();
                            updatePagination();
                        });
                        
                        // Xử lý chế độ xem
                        document.querySelectorAll('.view-btn').forEach(btn => {
                            btn.addEventListener('click', () => {
                                document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                                btn.classList.add('active');
                                currentView = btn.dataset.view;
                                renderProducts();
                            });
                        });
                        
                        // Xử lý nút phân trang
                        document.getElementById('prev-page').addEventListener('click', () => {
                            if (currentPage > 1) {
                                currentPage--;
                                renderProducts();
                                updatePagination();
                                window.scrollTo({top: 0, behavior: 'smooth'});
                            }
                        });
                        
                        document.getElementById('next-page').addEventListener('click', () => {
                            const totalPages = Math.ceil(totalProducts / productsPerPage);
                            if (currentPage < totalPages) {
                                currentPage++;
                                renderProducts();
                                updatePagination();
                                window.scrollTo({top: 0, behavior: 'smooth'});
                            }
                        });
                        
                        // Xử lý bộ lọc giá
                        document.getElementById('apply-price').addEventListener('click', () => {
                            const minValue = document.getElementById('price-from').value.replace(/\D/g, '') || 0;
                            const maxValue = document.getElementById('price-to').value.replace(/\D/g, '') || 50000000;
                            
                            filterState.priceRange.min = parseInt(minValue);
                            filterState.priceRange.max = parseInt(maxValue);
                            currentPage = 1;
                            loadProductData();
                        });
                        
                        // Xử lý bộ lọc đánh giá
                        document.querySelectorAll('input[data-rating]').forEach(input => {
                            input.addEventListener('change', () => {
                                filterState.rating = input.checked ? parseInt(input.dataset.rating) : null;
                                currentPage = 1;
                                loadProductData();
                            });
                        });
                        
                        // Xử lý bộ lọc tình trạng
                        document.querySelectorAll('input[data-availability]').forEach(input => {
                            input.addEventListener('change', () => {
                                const type = input.dataset.availability;
                                filterState.availability[type] = input.checked;
                                currentPage = 1;
                                loadProductData();
                            });
                        });
                        
                        // Xử lý xóa bộ lọc
                        document.getElementById('clear-filters').addEventListener('click', clearFilters);
                        document.getElementById('clear-search').addEventListener('click', clearFilters);
                    }
                    
                    // Xóa bộ lọc
                    function clearFilters() {
                        // Reset filter state
                        filterState = {
                            category: null,
                            priceRange: { min: 0, max: 50000000 },
                            rating: null,
                            availability: { in_stock: false, on_sale: false },
                            sort: 'featured',
                            search: ''
                        };
                        
                        // Reset UI
                        document.querySelector('input[data-category="all"]').checked = true;
                        document.querySelectorAll('input[data-rating]').forEach(input => {
                            input.checked = false;
                        });
                        document.querySelectorAll('input[data-availability]').forEach(input => {
                            input.checked = false;
                        });
                        document.getElementById('price-from').value = '';
                        document.getElementById('price-to').value = '';
                        document.getElementById('sort-by').value = 'featured';
                        
                        // Tải lại dữ liệu
                        currentPage = 1;
                        loadProductData();
                    }
                    
                    // Hiển thị lỗi
                    function showError(message) {
                        const productGrid = document.getElementById('product-grid');
                        productGrid.innerHTML = `
                            <div class="col-span-full py-8 text-center">
                                <i class="fas fa-exclamation-circle text-red-500 text-4xl mb-4"></i>
                                <p class="text-red-500 font-medium">${message}</p>
                            </div>
                        `;
                    }
                }
            })
            .catch(error => {
                console.error('Error loading product list page:', error);
                if (contentContainer) {
                    contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
                }
            });
    } catch (error) {
        console.error('Error loading product list page:', error);
        if (contentContainer) {
            contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
        }
    }
}

function loadProductDetailPage(productId) {
    console.log('Loading product detail page for product ID:', productId);

    try {
        // Tải nội dung trang chi tiết sản phẩm
        fetch('./pages/product_detail.html')
            .then(response => response.text())
            .then(html => {
                if (contentContainer) {
                    contentContainer.innerHTML = html;
                    
                    // Sau khi DOM được tải, tiến hành tải dữ liệu sản phẩm
                    loadProductData(productId);
                    
                    // Khởi tạo các sự kiện cho trang
                    initProductDetailEvents();
                }
            })
            .catch(error => {
                console.error('Error loading product detail page:', error);
                if (contentContainer) {
                    contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
                }
            });
    } catch (error) {
        console.error('Error loading product detail page:', error);
        if (contentContainer) {
            contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
        }
    }
    
    // Tải dữ liệu chi tiết sản phẩm từ API
    async function loadProductData(productId) {
        try {
            // Tải thông tin sản phẩm
            let product;
            try {
                // Thử tải từ API
                product = await fetchAPI(`/products/products/${productId}/`);
            } catch (error) {
                console.warn('Failed to fetch product data from API, using sample data:', error);
                // Sử dụng dữ liệu mẫu
                product = getSampleProductById(productId);
            }
            
            if (!product) {
                showError('Không tìm thấy sản phẩm. Sản phẩm có thể đã bị xóa hoặc không tồn tại.');
                return;
            }
            
            // Cập nhật thông tin sản phẩm vào UI
            updateProductUI(product);
            
            // Tải sản phẩm liên quan
            loadRelatedProducts(product.category);
            
            // Lưu sản phẩm đã xem
            saveViewedProduct(product);
            
            // Hiển thị sản phẩm đã xem gần đây
            showRecentlyViewedProducts();
        } catch (error) {
            console.error('Error loading product data:', error);
            showError('Có lỗi xảy ra khi tải dữ liệu sản phẩm. Vui lòng thử lại sau.');
        }
    }
    
    // Cập nhật UI với thông tin sản phẩm
    function updateProductUI(product) {
        // Cập nhật tiêu đề trang
        document.title = `${product.name} - Nội Thất Cao Cấp`;
        
        // Cập nhật breadcrumbs
        document.getElementById('product-name-breadcrumb').textContent = product.name;
        if (product.category) {
            const categoryLink = document.getElementById('category-breadcrumb');
            categoryLink.textContent = product.category;
            categoryLink.href = `/product_list.html?category=${product.category.toLowerCase().replace(/\s+/g, '-')}`;
        }
        
        // Cập nhật thông tin cơ bản
        document.getElementById('product-name').textContent = product.name;
        document.getElementById('product-price').textContent = formatCurrency(product.price);
        document.getElementById('product-sku').textContent = `SKU: ${product.sku || '#' + product.id}`;
        
        // Cập nhật hình ảnh chính
        if (product.image) {
            document.getElementById('main-product-image').src = product.image;
            document.getElementById('main-product-image').alt = product.name;
        }
        
        // Cập nhật thumbnails nếu có
        updateThumbnails(product);
        
        // Cập nhật đánh giá
        if (product.rating) {
            updateRatingStars(product.rating);
            document.getElementById('review-count').textContent = `(${product.review_count || 0} đánh giá)`;
        }
        
        // Cập nhật tình trạng kho hàng
        if (product.in_stock === false) {
            document.getElementById('stock-status').innerHTML = '<i class="fas fa-times-circle mr-1 text-red-500"></i> Hết hàng';
            document.getElementById('stock-status').className = 'text-sm text-red-500 mt-1';
            document.getElementById('add-to-cart').disabled = true;
            document.getElementById('add-to-cart').classList.add('opacity-50', 'cursor-not-allowed');
            document.getElementById('buy-now').disabled = true;
            document.getElementById('buy-now').classList.add('opacity-50', 'cursor-not-allowed');
        }
        
        // Cập nhật giá gốc và badge giảm giá nếu có
        if (product.original_price && product.original_price > product.price) {
            document.getElementById('product-original-price').textContent = formatCurrency(product.original_price);
            document.getElementById('product-original-price').classList.remove('hidden');
            
            // Hiển thị badge giảm giá
            if (product.discount_percentage) {
                document.getElementById('discount-badge').textContent = `-${product.discount_percentage}%`;
                document.getElementById('discount-badge').classList.remove('hidden');
            }
        }
        
        // Cập nhật mô tả ngắn gọn
        if (product.short_description) {
            document.getElementById('product-short-desc').textContent = product.short_description;
        } else if (product.description) {
            const shortDesc = product.description.split('.')[0] + '.';
            document.getElementById('product-short-desc').textContent = shortDesc;
        }
        
        // Cập nhật mô tả đầy đủ
        if (product.description) {
            document.getElementById('product-description').innerHTML = product.description;
        } else {
            document.getElementById('product-description').innerHTML = '<p>Chưa có thông tin mô tả cho sản phẩm này.</p>';
        }
        
        // Cập nhật thông số kỹ thuật
        updateSpecifications(product);
    }
    
    // Cập nhật gallery hình ảnh
    function updateThumbnails(product) {
        const thumbnailsContainer = document.getElementById('image-thumbnails');
        thumbnailsContainer.innerHTML = '';
        
        // Nếu có mảng hình ảnh
        if (product.images && product.images.length > 0) {
            // Thêm hình chính vào đầu nếu không có trong mảng
            if (!product.images.includes(product.image)) {
                product.images.unshift(product.image);
            }
            
            product.images.forEach((image, index) => {
                const thumbnail = document.createElement('div');
                thumbnail.className = `aspect-square bg-gray-100 rounded cursor-pointer overflow-hidden border ${index === 0 ? 'border-primary-500' : 'border-transparent'}`;
                thumbnail.innerHTML = `<img src="${image}" alt="${product.name} - Ảnh ${index + 1}" class="w-full h-full object-cover">`;
                
                // Sự kiện click để thay đổi hình chính
                thumbnail.addEventListener('click', () => {
                    document.getElementById('main-product-image').src = image;
                    // Cập nhật trạng thái active của thumbnails
                    document.querySelectorAll('#image-thumbnails > div').forEach(thumb => {
                        thumb.classList.remove('border-primary-500');
                        thumb.classList.add('border-transparent');
                    });
                    thumbnail.classList.remove('border-transparent');
                    thumbnail.classList.add('border-primary-500');
                });
                
                thumbnailsContainer.appendChild(thumbnail);
            });
        } else if (product.image) {
            // Nếu chỉ có 1 hình chính
            const thumbnail = document.createElement('div');
            thumbnail.className = 'aspect-square bg-gray-100 rounded border border-primary-500 cursor-pointer overflow-hidden';
            thumbnail.innerHTML = `<img src="${product.image}" alt="${product.name}" class="w-full h-full object-cover">`;
            thumbnailsContainer.appendChild(thumbnail);
        }
    }
    
    // Cập nhật đánh giá sao
    function updateRatingStars(rating) {
        const ratingContainer = document.getElementById('product-rating');
        ratingContainer.innerHTML = '';
        
        // Tính toán số sao đầy và số sao nửa
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        
        // Thêm sao đầy
        for (let i = 0; i < fullStars; i++) {
            ratingContainer.innerHTML += '<i class="fas fa-star"></i>';
        }
        
        // Thêm nửa sao nếu có
        if (hasHalfStar) {
            ratingContainer.innerHTML += '<i class="fas fa-star-half-alt"></i>';
        }
        
        // Thêm sao trống cho đủ 5 sao
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        for (let i = 0; i < emptyStars; i++) {
            ratingContainer.innerHTML += '<i class="far fa-star"></i>';
        }
    }
    
    // Cập nhật thông số kỹ thuật
    function updateSpecifications(product) {
        // Hàm hỗ trợ cập nhật giá trị nếu có
        const updateSpecValue = (id, value) => {
            const element = document.getElementById(id);
            if (element && value) {
                element.textContent = value;
            }
        };
        
        // Cập nhật các thông số
        if (product.specifications) {
            const specs = product.specifications;
            updateSpecValue('spec-dimensions', specs.dimensions);
            updateSpecValue('spec-weight', specs.weight);
            updateSpecValue('spec-package-dimensions', specs.package_dimensions);
            updateSpecValue('spec-material', specs.material);
            updateSpecValue('spec-surface', specs.surface);
            updateSpecValue('spec-origin', specs.origin);
            updateSpecValue('spec-brand', specs.brand);
            updateSpecValue('spec-warranty', specs.warranty);
        } else {
            // Cập nhật một số thông tin cơ bản nếu có
            updateSpecValue('spec-material', product.material);
            updateSpecValue('spec-brand', product.brand);
            updateSpecValue('spec-origin', product.origin);
            updateSpecValue('spec-warranty', '12 tháng');
        }
    }
    
    // Tải sản phẩm liên quan
    async function loadRelatedProducts(category) {
        try {
            const relatedContainer = document.getElementById('related-products');
            relatedContainer.innerHTML = '';
            
            let relatedProducts = [];
            try {
                // Thử lấy từ API
                const params = new URLSearchParams();
                if (category) {
                    params.append('category', category);
                }
                params.append('exclude', productId);
                params.append('limit', '4');
                
                relatedProducts = await fetchAPI(`/products/products/?${params.toString()}`);
                if (relatedProducts.results) {
                    relatedProducts = relatedProducts.results;
                }
            } catch (error) {
                console.warn('Failed to fetch related products from API, using sample data:', error);
                // Lọc sản phẩm mẫu liên quan
                relatedProducts = sampleProducts
                    .filter(p => p.id != productId && (!category || p.category === category))
                    .slice(0, 4);
            }
            
            // Nếu không tìm thấy sản phẩm liên quan
            if (relatedProducts.length === 0) {
                relatedContainer.parentElement.classList.add('hidden');
                return;
            }
            
            // Hiển thị container
            relatedContainer.parentElement.classList.remove('hidden');
            
            // Render sản phẩm liên quan
            for (const product of relatedProducts) {
                const card = document.createElement('div');
                card.innerHTML = await loadProductCard(product);
                relatedContainer.appendChild(card);
            }
        } catch (error) {
            console.error('Error loading related products:', error);
        }
    }
    
    // Lưu sản phẩm đã xem vào localStorage
    function saveViewedProduct(product) {
        try {
            // Lấy danh sách sản phẩm đã xem
            let viewedProducts = JSON.parse(localStorage.getItem('viewedProducts') || '[]');
            
            // Kiểm tra xem sản phẩm đã có trong danh sách chưa
            const index = viewedProducts.findIndex(p => p.id == product.id);
            if (index !== -1) {
                // Nếu có, xóa để thêm lại vào đầu danh sách
                viewedProducts.splice(index, 1);
            }
            
            // Thêm sản phẩm vào đầu danh sách
            viewedProducts.unshift({
                id: product.id,
                name: product.name,
                price: product.price,
                original_price: product.original_price,
                image: product.image,
                category: product.category,
                discount_percentage: product.discount_percentage,
                rating: product.rating
            });
            
            // Giới hạn danh sách lưu trữ 10 sản phẩm
            viewedProducts = viewedProducts.slice(0, 10);
            
            // Lưu lại vào localStorage
            localStorage.setItem('viewedProducts', JSON.stringify(viewedProducts));
        } catch (error) {
            console.error('Error saving viewed product:', error);
        }
    }
    
    // Hiển thị sản phẩm đã xem gần đây
    async function showRecentlyViewedProducts() {
        try {
            const container = document.getElementById('recently-viewed-products');
            const containerParent = document.getElementById('recently-viewed-container');
            
            // Lấy danh sách sản phẩm đã xem
            let viewedProducts = JSON.parse(localStorage.getItem('viewedProducts') || '[]');
            
            // Loại bỏ sản phẩm hiện tại
            viewedProducts = viewedProducts.filter(p => p.id != productId);
            
            // Nếu không có sản phẩm đã xem
            if (viewedProducts.length === 0) {
                containerParent.classList.add('hidden');
                return;
            }
            
            // Hiển thị container
            containerParent.classList.remove('hidden');
            container.innerHTML = '';
            
            // Hiển thị tối đa 4 sản phẩm
            const productsToShow = viewedProducts.slice(0, 4);
            
            // Render sản phẩm
            for (const product of productsToShow) {
                const card = document.createElement('div');
                card.innerHTML = await loadProductCard(product);
                container.appendChild(card);
            }
        } catch (error) {
            console.error('Error showing recently viewed products:', error);
        }
    }
    
    // Khởi tạo các sự kiện cho trang chi tiết sản phẩm
    function initProductDetailEvents() {
        // Xử lý tăng/giảm số lượng
        const quantityInput = document.getElementById('quantity');
        const decreaseBtn = document.getElementById('decrease-quantity');
        const increaseBtn = document.getElementById('increase-quantity');
        
        decreaseBtn.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });
        
        increaseBtn.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value);
            quantityInput.value = currentValue + 1;
        });
        
        // Xử lý thêm vào giỏ hàng
        document.getElementById('add-to-cart').addEventListener('click', () => {
            const quantity = parseInt(quantityInput.value);
            addToCart(productId, quantity);
        });
        
        // Xử lý mua ngay
        document.getElementById('buy-now').addEventListener('click', () => {
            const quantity = parseInt(quantityInput.value);
            addToCart(productId, quantity);
            // Chuyển tới trang giỏ hàng
            window.location.href = '/cart.html';
        });
    }
    
    // Hiển thị thông báo lỗi
    function showError(message) {
        contentContainer.innerHTML = `
            <div class="container mx-auto px-4 py-16 text-center">
                <i class="fas fa-exclamation-circle text-red-500 text-5xl mb-4"></i>
                <h2 class="text-2xl font-bold text-gray-800 mb-2">Đã xảy ra lỗi</h2>
                <p class="text-gray-600 mb-8">${message}</p>
                <a href="/product_list.html" class="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-3 rounded-lg inline-block">
                    Xem các sản phẩm khác
                </a>
            </div>
        `;
    }
    
    // Lấy sản phẩm mẫu theo ID
    function getSampleProductById(id) {
        const product = sampleProducts.find(p => p.id == id);
        if (product) {
            // Thêm một số thông tin mẫu cho sản phẩm
            return {
                ...product,
                sku: `SKU${product.id}`,
                short_description: `${product.name} với thiết kế hiện đại, chất lượng cao, phù hợp với nhiều không gian sống khác nhau.`,
                description: `
                    <h2>Giới thiệu ${product.name}</h2>
                    <p>${product.name} là sự kết hợp hoàn hảo giữa thiết kế hiện đại và tính năng tiện dụng. Với đường nét thiết kế tinh tế, sản phẩm này sẽ là điểm nhấn cho không gian sống của bạn.</p>
                    <p>Được sản xuất từ chất liệu cao cấp, ${product.name} đảm bảo độ bền và tính thẩm mỹ trong suốt quá trình sử dụng. Quá trình sản xuất tuân thủ các tiêu chuẩn quốc tế về an toàn và bảo vệ môi trường.</p>
                    <h3>Ưu điểm nổi bật</h3>
                    <ul>
                        <li>Thiết kế hiện đại, phù hợp với nhiều phong cách nội thất</li>
                        <li>Chất liệu cao cấp, bền đẹp theo thời gian</li>
                        <li>Tính năng tiện dụng, đáp ứng nhu cầu sử dụng</li>
                        <li>Màu sắc trang nhã, dễ dàng kết hợp với các đồ nội thất khác</li>
                    </ul>
                    <p>Với ${product.name}, không gian sống của bạn sẽ trở nên sang trọng và tiện nghi hơn bao giờ hết.</p>
                `,
                specifications: {
                    dimensions: "120 x 80 x 75 cm",
                    weight: "25 kg",
                    package_dimensions: "125 x 85 x 20 cm",
                    material: "Gỗ sồi tự nhiên",
                    surface: "Sơn PU cao cấp",
                    origin: "Việt Nam",
                    brand: "Nội Thất Cao Cấp",
                    warranty: "12 tháng"
                },
                in_stock: true
            };
        }
        return null;
    }
}

// Hàm định dạng tiền tệ
function formatCurrency(amount) {
    return amount.toLocaleString('vi-VN') + '₫';
}

function loadCartPage() {
    console.log('Loading cart page...');
    
    try {
        // Tải nội dung trang giỏ hàng
        fetch('./pages/cart.html')
            .then(response => response.text())
            .then(html => {
                if (contentContainer) {
                    contentContainer.innerHTML = html;
                    
                    // Sau khi DOM được tải, tiến hành hiển thị giỏ hàng
                    renderCart();
                    
                    // Khởi tạo các sự kiện cho trang giỏ hàng
                    initCartEvents();
                }
            })
            .catch(error => {
                console.error('Error loading cart page:', error);
                if (contentContainer) {
                    contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
                }
            });
    } catch (error) {
        console.error('Error loading cart page:', error);
        if (contentContainer) {
            contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
        }
    }
    
    // Hiển thị giỏ hàng
    async function renderCart() {
        try {
            // Lấy container hiển thị sản phẩm
            const cartItemsContainer = document.getElementById('cart-items');
            const emptyCartMessage = document.getElementById('empty-cart');
            const cartActions = document.getElementById('cart-actions');
            const cartQuantity = document.getElementById('cart-quantity');
            const checkoutButton = document.getElementById('proceed-checkout');
            
            // Kiểm tra giỏ hàng
            if (cart.length === 0) {
                // Hiển thị thông báo giỏ hàng trống
                if (emptyCartMessage) emptyCartMessage.classList.remove('hidden');
                if (cartActions) cartActions.classList.add('hidden');
                if (checkoutButton) checkoutButton.disabled = true;
                
                // Cập nhật tổng tiền
                updateCartTotals(0);
                if (cartQuantity) cartQuantity.textContent = '0';
                
                return;
            }
            
            // Ẩn thông báo giỏ hàng trống, hiện các action
            if (emptyCartMessage) emptyCartMessage.classList.add('hidden');
            if (cartActions) cartActions.classList.remove('hidden');
            if (checkoutButton) checkoutButton.disabled = false;
            
            // Xóa tất cả sản phẩm cũ trong container
            if (cartItemsContainer) {
                cartItemsContainer.innerHTML = '';
            }
            
            // Tổng giá trị giỏ hàng
            let totalAmount = 0;
            let totalItems = 0;
            
            // Lặp qua từng sản phẩm trong giỏ hàng
            for (const item of cart) {
                // Lấy thông tin sản phẩm từ API hoặc dữ liệu mẫu
                let product;
                try {
                    // Thử lấy từ API
                    product = await fetchAPI(`/products/products/${item.id}/`);
                } catch (error) {
                    console.warn('Failed to fetch product from API, using sample data:', error);
                    // Sử dụng dữ liệu mẫu
                    product = sampleProducts.find(p => p.id == item.id);
                }
                
                if (!product) continue;
                
                // Tính toán thành tiền
                const itemTotal = product.price * item.quantity;
                totalAmount += itemTotal;
                totalItems += item.quantity;
                
                // Tạo phần tử hiển thị sản phẩm
                const cartItemElement = document.createElement('div');
                cartItemElement.className = 'cart-item border-b border-gray-200 p-4';
                cartItemElement.dataset.id = item.id;
                
                cartItemElement.innerHTML = `
                    <div class="md:grid md:grid-cols-12 flex flex-wrap items-center">
                        <!-- Product Info -->
                        <div class="md:col-span-6 flex items-center mb-4 md:mb-0 w-full">
                            <div class="w-20 h-20 flex-shrink-0 bg-gray-100 rounded-md overflow-hidden">
                                <img src="${product.image || 'https://via.placeholder.com/80'}" alt="${product.name}" class="w-full h-full object-cover">
                            </div>
                            <div class="ml-4">
                                <h3 class="text-sm font-medium text-gray-800">
                                    <a href="/product_detail.html?id=${product.id}" class="hover:text-primary-600">${product.name}</a>
                                </h3>
                                <p class="text-sm text-gray-500">${product.category || ''}</p>
                            </div>
                        </div>
                        
                        <!-- Price -->
                        <div class="md:col-span-2 text-sm text-gray-800 mb-2 md:mb-0 md:text-center w-1/3 md:w-auto">
                            <span class="md:hidden inline-block w-16 text-gray-500">Giá:</span>
                            ${formatCurrency(product.price)}
                        </div>
                        
                        <!-- Quantity -->
                        <div class="md:col-span-2 flex items-center justify-center mb-2 md:mb-0 w-1/3 md:w-auto">
                            <div class="flex items-center border border-gray-300 rounded-md">
                                <button class="decrease-quantity w-8 h-8 text-gray-600 hover:bg-gray-100 flex items-center justify-center">
                                    <i class="fas fa-minus text-xs"></i>
                                </button>
                                <input type="number" value="${item.quantity}" min="1" class="item-quantity w-10 h-8 text-center text-sm border-0 focus:outline-none focus:ring-0" data-id="${item.id}">
                                <button class="increase-quantity w-8 h-8 text-gray-600 hover:bg-gray-100 flex items-center justify-center">
                                    <i class="fas fa-plus text-xs"></i>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Total -->
                        <div class="md:col-span-2 text-sm font-medium text-gray-800 md:text-right flex justify-between w-1/3 md:w-auto relative">
                            <span class="md:hidden text-gray-500">Tổng:</span>
                            <span class="item-total">${formatCurrency(itemTotal)}</span>
                            
                            <!-- Delete Button -->
                            <button class="remove-item text-gray-400 hover:text-red-500 md:absolute md:right-4" data-id="${item.id}">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                    </div>
                `;
                
                // Thêm vào container
                if (cartItemsContainer) {
                    cartItemsContainer.appendChild(cartItemElement);
                }
            }
            
            // Cập nhật tổng tiền
            updateCartTotals(totalAmount);
            
            // Cập nhật số lượng sản phẩm
            if (cartQuantity) cartQuantity.textContent = totalItems;
        } catch (error) {
            console.error('Error rendering cart:', error);
        }
    }
    
    // Cập nhật tổng tiền giỏ hàng
    function updateCartTotals(subtotal) {
        // Tính giảm giá (nếu có)
        const discount = 0; // Sẽ cập nhật sau khi có mã giảm giá
        
        // Tính tổng tiền sau giảm giá
        const total = subtotal - discount;
        
        // Cập nhật UI
        document.getElementById('subtotal').textContent = formatCurrency(subtotal);
        document.getElementById('discount').textContent = formatCurrency(discount);
        document.getElementById('total').textContent = formatCurrency(total);
    }
    
    // Cập nhật số lượng sản phẩm trong giỏ hàng
    function updateCartItem(productId, quantity) {
        // Tìm sản phẩm trong giỏ hàng
        const index = cart.findIndex(item => item.id == productId);
        
        if (index !== -1) {
            if (quantity <= 0) {
                // Nếu số lượng <= 0, xóa sản phẩm khỏi giỏ hàng
                removeCartItem(productId);
            } else {
                // Cập nhật số lượng
                cart[index].quantity = quantity;
                
                // Lưu giỏ hàng vào localStorage
                localStorage.setItem('cart', JSON.stringify(cart));
                
                // Render lại giỏ hàng
                renderCart();
            }
        }
    }
    
    // Xóa sản phẩm khỏi giỏ hàng
    function removeCartItem(productId) {
        // Lọc giỏ hàng, loại bỏ sản phẩm cần xóa
        cart = cart.filter(item => item.id != productId);
        
        // Lưu giỏ hàng vào localStorage
        localStorage.setItem('cart', JSON.stringify(cart));
        
        // Render lại giỏ hàng
        renderCart();
        
        // Cập nhật số lượng sản phẩm trong icon giỏ hàng
        updateCartCount();
    }
    
    // Xóa toàn bộ giỏ hàng
    function clearCart() {
        // Xóa mảng giỏ hàng
        cart = [];
        
        // Lưu giỏ hàng vào localStorage
        localStorage.setItem('cart', JSON.stringify(cart));
        
        // Render lại giỏ hàng
        renderCart();
        
        // Cập nhật số lượng sản phẩm trong icon giỏ hàng
        updateCartCount();
        
        // Hiển thị thông báo
        showNotification('Giỏ hàng đã được xóa!');
    }
    
    // Xử lý sự kiện trong trang giỏ hàng
    function initCartEvents() {
        // Xử lý sự kiện xóa sản phẩm
        document.addEventListener('click', function(e) {
            if (e.target.closest('.remove-item')) {
                const button = e.target.closest('.remove-item');
                const productId = button.dataset.id;
                removeCartItem(productId);
            }
        });
        
        // Xử lý sự kiện tăng số lượng
        document.addEventListener('click', function(e) {
            if (e.target.closest('.increase-quantity')) {
                const button = e.target.closest('.increase-quantity');
                const input = button.parentElement.querySelector('input');
                const productId = input.dataset.id;
                const newQuantity = parseInt(input.value) + 1;
                updateCartItem(productId, newQuantity);
            }
        });
        
        // Xử lý sự kiện giảm số lượng
        document.addEventListener('click', function(e) {
            if (e.target.closest('.decrease-quantity')) {
                const button = e.target.closest('.decrease-quantity');
                const input = button.parentElement.querySelector('input');
                const productId = input.dataset.id;
                const newQuantity = parseInt(input.value) - 1;
                if (newQuantity > 0) {
                    updateCartItem(productId, newQuantity);
                }
            }
        });
        
        // Xử lý sự kiện thay đổi số lượng trực tiếp
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('item-quantity')) {
                const input = e.target;
                const productId = input.dataset.id;
                let newQuantity = parseInt(input.value);
                
                // Đảm bảo số lượng hợp lệ
                if (isNaN(newQuantity) || newQuantity < 1) {
                    newQuantity = 1;
                    input.value = 1;
                }
                
                updateCartItem(productId, newQuantity);
            }
        });
        
        // Xử lý sự kiện xóa toàn bộ giỏ hàng
        const clearCartButton = document.getElementById('clear-cart');
        if (clearCartButton) {
            clearCartButton.addEventListener('click', function() {
                if (confirm('Bạn có chắc chắn muốn xóa toàn bộ giỏ hàng?')) {
                    clearCart();
                }
            });
        }
        
        // Xử lý sự kiện áp dụng mã giảm giá
        const applyCouponButton = document.getElementById('apply-coupon');
        if (applyCouponButton) {
            applyCouponButton.addEventListener('click', function() {
                const couponCode = document.getElementById('coupon-code').value.trim();
                if (couponCode) {
                    // Đây chỉ là demo, thực tế sẽ gọi API để kiểm tra mã
                    if (couponCode.toUpperCase() === 'SUMMER10') {
                        showNotification('Áp dụng mã giảm giá thành công!');
                        // Lưu mã giảm giá và render lại giỏ hàng
                        localStorage.setItem('couponCode', couponCode);
                        renderCart();
                    } else {
                        showNotification('Mã giảm giá không hợp lệ hoặc đã hết hạn!', 'error');
                    }
                } else {
                    showNotification('Vui lòng nhập mã giảm giá!', 'error');
                }
            });
        }
        
        // Xử lý sự kiện chuyển đến trang thanh toán
        const checkoutButton = document.getElementById('proceed-checkout');
        if (checkoutButton) {
            checkoutButton.addEventListener('click', function() {
                window.location.href = '/checkout.html';
            });
        }
    }
}

function loadCheckoutPage() {
    console.log('Loading checkout page...');
    
    try {
        // Tải nội dung trang thanh toán
        fetch('./pages/checkout.html')
            .then(response => response.text())
            .then(html => {
                if (contentContainer) {
                    contentContainer.innerHTML = html;
                    
                    // Sau khi DOM được tải, tiến hành hiển thị thông tin thanh toán
                    renderCheckout();
                    
                    // Khởi tạo các sự kiện cho trang thanh toán
                    initCheckoutEvents();
                }
            })
            .catch(error => {
                console.error('Error loading checkout page:', error);
                if (contentContainer) {
                    contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
                }
            });
    } catch (error) {
        console.error('Error loading checkout page:', error);
        if (contentContainer) {
            contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
        }
    }
    
    // Hiển thị thông tin thanh toán
    async function renderCheckout() {
        try {
            // Kiểm tra giỏ hàng
            if (cart.length === 0) {
                // Hiển thị cảnh báo giỏ hàng trống
                const emptyCartWarning = document.getElementById('empty-cart-warning');
                if (emptyCartWarning) {
                    emptyCartWarning.classList.remove('hidden');
                }
                
                // Vô hiệu hóa nút đặt hàng
                const placeOrderButton = document.getElementById('place-order');
                if (placeOrderButton) {
                    placeOrderButton.disabled = true;
                    placeOrderButton.classList.add('opacity-50', 'cursor-not-allowed');
                }
                
                // Cập nhật tổng tiền
                updateCheckoutTotals(0);
                
                return;
            }
            
            // Tải danh sách sản phẩm trong giỏ hàng
            const cartSummaryItems = document.getElementById('cart-summary-items');
            if (cartSummaryItems) {
                cartSummaryItems.innerHTML = '';
            }
            
            // Tổng giá trị đơn hàng
            let totalAmount = 0;
            
            // Lặp qua từng sản phẩm trong giỏ hàng
            for (const item of cart) {
                // Lấy thông tin sản phẩm từ API hoặc dữ liệu mẫu
                let product;
                try {
                    // Thử lấy từ API
                    product = await fetchAPI(`/products/products/${item.id}/`);
                } catch (error) {
                    console.warn('Failed to fetch product from API, using sample data:', error);
                    // Sử dụng dữ liệu mẫu
                    product = sampleProducts.find(p => p.id == item.id);
                }
                
                if (!product) continue;
                
                // Tính toán thành tiền
                const itemTotal = product.price * item.quantity;
                totalAmount += itemTotal;
                
                // Tạo phần tử hiển thị sản phẩm
                const cartItemElement = document.createElement('div');
                cartItemElement.className = 'flex items-center py-2';
                
                cartItemElement.innerHTML = `
                    <div class="w-12 h-12 flex-shrink-0 bg-gray-100 rounded-md overflow-hidden">
                        <img src="${product.image || 'https://via.placeholder.com/80'}" alt="${product.name}" class="w-full h-full object-cover">
                    </div>
                    <div class="flex-grow ml-3">
                        <div class="text-sm font-medium text-gray-800">${product.name}</div>
                        <div class="text-xs text-gray-500">SL: ${item.quantity}</div>
                    </div>
                    <div class="ml-2 text-sm font-medium text-gray-800">${formatCurrency(itemTotal)}</div>
                `;
                
                // Thêm vào container
                if (cartSummaryItems) {
                    cartSummaryItems.appendChild(cartItemElement);
                }
            }
            
            // Cập nhật tổng tiền
            updateCheckoutTotals(totalAmount);
        } catch (error) {
            console.error('Error rendering checkout:', error);
        }
    }
    
    // Cập nhật tổng tiền đơn hàng
    function updateCheckoutTotals(subtotal) {
        // Tính giảm giá (nếu có)
        const discount = 0; // Sẽ cập nhật sau khi có mã giảm giá
        
        // Phí vận chuyển
        let shipping = 0;
        const shippingMethod = document.querySelector('input[name="shipping-method"]:checked');
        if (shippingMethod && shippingMethod.value === 'express') {
            shipping = 50000; // Phí giao hàng nhanh: 50.000đ
        }
        
        // Tính tổng tiền sau giảm giá và phí vận chuyển
        const total = subtotal - discount + shipping;
        
        // Cập nhật UI
        document.getElementById('checkout-subtotal').textContent = formatCurrency(subtotal);
        document.getElementById('checkout-discount').textContent = formatCurrency(discount);
        document.getElementById('checkout-shipping').textContent = shipping > 0 ? formatCurrency(shipping) : 'Miễn phí';
        document.getElementById('checkout-total').textContent = formatCurrency(total);
    }
    
    // Khởi tạo sự kiện cho trang thanh toán
    function initCheckoutEvents() {
        // Xử lý sự kiện thay đổi phương thức vận chuyển
        const shippingMethods = document.querySelectorAll('input[name="shipping-method"]');
        shippingMethods.forEach(method => {
            method.addEventListener('change', function() {
                // Lấy tạm tính hiện tại
                const subtotalText = document.getElementById('checkout-subtotal').textContent;
                const subtotal = parseFloat(subtotalText.replace(/[^0-9]/g, ''));
                
                // Cập nhật tổng tiền với phương thức vận chuyển mới
                updateCheckoutTotals(subtotal);
            });
        });
        
        // Xử lý sự kiện khi chọn tỉnh/thành phố
        const provinceSelect = document.getElementById('province');
        if (provinceSelect) {
            provinceSelect.addEventListener('change', function() {
                const districtSelect = document.getElementById('district');
                const wardSelect = document.getElementById('ward');
                
                // Reset quận/huyện và phường/xã
                if (districtSelect) {
                    districtSelect.innerHTML = '<option value="">Chọn Quận/Huyện</option>';
                    districtSelect.disabled = !provinceSelect.value;
                }
                
                if (wardSelect) {
                    wardSelect.innerHTML = '<option value="">Chọn Phường/Xã</option>';
                    wardSelect.disabled = true;
                }
                
                // Nếu đã chọn tỉnh/thành phố, thêm dữ liệu mẫu cho quận/huyện
                if (provinceSelect.value) {
                    if (districtSelect) {
                        // Thêm dữ liệu mẫu cho quận/huyện
                        const districts = getDistricts(provinceSelect.value);
                        districts.forEach(district => {
                            const option = document.createElement('option');
                            option.value = district.value;
                            option.textContent = district.text;
                            districtSelect.appendChild(option);
                        });
                    }
                }
            });
        }
        
        // Xử lý sự kiện khi chọn quận/huyện
        const districtSelect = document.getElementById('district');
        if (districtSelect) {
            districtSelect.addEventListener('change', function() {
                const wardSelect = document.getElementById('ward');
                
                // Reset phường/xã
                if (wardSelect) {
                    wardSelect.innerHTML = '<option value="">Chọn Phường/Xã</option>';
                    wardSelect.disabled = !districtSelect.value;
                }
                
                // Nếu đã chọn quận/huyện, thêm dữ liệu mẫu cho phường/xã
                if (districtSelect.value) {
                    if (wardSelect) {
                        // Thêm dữ liệu mẫu cho phường/xã
                        const wards = getWards(districtSelect.value);
                        wards.forEach(ward => {
                            const option = document.createElement('option');
                            option.value = ward.value;
                            option.textContent = ward.text;
                            wardSelect.appendChild(option);
                        });
                    }
                }
            });
        }
        
        // Xử lý sự kiện nút đặt hàng
        const checkoutForm = document.getElementById('checkout-form');
        if (checkoutForm) {
            checkoutForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Kiểm tra giỏ hàng
                if (cart.length === 0) {
                    showNotification('Giỏ hàng của bạn đang trống!', 'error');
                    return;
                }
                
                // Lấy thông tin form
                const formData = new FormData(checkoutForm);
                const orderData = {
                    id: 'ORD-' + Math.floor(100000 + Math.random() * 900000), // Tạo mã đơn hàng ngẫu nhiên
                    order_date: new Date().toLocaleDateString('vi-VN'),
                    customer: {
                        fullname: formData.get('fullname'),
                        phone: formData.get('phone'),
                        email: formData.get('email')
                    },
                    shipping: {
                        address: formData.get('address'),
                        province: formData.get('province'),
                        district: formData.get('district'),
                        ward: formData.get('ward'),
                        note: formData.get('note')
                    },
                    shipping_method: document.querySelector('input[name="shipping-method"]:checked').value,
                    payment_method: document.querySelector('input[name="payment-method"]:checked').value,
                    items: cart,
                    totals: {
                        subtotal: document.getElementById('checkout-subtotal').textContent,
                        discount: document.getElementById('checkout-discount').textContent,
                        shipping: document.getElementById('checkout-shipping').textContent,
                        total: document.getElementById('checkout-total').textContent
                    },
                    estimated_delivery: getEstimatedDelivery(document.querySelector('input[name="shipping-method"]:checked').value)
                };
                
                // Lưu thông tin đơn hàng vào localStorage
                localStorage.setItem('lastOrder', JSON.stringify(orderData));
                
                // Xóa giỏ hàng
                cart = [];
                localStorage.setItem('cart', JSON.stringify(cart));
                
                // Chuyển đến trang xác nhận đơn hàng
                window.location.href = '/order_confirmation.html';
            });
        }
    }
    
    // Hàm ước tính thời gian giao hàng
    function getEstimatedDelivery(shippingMethod) {
        const today = new Date();
        
        // Tính ngày bắt đầu giao hàng (bỏ qua cuối tuần)
        let startDay = new Date(today);
        startDay.setDate(today.getDate() + 1); // Bắt đầu từ ngày mai
        
        // Nếu ngày mai là chủ nhật, thêm 1 ngày
        if (startDay.getDay() === 0) {
            startDay.setDate(startDay.getDate() + 1);
        }
        
        // Tính ngày kết thúc giao hàng dựa vào phương thức vận chuyển
        let endDay = new Date(startDay);
        
        if (shippingMethod === 'express') {
            // Giao hàng nhanh: 1-2 ngày làm việc
            endDay.setDate(startDay.getDate() + 2);
            
            // Nếu ngày kết thúc là chủ nhật, thêm 1 ngày
            if (endDay.getDay() === 0) {
                endDay.setDate(endDay.getDate() + 1);
            }
        } else {
            // Giao hàng tiêu chuẩn: 3-5 ngày làm việc
            endDay.setDate(startDay.getDate() + 5);
            
            // Nếu ngày kết thúc là chủ nhật, thêm 1 ngày
            if (endDay.getDay() === 0) {
                endDay.setDate(endDay.getDate() + 1);
            }
        }
        
        // Định dạng ngày tháng
        const formatDate = (date) => {
            return date.toLocaleDateString('vi-VN');
        };
        
        return `${formatDate(startDay)} - ${formatDate(endDay)}`;
    }
    
    // Hàm mẫu lấy danh sách quận/huyện
    function getDistricts(provinceValue) {
        // Dữ liệu mẫu, trong thực tế sẽ lấy từ API
        const districtData = {
            'hanoi': [
                { value: 'cau-giay', text: 'Cầu Giấy' },
                { value: 'hoan-kiem', text: 'Hoàn Kiếm' },
                { value: 'hai-ba-trung', text: 'Hai Bà Trưng' },
                { value: 'dong-da', text: 'Đống Đa' }
            ],
            'hcm': [
                { value: 'quan-1', text: 'Quận 1' },
                { value: 'quan-3', text: 'Quận 3' },
                { value: 'quan-7', text: 'Quận 7' },
                { value: 'binh-thanh', text: 'Bình Thạnh' }
            ],
            'danang': [
                { value: 'hai-chau', text: 'Hải Châu' },
                { value: 'thanh-khe', text: 'Thanh Khê' },
                { value: 'son-tra', text: 'Sơn Trà' },
                { value: 'ngu-hanh-son', text: 'Ngũ Hành Sơn' }
            ]
        };
        
        return districtData[provinceValue] || [];
    }
    
    // Hàm mẫu lấy danh sách phường/xã
    function getWards(districtValue) {
        // Dữ liệu mẫu, trong thực tế sẽ lấy từ API
        const wardData = {
            'cau-giay': [
                { value: 'dich-vong', text: 'Dịch Vọng' },
                { value: 'mai-dich', text: 'Mai Dịch' },
                { value: 'quan-hoa', text: 'Quan Hoa' }
            ],
            'quan-1': [
                { value: 'ben-nghe', text: 'Bến Nghé' },
                { value: 'ben-thanh', text: 'Bến Thành' },
                { value: 'da-kao', text: 'Đa Kao' }
            ],
            'hai-chau': [
                { value: 'hai-chau-1', text: 'Hải Châu 1' },
                { value: 'hai-chau-2', text: 'Hải Châu 2' },
                { value: 'thach-thang', text: 'Thạch Thang' }
            ]
        };
        
        // Trả về một số phường/xã mẫu cho các quận/huyện khác
        if (!wardData[districtValue]) {
            return [
                { value: 'phuong-1', text: 'Phường 1' },
                { value: 'phuong-2', text: 'Phường 2' },
                { value: 'phuong-3', text: 'Phường 3' }
            ];
        }
        
        return wardData[districtValue];
    }
}

// Thêm hàm tải trang xác nhận đơn hàng
function loadOrderConfirmationPage() {
    console.log('Loading order confirmation page...');
    
    try {
        // Tải nội dung trang xác nhận đơn hàng
        fetch('./pages/order_confirmation.html')
            .then(response => response.text())
            .then(html => {
                if (contentContainer) {
                    contentContainer.innerHTML = html;
                    
                    // Sau khi DOM được tải, tiến hành hiển thị thông tin đơn hàng
                    renderOrderConfirmation();
                }
            })
            .catch(error => {
                console.error('Error loading order confirmation page:', error);
                if (contentContainer) {
                    contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
                }
            });
    } catch (error) {
        console.error('Error loading order confirmation page:', error);
        if (contentContainer) {
            contentContainer.innerHTML = '<div class="p-8 text-center text-red-500">Có lỗi xảy ra khi tải trang. Vui lòng thử lại sau.</div>';
        }
    }
    
    // Hiển thị thông tin đơn hàng
    function renderOrderConfirmation() {
        try {
            // Lấy thông tin đơn hàng từ localStorage
            const orderData = JSON.parse(localStorage.getItem('lastOrder'));
            
            // Nếu không có thông tin đơn hàng, chuyển về trang chủ
            if (!orderData) {
                window.location.href = '/';
                return;
            }
            
            // Cập nhật thông tin đơn hàng trong giao diện
            document.getElementById('order-number').textContent = orderData.id;
            document.getElementById('order-date').textContent = orderData.order_date;
            
            // Cập nhật thông tin người nhận
            document.getElementById('recipient-name').textContent = orderData.customer.fullname;
            document.getElementById('recipient-phone').textContent = orderData.customer.phone;
            document.getElementById('recipient-email').textContent = orderData.customer.email;
            
            // Cập nhật địa chỉ giao hàng
            document.getElementById('shipping-address').textContent = orderData.shipping.address;
            
            // Lấy tên tỉnh/thành phố, quận/huyện từ dữ liệu đơn hàng
            let provinceName = getProvinceName(orderData.shipping.province);
            let districtName = getDistrictName(orderData.shipping.district);
            let wardName = getWardName(orderData.shipping.ward);
            
            document.getElementById('shipping-city').textContent = `${wardName}, ${districtName}, ${provinceName}`;
            
            // Cập nhật ghi chú nếu có
            if (orderData.shipping.note) {
                document.getElementById('shipping-note').textContent = `Ghi chú: ${orderData.shipping.note}`;
            } else {
                document.getElementById('shipping-note').classList.add('hidden');
            }
            
            // Cập nhật phương thức giao hàng
            const shippingMethodText = orderData.shipping_method === 'express' 
                ? 'Giao hàng nhanh (1-2 ngày)' 
                : 'Giao hàng tiêu chuẩn (3-5 ngày)';
            document.getElementById('shipping-method').textContent = shippingMethodText;
            
            // Cập nhật dự kiến giao hàng
            document.getElementById('estimated-delivery').textContent = orderData.estimated_delivery;
            
            // Cập nhật phương thức thanh toán
            const paymentMethodElement = document.getElementById('payment-method');
            let paymentMethodText = '';
            let paymentMethodIcon = '';
            
            switch(orderData.payment_method) {
                case 'cod':
                    paymentMethodText = 'Thanh toán khi nhận hàng (COD)';
                    paymentMethodIcon = '<i class="fas fa-money-bill-wave text-gray-600 mr-2"></i>';
                    break;
                case 'bank-transfer':
                    paymentMethodText = 'Chuyển khoản ngân hàng';
                    paymentMethodIcon = '<i class="fas fa-university text-gray-600 mr-2"></i>';
                    break;
                case 'momo':
                    paymentMethodText = 'Ví điện tử MoMo';
                    paymentMethodIcon = '<img src="https://upload.wikimedia.org/wikipedia/vi/f/fe/MoMo_Logo.png" alt="MoMo" class="h-5 mr-2">';
                    break;
                case 'credit-card':
                    paymentMethodText = 'Thẻ tín dụng/Ghi nợ';
                    paymentMethodIcon = '<i class="fas fa-credit-card text-gray-600 mr-2"></i>';
                    break;
            }
            
            paymentMethodElement.innerHTML = paymentMethodIcon + paymentMethodText;
            
            // Cập nhật trạng thái thanh toán
            const paymentStatusElement = document.getElementById('payment-status');
            if (orderData.payment_method === 'cod') {
                paymentStatusElement.textContent = 'Chờ thanh toán';
                paymentStatusElement.className = 'text-sm font-medium text-orange-500';
            } else {
                paymentStatusElement.textContent = 'Đã thanh toán';
                paymentStatusElement.className = 'text-sm font-medium text-green-500';
            }
            
            // Render danh sách sản phẩm đã đặt
            renderOrderItems(orderData.items);
            
            // Cập nhật tổng tiền
            document.getElementById('order-subtotal').textContent = orderData.totals.subtotal;
            document.getElementById('order-discount').textContent = orderData.totals.discount;
            document.getElementById('order-shipping').textContent = orderData.totals.shipping;
            document.getElementById('order-total').textContent = orderData.totals.total;
            
        } catch (error) {
            console.error('Error rendering order confirmation:', error);
        }
    }
    
    // Render danh sách sản phẩm đã đặt
    async function renderOrderItems(items) {
        const orderItemsContainer = document.getElementById('order-items');
        if (!orderItemsContainer) return;
        
        // Xóa sản phẩm mẫu
        orderItemsContainer.innerHTML = '';
        
        // Render từng sản phẩm
        for (const item of items) {
            // Lấy thông tin sản phẩm từ API hoặc dữ liệu mẫu
            let product;
            try {
                // Thử lấy từ API
                product = await fetchAPI(`/products/products/${item.id}/`);
            } catch (error) {
                console.warn('Failed to fetch product from API, using sample data:', error);
                // Sử dụng dữ liệu mẫu
                product = sampleProducts.find(p => p.id == item.id);
            }
            
            if (!product) continue;
            
            // Tính thành tiền
            const itemTotal = product.price * item.quantity;
            
            // Tạo phần tử hiển thị sản phẩm
            const orderItemElement = document.createElement('div');
            orderItemElement.className = 'py-4';
            
            orderItemElement.innerHTML = `
                <div class="flex items-start">
                    <div class="w-16 h-16 flex-shrink-0 bg-gray-100 rounded-md overflow-hidden">
                        <img src="${product.image || 'https://via.placeholder.com/80'}" alt="${product.name}" class="w-full h-full object-cover">
                    </div>
                    <div class="ml-4 flex-grow">
                        <h4 class="text-sm font-medium text-gray-800">${product.name}</h4>
                        <p class="text-xs text-gray-500 mt-1">${product.category || ''}</p>
                        <div class="flex justify-between mt-1">
                            <span class="text-xs text-gray-500">SL: ${item.quantity}</span>
                            <span class="text-sm font-medium text-gray-800">${formatCurrency(itemTotal)}</span>
                        </div>
                    </div>
                </div>
            `;
            
            // Thêm vào container
            orderItemsContainer.appendChild(orderItemElement);
        }
    }
    
    // Hàm lấy tên tỉnh/thành phố từ value
    function getProvinceName(provinceValue) {
        const provinceMap = {
            'hanoi': 'Hà Nội',
            'hcm': 'TP. Hồ Chí Minh',
            'danang': 'Đà Nẵng'
        };
        
        return provinceMap[provinceValue] || provinceValue;
    }
    
    // Hàm lấy tên quận/huyện từ value
    function getDistrictName(districtValue) {
        const districtMap = {
            'cau-giay': 'Cầu Giấy',
            'hoan-kiem': 'Hoàn Kiếm',
            'hai-ba-trung': 'Hai Bà Trưng',
            'dong-da': 'Đống Đa',
            'quan-1': 'Quận 1',
            'quan-3': 'Quận 3',
            'quan-7': 'Quận 7',
            'binh-thanh': 'Bình Thạnh',
            'hai-chau': 'Hải Châu',
            'thanh-khe': 'Thanh Khê',
            'son-tra': 'Sơn Trà',
            'ngu-hanh-son': 'Ngũ Hành Sơn'
        };
        
        return districtMap[districtValue] || districtValue;
    }
    
    // Hàm lấy tên phường/xã từ value
    function getWardName(wardValue) {
        const wardMap = {
            'dich-vong': 'Dịch Vọng',
            'mai-dich': 'Mai Dịch',
            'quan-hoa': 'Quan Hoa',
            'ben-nghe': 'Bến Nghé',
            'ben-thanh': 'Bến Thành',
            'da-kao': 'Đa Kao',
            'hai-chau-1': 'Hải Châu 1',
            'hai-chau-2': 'Hải Châu 2',
            'thach-thang': 'Thạch Thang',
            'phuong-1': 'Phường 1',
            'phuong-2': 'Phường 2',
            'phuong-3': 'Phường 3'
        };
        
        return wardMap[wardValue] || wardValue;
    }
}
