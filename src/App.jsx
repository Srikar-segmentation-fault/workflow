import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import ManagerDashboard from './pages/ManagerDashboard';
import EmployeeDashboard from './pages/EmployeeDashboard';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Manager-only */}
          <Route
            path="/manager"
            element={
              <ProtectedRoute allowedRole="manager">
                <ManagerDashboard />
              </ProtectedRoute>
            }
          />

          {/* Employee-only */}
          <Route
            path="/employee"
            element={
              <ProtectedRoute allowedRole="employee">
                <EmployeeDashboard />
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
