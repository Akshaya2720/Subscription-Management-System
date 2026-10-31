import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Eye, EyeOff, Lock, Mail, ShieldCheck } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { authService } from '../../services/auth';
import { UserRole } from '../../types';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid business email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRole, setSelectedRole] = useState<UserRole>('admin');
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'admin@verisub.io',
      password: 'password123',
    },
  });

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role);
    if (role === 'admin') {
      setValue('email', 'admin@verisub.io');
    } else if (role === 'staff') {
      setValue('email', 'staff@verisub.io');
    } else {
      setValue('email', 'billing@acmetechnologies.com');
    }
  };

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setServerError(null);
    try {
      const { user } = await authService.login({
        email: data.email,
        password: data.password,
        role: selectedRole,
      });

      if (user.role === 'customer') {
        navigate('/portal/dashboard');
      } else {
        navigate('/admin/overview');
      }
    } catch (err: any) {
      setServerError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4 dark:bg-slate-950">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
        {/* Brand Header */}
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white font-black text-xl shadow-md">
            V
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Welcome to VERISUB
          </h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Intelligent Subscription & Billing Verification Platform
          </p>
        </div>

        {/* Demo Role Selection Quick Pills */}
        <div className="mt-6 rounded-xl bg-slate-50 p-1.5 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
          <p className="text-[11px] font-semibold text-center text-slate-500 uppercase tracking-wider mb-1">
            Quick Persona Login
          </p>
          <div className="grid grid-cols-3 gap-1">
            <button
              type="button"
              onClick={() => handleRoleSelect('admin')}
              className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                selectedRole === 'admin'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
              }`}
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => handleRoleSelect('staff')}
              className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                selectedRole === 'staff'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
              }`}
            >
              Staff
            </button>
            <button
              type="button"
              onClick={() => handleRoleSelect('customer')}
              className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                selectedRole === 'customer'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-300'
              }`}
            >
              Customer
            </button>
          </div>
        </div>

        {/* Server Error Alert */}
        {serverError && (
          <div className="mt-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-400">
            {serverError}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <Input
            label="Work Email"
            type="email"
            placeholder="name@company.com"
            leftIcon={<Mail className="h-4 w-4" />}
            error={errors.email?.message}
            {...register('email')}
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              leftIcon={<Lock className="h-4 w-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              error={errors.password?.message}
              {...register('password')}
            />
          </div>

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 cursor-pointer text-slate-600 dark:text-slate-400">
              <input type="checkbox" defaultChecked className="rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
              Remember me
            </label>
            <Link
              to="/auth/forgot-password"
              className="font-semibold text-brand-600 hover:text-brand-500 dark:text-brand-400"
            >
              Forgot password?
            </Link>
          </div>

          <Button type="submit" className="w-full mt-2" isLoading={isLoading} size="lg">
            Sign In to {selectedRole === 'customer' ? 'Customer Portal' : 'Workspace'}
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-slate-500">
          Need an enterprise account?{' '}
          <Link
            to="/auth/register-org"
            className="font-semibold text-brand-600 hover:underline dark:text-brand-400"
          >
            Register Organization
          </Link>
        </div>

        <div className="mt-6 flex items-center justify-center gap-2 border-t border-slate-100 pt-4 text-[11px] text-slate-400 dark:border-slate-800">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          <span>Secured with JWT & SHA-256 Hash Chain Integrity</span>
        </div>
      </div>
    </div>
  );
};
