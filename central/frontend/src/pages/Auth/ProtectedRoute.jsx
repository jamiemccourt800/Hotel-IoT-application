import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ allowedRoles, children }) => {
  const storedUser = localStorage.getItem("user");
  const user = storedUser ? JSON.parse(storedUser) : null;

  if (!user) return <Navigate to="/" replace />;

  return allowedRoles.includes(user.role) ? children : <Navigate to="/unauthorized" replace />;
};

export default ProtectedRoute;
