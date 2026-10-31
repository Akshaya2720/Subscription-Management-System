import React, { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
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
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100">
      {/* Sidebar Navigation */}
      <Sidebar role={currentUser.role} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav user={currentUser} onRoleChange={handleRoleChange} />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
