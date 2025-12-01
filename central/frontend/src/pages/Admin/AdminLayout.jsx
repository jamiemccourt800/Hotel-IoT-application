import { Outlet } from "react-router-dom";
import AdminHeader from "../../components/header/adminheader";

const AdminLayout = () => {
  return (
    <div>
      <AdminHeader />
      <div className="admin-content p-6">
        <Outlet />
      </div>
    </div>
  );
};

export default AdminLayout;
