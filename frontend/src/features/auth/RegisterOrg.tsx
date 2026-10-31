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
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4 dark:bg-slate-950">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white font-black text-xl shadow-md">
            V
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Register Organization & Admin
          </h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Set up your enterprise subscription management and billing verification workspace
          </p>
        </div>

        {serverError && (
          <div className="mt-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-400">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Organization Name"
              placeholder="e.g. Acme Corp"
              leftIcon={<Building className="h-4 w-4" />}
              error={errors.organization_name?.message}
              {...register('organization_name')}
            />
            <Input
              label="Company Domain"
              placeholder="acme.com"
              leftIcon={<Globe className="h-4 w-4" />}
              error={errors.domain?.message}
              {...register('domain')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Admin Full Name"
              placeholder="Jane Doe"
              leftIcon={<UserIcon className="h-4 w-4" />}
              error={errors.admin_name?.message}
              {...register('admin_name')}
            />
            <Input
              label="Admin Work Email"
              type="email"
              placeholder="jane@acme.com"
              leftIcon={<Mail className="h-4 w-4" />}
              error={errors.admin_email?.message}
              {...register('admin_email')}
            />
          </div>

          <Input
            label="Master Admin Password"
            type="password"
            placeholder="At least 8 characters"
            leftIcon={<Lock className="h-4 w-4" />}
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

        <div className="mt-6 text-center text-xs text-slate-500">
          Already registered?{' '}
          <Link
            to="/auth/login"
            className="font-semibold text-brand-600 hover:underline dark:text-brand-400"
          >
            Sign in here
          </Link>
        </div>
      </div>
    </div>
  );
};
