import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ user, allowedRoles, children }) => {
  if (!user) return <Navigate to="/" replace />;

  return allowedRoles.includes(user.role)
    ? children
    : <Navigate to="/unauthorized" replace />;
};

export default ProtectedRoute;