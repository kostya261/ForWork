// ForWork ERP API Client

const API_BASE = '/api';

// Получение CSRF-токена из кук
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Базовый fetch с CSRF-токеном
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        credentials: 'same-origin',
    };

    const url = endpoint.startsWith('/') ? `${API_BASE}${endpoint}` : `${API_BASE}/${endpoint}`;

    try {
        const response = await fetch(url, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('API Error:', response.status, errorData);
            throw new Error(errorData.detail || JSON.stringify(errorData) || `HTTP ${response.status}`);
        }

        // Для DELETE может не быть тела ответа
        if (response.status === 204) {
            return null;
        }

        return response.json();
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// API методы для задач
const TaskAPI = {
    list: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`tasks/${query ? '?' + query : ''}`);
    },

    get: (id) => apiRequest(`tasks/${id}/`),

    create: (data) => apiRequest('tasks/', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    update: (id, data) => apiRequest(`tasks/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
    }),

    delete: (id) => apiRequest(`tasks/${id}/`, {
        method: 'DELETE',
    }),

    updateStatus: (id, status, comment = '') => apiRequest(`tasks/${id}/update_status/`, {
        method: 'POST',
        body: JSON.stringify({ status, comment }),
    }),

    addComment: (id, text) => apiRequest(`tasks/${id}/comments/`, {
        method: 'POST',
        body: JSON.stringify({ text }),
    }),

    addMaterial: (id, data) => apiRequest(`tasks/${id}/add_material/`, {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    consumeMaterial: (id, requirementId, quantity) => apiRequest(`tasks/${id}/consume_material/`, {
        method: 'POST',
        body: JSON.stringify({ requirement_id: requirementId, quantity }),
    }),

    addInventory: (id, data) => apiRequest(`tasks/${id}/add_inventory/`, {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    statistics: () => apiRequest('tasks/statistics/'),
};

// Уведомления
function showToast(message, type = 'info') {
    // Удаляем старые тосты
    const oldToasts = document.querySelectorAll('.toast-message');
    oldToasts.forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast-message alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'bottom: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
}

// Глобально доступные функции
window.TaskAPI = TaskAPI;
window.apiRequest = apiRequest;
window.showToast = showToast;