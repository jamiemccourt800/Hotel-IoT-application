import Logo from './logo';
import { Link, useNavigate } from 'react-router-dom';

const AdminHeader = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };

  return (
    <div className="header flex justify-between items-center shadow-md p-4 px-6 bg-gray-800 text-white">
      <Logo user="Admin" />
      <div className="flex items-center gap-6">
        <Link to="/admin/dashboard" className="hover:underline">
          Dashboard
        </Link>
        <button onClick={handleLogout} className="hover:underline">
          Logout
        </button>
      </div>
    </div>
  );
};

export default AdminHeader;
