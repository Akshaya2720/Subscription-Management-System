import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building,
  UserPlus,
  Check,
  Save,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { settingsService, OrgSettingsPayload } from '../../services/settingsService';

export const SettingsView: React.FC = () => {
  const queryClient = useQueryClient();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [, setInviteModalOpen] = useState(false);

  const { data: settings } = useQuery({
    queryKey: ['orgSettings'],
    queryFn: () => settingsService.getSettings(),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<OrgSettingsPayload>) => settingsService.updateSettings(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orgSettings'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  const handleSaveSettings = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    updateMutation.mutate({
      name: formData.get('name') as string,
      currency: formData.get('currency') as string,
      timezone: formData.get('timezone') as string,
      billing_email: formData.get('billing_email') as string,
      tax_id: formData.get('tax_id') as string,
      grace_period_days: Number(formData.get('grace_period_days')),
      auto_retry_failed_payments: formData.get('auto_retry_failed_payments') === 'on',
      tax_rate_default: Number(formData.get('tax_rate_default')),
    });
  };

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Organization & Governance', path: '/admin/settings' },
          { label: 'Audit Trail (SHA-256)', path: '/admin/audit', badge: 'Active' },
          { label: 'Financial Reports', path: '/admin/reports' },
        ]}
      />

      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
          Workspace Settings & Governance
        </h1>
        <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
          Configure organization identity, tax rules, automated dunning retry policies, and team permissions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Organization & Billing Preferences */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building className="h-4 w-4 text-[#0071e3]" />
                <CardTitle>Organization Profile & Tax Parameters</CardTitle>
              </div>
              <CardDescription>Master business entity details stamped on generated invoices</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveSettings} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Organization Legal Name"
                    name="name"
                    defaultValue={settings?.name}
                  />
                  <Input
                    label="Billing Department Email"
                    type="email"
                    name="billing_email"
                    defaultValue={settings?.billing_email}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <Select
                    label="Base Operating Currency"
                    name="currency"
                    defaultValue={settings?.currency || 'USD'}
                    options={[
                      { label: 'USD ($)', value: 'USD' },
                      { label: 'EUR (€)', value: 'EUR' },
                      { label: 'GBP (£)', value: 'GBP' },
                      { label: 'INR (₹)', value: 'INR' },
                    ]}
                  />
                  <Select
                    label="Standard Timezone"
                    name="timezone"
                    defaultValue={settings?.timezone || 'America/New_York (UTC-5)'}
                    options={[
                      { label: 'Eastern Time (UTC-5)', value: 'America/New_York (UTC-5)' },
                      { label: 'Pacific Time (UTC-8)', value: 'America/Los_Angeles (UTC-8)' },
                      { label: 'UTC', value: 'UTC' },
                      { label: 'London GMT', value: 'Europe/London' },
                    ]}
                  />
                  <Input
                    label="Default Tax Rate (%)"
                    type="number"
                    step="0.1"
                    name="tax_rate_default"
                    defaultValue={settings?.tax_rate_default || 8.0}
                  />
                </div>

                <Input
                  label="Tax ID / Corporate EIN"
                  name="tax_id"
                  defaultValue={settings?.tax_id}
                />

                <div className="rounded-2xl border border-black/[0.08] bg-[#f5f5f7] p-4 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#1d1d1f]">
                    Dunning & Billing Retry Preferences
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Grace Period (Days)"
                      type="number"
                      name="grace_period_days"
                      defaultValue={settings?.grace_period_days || 7}
                    />
                    <div className="flex items-center pt-6">
                      <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1d1d1f]">
                        <input
                          type="checkbox"
                          name="auto_retry_failed_payments"
                          defaultChecked={settings?.auto_retry_failed_payments}
                          className="rounded text-[#0071e3]"
                        />
                        Auto-Retry Failed Recurring Charges
                      </label>
                    </div>
                  </div>
                </div>

                {saveSuccess && (
                  <div className="flex items-center gap-2 rounded-2xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
                    <Check className="h-4 w-4" />
                    Organization settings updated and synchronized with backend.
                  </div>
                )}

                <Button type="submit" isLoading={updateMutation.isPending} leftIcon={<Save className="h-4 w-4" />}>
                  Save Workspace Settings
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: User & Staff Role Management */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Team & Staff Access</CardTitle>
                <CardDescription>Assigned role credentials</CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={() => setInviteModalOpen(true)} leftIcon={<UserPlus className="h-3.5 w-3.5" />}>
                Invite
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="divide-y divide-black/[0.05] text-xs">
                <div className="py-2.5 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-[#1d1d1f]">Alex Mercer</p>
                    <p className="text-[11px] text-[#6e6e73]">admin@verisub.io</p>
                  </div>
                  <Badge variant="purple" size="sm">ADMIN</Badge>
                </div>
                <div className="py-2.5 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-[#1d1d1f]">Jordan Blake</p>
                    <p className="text-[11px] text-[#6e6e73]">staff@verisub.io</p>
                  </div>
                  <Badge variant="info" size="sm">STAFF</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
