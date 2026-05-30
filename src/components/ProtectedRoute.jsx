import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, allowedRole }) {
  const { token, role } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && role !== allowedRole) {
    // Redirect to the correct dashboard based on actual role
    return <Navigate to={role === 'manager' ? '/manager' : '/employee'} replace />;
  }

  return children;
}
