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
    <div className="flex h-screen w-screen overflow-hidden bg-[#08090a] font-sans text-slate-100 selection:bg-violet-600 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar role={currentUser.role} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden bg-[#08090a]">
        <TopNav user={currentUser} onRoleChange={handleRoleChange} />
        <main className="flex-1 overflow-y-auto p-5 md:p-8 bg-[#08090a]">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
