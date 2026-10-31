import React from 'react';
import { Building, CreditCard } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { authService } from '../../services/auth';

export const CustomerProfile: React.FC = () => {
  const user = authService.getCurrentUser();

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
          Client Account Profile & Billing Details
        </h1>
        <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
          Review business registration, billing address, and default payment method profiles
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building className="h-4 w-4 text-[#0071e3]" />
              <CardTitle>Company Entity</CardTitle>
            </div>
            <CardDescription>Primary organization data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Legal Name</span>
              <span className="font-semibold text-[#1d1d1f]">
                {user?.organization_name || 'Acme Technologies Inc.'}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Billing Email</span>
              <span className="text-[#1d1d1f]">{user?.email}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Tax / VAT ID</span>
              <span className="font-mono text-[#1d1d1f]">US-948210492</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#6e6e73]">Registered Office</span>
              <span className="text-[#1d1d1f]">
                100 Innovation Way, Suite 400, San Francisco, CA
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-[#0071e3]" />
              <CardTitle>Default Payment Method</CardTitle>
            </div>
            <CardDescription>Configured for automatic subscription renewals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-black/[0.08] bg-[#f5f5f7] p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-2xs font-bold text-[#1d1d1f] border border-black/[0.06]">
                  VISA
                </div>
                <div>
                  <p className="text-xs font-bold text-[#1d1d1f]">Visa ending in 4242</p>
                  <p className="text-[11px] text-[#6e6e73]">Expires 12/2028 • Default</p>
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
