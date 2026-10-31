import React from 'react';
import { Building, Mail, MapPin, CreditCard, ShieldCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { authService } from '../../services/auth';

export const CustomerProfile: React.FC = () => {
  const user = authService.getCurrentUser();

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Client Account Profile & Billing Details
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Review business registration, billing address, and default payment method profiles
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building className="h-4 w-4 text-brand-600" />
              <CardTitle>Company Entity</CardTitle>
            </div>
            <CardDescription>Primary organization data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Legal Name</span>
              <span className="font-semibold text-slate-900 dark:text-white">
                {user?.organization_name || 'Acme Technologies Inc.'}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Billing Email</span>
              <span className="text-slate-900 dark:text-white">{user?.email}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Tax / VAT ID</span>
              <span className="font-mono text-slate-900 dark:text-white">US-948210492</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Registered Office</span>
              <span className="text-slate-900 dark:text-white">
                100 Innovation Way, Suite 400, San Francisco, CA
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-brand-600" />
              <CardTitle>Default Payment Method</CardTitle>
            </div>
            <CardDescription>Configured for automatic subscription renewals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white dark:bg-slate-700 shadow-xs font-bold text-slate-800 dark:text-white">
                  VISA
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-900 dark:text-white">Visa ending in 4242</p>
                  <p className="text-[11px] text-slate-400">Expires 12/2028 • Default</p>
                </div>
              </div>
              <Badge variant="success" size="sm">ACTIVE</Badge>
            </div>

            <Button variant="outline" size="sm" className="w-full">
              Update Payment Method
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
