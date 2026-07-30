import React from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth.store";
import { UserRole } from "@/types";

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
}

export function RoleGuard({ children, allowedRoles }: RoleGuardProps) {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <h2 className="text-2xl font-bold text-destructive">Unauthorized Access</h2>
        <p className="text-muted-foreground text-sm text-center max-w-md">
          Your account role ({user.role}) possesses insufficient credentials to view this resource. 
          Please contact your administrator if you require access.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
