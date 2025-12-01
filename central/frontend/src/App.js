import './App.css';
import Home from './pages/home';
import { ToastContainer } from 'react-toastify';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useNavigate,
} from 'react-router-dom';
import LoginPage from './pages/login';
import AdminDashboard from './pages/Admin/admin-dashboard';
import ProtectedRoute from './pages/Auth/ProtectedRoute';
import Unauthorized from './pages/Auth/Unauthorized';
import GrafanaDashboard from './pages/Admin/GrafanaDashboard/GrafanaDashboard';
import AdminHeader from './components/header/adminheader';
import { useEffect } from 'react';

const NotFound = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-5xl font-bold text-red-600 mb-4">404</h1>
      <p className="text-lg text-gray-700 mb-6">Page Not Found</p>
      <button
        onClick={() => navigate('/')}
        className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
      >
        Go to Login
      </button>
    </div>
  );
};

function App() {
  const storedUser = localStorage.getItem('user');
  const user = storedUser ? JSON.parse(storedUser) : null;

  const checkCommandService = async () => {
    try {
      fetch('/command/health');
    } catch (error) {
      console.error('Command Service is not reachable:', error);
    }
  };

  const checkBookingService = async () => {
    try {
      await fetch('/booking-api/health');
    } catch (error) {
      console.error('Booking Service is not reachable:', error);
    }
  };

  useEffect(() => {
    const runChecks = async () => {
      await checkCommandService();
      await checkBookingService();
    };
    runChecks();
  }, []);

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Landing route */}
          <Route
            path="/home"
            element = {<Home/>
            }
          />

          <Route path="/" element={<LoginPage />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Admin protected parent */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute user={user} allowedRoles={['admin']}>
                <AdminHeader />
                <Outlet />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="grafana" element={<GrafanaDashboard />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
        <ToastContainer />
      </BrowserRouter>
    </div>
  );
}

export default App;
