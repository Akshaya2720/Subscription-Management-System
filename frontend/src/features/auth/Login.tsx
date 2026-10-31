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
    <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7] p-6 selection:bg-[#0071e3] selection:text-white">
      <div className="w-full max-w-md rounded-3xl border border-black/[0.08] bg-white p-8 shadow-apple-card sm:p-10">
        {/* Apple Monomark Brand Header */}
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1d1d1f] text-white font-black text-2xl shadow-sm tracking-tight">
            V
          </div>
          <h2 className="mt-5 text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Sign in to VERISUB
          </h2>
          <p className="mt-1.5 text-xs text-[#6e6e73]">
            Intelligent Subscription & Billing Verification Platform
          </p>
        </div>

        {/* Demo Persona Segmented Control */}
        <div className="mt-6 rounded-2xl bg-[#f5f5f7] p-1.5 border border-black/[0.04]">
          <p className="text-[11px] font-semibold text-center text-[#86868b] uppercase tracking-wider mb-1.5">
            Quick Persona Login
          </p>
          <div className="grid grid-cols-3 gap-1 bg-[#e8e8ed]/70 p-1 rounded-xl">
            <button
              type="button"
              onClick={() => handleRoleSelect('admin')}
              className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                selectedRole === 'admin'
                  ? 'bg-white text-[#1d1d1f] shadow-xs'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              }`}
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => handleRoleSelect('staff')}
              className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                selectedRole === 'staff'
                  ? 'bg-white text-[#1d1d1f] shadow-xs'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              }`}
            >
              Staff
            </button>
            <button
              type="button"
              onClick={() => handleRoleSelect('customer')}
              className={`rounded-lg py-1.5 text-xs font-semibold transition-all ${
                selectedRole === 'customer'
                  ? 'bg-white text-[#1d1d1f] shadow-xs'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              }`}
            >
              Customer
            </button>
          </div>
        </div>

        {/* Server Error Alert */}
        {serverError && (
          <div className="mt-4 rounded-xl bg-rose-50 border border-rose-200/80 p-3.5 text-xs font-medium text-rose-800">
            {serverError}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <Input
            label="Work Email"
            type="email"
            placeholder="name@company.com"
            leftIcon={<Mail className="h-4 w-4 text-[#86868b]" />}
            error={errors.email?.message}
            {...register('email')}
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              leftIcon={<Lock className="h-4 w-4 text-[#86868b]" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-[#86868b] hover:text-[#1d1d1f] transition-colors"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              error={errors.password?.message}
              {...register('password')}
            />
          </div>

          <div className="flex items-center justify-between text-xs pt-1">
            <label className="flex items-center gap-2 cursor-pointer text-[#424245] select-none">
              <input
                type="checkbox"
                defaultChecked
                className="h-4 w-4 rounded border-[#d2d2d7] text-[#0071e3] focus:ring-[#0071e3]"
              />
              Remember me
            </label>
            <Link
              to="/auth/forgot-password"
              className="font-medium text-[#0071e3] hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          <Button type="submit" className="w-full mt-3" isLoading={isLoading} size="lg">
            Sign In to {selectedRole === 'customer' ? 'Customer Portal' : 'Workspace'}
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-[#6e6e73]">
          Need an enterprise account?{' '}
          <Link
            to="/auth/register-org"
            className="font-semibold text-[#0071e3] hover:underline"
          >
            Register Organization
          </Link>
        </div>

        <div className="mt-6 flex items-center justify-center gap-2 border-t border-black/[0.06] pt-4 text-[11px] text-[#86868b]">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span>Secured with JWT & SHA-256 Hash Chain Integrity</span>
        </div>
      </div>
    </div>
  );
};
