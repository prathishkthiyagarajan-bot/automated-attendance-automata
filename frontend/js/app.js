// Automated Attendance Management System Using Finite Automata
// Complete Frontend Application (React 18, Tailwind CSS, Chart.js)

const { useState, useEffect, useContext, createContext, useMemo, useRef } = React;

// ==============================================================================
// Contexts: Auth, Theme, Toast, Modal
// ==============================================================================

const AuthContext = createContext(null);
const ThemeContext = createContext(null);
const ToastContext = createContext(null);

const API_BASE = '/api';

const getAuthHeaders = () => {
    const userStr = localStorage.getItem('attendance_user');
    const headers = { 'Content-Type': 'application/json' };
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            if (user && user.id) {
                headers['X-User-Id'] = user.id.toString();
            }
        } catch (e) {}
    }
    return headers;
};

const apiCall = async (endpoint, options = {}) => {
    const defaultHeaders = getAuthHeaders();
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...(options.headers || {})
        }
    };
    const res = await fetch(`${API_BASE}${endpoint}`, config);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const error = new Error(data.error || `Request failed with status ${res.status}`);
        error.data = data;
        error.status = res.status;
        throw error;
    }
    return data;
};

// ==============================================================================
// Main Root App Component
// ==============================================================================

function App() {
    // Theme state
    const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'light');
    useEffect(() => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('app_theme', theme);
    }, [theme]);

    const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

    // Auth state
    const [user, setUser] = useState(() => {
        const saved = localStorage.getItem('attendance_user');
        return saved ? JSON.parse(saved) : null;
    });

    // Navigation state
    const [currentPage, setCurrentPage] = useState(() => {
        const savedUser = localStorage.getItem('attendance_user');
        if (!savedUser) return 'login';
        const u = JSON.parse(savedUser);
        if (u.role === 'admin') return 'admin-dashboard';
        if (u.role === 'faculty') return 'faculty-dashboard';
        return 'student-dashboard';
    });

    const [pageParams, setPageParams] = useState({});

    // Toast state
    const [toasts, setToasts] = useState([]);
    const showToast = (message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, duration);
    };

    // Modal state
    const [modal, setModal] = useState({ isOpen: false, title: '', message: '', onConfirm: null, confirmText: 'Confirm', isDanger: false, promptInput: false, promptValue: '' });

    const openConfirmModal = ({ title, message, onConfirm, confirmText = 'Confirm', isDanger = false }) => {
        setModal({ isOpen: true, title, message, onConfirm, confirmText, isDanger, promptInput: false, promptValue: '' });
    };

    const openPromptModal = ({ title, message, onConfirm, confirmText = 'Submit', placeholder = 'Enter reason...' }) => {
        setModal({ isOpen: true, title, message, onConfirm, confirmText, isDanger: false, promptInput: true, promptValue: '', placeholder });
    };

    const closeModal = () => {
        setModal(prev => ({ ...prev, isOpen: false }));
    };

    const login = (userData) => {
        setUser(userData);
        localStorage.setItem('attendance_user', JSON.stringify(userData));
        if (userData.role === 'admin') setCurrentPage('admin-dashboard');
        else if (userData.role === 'faculty') setCurrentPage('faculty-dashboard');
        else setCurrentPage('student-dashboard');
        showToast(`Welcome back, ${userData.name}!`, 'success');
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('attendance_user');
        setCurrentPage('login');
        showToast('You have been logged out.', 'info');
    };

    const navigate = (page, params = {}) => {
        setCurrentPage(page);
        setPageParams(params);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Render active page
    const renderPage = () => {
        if (!user && currentPage !== 'login') {
            return <LoginPage onLogin={login} />;
        }

        switch (currentPage) {
            case 'login':
                return <LoginPage onLogin={login} />;
            case 'admin-dashboard':
                return <AdminDashboard navigate={navigate} />;
            case 'faculty-dashboard':
                return <FacultyDashboard navigate={navigate} user={user} />;
            case 'student-dashboard':
                return <StudentDashboard navigate={navigate} user={user} />;
            case 'attendance-marking':
                return <AttendanceMarkingPage pageParams={pageParams} navigate={navigate} user={user} />;
            case 'attendance-reports':
                return <AttendanceReportsPage user={user} />;
            case 'dfa-visualization':
                return <DfaPage />;
            case 'departments':
                return <DepartmentManagementPage />;
            case 'faculty':
                return <FacultyManagementPage />;
            case 'students':
                return <StudentManagementPage />;
            case 'subjects':
                return <SubjectManagementPage />;
            case 'audit-logs':
                return <AuditLogsPage user={user} />;
            case 'profile':
                return <ProfilePage user={user} />;
            default:
                return <AdminDashboard navigate={navigate} />;
        }
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, navigate, currentPage }}>
            <ThemeContext.Provider value={{ theme, toggleTheme }}>
                <ToastContext.Provider value={{ showToast, openConfirmModal, openPromptModal }}>
                    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-900">
                        {/* Sidebar */}
                        {user && (
                            <Sidebar
                                currentPage={currentPage}
                                navigate={navigate}
                                user={user}
                                onLogout={logout}
                            />
                        )}

                        {/* Main Container */}
                        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                            {user && (
                                <Navbar
                                    user={user}
                                    theme={theme}
                                    toggleTheme={toggleTheme}
                                    onLogout={logout}
                                    currentPage={currentPage}
                                    navigate={navigate}
                                />
                            )}
                            <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
                                {renderPage()}
                            </main>
                        </div>
                    </div>

                    {/* Toast Overlay */}
                    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none">
                        {toasts.map(t => (
                            <div
                                key={t.id}
                                className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl shadow-2xl border text-sm transition-all transform animate-bounce-short ${
                                    t.type === 'success' ? 'bg-emerald-50 dark:bg-emerald-950/90 border-emerald-300 text-emerald-900 dark:text-emerald-100' :
                                    t.type === 'error' ? 'bg-rose-50 dark:bg-rose-950/90 border-rose-300 text-rose-900 dark:text-rose-100' :
                                    t.type === 'warning' ? 'bg-amber-50 dark:bg-amber-950/90 border-amber-300 text-amber-900 dark:text-amber-100' :
                                    'bg-indigo-50 dark:bg-indigo-950/90 border-indigo-300 text-indigo-900 dark:text-indigo-100'
                                }`}
                            >
                                <span className="text-lg">
                                    {t.type === 'success' && <i className="fa-solid fa-circle-check text-emerald-600"></i>}
                                    {t.type === 'error' && <i className="fa-solid fa-triangle-exclamation text-rose-600"></i>}
                                    {t.type === 'warning' && <i className="fa-solid fa-circle-exclamation text-amber-600"></i>}
                                    {t.type === 'info' && <i className="fa-solid fa-circle-info text-indigo-600"></i>}
                                </span>
                                <div className="flex-1">
                                    <p className="font-medium whitespace-pre-line leading-relaxed">{t.message}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Confirmation / Prompt Modal */}
                    {modal.isOpen && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
                            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-700">
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                    {modal.isDanger ? (
                                        <span className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-600">
                                            <i className="fa-solid fa-triangle-exclamation"></i>
                                        </span>
                                    ) : (
                                        <span className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600">
                                            <i className="fa-solid fa-shield-halved"></i>
                                        </span>
                                    )}
                                    {modal.title}
                                </h3>
                                <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                                    {modal.message}
                                </p>

                                {modal.promptInput && (
                                    <div className="mt-4">
                                        <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                                            Audit Reason (Mandatory)
                                        </label>
                                        <textarea
                                            value={modal.promptValue}
                                            onChange={(e) => setModal(prev => ({ ...prev, promptValue: e.target.value }))}
                                            placeholder={modal.placeholder}
                                            rows="3"
                                            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
                                        />
                                    </div>
                                )}

                                <div className="mt-6 flex justify-end gap-3">
                                    <button
                                        onClick={closeModal}
                                        className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 text-sm font-medium"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => {
                                            if (modal.promptInput && !modal.promptValue.trim()) {
                                                alert("Audit reason is required.");
                                                return;
                                            }
                                            if (modal.onConfirm) modal.onConfirm(modal.promptValue);
                                            closeModal();
                                        }}
                                        className={`px-4 py-2 rounded-xl text-white text-sm font-semibold shadow-md ${
                                            modal.isDanger
                                                ? 'bg-rose-600 hover:bg-rose-700'
                                                : 'bg-indigo-600 hover:bg-indigo-700'
                                        }`}
                                    >
                                        {modal.confirmText}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </ToastContext.Provider>
            </ThemeContext.Provider>
        </AuthContext.Provider>
    );
}

// ==============================================================================
// Navigation Components: Navbar & Sidebar
// ==============================================================================

function Navbar({ user, theme, toggleTheme, onLogout, currentPage, navigate }) {
    const roleColors = {
        admin: 'bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800',
        faculty: 'bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800',
        student: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800'
    };

    return (
        <header className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-4 md:px-6 z-10">
            <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                    <span className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center text-white shadow-md">
                        <i className="fa-solid fa-network-wired text-lg"></i>
                    </span>
                    <div className="hidden sm:block">
                        <h1 className="text-base font-bold text-slate-800 dark:text-white leading-tight">
                            Automated Attendance System
                        </h1>
                        <p className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
                            Governed by Finite Automata (DFA)
                        </p>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3">
                {/* DFA Quick Indicator */}
                <button
                    onClick={() => navigate('dfa-visualization')}
                    title="View Finite Automata Definition & State Machine"
                    className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-xs font-semibold border border-indigo-200 dark:border-indigo-800 hover:bg-indigo-100"
                >
                    <i className="fa-solid fa-code-fork"></i>
                    <span>DFA: M=(Q, Σ, δ, q₀, F)</span>
                </button>

                {/* Dark Mode Toggle */}
                <button
                    onClick={toggleTheme}
                    title="Toggle Theme"
                    className="w-9 h-9 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                    {theme === 'dark' ? <i className="fa-solid fa-sun text-amber-400"></i> : <i className="fa-solid fa-moon text-slate-700"></i>}
                </button>

                {/* Role Badge */}
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${roleColors[user.role]}`}>
                    {user.role}
                </span>

                {/* User menu */}
                <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-700">
                    <button
                        onClick={() => navigate('profile')}
                        className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400"
                    >
                        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold">
                            {user.name.charAt(0)}
                        </div>
                        <span className="hidden md:inline max-w-[140px] truncate">{user.name}</span>
                    </button>
                    <button
                        onClick={onLogout}
                        title="Sign out"
                        className="p-2 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                    >
                        <i className="fa-solid fa-right-from-bracket"></i>
                    </button>
                </div>
            </div>
        </header>
    );
}

