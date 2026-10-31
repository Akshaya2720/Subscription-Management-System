import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Badge } from '../../components/common/Badge';
import { authService } from '../../services/auth';
import { Shield, Check } from 'lucide-react';

export const UserProfile: React.FC = () => {
  const [currentUser] = useState(authService.getCurrentUser());
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-[#1d1d1f]">
          User Profile & Security
        </h2>
        <p className="text-xs text-[#6e6e73] mt-0.5">
          Manage your personal account credentials, role permissions, and active sessions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>Update your personal information and contact preferences</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Full Name"
                  defaultValue={currentUser?.full_name || 'Alex Mercer'}
                />
                <Input
                  label="Work Email"
                  type="email"
                  defaultValue={currentUser?.email || 'admin@verisub.io'}
                  disabled
                  helperText="Managed by organization workspace SSO"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Organization"
                  defaultValue={currentUser?.organization_name || 'Verisub Corp Inc.'}
                  disabled
                />
                <div className="space-y-1.5 text-left">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#6e6e73]">
                    Assigned Role
                  </label>
                  <div className="pt-2">
                    <Badge variant="info" size="md">
                      {currentUser?.role?.toUpperCase() || 'ADMIN'}
                    </Badge>
                  </div>
                </div>
              </div>

              {isSaved && (
                <div className="flex items-center gap-2 rounded-xl bg-emerald-50 border border-emerald-200/80 p-3.5 text-xs font-medium text-emerald-800">
                  <Check className="h-4 w-4" />
                  Profile settings saved successfully.
                </div>
              )}

              <Button type="submit" className="mt-4">
                Save Changes
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Role Permissions Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-[#0071e3]" />
              <CardTitle>Active Permissions</CardTitle>
            </div>
            <CardDescription>Access control policies enforced by backend JWT</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-2xl bg-[#f5f5f7] p-3.5 border border-black/[0.04]">
              <p className="text-xs font-bold text-[#1d1d1f]">Role Scope</p>
              <p className="text-xs text-[#6e6e73] mt-1 leading-relaxed">
                {currentUser?.role === 'admin'
                  ? 'Super Administrator (Full platform read/write authority across all modules)'
                  : currentUser?.role === 'staff'
                  ? 'Operations Staff (Customer management, quotations, subscriptions & verification review)'
                  : 'Customer Self-Service (Invoices, subscriptions & billing dispute filing)'}
              </p>
            </div>

            <div className="space-y-1 pt-2">
              <p className="text-xs font-semibold text-[#6e6e73] uppercase tracking-wider">
                Granted Capabilities:
              </p>
              <ul className="text-xs text-[#424245] space-y-1.5 list-disc pl-4">
                <li>JWT Token Authorization</li>
                <li>Contract-to-Bill Verification Access</li>
                <li>Live Telemetry Auditing</li>
                <li>SHA-256 Hash Integrity Validator</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
