// API Client for Automated Attendance Management System Using Finite Automata

const getApiBaseUrl = () => {
    if (typeof window !== 'undefined' && window.API_BASE_URL) return window.API_BASE_URL;
    if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
        return '/api';
    }
    if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
        return '/api';
    }
    return 'https://automated-attendance-automata-1.onrender.com/api';
};

const API_BASE = getApiBaseUrl();

const getAuthHeaders = () => {
    const userStr = localStorage.getItem('attendance_user');
    const headers = { 'Content-Type': 'application/json' };
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            if (user && user.id) {
                headers['X-User-Id'] = user.id.toString();
            }
        } catch (e) {
            console.error('Error parsing user from localStorage', e);
        }
    }
    return headers;
};

const handleResponse = async (response) => {
    const data = await response.json();
    if (!response.ok) {
        const errorMsg = data.error || `HTTP ${response.status} Error`;
        const err = new Error(errorMsg);
        err.data = data;
        err.status = response.status;
        throw err;
    }
    return data;
};

export const api = {
    // Auth
    login: async (email, password) => {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        return handleResponse(res);
    },
    getDemoUsers: async () => {
        const res = await fetch(`${API_BASE}/auth/demo-users`);
        return handleResponse(res);
    },

    // DFA
    getDfaInfo: async () => {
        const res = await fetch(`${API_BASE}/dfa/info`);
        return handleResponse(res);
    },
    simulateDfa: async (initialState, sequence, role = 'faculty') => {
        const res = await fetch(`${API_BASE}/dfa/simulate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ initial_state: initialState, sequence, role })
        });
        return handleResponse(res);
    },

    // Attendance
    getAttendanceSheet: async (subjectId, date) => {
        const res = await fetch(`${API_BASE}/attendance/sheet?subject_id=${subjectId}&date=${date}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(res);
    },
    markAttendance: async (studentId, subjectId, date, symbol, reason = '') => {
        const res = await fetch(`${API_BASE}/attendance/mark`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                student_id: studentId,
                subject_id: subjectId,
                date,
                symbol,
                reason
            })
        });
        return handleResponse(res);
    },
    batchMarkAttendance: async (subjectId, date, symbol) => {
        const res = await fetch(`${API_BASE}/attendance/batch`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ subject_id: subjectId, date, symbol })
        });
        return handleResponse(res);
    },
    finalizeAttendance: async (subjectId, date) => {
        const res = await fetch(`${API_BASE}/attendance/finalize`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ subject_id: subjectId, date })
        });
        return handleResponse(res);
    },
    adminResetAttendance: async (attendanceId, reason) => {
        const res = await fetch(`${API_BASE}/attendance/reset`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ attendance_id: attendanceId, reason })
        });
        return handleResponse(res);
    },

    // Reports
    getReports: async (filters = {}) => {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([k, v]) => {
            if (v !== '' && v !== null && v !== undefined) params.append(k, v);
        });
        const res = await fetch(`${API_BASE}/attendance/reports?${params.toString()}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(res);
    },
    getExportCsvUrl: (filters = {}) => {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([k, v]) => {
            if (v !== '' && v !== null && v !== undefined) params.append(k, v);
        });
        return `${API_BASE}/attendance/export-csv?${params.toString()}`;
    },

    // Dashboards
    getAdminDashboard: async () => {
        const res = await fetch(`${API_BASE}/dashboard/admin`, { headers: getAuthHeaders() });
        return handleResponse(res);
    },
    getFacultyDashboard: async () => {
        const res = await fetch(`${API_BASE}/dashboard/faculty`, { headers: getAuthHeaders() });
        return handleResponse(res);
    },
    getStudentDashboard: async () => {
        const res = await fetch(`${API_BASE}/dashboard/student`, { headers: getAuthHeaders() });
        return handleResponse(res);
    },

    // Admin CRUD
    getDepartments: async () => {
        const res = await fetch(`${API_BASE}/admin/departments`, { headers: getAuthHeaders() });
        return handleResponse(res);
    },
    createDepartment: async (dept) => {
        const res = await fetch(`${API_BASE}/admin/departments`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(dept)
        });
        return handleResponse(res);
    },
    deleteDepartment: async (id) => {
        const res = await fetch(`${API_BASE}/admin/departments/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(res);
    },

    getFaculty: async () => {
        const res = await fetch(`${API_BASE}/admin/faculty`, { headers: getAuthHeaders() });
        return handleResponse(res);
    },
    createFaculty: async (fac) => {
        const res = await fetch(`${API_BASE}/admin/faculty`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(fac)
        });
        return handleResponse(res);
    },
    deleteFaculty: async (id) => {
        const res = await fetch(`${API_BASE}/admin/faculty/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(res);
    },

    getStudents: async () => {
        const res = await fetch(`${API_BASE}/admin/students`, { headers: getAuthHeaders() });
        return handleResponse(res);
    },
    createStudent: async (student) => {
        const res = await fetch(`${API_BASE}/admin/students`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(student)
        });
        return handleResponse(res);
    },
    deleteStudent: async (id) => {
        const res = await fetch(`${API_BASE}/admin/students/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(res);
    },

    getSubjects: async (deptId = '') => {
        const url = deptId ? `${API_BASE}/admin/subjects?department_id=${deptId}` : `${API_BASE}/admin/subjects`;
        const res = await fetch(url, { headers: getAuthHeaders() });
        return handleResponse(res);
    },
    createSubject: async (subj) => {
        const res = await fetch(`${API_BASE}/admin/subjects`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(subj)
        });
        return handleResponse(res);
    },
    deleteSubject: async (id) => {
        const res = await fetch(`${API_BASE}/admin/subjects/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(res);
    },

    getAuditLogs: async (limit = 100) => {
        const res = await fetch(`${API_BASE}/admin/audit-logs?limit=${limit}`, { headers: getAuthHeaders() });
        return handleResponse(res);
    }
};
