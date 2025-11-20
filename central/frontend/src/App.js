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

function App() {
  const user = { name: "Ibukun", role: "admin" };

  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path='/' element={<GrafanaDashboard/>}/>
          <Route path="/home" element={<Home />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path='/unauthorized' element={<Unauthorized/>}/>
          {/* Admin protected parent */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute user={user} allowedRoles={["admin"]}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="grafana" element={<GrafanaDashboard />} />
          </Route>
        </Routes>
      </div>
      <ToastContainer />
    </BrowserRouter>
  );
}


const AdminLayout = () => {
  return (
    <div>
      <AdminHeader/>
      <Outlet />
    </div>
  );
};

export default App;
