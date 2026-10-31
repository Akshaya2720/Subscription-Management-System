import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Building, Mail, Lock, User as UserIcon, Globe, ArrowRight } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { authService } from '../../services/auth';

const registerSchema = z.object({
  organization_name: z.string().min(2, 'Organization name must be at least 2 characters'),
  domain: z.string().optional(),
  admin_name: z.string().min(2, 'Admin full name is required'),
  admin_email: z.string().email('Valid business email is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  currency: z.string().min(1, 'Please select default billing currency'),
  timezone: z.string().min(1, 'Please select timezone'),
});

type RegisterFormData = z.infer<typeof registerSchema>;

export const RegisterOrg: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      organization_name: '',
      domain: '',
      admin_name: '',
      admin_email: '',
      password: '',
      currency: 'USD',
      timezone: 'America/New_York (UTC-5)',
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setServerError(null);
    try {
      await authService.registerOrganization(data);
      navigate('/admin/overview');
    } catch (err: any) {
      setServerError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7] p-6 selection:bg-[#0071e3] selection:text-white">
      <div className="w-full max-w-lg rounded-3xl border border-black/[0.08] bg-white p-8 shadow-apple-card sm:p-10">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1d1d1f] text-white font-black text-2xl shadow-sm tracking-tight">
            V
          </div>
          <h2 className="mt-5 text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Create your Organization
          </h2>
          <p className="mt-1.5 text-xs text-[#6e6e73]">
            Set up enterprise subscription management and billing verification
          </p>
        </div>

        {serverError && (
          <div className="mt-4 rounded-xl bg-rose-50 border border-rose-200/80 p-3.5 text-xs font-medium text-rose-800">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Organization Name"
              placeholder="e.g. Acme Corp"
              leftIcon={<Building className="h-4 w-4 text-[#86868b]" />}
              error={errors.organization_name?.message}
              {...register('organization_name')}
            />
            <Input
              label="Company Domain"
              placeholder="acme.com"
              leftIcon={<Globe className="h-4 w-4 text-[#86868b]" />}
              error={errors.domain?.message}
              {...register('domain')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Admin Full Name"
              placeholder="Jane Doe"
              leftIcon={<UserIcon className="h-4 w-4 text-[#86868b]" />}
              error={errors.admin_name?.message}
              {...register('admin_name')}
            />
            <Input
              label="Admin Work Email"
              type="email"
              placeholder="jane@acme.com"
              leftIcon={<Mail className="h-4 w-4 text-[#86868b]" />}
              error={errors.admin_email?.message}
              {...register('admin_email')}
            />
          </div>

          <Input
            label="Master Admin Password"
            type="password"
            placeholder="At least 8 characters"
            leftIcon={<Lock className="h-4 w-4 text-[#86868b]" />}
            error={errors.password?.message}
            {...register('password')}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Default Currency"
              options={[
                { label: 'USD ($)', value: 'USD' },
                { label: 'EUR (€)', value: 'EUR' },
                { label: 'GBP (£)', value: 'GBP' },
                { label: 'INR (₹)', value: 'INR' },
              ]}
              {...register('currency')}
            />
            <Select
              label="Timezone"
              options={[
                { label: 'Eastern Time (US & Canada)', value: 'America/New_York (UTC-5)' },
                { label: 'Pacific Time (US & Canada)', value: 'America/Los_Angeles (UTC-8)' },
                { label: 'UTC', value: 'UTC' },
                { label: 'London (GMT)', value: 'Europe/London' },
                { label: 'India Standard Time (IST)', value: 'Asia/Kolkata (UTC+5:30)' },
              ]}
              {...register('timezone')}
            />
          </div>

          <Button
            type="submit"
            className="w-full mt-4"
            size="lg"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="h-4 w-4" />}
          >
            Create Organization & Launch Admin
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-[#6e6e73]">
          Already registered?{' '}
          <Link
            to="/auth/login"
            className="font-semibold text-[#0071e3] hover:underline"
          >
            Sign in here
          </Link>
        </div>
      </div>
    </div>
  );
};
