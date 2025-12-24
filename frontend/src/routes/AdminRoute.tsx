import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../api/useAuth";
import { useEffect } from "react";

export default function AdminRoute() {
  const { user, fetchCurrentUser, isLoading } = useAuth();

  useEffect(() => {
    if (!user && !isLoading) {
      fetchCurrentUser();
    }
  }, [user, isLoading, fetchCurrentUser]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-slate-600">로딩 중...</div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (user.role?.toLowerCase() !== "admin") return <Navigate to="/" replace />;

  return <Outlet />;
}
