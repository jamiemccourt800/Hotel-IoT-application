import './App.css';
import Home from './pages/home';
import { ToastContainer } from 'react-toastify';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './pages/login';
import AdminDashboard from './pages/Admin/admin-dashboard';
import ProtectedRoute from './pages/Auth/ProtectedRoute';
import Unauthorized from './pages/Auth/Unauthorized';
import GrafanaDashboard from './pages/Admin/GrafanaDashboard/GrafanaDashboard';
import AdminHeader from './components/header/adminheader';
import { useEffect } from 'react';
import { axiosInstance, bookingApiAxiosInstance } from './utils/axiosInstance';

// simple placeholder for unmatched routes
const NotFound = () => <h2>404 - Page Not Found</h2>;

function App() {
   const storedUser = localStorage.getItem("user");
  const user = storedUser ? JSON.parse(storedUser) : null;

  const checkCommandService = async () => {
    try {
      await axiosInstance.get('/health');
    } catch (error) {
      console.error('Command Service is not reachable:', error);
    }
  };

  const checkBookingService = async () => {
    try {
      await bookingApiAxiosInstance.get('/health');
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
          <Route path="/home" element={<Home />} />

          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Admin protected parent */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute user={user} allowedRoles={["admin"]}>
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
        {/* <ToastContainer /> */}
      </BrowserRouter>
    </div>
  );
}

export default App;
