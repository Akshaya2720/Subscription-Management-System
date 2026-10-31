import React, { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { TopNav } from './TopNav';
import { authService } from '../../services/auth';
import { UserRole } from '../../types';

export const AppLayout: React.FC = () => {
  const [currentUser, setCurrentUser] = useState(authService.getCurrentUser());

  if (!currentUser) {
    return <Navigate to="/auth/login" replace />;
  }

  const handleRoleChange = (newRole: UserRole) => {
    const updatedUser = authService.switchRole(newRole);
    setCurrentUser({ ...updatedUser });
  };

  return (
    <div className="min-h-screen w-screen overflow-x-hidden font-sans text-slate-100 selection:bg-blue-600 selection:text-white flex flex-col">
      {/* Supaste Floating Dynamic Island Header */}
      <TopNav user={currentUser} onRoleChange={handleRoleChange} />

      {/* Main Content Viewport */}
      <main className="flex-1 px-4 sm:px-6 pb-12">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