function Sidebar({ currentPage, navigate, user, onLogout }) {
    const [collapsed, setCollapsed] = useState(false);

    const navItems = useMemo(() => {
        const common = [
            { id: 'dfa-visualization', label: 'DFA State Machine', icon: 'fa-diagram-project' }
        ];

        if (user.role === 'admin') {
            return [
                { id: 'admin-dashboard', label: 'Dashboard', icon: 'fa-chart-pie' },
                { id: 'attendance-marking', label: 'Attendance Marking', icon: 'fa-clipboard-check' },
                { id: 'attendance-reports', label: 'Attendance Reports', icon: 'fa-file-lines' },
                { id: 'departments', label: 'Departments', icon: 'fa-building-columns' },
                { id: 'faculty', label: 'Faculty Management', icon: 'fa-chalkboard-user' },
                { id: 'students', label: 'Student Directory', icon: 'fa-user-graduate' },
                { id: 'subjects', label: 'Subjects & Curriculum', icon: 'fa-book-bookmark' },
                { id: 'audit-logs', label: 'DFA Audit Logs', icon: 'fa-shield-halved' },
                ...common
            ];
        } else if (user.role === 'faculty') {
            return [
                { id: 'faculty-dashboard', label: 'Faculty Dashboard', icon: 'fa-chart-pie' },
                { id: 'attendance-marking', label: 'Mark Attendance', icon: 'fa-clipboard-check' },
                { id: 'attendance-reports', label: 'Attendance Analytics', icon: 'fa-file-lines' },
                ...common
            ];
        } else {
            return [
                { id: 'student-dashboard', label: 'My Attendance Portal', icon: 'fa-chart-user' },
                ...common
            ];
        }
    }, [user.role]);

    return (
        <aside className={`${collapsed ? 'w-20' : 'w-64'} bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col transition-all duration-300 z-20`}>
            {/* College header */}
            <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                {!collapsed && (
                    <div className="flex items-center gap-2">
                        <i className="fa-solid fa-graduation-cap text-indigo-600 text-xl"></i>
                        <span className="font-black text-sm tracking-wide text-slate-800 dark:text-white uppercase">
                            Univ Portal
                        </span>
                    </div>
                )}
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 mx-auto"
                >
                    <i className={`fa-solid ${collapsed ? 'fa-angles-right' : 'fa-angles-left'}`}></i>
                </button>
            </div>

            {/* Navigation links */}
            <nav className="flex-1 overflow-y-auto p-3 space-y-1">
                {navItems.map(item => {
                    const isActive = (currentPage === item.id);
                    return (
                        <button
                            key={item.id}
                            onClick={() => navigate(item.id)}
                            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                                isActive
                                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/60 hover:text-slate-900 dark:hover:text-slate-100'
                            }`}
                            title={collapsed ? item.label : ''}
                        >
                            <i className={`fa-solid ${item.icon} w-5 text-center text-base`}></i>
                            {!collapsed && <span>{item.label}</span>}
                        </button>
                    );
                })}
            </nav>

            {/* Bottom User Card */}
            <div className="p-3 border-t border-slate-200 dark:border-slate-700">
                <div className={`flex items-center gap-3 p-2 rounded-xl bg-slate-50 dark:bg-slate-700/40 ${collapsed ? 'justify-center' : ''}`}>
                    <div className="w-9 h-9 rounded-lg bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 flex items-center justify-center font-bold">
                        {user.name.charAt(0)}
                    </div>
                    {!collapsed && (
                        <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-800 dark:text-white truncate">{user.name}</p>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}

// ==============================================================================
// Login Page with 1-Click Demo Credentials
// ==============================================================================

function LoginPage({ onLogin }) {
    const [email, setEmail] = useState('admin@college.edu');
    const [password, setPassword] = useState('admin123');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [demoUsers, setDemoUsers] = useState([]);

    useEffect(() => {
        apiCall('/auth/demo-users')
            .then(data => {
                if (data.success) setDemoUsers(data.demo_users);
            })
            .catch(() => {});
    }, []);

    const handleSubmit = async (e) => {
        if (e) e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            if (data.success) {
                onLogin(data.user);
            }
        } catch (err) {
            setError(err.message || 'Login failed. Please verify credentials.');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectDemo = (demoEmail, demoPw) => {
        setEmail(demoEmail);
        setPassword(demoPw);
        setError('');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-4">
            <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Left side: Information & DFA highlight */}
                <div className="lg:col-span-6 text-white space-y-6">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-semibold">
                        <i className="fa-solid fa-atom animate-spin"></i>
                        Theoretical Computer Science & Web Engineering
                    </div>
                    <h1 className="text-4xl font-extrabold tracking-tight leading-tight">
                        Automated Attendance Management System
                    </h1>
                    <p className="text-slate-300 text-base leading-relaxed">
                        A modern full-stack college attendance portal strictly enforced by <strong className="text-indigo-400">Deterministic Finite Automata (DFA)</strong> to validate states, eliminate duplicate recording, and secure finalized attendance logs.
                    </p>

                    <div className="space-y-3 pt-2">
                        <div className="flex items-center gap-3 text-sm text-slate-200">
                            <span className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                                <i className="fa-solid fa-check"></i>
                            </span>
                            <span>Formal 5-tuple verification: δ(State, Symbol) validation</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-slate-200">
                            <span className="w-7 h-7 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
                                <i className="fa-solid fa-lock"></i>
                            </span>
                            <span>Immutable S4 Finalization with Authorized Admin Reset</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-slate-200">
                            <span className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
                                <i className="fa-solid fa-bell"></i>
                            </span>
                            <span>Automatic Critical Warnings for attendance &lt; 75%</span>
                        </div>
                    </div>
                </div>

                {/* Right side: Login Card */}
                <div className="lg:col-span-6 bg-white dark:bg-slate-800 rounded-3xl p-8 shadow-2xl border border-slate-200 dark:border-slate-700">
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-2">
                        Sign In to Your Account
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
                        Select a role or choose from 1-click demo accounts below.
                    </p>

                    {error && (
                        <div className="mb-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                            <i className="fa-solid fa-circle-exclamation text-base"></i>
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
                                Email Address
                            </label>
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="name@college.edu"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase mb-1">
                                Password
                            </label>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2"
                        >
                            {loading ? <i className="fa-solid fa-spinner fa-spin"></i> : <i className="fa-solid fa-right-to-bracket"></i>}
                            <span>Sign In</span>
                        </button>
                    </form>

                    {/* Quick Demo Accounts */}
                    <div className="mt-6 pt-5 border-t border-slate-200 dark:border-slate-700">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
                            1-Click Demo Profiles:
                        </span>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <button
                                type="button"
                                onClick={() => handleSelectDemo('admin@college.edu', 'admin123')}
                                className="p-2 rounded-lg bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 font-medium text-left border border-purple-200 dark:border-purple-900"
                            >
                                <span className="font-bold block">🔑 Admin</span>
                                <span className="text-[10px] text-purple-500 truncate block">Dr. Alan Turing</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => handleSelectDemo('faculty1@college.edu', 'faculty123')}
                                className="p-2 rounded-lg bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-medium text-left border border-emerald-200 dark:border-emerald-900"
                            >
                                <span className="font-bold block">👩‍🏫 Faculty (CSE)</span>
                                <span className="text-[10px] text-emerald-500 truncate block">Prof. Grace Hopper</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => handleSelectDemo('student1@college.edu', 'student123')}
                                className="p-2 rounded-lg bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 font-medium text-left border border-blue-200 dark:border-blue-900"
                            >
                                <span className="font-bold block">🎓 Student (High %)</span>
                                <span className="text-[10px] text-blue-500 truncate block">Alice Walker (90%)</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => handleSelectDemo('student8@college.edu', 'student123')}
                                className="p-2 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 font-medium text-left border border-rose-200 dark:border-rose-900"
                            >
                                <span className="font-bold block">⚠️ Student (&lt; 75%)</span>
                                <span className="text-[10px] text-rose-500 truncate block">Hannah Abbott (Warning)</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ==============================================================================
// Admin Dashboard
// ==============================================================================

function AdminDashboard({ navigate }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const chartRef = useRef(null);
    const doughnutRef = useRef(null);

    useEffect(() => {
        apiCall('/dashboard/admin')
            .then(res => {
                if (res.success) setData(res);
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    // Render Chart.js Department Bar Chart
    useEffect(() => {
        if (!data || !data.department_stats) return;

        const ctx = document.getElementById('deptChart');
        if (!ctx) return;

        if (chartRef.current) chartRef.current.destroy();

        const labels = data.department_stats.map(d => d.department_code);
        const percentages = data.department_stats.map(d => d.percentage);

        chartRef.current = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Attendance %',
                    data: percentages,
                    backgroundColor: ['#6366f1', '#10b981', '#f59e0b'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + '%' }
                    }
                }
            }
        });

        return () => {
            if (chartRef.current) chartRef.current.destroy();
        };
    }, [data]);

    // Render Chart.js DFA State Distribution Doughnut
    useEffect(() => {
        if (!data || !data.state_distribution) return;

        const ctx = document.getElementById('stateDoughnut');
        if (!ctx) return;

        if (doughnutRef.current) doughnutRef.current.destroy();

        const stateColors = {
            'S0': '#9ca3af',
            'S1': '#10b981',
            'S2': '#ef4444',
            'S3': '#f59e0b',
            'S4': '#3b82f6'
        };

        const stateLabels = {
            'S0': 'S0: Not Marked',
            'S1': 'S1: Present',
            'S2': 'S2: Absent',
            'S3': 'S3: Late',
            'S4': 'S4: Finalized'
        };

        const labels = data.state_distribution.map(s => stateLabels[s.automata_state] || s.automata_state);
        const counts = data.state_distribution.map(s => s.count);
        const bgColors = data.state_distribution.map(s => stateColors[s.automata_state] || '#cbd5e1');

        doughnutRef.current = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: counts,
                    backgroundColor: bgColors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });

        return () => {
            if (doughnutRef.current) doughnutRef.current.destroy();
        };
    }, [data]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 text-slate-500">
                <i className="fa-solid fa-spinner fa-spin text-3xl"></i>
            </div>
        );
    }

    const { counts, recent_logs } = data;

    return (
        <div className="space-y-6">
            {/* Top Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Students</p>
                        <h3 className="text-2xl font-black text-slate-800 dark:text-white mt-1">{counts.students}</h3>
                        <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-medium">Across 3 Departments</p>
                    </div>
                    <span className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xl">
                        <i className="fa-solid fa-user-graduate"></i>
                    </span>
                </div>

                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Faculty Members</p>
                        <h3 className="text-2xl font-black text-slate-800 dark:text-white mt-1">{counts.faculty}</h3>
                        <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1 font-medium">Assigned to 6 Subjects</p>
                    </div>
                    <span className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xl">
                        <i className="fa-solid fa-chalkboard-user"></i>
                    </span>
                </div>

                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Departments</p>
                        <h3 className="text-2xl font-black text-slate-800 dark:text-white mt-1">{counts.departments}</h3>
                        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1 font-medium">CSE, ECE, IT</p>
                    </div>
                    <span className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 flex items-center justify-center text-xl">
                        <i className="fa-solid fa-building-columns"></i>
                    </span>
                </div>

                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Attendance Logs</p>
                        <h3 className="text-2xl font-black text-slate-800 dark:text-white mt-1">{counts.attendance_records}</h3>
                        <p className="text-xs text-purple-600 dark:text-purple-400 mt-1 font-medium">DFA Verified Transitions</p>
                    </div>
                    <span className="w-12 h-12 rounded-xl bg-purple-50 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400 flex items-center justify-center text-xl">
                        <i className="fa-solid fa-clipboard-check"></i>
                    </span>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-7 bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h4 className="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
                            <i className="fa-solid fa-chart-column text-indigo-600"></i>
                            Department Attendance Performance
                        </h4>
                        <button
                            onClick={() => navigate('attendance-reports')}
                            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                        >
                            View Full Report →
                        </button>
                    </div>
                    <div className="h-64">
                        <canvas id="deptChart"></canvas>
                    </div>
                </div>

                <div className="lg:col-span-5 bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h4 className="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
                            <i className="fa-solid fa-chart-pie text-blue-600"></i>
                            DFA State Distribution
                        </h4>
                        <button
                            onClick={() => navigate('dfa-visualization')}
                            className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                        >
                            DFA Graph →
                        </button>
                    </div>
                    <div className="h-64">
                        <canvas id="stateDoughnut"></canvas>
                    </div>
                </div>
            </div>

            {/* Recent DFA Activity Logs Feed */}
            <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h4 className="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
                            <i className="fa-solid fa-timeline text-purple-600"></i>
                            Recent Finite Automata Transitions (Audit Trail)
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                            Live stream of mathematical state changes governed by δ(state, symbol)
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('audit-logs')}
                        className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 font-semibold text-slate-700 dark:text-slate-300"
                    >
                        View All Logs
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                            <tr>
                                <th className="px-4 py-3">Timestamp</th>
                                <th className="px-4 py-3">Student</th>
                                <th className="px-4 py-3">Subject</th>
                                <th className="px-4 py-3">DFA Transition δ</th>
                                <th className="px-4 py-3">Input Symbol</th>
                                <th className="px-4 py-3">Audit Reason / Description</th>
                                <th className="px-4 py-3">Actor</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {recent_logs.map(log => (
                                <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-750">
                                    <td className="px-4 py-3 font-mono text-slate-500 whitespace-nowrap">
                                        {log.timestamp}
                                    </td>
                                    <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200">
                                        {log.student_name} <span className="font-normal text-slate-400">({log.register_number})</span>
                                    </td>
                                    <td className="px-4 py-3 font-bold text-indigo-600 dark:text-indigo-400">
                                        {log.subject_code}
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <span className="font-mono font-bold">
                                            <span className="text-slate-500">{log.previous_state}</span>
                                            <span className="text-slate-400 mx-1.5">→</span>
                                            <span className={`px-2 py-0.5 rounded ${
                                                log.next_state === 'S1' ? 'badge-s1' :
                                                log.next_state === 'S2' ? 'badge-s2' :
                                                log.next_state === 'S3' ? 'badge-s3' :
                                                log.next_state === 'S4' ? 'badge-s4' : 'badge-s0'
                                            }`}>
                                                {log.next_state}
                                            </span>
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 font-mono font-bold">
                                        <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700">
                                            {log.input_symbol}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                                        {log.reason || 'Routine attendance marking'}
                                    </td>
                                    <td className="px-4 py-3 text-slate-500 font-medium">
                                        {log.changed_by_name || 'System'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

// ==============================================================================
// Faculty Dashboard
// ==============================================================================

function FacultyDashboard({ navigate, user }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiCall('/dashboard/faculty')
            .then(res => {
                if (res.success) setData(res);
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 text-slate-500">
                <i className="fa-solid fa-spinner fa-spin text-3xl"></i>
            </div>
        );
    }

    const { subjects, today } = data;

    return (
        <div className="space-y-6">
            {/* Greeting Header */}
            <div className="p-6 rounded-3xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <span className="px-3 py-1 rounded-full bg-white/20 text-xs font-semibold uppercase tracking-wider">
                        Faculty Portal • {user.department_code || 'Dept'}
                    </span>
                    <h2 className="text-2xl md:text-3xl font-extrabold mt-2">
                        Welcome, {user.name}
                    </h2>
                    <p className="text-emerald-100 text-sm mt-1">
                        Assigned Subjects: {subjects.length} • Session Date: <span className="font-mono font-bold">{today}</span>
                    </p>
                </div>
                <button
                    onClick={() => navigate('attendance-marking')}
                    className="px-5 py-2.5 rounded-xl bg-white text-emerald-800 hover:bg-emerald-50 font-bold text-sm shadow-md transition-all flex items-center gap-2 self-start md:self-center"
                >
                    <i className="fa-solid fa-clipboard-check"></i>
                    <span>Mark Today's Attendance</span>
                </button>
            </div>

            {/* Assigned Subjects Grid */}
            <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-book-open text-emerald-600"></i>
                Your Assigned Classes & Subjects
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {subjects.map(sub => {
                    const isFinalized = (sub.today_state === 'S4');
                    const isMarked = (sub.today_marked_count > 0);

                    return (
                        <div
                            key={sub.id}
                            className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-5 hover:shadow-md transition-all flex flex-col justify-between"
                        >
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <span className="px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 font-mono font-bold text-xs">
                                        {sub.subject_code}
                                    </span>
                                    <span className="text-xs font-semibold text-slate-500">
                                        Sem {sub.semester} • {sub.credits} Credits
                                    </span>
                                </div>
                                <h4 className="text-base font-bold text-slate-800 dark:text-white mb-2">
                                    {sub.subject_name}
                                </h4>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    Enrolled Students: <strong className="text-slate-700 dark:text-slate-200">{sub.enrolled_students}</strong>
                                </p>
                            </div>

                            <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
                                <div>
                                    {isFinalized ? (
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                                            <i className="fa-solid fa-lock"></i> Finalized (S4)
                                        </span>
                                    ) : isMarked ? (
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                                            <i className="fa-solid fa-pen"></i> In Progress
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                                            <i className="fa-regular fa-circle"></i> Unmarked (S0)
                                        </span>
                                    )}
                                </div>
                                <button
                                    onClick={() => navigate('attendance-marking', { subjectId: sub.id, date: today })}
                                    className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-sm flex items-center gap-1.5"
                                >
                                    <span>Take Attendance</span>
                                    <i className="fa-solid fa-arrow-right text-[10px]"></i>
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// ==============================================================================
// Student Dashboard (Percentages & Critical Warnings)
// ==============================================================================

function StudentDashboard({ navigate, user }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const lineChartRef = useRef(null);

    useEffect(() => {
        apiCall('/dashboard/student')
            .then(res => {
                if (res.success) setData(res);
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    // Render Monthly Trend Chart
    useEffect(() => {
        if (!data || !data.monthly_trend) return;
        const ctx = document.getElementById('studentMonthlyChart');
        if (!ctx) return;

        if (lineChartRef.current) lineChartRef.current.destroy();

        const labels = data.monthly_trend.map(m => m.month);
        const dataPoints = data.monthly_trend.map(m => (m.total > 0 ? Math.round((m.present / m.total) * 100) : 0));

        lineChartRef.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.length ? labels : ['Current Month'],
                datasets: [{
                    label: 'Attendance %',
                    data: dataPoints.length ? dataPoints : [data.summary.overall_percentage],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + '%' }
                    }
                }
            }
        });

        return () => {
            if (lineChartRef.current) lineChartRef.current.destroy();
        };
    }, [data]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 text-slate-500">
                <i className="fa-solid fa-spinner fa-spin text-3xl"></i>
            </div>
        );
    }

    const { profile, summary, subjects } = data;
    const isWarning = summary.warning;

    // Calculate required classes needed to reach 75%
    // (Present + x) / (Total + x) >= 0.75  =>  Present + x >= 0.75 * Total + 0.75 * x  =>  0.25 * x >= 0.75 * Total - Present  =>  x >= 3 * Total - 4 * Present
    const classesNeeded = isWarning
        ? Math.max(0, Math.ceil(3 * summary.total_conducted - 4 * summary.present))
        : 0;

    return (
        <div className="space-y-6">
            {/* Student Profile & Summary Card */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white flex items-center justify-center text-2xl font-bold shadow-md">
                        {profile.name.charAt(0)}
                    </div>
                    <div>
                        <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 text-xs font-bold uppercase tracking-wider">
                            {profile.department_code} • Semester {profile.semester}
                        </span>
                        <h2 className="text-2xl font-black text-slate-800 dark:text-white mt-1">
                            {profile.name}
                        </h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                            Register No: {profile.register_number} • {profile.email}
                        </p>
                    </div>
                </div>

                {/* Overall Attendance Percentage Gauge */}
                <div className={`p-4 rounded-2xl border flex items-center gap-4 ${
                    isWarning
                        ? 'bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900'
                        : 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900'
                }`}>
                    <div className="text-center">
                        <div className={`text-4xl font-black ${isWarning ? 'text-rose-600' : 'text-emerald-600'}`}>
                            {summary.overall_percentage}%
                        </div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                            Overall Attendance
                        </span>
                    </div>
                    <div className="border-l border-slate-200 dark:border-slate-700 pl-4 text-xs space-y-1">
                        <p className="text-slate-600 dark:text-slate-300">Conducted: <strong>{summary.total_conducted}</strong></p>
                        <p className="text-emerald-600 font-semibold">Present: <strong>{summary.present}</strong></p>
                        <p className="text-rose-600 font-semibold">Absent: <strong>{summary.absent}</strong></p>
                        <p className="text-amber-600 font-semibold">Late: <strong>{summary.late}</strong></p>
                    </div>
                </div>
            </div>

            {/* CRITICAL ATTENDANCE WARNING BANNER (When < 75%) */}
            {isWarning && (
                <div className="p-5 rounded-2xl bg-gradient-to-r from-rose-600 to-red-700 text-white shadow-xl flex items-start gap-4 animate-pulse-gentle">
                    <span className="text-3xl p-2 rounded-xl bg-white/20">
                        <i className="fa-solid fa-triangle-exclamation"></i>
                    </span>
                    <div className="flex-1">
                        <h4 className="text-lg font-bold">
                            CRITICAL ATTENDANCE WARNING: BELOW 75% MANDATORY THRESHOLD
                        </h4>
                        <p className="text-rose-100 text-sm mt-1 leading-relaxed">
                            Your aggregate attendance is currently <strong className="text-white underline">{summary.overall_percentage}%</strong>, which fails the institutional minimum requirement of 75%.
                        </p>
                        <p className="text-xs text-rose-200 mt-2 font-medium">
                            📌 <strong>Remedial Plan:</strong> You have attended {summary.present} out of {summary.total_conducted} conducted classes. You must attend the next <strong className="text-white underline text-sm">{classesNeeded} consecutive class session(s)</strong> without any absence to restore your attendance to 75.0%.
                        </p>
                    </div>
                </div>
            )}

            {/* Subject Breakdown Cards */}
            <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-book-bookmark text-blue-600"></i>
                Subject-Wise Attendance Breakdown
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {subjects.map(s => {
                    const subWarning = s.warning;
                    return (
                        <div
                            key={s.subject_id}
                            className={`p-5 rounded-2xl bg-white dark:bg-slate-800 border shadow-sm ${
                                subWarning
                                    ? 'border-rose-300 dark:border-rose-900/60'
                                    : 'border-slate-200 dark:border-slate-700'
                            }`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                                    {s.subject_code}
                                </span>
                                {subWarning ? (
                                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 flex items-center gap-1">
                                        <i className="fa-solid fa-triangle-exclamation text-[10px]"></i> Warning (&lt; 75%)
                                    </span>
                                ) : (
                                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 flex items-center gap-1">
                                        <i className="fa-solid fa-circle-check text-[10px]"></i> Satisfactory
                                    </span>
                                )}
                            </div>

                            <h4 className="text-base font-bold text-slate-800 dark:text-white">
                                {s.subject_name}
                            </h4>

                            {/* Percentage Bar */}
                            <div className="mt-4">
                                <div className="flex justify-between text-xs font-semibold mb-1">
                                    <span className="text-slate-500">Attendance Percentage</span>
                                    <span className={subWarning ? 'text-rose-600 font-bold' : 'text-emerald-600 font-bold'}>
                                        {s.percentage}%
                                    </span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
                                    <div
                                        className={`h-2.5 rounded-full ${subWarning ? 'bg-rose-500' : 'bg-emerald-500'}`}
                                        style={{ width: `${Math.min(100, s.percentage)}%` }}
                                    ></div>
                                </div>
                            </div>

                            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/60 grid grid-cols-4 gap-2 text-center text-xs">
                                <div className="p-1.5 rounded-lg bg-slate-50 dark:bg-slate-700/40">
                                    <span className="text-slate-400 block text-[10px]">Classes</span>
                                    <span className="font-bold text-slate-700 dark:text-slate-200">{s.total_conducted}</span>
                                </div>
                                <div className="p-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300">
                                    <span className="block text-[10px]">Present</span>
                                    <span className="font-bold">{s.present_count}</span>
                                </div>
                                <div className="p-1.5 rounded-lg bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300">
                                    <span className="block text-[10px]">Absent</span>
                                    <span className="font-bold">{s.absent_count}</span>
                                </div>
                                <div className="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-300">
                                    <span className="block text-[10px]">Late</span>
                                    <span className="font-bold">{s.late_count}</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Monthly Trend Chart */}
            <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <h4 className="text-base font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                    <i className="fa-solid fa-chart-line text-blue-600"></i>
                    Monthly Attendance History
                </h4>
                <div className="h-64">
                    <canvas id="studentMonthlyChart"></canvas>
                </div>
            </div>
        </div>
    );
}

// ==============================================================================
// Attendance Marking Page (Strictly Governed by DFA Engine)
// ==============================================================================

function AttendanceMarkingPage({ pageParams, navigate, user }) {
    const { showToast, openConfirmModal, openPromptModal } = useContext(ToastContext);

    const [departments, setDepartments] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [selectedDept, setSelectedDept] = useState('');
    const [selectedSubject, setSelectedSubject] = useState(pageParams.subjectId || '');
    const [selectedDate, setSelectedDate] = useState(pageParams.date || new Date().toISOString().split('T')[0]);

    const [sheetData, setSheetData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);

    // Load departments
    useEffect(() => {
        apiCall('/admin/departments')
            .then(res => {
                if (res.success) {
                    setDepartments(res.departments);
                    if (res.departments.length && !selectedDept) {
                        setSelectedDept(res.departments[0].id);
                    }
                }
            })
            .catch(() => {});
    }, []);

    // Load subjects when dept changes
    useEffect(() => {
        if (!selectedDept) return;
        apiCall(`/admin/subjects?department_id=${selectedDept}`)
            .then(res => {
                if (res.success) {
                    setSubjects(res.subjects);
                    if (res.subjects.length && !selectedSubject) {
                        setSelectedSubject(res.subjects[0].id);
                    }
                }
            })
            .catch(() => {});
    }, [selectedDept]);

    // Load attendance sheet
    const loadSheet = () => {
        if (!selectedSubject || !selectedDate) return;
        setLoading(true);
        apiCall(`/attendance/sheet?subject_id=${selectedSubject}&date=${selectedDate}`)
            .then(res => {
                if (res.success) setSheetData(res);
            })
            .catch(err => {
                showToast(err.message, 'error');
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        loadSheet();
    }, [selectedSubject, selectedDate]);

    // Mark single student via DFA Symbol (P, A, L)
    const handleMark = async (studentId, symbol) => {
        setActionLoading(true);
        try {
            const res = await apiCall('/attendance/mark', {
                method: 'POST',
                body: JSON.stringify({
                    student_id: studentId,
                    subject_id: selectedSubject,
                    date: selectedDate,
                    symbol: symbol
                })
            });
            if (res.success) {
                showToast(res.message, 'success', 2500);
                loadSheet();
            }
        } catch (err) {
            // DFA Rejection
            showToast(err.message, 'error', 6000);
        } finally {
            setActionLoading(false);
        }
    };

    // Batch Mark All Present (P)
    const handleBatchMark = async () => {
        setActionLoading(true);
        try {
            const res = await apiCall('/attendance/batch', {
                method: 'POST',
                body: JSON.stringify({
                    subject_id: selectedSubject,
                    date: selectedDate,
                    symbol: 'P'
                })
            });
            if (res.success) {
                showToast(`Batch update: Marked ${res.updated_count} students as Present (P).`, 'success');
                loadSheet();
            }
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setActionLoading(false);
        }
    };

    // Finalize Session (F)
    const handleFinalize = () => {
        openConfirmModal({
            title: "Finalize Attendance Session (DFA Symbol F)",
            message: "Finalizing will transition all student records to DFA State S4 (Accepting/Terminal). Attendance will be permanently locked against modifications by faculty. Are you sure you wish to finalize?",
            confirmText: "Finalize & Lock (F)",
            isDanger: false,
            onConfirm: async () => {
                setActionLoading(true);
                try {
                    const res = await apiCall('/attendance/finalize', {
                        method: 'POST',
                        body: JSON.stringify({
                            subject_id: selectedSubject,
                            date: selectedDate
                        })
                    });
                    if (res.success) {
                        showToast(res.message, 'success');
                        loadSheet();
                    }
                } catch (err) {
                    showToast(err.message, 'error', 6000);
                } finally {
                    setActionLoading(false);
                }
            }
        });
    };

    // Authorized Admin Reset (R)
    const handleAdminReset = (attendanceId) => {
        openPromptModal({
            title: "Authorized Admin DFA Reset: δ(S4, R) → S0",
            message: "This will reset the finalized attendance record back to State S0 (Not Marked). A mandatory audit explanation is required for institutional compliance.",
            placeholder: "e.g., Medical certificate verified; Dean authorized attendance correction.",
            confirmText: "Execute Admin Reset (R)",
            onConfirm: async (reason) => {
                setActionLoading(true);
                try {
                    const res = await apiCall('/attendance/reset', {
                        method: 'POST',
                        body: JSON.stringify({
                            attendance_id: attendanceId,
                            reason: reason
                        })
                    });
                    if (res.success) {
                        showToast(res.message, 'success');
                        loadSheet();
                    }
                } catch (err) {
                    showToast(err.message, 'error');
                } finally {
                    setActionLoading(false);
                }
            }
        });
    };

    const isFinalized = sheetData ? sheetData.is_finalized : false;

    return (
        <div className="space-y-6">
            {/* Filter Bar */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-3">
                    <div>
                        <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">Department</label>
                        <select
                            value={selectedDept}
                            onChange={(e) => setSelectedDept(e.target.value)}
                            className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                        >
                            {departments.map(d => (
                                <option key={d.id} value={d.id}>{d.department_code} - {d.department_name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">Subject</label>
                        <select
                            value={selectedSubject}
                            onChange={(e) => setSelectedSubject(e.target.value)}
                            className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white min-w-[200px]"
                        >
                            {subjects.map(s => (
                                <option key={s.id} value={s.id}>{s.subject_code} - {s.subject_name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">Session Date</label>
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white font-mono"
                        />
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={loadSheet}
                        disabled={loading}
                        className="px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300"
                    >
                        <i className={`fa-solid fa-arrows-rotate mr-1 ${loading ? 'fa-spin' : ''}`}></i> Refresh
                    </button>
                    {!isFinalized && (
                        <>
                            <button
                                onClick={handleBatchMark}
                                disabled={actionLoading || loading}
                                className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm"
                            >
                                <i className="fa-solid fa-check-double mr-1"></i> Mark All Present (P)
                            </button>
                            <button
                                onClick={handleFinalize}
                                disabled={actionLoading || loading}
                                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md flex items-center gap-1.5"
                            >
                                <i className="fa-solid fa-lock"></i>
                                <span>Finalize Attendance (F)</span>
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Session State Banner */}
            {isFinalized ? (
                <div className="p-4 rounded-2xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center text-lg shadow-sm">
                            <i className="fa-solid fa-lock"></i>
                        </span>
                        <div>
                            <h4 className="text-sm font-bold text-blue-950 dark:text-blue-200">
                                Session Attendance is FINALIZED (DFA State S4)
                            </h4>
                            <p className="text-xs text-blue-700 dark:text-blue-300">
                                This session is locked in terminal state S4. Routine edits (P, A, L) are rejected by the DFA transition table.
                            </p>
                        </div>
                    </div>
                    {user.role === 'admin' && (
                        <span className="text-xs font-bold text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/50 px-3 py-1 rounded-lg">
                            Admin Override Reset (R) Available Below
                        </span>
                    )}
                </div>
            ) : (
                <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center text-lg shadow-sm">
                            <i className="fa-solid fa-pen-to-square"></i>
                        </span>
                        <div>
                            <h4 className="text-sm font-bold text-slate-800 dark:text-white">
                                Active Attendance Worksheet (Pre-Finalization)
                            </h4>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                Permitted DFA Transitions: S0 → S1 (P), S0 → S2 (A), S0 → S3 (L). Intermediate corrections allowed.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Students Attendance Table */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                    <h3 className="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <i className="fa-solid fa-list-check text-indigo-600"></i>
                        Enrolled Students ({sheetData ? sheetData.total_enrolled : 0})
                    </h3>
                    <div className="flex items-center gap-2 text-xs">
                        <span className="text-slate-400">Legend:</span>
                        <span className="badge-s1 px-2 py-0.5 rounded font-bold">P: Present</span>
                        <span className="badge-s2 px-2 py-0.5 rounded font-bold">A: Absent</span>
                        <span className="badge-s3 px-2 py-0.5 rounded font-bold">L: Late</span>
                        <span className="badge-s0 px-2 py-0.5 rounded font-bold">S0: Not Marked</span>
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-48 text-slate-400">
                        <i className="fa-solid fa-spinner fa-spin text-2xl"></i>
                    </div>
                ) : sheetData && sheetData.students.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                                <tr>
                                    <th className="px-4 py-3">Register Number</th>
                                    <th className="px-4 py-3">Student Name</th>
                                    <th className="px-4 py-3">Current Status</th>
                                    <th className="px-4 py-3">DFA State</th>
                                    <th className="px-4 py-3 text-center">Finite Automata Actions (Inputs Σ)</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {sheetData.students.map(s => {
                                    const state = s.automata_state;
                                    const status = s.status;
                                    const studentFinalized = (state === 'S4');

                                    return (
                                        <tr key={s.student_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-750">
                                            <td className="px-4 py-3 font-mono font-bold text-slate-700 dark:text-slate-300">
                                                {s.register_number}
                                            </td>
                                            <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                                                {s.name}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`px-2.5 py-1 rounded-full font-bold text-[11px] ${
                                                    state === 'S1' ? 'badge-s1' :
                                                    state === 'S2' ? 'badge-s2' :
                                                    state === 'S3' ? 'badge-s3' :
                                                    state === 'S4' ? 'badge-s4' : 'badge-s0'
                                                }`}>
                                                    {status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 font-mono font-bold">
                                                <span className={`px-2 py-0.5 rounded text-[11px] ${
                                                    state === 'S1' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300' :
                                                    state === 'S2' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300' :
                                                    state === 'S3' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300' :
                                                    state === 'S4' ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300' :
                                                    'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                                                }`}>
                                                    {state}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center justify-center gap-2">
                                                    {studentFinalized ? (
                                                        user.role === 'admin' ? (
                                                            <button
                                                                onClick={() => handleAdminReset(s.attendance_id)}
                                                                className="px-3 py-1 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs shadow-sm flex items-center gap-1"
                                                            >
                                                                <i className="fa-solid fa-rotate-left"></i>
                                                                <span>Admin Reset δ(S4, R)</span>
                                                            </button>
                                                        ) : (
                                                            <span className="text-slate-400 font-medium italic flex items-center gap-1">
                                                                <i className="fa-solid fa-lock text-[10px]"></i> Locked (S4)
                                                            </span>
                                                        )
                                                    ) : (
                                                        <>
                                                            <button
                                                                onClick={() => handleMark(s.student_id, 'P')}
                                                                disabled={actionLoading}
                                                                className={`px-3 py-1 rounded-lg font-bold text-xs transition-all ${
                                                                    state === 'S1'
                                                                        ? 'bg-emerald-600 text-white ring-2 ring-emerald-400'
                                                                        : 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300'
                                                                }`}
                                                            >
                                                                P
                                                            </button>
                                                            <button
                                                                onClick={() => handleMark(s.student_id, 'A')}
                                                                disabled={actionLoading}
                                                                className={`px-3 py-1 rounded-lg font-bold text-xs transition-all ${
                                                                    state === 'S2'
                                                                        ? 'bg-rose-600 text-white ring-2 ring-rose-400'
                                                                        : 'bg-rose-100 text-rose-800 hover:bg-rose-200 dark:bg-rose-950/60 dark:text-rose-300'
                                                                }`}
                                                            >
                                                                A
                                                            </button>
                                                            <button
                                                                onClick={() => handleMark(s.student_id, 'L')}
                                                                disabled={actionLoading}
                                                                className={`px-3 py-1 rounded-lg font-bold text-xs transition-all ${
                                                                    state === 'S3'
                                                                        ? 'bg-amber-600 text-white ring-2 ring-amber-400'
                                                                        : 'bg-amber-100 text-amber-800 hover:bg-amber-200 dark:bg-amber-950/60 dark:text-amber-300'
                                                                }`}
                                                            >
                                                                L
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-8 text-center text-slate-500">
                        No students enrolled in this subject.
                    </div>
                )}
            </div>
        </div>
    );
}

// ==============================================================================
// Attendance Reports Page
// ==============================================================================

function AttendanceReportsPage({ user }) {
    const { showToast } = useContext(ToastContext);

    const [departments, setDepartments] = useState([]);
    const [subjects, setSubjects] = useState([]);

    const [filterDept, setFilterDept] = useState('');
    const [filterSem, setFilterSem] = useState('');
    const [filterSubject, setFilterSubject] = useState('');
    const [fromDate, setFromDate] = useState('');
    const [toDate, setToDate] = useState('');
    const [searchQuery, setSearchQuery] = useState('');

    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        apiCall('/admin/departments')
            .then(res => {
                if (res.success) setDepartments(res.departments);
            })
            .catch(() => {});

        apiCall('/admin/subjects')
            .then(res => {
                if (res.success) setSubjects(res.subjects);
            })
            .catch(() => {});
    }, []);

    const fetchReports = () => {
        setLoading(true);
        const query = new URLSearchParams();
        if (filterDept) query.append('department_id', filterDept);
        if (filterSem) query.append('semester', filterSem);
        if (filterSubject) query.append('subject_id', filterSubject);
        if (fromDate) query.append('from_date', fromDate);
        if (toDate) query.append('to_date', toDate);

        apiCall(`/attendance/reports?${query.toString()}`)
            .then(res => {
                if (res.success) setReports(res.reports);
            })
            .catch(err => showToast(err.message, 'error'))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchReports();
    }, [filterDept, filterSem, filterSubject, fromDate, toDate]);

    const filtered = useMemo(() => {
        if (!searchQuery.trim()) return reports;
        const q = searchQuery.toLowerCase();
        return reports.filter(r =>
            r.student_name.toLowerCase().includes(q) ||
            r.register_number.toLowerCase().includes(q) ||
            r.subject_code.toLowerCase().includes(q)
        );
    }, [reports, searchQuery]);

    // Download CSV
    const handleExportCsv = () => {
        const query = new URLSearchParams();
        if (filterDept) query.append('department_id', filterDept);
        if (filterSem) query.append('semester', filterSem);
        if (filterSubject) query.append('subject_id', filterSubject);
        if (fromDate) query.append('from_date', fromDate);
        if (toDate) query.append('to_date', toDate);

        window.location.href = `/api/attendance/export-csv?${query.toString()}`;
    };

    // Calculate analytics metrics
    const totalStudents = filtered.length;
    const warningCount = filtered.filter(r => r.below_threshold).length;
    const avgPercentage = totalStudents > 0
        ? Math.round(filtered.reduce((acc, cur) => acc + cur.attendance_percentage, 0) / totalStudents)
        : 0;

    return (
        <div className="space-y-6">
            {/* Top Stat Pills */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Evaluated Records</p>
                        <h3 className="text-2xl font-black text-slate-800 dark:text-white mt-1">{totalStudents}</h3>
                    </div>
                    <span className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-lg">
                        <i className="fa-solid fa-users"></i>
                    </span>
                </div>

                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Average Attendance</p>
                        <h3 className="text-2xl font-black text-slate-800 dark:text-white mt-1">{avgPercentage}%</h3>
                    </div>
                    <span className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-lg">
                        <i className="fa-solid fa-percent"></i>
                    </span>
                </div>

                <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold text-rose-500 uppercase tracking-wider">Critical Warnings (&lt; 75%)</p>
                        <h3 className="text-2xl font-black text-rose-600 mt-1">{warningCount}</h3>
                    </div>
                    <span className="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center text-lg">
                        <i className="fa-solid fa-triangle-exclamation"></i>
                    </span>
                </div>
            </div>

            {/* Filter Controls */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-3">
                    <select
                        value={filterDept}
                        onChange={(e) => setFilterDept(e.target.value)}
                        className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        <option value="">All Departments</option>
                        {departments.map(d => <option key={d.id} value={d.id}>{d.department_code}</option>)}
                    </select>

                    <select
                        value={filterSem}
                        onChange={(e) => setFilterSem(e.target.value)}
                        className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        <option value="">All Semesters</option>
                        {[1, 2, 3, 4, 5, 6, 7, 8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                    </select>

                    <select
                        value={filterSubject}
                        onChange={(e) => setFilterSubject(e.target.value)}
                        className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        <option value="">All Subjects</option>
                        {subjects.map(s => <option key={s.id} value={s.id}>{s.subject_code} - {s.subject_name}</option>)}
                    </select>

                    <input
                        type="date"
                        value={fromDate}
                        onChange={(e) => setFromDate(e.target.value)}
                        placeholder="From Date"
                        className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />

                    <input
                        type="date"
                        value={toDate}
                        onChange={(e) => setToDate(e.target.value)}
                        placeholder="To Date"
                        className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative">
                        <i className="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search student or reg no..."
                            className="pl-8 pr-3 py-2 rounded-xl text-xs border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white w-48"
                        />
                    </div>

                    <button
                        onClick={handleExportCsv}
                        className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm flex items-center gap-1.5"
                    >
                        <i className="fa-solid fa-file-csv"></i>
                        <span>Export CSV</span>
                    </button>
                </div>
            </div>

            {/* Reports Table */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center h-48 text-slate-400">
                        <i className="fa-solid fa-spinner fa-spin text-2xl"></i>
                    </div>
                ) : filtered.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                                <tr>
                                    <th className="px-4 py-3">Register Number</th>
                                    <th className="px-4 py-3">Student Name</th>
                                    <th className="px-4 py-3">Department</th>
                                    <th className="px-4 py-3">Subject</th>
                                    <th className="px-4 py-3 text-center">Conducted</th>
                                    <th className="px-4 py-3 text-center">Present</th>
                                    <th className="px-4 py-3 text-center">Absent</th>
                                    <th className="px-4 py-3 text-center">Late</th>
                                    <th className="px-4 py-3">Attendance %</th>
                                    <th className="px-4 py-3 text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {filtered.map((r, idx) => {
                                    const isCritical = r.below_threshold;
                                    return (
                                        <tr key={idx} className={isCritical ? 'bg-rose-50/30 dark:bg-rose-950/20' : 'hover:bg-slate-50/50'}>
                                            <td className="px-4 py-3 font-mono font-bold text-slate-700 dark:text-slate-300">
                                                {r.register_number}
                                            </td>
                                            <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                                                {r.student_name}
                                            </td>
                                            <td className="px-4 py-3 font-medium text-slate-600 dark:text-slate-300">
                                                {r.department_code} (Sem {r.semester})
                                            </td>
                                            <td className="px-4 py-3 font-bold text-indigo-600 dark:text-indigo-400">
                                                {r.subject_code}
                                            </td>
                                            <td className="px-4 py-3 text-center font-semibold text-slate-700 dark:text-slate-200">
                                                {r.total_conducted}
                                            </td>
                                            <td className="px-4 py-3 text-center text-emerald-600 font-bold">
                                                {r.present_count}
                                            </td>
                                            <td className="px-4 py-3 text-center text-rose-600 font-bold">
                                                {r.absent_count}
                                            </td>
                                            <td className="px-4 py-3 text-center text-amber-600 font-bold">
                                                {r.late_count}
                                            </td>
                                            <td className="px-4 py-3 font-bold">
                                                <div className="flex items-center gap-2">
                                                    <span className={isCritical ? 'text-rose-600' : 'text-emerald-600'}>
                                                        {r.attendance_percentage}%
                                                    </span>
                                                    <div className="w-16 bg-slate-100 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
                                                        <div
                                                            className={`h-1.5 rounded-full ${isCritical ? 'bg-rose-500' : 'bg-emerald-500'}`}
                                                            style={{ width: `${Math.min(100, r.attendance_percentage)}%` }}
                                                        ></div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                {isCritical ? (
                                                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                                                        <i className="fa-solid fa-triangle-exclamation text-[10px]"></i> &lt; 75% Alert
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                                                        <i className="fa-solid fa-check text-[10px]"></i> Normal
                                                    </span>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-8 text-center text-slate-500">
                        No attendance records match the selected filter criteria.
                    </div>
                )}
            </div>
        </div>
    );
}

// ==============================================================================
// DFA State Machine & Automaton Simulator Page
// ==============================================================================

function DfaPage() {
    const [selectedNode, setSelectedNode] = useState('S0');

    return (
        <div className="space-y-6">
            {/* Theoretical Finite Automata Introduction Banner */}
            <div className="p-6 rounded-3xl bg-gradient-to-r from-blue-900 via-indigo-900 to-purple-900 text-white shadow-xl">
                <div className="flex items-center gap-2 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
                    <i className="fa-solid fa-shapes"></i> Mathematical Automata Theory
                </div>
                <h2 className="text-2xl md:text-3xl font-extrabold mt-1">
                    Deterministic Finite Automaton (DFA) Architecture
                </h2>
                <p className="text-indigo-200 text-sm mt-2 max-w-4xl leading-relaxed">
                    The attendance lifecycle is formally modeled as a 5-tuple <span className="font-mono font-bold text-white">M = (Q, Σ, δ, q₀, F)</span>.
                    Every attendance mutation is checked against transition table <span className="font-mono font-bold text-white">δ</span> before any database commit, guaranteeing that invalid operations (e.g. altering finalized sessions or finalizing without attendance marks) are rejected at the theoretical gate.
                </p>
            </div>

            {/* Visual DFA Diagram Component */}
            {/* Loaded from components/DfaDiagram.js or rendered with SVG */}
            <DfaVisualDiagram activeState={selectedNode} onSelectState={setSelectedNode} />

            {/* Interactive DFA Simulator Component */}
            <DfaSimulatorWidget onStepChange={setSelectedNode} />
        </div>
    );
}

// Reusable Visual SVG Diagram for DFA
function DfaVisualDiagram({ activeState, onSelectState }) {
    const [selectedState, setSelectedState] = useState(activeState || 'S0');

    const states = [
        { id: 'S0', name: 'Not Marked', x: 120, y: 260, color: '#9ca3af', border: '#4b5563', isInitial: true, isFinal: false },
        { id: 'S1', name: 'Present', x: 420, y: 110, color: '#10b981', border: '#059669', isInitial: false, isFinal: false },
        { id: 'S2', name: 'Absent', x: 420, y: 410, color: '#ef4444', border: '#dc2626', isInitial: false, isFinal: false },
        { id: 'S3', name: 'Late', x: 420, y: 260, color: '#f59e0b', border: '#d97706', isInitial: false, isFinal: false },
        { id: 'S4', name: 'Finalized', x: 780, y: 260, color: '#3b82f6', border: '#2563eb', isInitial: false, isFinal: true }
    ];

    const stateDetails = {
        'S0': {
            title: 'S0: Not Marked (Initial State q₀)',
            desc: 'Initial session state when student attendance has not yet been taken.',
            allowedInputs: ['P → S1 (Mark Present)', 'A → S2 (Mark Absent)', 'L → S3 (Mark Late)'],
            rejectedInputs: ['F (Finalize): REJECTED - Cannot finalize unmarked attendance!'],
            roles: 'Faculty, Administrator'
        },
        'S1': {
            title: 'S1: Present State',
            desc: 'Student is marked Present for this class session.',
            allowedInputs: ['P → S1 (Confirm)', 'A → S2 (Correction to Absent)', 'L → S3 (Correction to Late)', 'F → S4 (Finalize)'],
            rejectedInputs: ['R: Forbidden for faculty (Admin only)'],
            roles: 'Faculty, Administrator'
        },
        'S2': {
            title: 'S2: Absent State',
            desc: 'Student is recorded as Absent for this class session.',
            allowedInputs: ['A → S2 (Confirm)', 'P → S1 (Correction to Present)', 'L → S3 (Correction to Late)', 'F → S4 (Finalize)'],
            rejectedInputs: ['R: Forbidden for faculty (Admin only)'],
            roles: 'Faculty, Administrator'
        },
        'S3': {
            title: 'S3: Late State',
            desc: 'Student arrived late to class but is present with late penalty flag.',
            allowedInputs: ['L → S3 (Confirm)', 'P → S1 (Correction to Present)', 'A → S2 (Correction to Absent)', 'F → S4 (Finalize)'],
            rejectedInputs: ['R: Forbidden for faculty (Admin only)'],
            roles: 'Faculty, Administrator'
        },
        'S4': {
            title: 'S4: Attendance Finalized (Accepting/Terminal State F)',
            desc: 'Session attendance has been approved and permanently locked. Record is immutable.',
            allowedInputs: ['R → S0 (Authorized Admin Reset with audit reason only)'],
            rejectedInputs: ['P: REJECTED (Record locked)', 'A: REJECTED (Record locked)', 'L: REJECTED (Record locked)', 'F: REJECTED (Already finalized)'],
            roles: 'Administrator Only (via Symbol R)'
        }
    };

    const handleNodeClick = (id) => {
        setSelectedState(id);
        if (onSelectState) onSelectState(id);
    };

    const active = activeState || selectedState;
    const currInfo = stateDetails[active] || stateDetails['S0'];

    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-700 gap-4">
                <div>
                    <h3 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <span className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400">
                            <i className="fa-solid fa-diagram-project"></i>
                        </span>
                        DFA State Transition Diagram
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Mathematical 5-tuple: <span className="font-mono text-blue-600 dark:text-blue-400 font-bold">M = (&#123;S0,S1,S2,S3,S4&#125;, &#123;P,A,L,F,R&#125;, δ, S0, &#123;S4&#125;)</span>
                    </p>
                </div>

                <div className="flex items-center gap-2 text-xs font-medium">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-s0">
                        <span className="w-2 h-2 rounded-full bg-slate-400"></span> S0: Not Marked
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-s1">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span> S1: Present
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-s2">
                        <span className="w-2 h-2 rounded-full bg-rose-500"></span> S2: Absent
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-s3">
                        <span className="w-2 h-2 rounded-full bg-amber-500"></span> S3: Late
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-s4">
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span> S4: Finalized (F)
                    </span>
                </div>
            </div>

            {/* SVG Visual Canvas */}
            <div className="relative my-4 bg-slate-50/60 dark:bg-slate-900/60 rounded-xl border border-slate-100 dark:border-slate-800 overflow-x-auto">
                <svg viewBox="0 0 950 520" className="w-full min-w-[750px] h-[380px]">
                    <defs>
                        <marker id="arrow" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                        </marker>
                        <marker id="arrow-green" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                        </marker>
                        <marker id="arrow-red" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
                        </marker>
                        <marker id="arrow-amber" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
                        </marker>
                        <marker id="arrow-blue" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
                        </marker>
                        <marker id="arrow-purple" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6" />
                        </marker>
                    </defs>

                    {/* Start Arrow into S0 */}
                    <line x1="30" y1="260" x2="75" y2="260" stroke="#475569" strokeWidth="2.5" markerEnd="url(#arrow)" />
                    <text x="35" y="248" fill="#64748b" fontSize="11" fontWeight="bold">Start</text>

                    {/* S0 -> S1 (P) */}
                    <path d="M 155 240 Q 250 140 375 125" fill="none" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrow-green)" />
                    <text x="250" y="170" fill="#059669" fontSize="12" fontWeight="bold">P (Present)</text>

                    {/* S0 -> S3 (L) */}
                    <path d="M 165 260 L 375 260" fill="none" stroke="#f59e0b" strokeWidth="2" markerEnd="url(#arrow-amber)" />
                    <text x="255" y="252" fill="#d97706" fontSize="12" fontWeight="bold">L (Late)</text>

                    {/* S0 -> S2 (A) */}
                    <path d="M 155 280 Q 250 380 375 395" fill="none" stroke="#ef4444" strokeWidth="2" markerEnd="url(#arrow-red)" />
                    <text x="250" y="355" fill="#dc2626" fontSize="12" fontWeight="bold">A (Absent)</text>

                    {/* S1, S3, S2 -> S4 (Finalize F) */}
                    <path d="M 465 125 Q 600 140 735 240" fill="none" stroke="#3b82f6" strokeWidth="2.5" markerEnd="url(#arrow-blue)" />
                    <text x="590" y="170" fill="#2563eb" fontSize="12" fontWeight="bold">F (Finalize)</text>

                    <path d="M 465 260 L 735 260" fill="none" stroke="#3b82f6" strokeWidth="2.5" markerEnd="url(#arrow-blue)" />
                    <text x="580" y="252" fill="#2563eb" fontSize="12" fontWeight="bold">F (Finalize)</text>

                    <path d="M 465 395 Q 600 380 735 280" fill="none" stroke="#3b82f6" strokeWidth="2.5" markerEnd="url(#arrow-blue)" />
                    <text x="590" y="355" fill="#2563eb" fontSize="12" fontWeight="bold">F (Finalize)</text>

                    {/* Authorized Admin Reset: S4 -> S0 */}
                    <path d="M 760 305 C 720 480 200 480 140 305" fill="none" stroke="#8b5cf6" strokeWidth="2.5" strokeDasharray="6,4" markerEnd="url(#arrow-purple)" />
                    <text x="450" y="465" fill="#7c3aed" fontSize="12" fontWeight="bold" textAnchor="middle">
                        δ(S4, R) → S0 [Authorized Admin Reset with Audit Record]
                    </text>

                    {/* Nodes */}
                    {states.map(s => {
                        const isCurrent = (active === s.id);
                        return (
                            <g
                                key={s.id}
                                className={`dfa-node ${isCurrent ? 'active-state' : ''}`}
                                onClick={() => handleNodeClick(s.id)}
                            >
                                {s.isFinal && (
                                    <circle cx={s.x} cy={s.y} r="50" fill="none" stroke={s.border} strokeWidth="2.5" />
                                )}
                                <circle
                                    cx={s.x}
                                    cy={s.y}
                                    r="42"
                                    fill={isCurrent ? s.color : '#ffffff'}
                                    stroke={s.border}
                                    strokeWidth={isCurrent ? '4' : '2'}
                                />
                                <text
                                    x={s.x}
                                    y={s.y - 4}
                                    fill={isCurrent ? '#ffffff' : '#1e293b'}
                                    fontSize="16"
                                    fontWeight="bold"
                                    textAnchor="middle"
                                    dominantBaseline="middle"
                                >
                                    {s.id}
                                </text>
                                <text
                                    x={s.x}
                                    y={s.y + 15}
                                    fill={isCurrent ? '#f8fafc' : '#64748b'}
                                    fontSize="10"
                                    fontWeight="600"
                                    textAnchor="middle"
                                    dominantBaseline="middle"
                                >
                                    {s.name}
                                </text>
                            </g>
                        );
                    })}
                </svg>
            </div>

            {/* State Inspector Details */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">State Inspector</span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                        Selected: {currInfo.title}
                    </span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-300">{currInfo.desc}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 text-xs">
                    <div className="p-3 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40">
                        <span className="font-bold text-emerald-800 dark:text-emerald-300 block mb-1">
                            ✓ Permitted δ Transitions:
                        </span>
                        <ul className="space-y-0.5 text-emerald-700 dark:text-emerald-400 font-medium">
                            {currInfo.allowedInputs.map((inp, idx) => <li key={idx}>• {inp}</li>)}
                        </ul>
                    </div>
                    <div className="p-3 rounded-lg bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/40">
                        <span className="font-bold text-rose-800 dark:text-rose-300 block mb-1">
                            ✗ Prohibited / Rejected Transitions:
                        </span>
                        <ul className="space-y-0.5 text-rose-700 dark:text-rose-400 font-medium">
                            {currInfo.rejectedInputs.map((inp, idx) => <li key={idx}>• {inp}</li>)}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Reusable DFA Simulator Widget
function DfaSimulatorWidget({ onStepChange }) {
    const [initialState, setInitialState] = useState('S0');
    const [sequence, setSequence] = useState(['P', 'F']);
    const [role, setRole] = useState('faculty');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const runSimulation = async (seq = sequence, init = initialState, r = role) => {
        setLoading(true);
        try {
            const data = await apiCall('/dfa/simulate', {
                method: 'POST',
                body: JSON.stringify({ initial_state: init, sequence: seq, role: r })
            });
            if (data.success) {
                setResult(data.simulation);
                if (onStepChange && data.simulation.final_state) {
                    onStepChange(data.simulation.final_state);
                }
            }
        } catch (err) {
            console.error('Simulation error', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        runSimulation();
    }, []);

    const addSymbol = (sym) => {
        const next = [...sequence, sym];
        setSequence(next);
        runSimulation(next, initialState, role);
    };

    const clearSequence = () => {
        setSequence([]);
        runSimulation([], initialState, role);
    };

    const loadPreset = (presetSeq, presetRole = 'faculty') => {
        setSequence(presetSeq);
        setRole(presetRole);
        runSimulation(presetSeq, initialState, presetRole);
    };

    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-700 gap-4">
                <div>
                    <h3 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <span className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400">
                            <i className="fa-solid fa-flask-vial"></i>
                        </span>
                        Interactive Automaton Trace Runner
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Input string sequence runner to test valid and rejected transitions in real time.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">Simulate Role:</label>
                    <select
                        value={role}
                        onChange={(e) => {
                            setRole(e.target.value);
                            runSimulation(sequence, initialState, e.target.value);
                        }}
                        className="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200"
                    >
                        <option value="faculty">Faculty User</option>
                        <option value="admin">Administrator User</option>
                        <option value="student">Student User</option>
                    </select>
                </div>
            </div>

            {/* Quick Test Presets */}
            <div className="mt-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-2">
                    Test Scenarios & Presets:
                </span>
                <div className="flex flex-wrap gap-2 text-xs">
                    <button
                        onClick={() => loadPreset(['P', 'F'], 'faculty')}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 font-medium text-slate-700 dark:text-slate-300"
                    >
                        ✓ Normal Flow: P → F
                    </button>
                    <button
                        onClick={() => loadPreset(['A', 'L', 'P', 'F'], 'faculty')}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 font-medium text-slate-700 dark:text-slate-300"
                    >
                        ✓ Corrections: A → L → P → F
                    </button>
                    <button
                        onClick={() => loadPreset(['F'], 'faculty')}
                        className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 font-medium border border-rose-200 dark:border-rose-900"
                    >
                        ✗ Invalid: S0 → F (Premature Finalize)
                    </button>
                    <button
                        onClick={() => loadPreset(['P', 'F', 'A'], 'faculty')}
                        className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 font-medium border border-rose-200 dark:border-rose-900"
                    >
                        ✗ Invalid: P → F → A (Edit Finalized S4)
                    </button>
                    <button
                        onClick={() => loadPreset(['P', 'F', 'R', 'P'], 'admin')}
                        className="px-3 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-400 font-medium border border-purple-200 dark:border-purple-900"
                    >
                        ✓ Admin Override: P → F → R → P
                    </button>
                </div>
            </div>

            {/* Sequence Builder & Alphabet Buttons */}
            <div className="mt-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-600 dark:text-slate-300">Input String Σ*:</span>
                        <div className="flex items-center gap-1.5 flex-wrap min-h-[32px] p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-slate-300 dark:border-slate-700 font-mono text-sm">
                            {sequence.length === 0 ? (
                                <span className="text-slate-400 text-xs italic px-2">λ (Empty sequence)</span>
                            ) : (
                                sequence.map((sym, idx) => (
                                    <span
                                        key={idx}
                                        className={`px-2 py-0.5 rounded font-bold text-xs ${
                                            sym === 'P' ? 'badge-s1' :
                                            sym === 'A' ? 'badge-s2' :
                                            sym === 'L' ? 'badge-s3' :
                                            sym === 'F' ? 'badge-s4' : 'bg-purple-100 text-purple-800 dark:bg-purple-900/60 dark:text-purple-300'
                                        }`}
                                    >
                                        {sym}
                                    </span>
                                ))
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={clearSequence}
                            className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
                        >
                            <i className="fa-solid fa-trash-can mr-1"></i> Clear
                        </button>
                        <button
                            onClick={() => runSimulation()}
                            disabled={loading}
                            className="text-xs px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold shadow-sm"
                        >
                            {loading ? <i className="fa-solid fa-spinner fa-spin mr-1"></i> : <i className="fa-solid fa-play mr-1"></i>} Run DFA
                        </button>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                    <span className="text-xs font-semibold text-slate-500">Append Alphabet Symbol:</span>
                    <button onClick={() => addSymbol('P')} className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold">+ P (Present)</button>
                    <button onClick={() => addSymbol('A')} className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold">+ A (Absent)</button>
                    <button onClick={() => addSymbol('L')} className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold">+ L (Late)</button>
                    <button onClick={() => addSymbol('F')} className="px-3 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold">+ F (Finalize)</button>
                    <button onClick={() => addSymbol('R')} className="px-3 py-1 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold">+ R (Admin Reset)</button>
                </div>
            </div>

            {/* Trace Table */}
            {result && (
                <div className="mt-5 space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <div className="flex items-center gap-2 text-xs">
                            <span className="font-bold text-slate-600 dark:text-slate-300">DFA Status:</span>
                            {result.is_accepted ? (
                                <span className="px-3 py-1 rounded-full font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 flex items-center gap-1">
                                    <i className="fa-solid fa-circle-check"></i> STRING ACCEPTED
                                </span>
                            ) : (
                                <span className="px-3 py-1 rounded-full font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300 flex items-center gap-1">
                                    <i className="fa-solid fa-circle-xmark"></i> STRING REJECTED
                                </span>
                            )}
                        </div>
                        <div className="text-xs font-mono text-slate-500">
                            Final State: <strong className="text-slate-900 dark:text-white">{result.final_state}</strong>
                        </div>
                    </div>

                    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-700">
                                <tr>
                                    <th className="px-3 py-2">Step</th>
                                    <th className="px-3 py-2">Input</th>
                                    <th className="px-3 py-2">State</th>
                                    <th className="px-3 py-2">Status</th>
                                    <th className="px-3 py-2">Mathematical Explanation</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {result.trace.map((step, idx) => (
                                    <tr key={idx} className={step.valid ? 'bg-white dark:bg-slate-800' : 'bg-rose-50/50 dark:bg-rose-950/20'}>
                                        <td className="px-3 py-2 font-mono text-slate-500">#{step.step}</td>
                                        <td className="px-3 py-2 font-mono font-bold">{step.input || '—'}</td>
                                        <td className="px-3 py-2 font-mono font-bold">{step.state}</td>
                                        <td className="px-3 py-2 font-bold">{step.valid ? '✓ Valid' : '✗ Rejected'}</td>
                                        <td className="px-3 py-2 text-slate-600 dark:text-slate-300">{step.message}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

// ==============================================================================
// Admin Management Pages: Departments, Faculty, Students, Subjects, Audit Logs, Profile
// ==============================================================================

function DepartmentManagementPage() {
    const { showToast, openConfirmModal } = useContext(ToastContext);
    const [departments, setDepartments] = useState([]);
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [loading, setLoading] = useState(false);

    const loadDepts = () => {
        apiCall('/admin/departments').then(res => {
            if (res.success) setDepartments(res.departments);
        });
    };

    useEffect(() => { loadDepts(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!name || !code) return;
        setLoading(true);
        try {
            const res = await apiCall('/admin/departments', {
                method: 'POST',
                body: JSON.stringify({ department_name: name, department_code: code })
            });
            if (res.success) {
                showToast(res.message, 'success');
                setName('');
                setCode('');
                loadDepts();
            }
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = (id, deptName) => {
        openConfirmModal({
            title: `Delete Department: ${deptName}?`,
            message: "Deleting this department will delete all affiliated students, faculty assignments, and records. Proceed?",
            confirmText: "Delete Department",
            isDanger: true,
            onConfirm: async () => {
                try {
                    const res = await apiCall(`/admin/departments/${id}`, { method: 'DELETE' });
                    if (res.success) {
                        showToast(res.message, 'success');
                        loadDepts();
                    }
                } catch (err) {
                    showToast(err.message, 'error');
                }
            }
        });
    };

    return (
        <div className="space-y-6 max-w-5xl">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-building-columns text-indigo-600"></i>
                Department Management
            </h2>

            {/* Create Dept Form */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                <h4 className="text-sm font-bold text-slate-800 dark:text-white mb-3">Add New Department</h4>
                <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                        type="text"
                        placeholder="Department Name (e.g. Mechanical Engineering)"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                    <input
                        type="text"
                        placeholder="Department Code (e.g. MECH)"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white font-mono uppercase"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm"
                    >
                        {loading ? 'Creating...' : '+ Create Department'}
                    </button>
                </form>
            </div>

            {/* Departments List */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                        <tr>
                            <th className="px-4 py-3">Code</th>
                            <th className="px-4 py-3">Department Name</th>
                            <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {departments.map(d => (
                            <tr key={d.id} className="hover:bg-slate-50/50">
                                <td className="px-4 py-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                                    {d.department_code}
                                </td>
                                <td className="px-4 py-3 font-semibold text-slate-800 dark:text-white">
                                    {d.department_name}
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => handleDelete(d.id, d.department_name)}
                                        className="text-rose-600 hover:text-rose-800 p-1.5 rounded-lg hover:bg-rose-50"
                                    >
                                        <i className="fa-solid fa-trash-can"></i>
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function FacultyManagementPage() {
    const { showToast, openConfirmModal } = useContext(ToastContext);
    const [faculty, setFaculty] = useState([]);
    const [depts, setDepts] = useState([]);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [deptId, setDeptId] = useState('');
    const [designation, setDesignation] = useState('Assistant Professor');

    const loadData = () => {
        apiCall('/admin/faculty').then(res => { if (res.success) setFaculty(res.faculty); });
        apiCall('/admin/departments').then(res => {
            if (res.success) {
                setDepts(res.departments);
                if (res.departments.length && !deptId) setDeptId(res.departments[0].id);
            }
        });
    };

    useEffect(() => { loadData(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await apiCall('/admin/faculty', {
                method: 'POST',
                body: JSON.stringify({ name, email, department_id: deptId, designation })
            });
            if (res.success) {
                showToast(res.message, 'success');
                setName('');
                setEmail('');
                loadData();
            }
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    const handleDelete = (id, facultyName) => {
        openConfirmModal({
            title: `Remove Faculty: ${facultyName}?`,
            message: "Are you sure you wish to delete this faculty account?",
            confirmText: "Delete Faculty",
            isDanger: true,
            onConfirm: async () => {
                const res = await apiCall(`/admin/faculty/${id}`, { method: 'DELETE' });
                if (res.success) {
                    showToast(res.message, 'success');
                    loadData();
                }
            }
        });
    };

    return (
        <div className="space-y-6 max-w-5xl">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-chalkboard-user text-indigo-600"></i>
                Faculty Directory & Assignments
            </h2>

            {/* Add Faculty Form */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                <h4 className="text-sm font-bold text-slate-800 dark:text-white mb-3">Register New Faculty Member</h4>
                <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <input
                        type="text"
                        placeholder="Faculty Name (e.g. Dr. John Doe)"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                    <input
                        type="email"
                        placeholder="Email Address"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                    <select
                        value={deptId}
                        onChange={(e) => setDeptId(e.target.value)}
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        {depts.map(d => <option key={d.id} value={d.id}>{d.department_code} - {d.department_name}</option>)}
                    </select>
                    <button
                        type="submit"
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm"
                    >
                        + Add Faculty
                    </button>
                </form>
            </div>

            {/* Faculty List Table */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                        <tr>
                            <th className="px-4 py-3">Faculty Name</th>
                            <th className="px-4 py-3">Email</th>
                            <th className="px-4 py-3">Department</th>
                            <th className="px-4 py-3">Designation</th>
                            <th className="px-4 py-3">Assigned Classes</th>
                            <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {faculty.map(f => (
                            <tr key={f.id} className="hover:bg-slate-50/50">
                                <td className="px-4 py-3 font-bold text-slate-800 dark:text-white">{f.name}</td>
                                <td className="px-4 py-3 font-mono text-slate-500">{f.email}</td>
                                <td className="px-4 py-3 font-semibold text-indigo-600">{f.department_code}</td>
                                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{f.designation}</td>
                                <td className="px-4 py-3 font-semibold">{f.subjects_count} subjects</td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => handleDelete(f.id, f.name)}
                                        className="text-rose-600 hover:text-rose-800 p-1.5 rounded-lg hover:bg-rose-50"
                                    >
                                        <i className="fa-solid fa-trash-can"></i>
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function StudentManagementPage() {
    const { showToast, openConfirmModal } = useContext(ToastContext);
    const [students, setStudents] = useState([]);
    const [depts, setDepts] = useState([]);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [regNo, setRegNo] = useState('');
    const [deptId, setDeptId] = useState('');
    const [semester, setSemester] = useState(5);

    const loadData = () => {
        apiCall('/admin/students').then(res => { if (res.success) setStudents(res.students); });
        apiCall('/admin/departments').then(res => {
            if (res.success) {
                setDepts(res.departments);
                if (res.departments.length && !deptId) setDeptId(res.departments[0].id);
            }
        });
    };

    useEffect(() => { loadData(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await apiCall('/admin/students', {
                method: 'POST',
                body: JSON.stringify({ name, email, register_number: regNo, department_id: deptId, semester })
            });
            if (res.success) {
                showToast(res.message, 'success');
                setName('');
                setEmail('');
                setRegNo('');
                loadData();
            }
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    const handleDelete = (id, studentName) => {
        openConfirmModal({
            title: `Delete Student: ${studentName}?`,
            message: "Deleting this student will remove all their enrollments and attendance logs. Proceed?",
            confirmText: "Delete Student",
            isDanger: true,
            onConfirm: async () => {
                const res = await apiCall(`/admin/students/${id}`, { method: 'DELETE' });
                if (res.success) {
                    showToast(res.message, 'success');
                    loadData();
                }
            }
        });
    };

    return (
        <div className="space-y-6 max-w-5xl">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-user-graduate text-indigo-600"></i>
                Student Directory & Enrolment
            </h2>

            {/* Register Student Form */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                <h4 className="text-sm font-bold text-slate-800 dark:text-white mb-3">Enroll New Student</h4>
                <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                    <input
                        type="text"
                        placeholder="Full Name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                    <input
                        type="email"
                        placeholder="Email Address"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                    <input
                        type="text"
                        placeholder="Register No (e.g. 2024CSE011)"
                        value={regNo}
                        onChange={(e) => setRegNo(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white font-mono uppercase"
                    />
                    <select
                        value={deptId}
                        onChange={(e) => setDeptId(e.target.value)}
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        {depts.map(d => <option key={d.id} value={d.id}>{d.department_code}</option>)}
                    </select>
                    <button
                        type="submit"
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm"
                    >
                        + Enroll Student
                    </button>
                </form>
            </div>

            {/* Students Table */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                        <tr>
                            <th className="px-4 py-3">Reg No</th>
                            <th className="px-4 py-3">Student Name</th>
                            <th className="px-4 py-3">Email</th>
                            <th className="px-4 py-3">Department</th>
                            <th className="px-4 py-3">Semester</th>
                            <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {students.map(s => (
                            <tr key={s.id} className="hover:bg-slate-50/50">
                                <td className="px-4 py-3 font-mono font-bold text-slate-800 dark:text-slate-200">{s.register_number}</td>
                                <td className="px-4 py-3 font-bold text-slate-800 dark:text-white">{s.name}</td>
                                <td className="px-4 py-3 text-slate-500">{s.email}</td>
                                <td className="px-4 py-3 font-semibold text-indigo-600">{s.department_code}</td>
                                <td className="px-4 py-3 font-medium">Sem {s.semester}</td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => handleDelete(s.id, s.name)}
                                        className="text-rose-600 hover:text-rose-800 p-1.5 rounded-lg hover:bg-rose-50"
                                    >
                                        <i className="fa-solid fa-trash-can"></i>
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function SubjectManagementPage() {
    const { showToast, openConfirmModal } = useContext(ToastContext);
    const [subjects, setSubjects] = useState([]);
    const [depts, setDepts] = useState([]);
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [deptId, setDeptId] = useState('');
    const [semester, setSemester] = useState(5);
    const [credits, setCredits] = useState(3);

    const loadData = () => {
        apiCall('/admin/subjects').then(res => { if (res.success) setSubjects(res.subjects); });
        apiCall('/admin/departments').then(res => {
            if (res.success) {
                setDepts(res.departments);
                if (res.departments.length && !deptId) setDeptId(res.departments[0].id);
            }
        });
    };

    useEffect(() => { loadData(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await apiCall('/admin/subjects', {
                method: 'POST',
                body: JSON.stringify({ subject_name: name, subject_code: code, department_id: deptId, semester, credits })
            });
            if (res.success) {
                showToast(res.message, 'success');
                setName('');
                setCode('');
                loadData();
            }
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    const handleDelete = (id, subjectName) => {
        openConfirmModal({
            title: `Delete Subject: ${subjectName}?`,
            message: "Deleting this subject will remove all corresponding attendance logs. Proceed?",
            confirmText: "Delete Subject",
            isDanger: true,
            onConfirm: async () => {
                const res = await apiCall(`/admin/subjects/${id}`, { method: 'DELETE' });
                if (res.success) {
                    showToast(res.message, 'success');
                    loadData();
                }
            }
        });
    };

    return (
        <div className="space-y-6 max-w-5xl">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-book-bookmark text-indigo-600"></i>
                Subjects & Curriculum
            </h2>

            {/* Create Subject Form */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                <h4 className="text-sm font-bold text-slate-800 dark:text-white mb-3">Add Subject to Curriculum</h4>
                <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                    <input
                        type="text"
                        placeholder="Subject Name (e.g. Compiler Design)"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    />
                    <input
                        type="text"
                        placeholder="Subject Code (e.g. CS401)"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        required
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white font-mono uppercase"
                    />
                    <select
                        value={deptId}
                        onChange={(e) => setDeptId(e.target.value)}
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        {depts.map(d => <option key={d.id} value={d.id}>{d.department_code}</option>)}
                    </select>
                    <select
                        value={credits}
                        onChange={(e) => setCredits(Number(e.target.value))}
                        className="px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-800 dark:text-white"
                    >
                        {[1, 2, 3, 4, 5].map(c => <option key={c} value={c}>{c} Credits</option>)}
                    </select>
                    <button
                        type="submit"
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm"
                    >
                        + Create Subject
                    </button>
                </form>
            </div>

            {/* Subjects Table */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                        <tr>
                            <th className="px-4 py-3">Code</th>
                            <th className="px-4 py-3">Subject Name</th>
                            <th className="px-4 py-3">Department</th>
                            <th className="px-4 py-3">Semester</th>
                            <th className="px-4 py-3">Credits</th>
                            <th className="px-4 py-3">Assigned Faculty</th>
                            <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {subjects.map(s => (
                            <tr key={s.id} className="hover:bg-slate-50/50">
                                <td className="px-4 py-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">{s.subject_code}</td>
                                <td className="px-4 py-3 font-bold text-slate-800 dark:text-white">{s.subject_name}</td>
                                <td className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">{s.department_code}</td>
                                <td className="px-4 py-3 font-medium">Sem {s.semester}</td>
                                <td className="px-4 py-3 font-medium">{s.credits} Credits</td>
                                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{s.assigned_faculty_name || 'Unassigned'}</td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => handleDelete(s.id, s.subject_name)}
                                        className="text-rose-600 hover:text-rose-800 p-1.5 rounded-lg hover:bg-rose-50"
                                    >
                                        <i className="fa-solid fa-trash-can"></i>
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function AuditLogsPage({ user }) {
    const { showToast, openPromptModal } = useContext(ToastContext);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadLogs = () => {
        setLoading(true);
        apiCall('/admin/audit-logs?limit=150')
            .then(res => { if (res.success) setLogs(res.logs); })
            .catch(err => showToast(err.message, 'error'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadLogs(); }, []);

    // Authorized Admin Reset directly from audit log row if next_state == S4
    const handleReset = (attendanceId) => {
        openPromptModal({
            title: "Authorized Admin DFA Reset: δ(S4, R) → S0",
            message: "Execute state reset on this finalized record. Please enter the reason for this administrative override.",
            placeholder: "e.g., Authorized attendance recalculation per committee resolution.",
            onConfirm: async (reason) => {
                try {
                    const res = await apiCall('/attendance/reset', {
                        method: 'POST',
                        body: JSON.stringify({ attendance_id: attendanceId, reason })
                    });
                    if (res.success) {
                        showToast(res.message, 'success');
                        loadLogs();
                    }
                } catch (err) {
                    showToast(err.message, 'error');
                }
            }
        });
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <i className="fa-solid fa-shield-halved text-purple-600"></i>
                        Finite Automata Audit & Compliance Trail
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Cryptographically traceable ledger of every mathematical state transition δ in the college database.
                    </p>
                </div>
                <button
                    onClick={loadLogs}
                    className="px-3.5 py-2 rounded-xl border border-slate-300 dark:border-slate-600 text-xs font-semibold hover:bg-slate-100 self-start md:self-auto"
                >
                    <i className="fa-solid fa-arrows-rotate mr-1"></i> Refresh Ledger
                </button>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center h-48 text-slate-400">
                        <i className="fa-solid fa-spinner fa-spin text-2xl"></i>
                    </div>
                ) : logs.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200 dark:border-slate-700">
                                <tr>
                                    <th className="px-4 py-3">Log ID</th>
                                    <th className="px-4 py-3">Timestamp</th>
                                    <th className="px-4 py-3">Student & Reg No</th>
                                    <th className="px-4 py-3">Subject</th>
                                    <th className="px-4 py-3">Date</th>
                                    <th className="px-4 py-3">DFA Transition δ</th>
                                    <th className="px-4 py-3">Symbol</th>
                                    <th className="px-4 py-3">Reason / Audit Trail</th>
                                    <th className="px-4 py-3">Actor</th>
                                    {user.role === 'admin' && <th className="px-4 py-3 text-right">Admin Action</th>}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {logs.map(log => (
                                    <tr key={log.id} className="hover:bg-slate-50/50">
                                        <td className="px-4 py-3 font-mono text-slate-400">#{log.id}</td>
                                        <td className="px-4 py-3 font-mono text-slate-500 whitespace-nowrap">{log.timestamp}</td>
                                        <td className="px-4 py-3 font-semibold text-slate-800 dark:text-white">
                                            {log.student_name} <span className="font-normal text-slate-400">({log.register_number})</span>
                                        </td>
                                        <td className="px-4 py-3 font-bold text-indigo-600">{log.subject_code}</td>
                                        <td className="px-4 py-3 font-mono text-slate-600 dark:text-slate-300">{log.attendance_date}</td>
                                        <td className="px-4 py-3 font-mono font-bold whitespace-nowrap">
                                            <span className="text-slate-500">{log.previous_state}</span>
                                            <span className="text-slate-400 mx-1">→</span>
                                            <span className={`px-2 py-0.5 rounded ${
                                                log.next_state === 'S1' ? 'badge-s1' :
                                                log.next_state === 'S2' ? 'badge-s2' :
                                                log.next_state === 'S3' ? 'badge-s3' :
                                                log.next_state === 'S4' ? 'badge-s4' : 'badge-s0'
                                            }`}>
                                                {log.next_state}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 font-mono font-bold">
                                            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700">{log.input_symbol}</span>
                                        </td>
                                        <td className="px-4 py-3 text-slate-600 dark:text-slate-300 max-w-xs truncate" title={log.reason}>
                                            {log.reason || 'Transition recorded'}
                                        </td>
                                        <td className="px-4 py-3 text-slate-500">{log.changed_by_name || 'System'}</td>
                                        {user.role === 'admin' && (
                                            <td className="px-4 py-3 text-right">
                                                {log.next_state === 'S4' ? (
                                                    <button
                                                        onClick={() => handleReset(log.attendance_id)}
                                                        className="px-2.5 py-1 rounded bg-purple-100 text-purple-700 hover:bg-purple-200 dark:bg-purple-900/40 dark:text-purple-300 text-[11px] font-bold"
                                                    >
                                                        Reset δ(S4,R)
                                                    </button>
                                                ) : (
                                                    <span className="text-slate-400 text-[11px]">—</span>
                                                )}
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-8 text-center text-slate-500">No audit records found.</div>
                )}
            </div>
        </div>
    );
}

function ProfilePage({ user }) {
    return (
        <div className="max-w-3xl space-y-6">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <i className="fa-solid fa-id-badge text-indigo-600"></i>
                Account Profile & Security Settings
            </h2>

            <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-6">
                <div className="flex items-center gap-4 pb-6 border-b border-slate-100 dark:border-slate-700">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center text-2xl font-bold">
                        {user.name.charAt(0)}
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">{user.name}</h3>
                        <p className="text-xs text-slate-500 font-mono mt-0.5">{user.email}</p>
                        <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                            Role: {user.role}
                        </span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/50">
                        <span className="text-slate-400 font-medium block">Department Affiliation</span>
                        <span className="text-slate-800 dark:text-white font-bold text-sm mt-1 block">
                            {user.department_name ? `${user.department_code} - ${user.department_name}` : 'Institutional Administration'}
                        </span>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-700/50">
                        <span className="text-slate-400 font-medium block">User ID / Identifier</span>
                        <span className="text-slate-800 dark:text-white font-mono font-bold text-sm mt-1 block">
                            {user.register_number ? `Register No: ${user.register_number}` : `User ID #${user.id}`}
                        </span>
                    </div>
                </div>

                <div className="pt-4 border-t border-slate-100 dark:border-slate-700">
                    <h4 className="text-sm font-bold text-slate-800 dark:text-white mb-2">
                        Finite Automata Security & Role Authorization
                    </h4>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                        Your account is bound to role <strong>{user.role}</strong>. The backend DFA validator prevents execution of operations outside your mathematical authorization set. All state transitions initiated by your account are cryptographically recorded in the attendance audit log.
                    </p>
                </div>
            </div>
        </div>
    );
}

// Mount React Root
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
