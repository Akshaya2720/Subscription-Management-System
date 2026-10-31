import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Lock, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { authService } from '../../services/auth';

const schema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type FormData = z.infer<typeof schema>;

export const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      await authService.resetPassword(data.password);
      setIsSuccess(true);
      setTimeout(() => navigate('/auth/login'), 2000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7] p-6 selection:bg-[#0071e3] selection:text-white">
      <div className="w-full max-w-md rounded-3xl border border-black/[0.08] bg-white p-8 shadow-apple-card sm:p-10">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1d1d1f] text-white font-black text-2xl shadow-sm tracking-tight">
            V
          </div>
          <h2 className="mt-5 text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Set New Password
          </h2>
          <p className="mt-1.5 text-xs text-[#6e6e73]">
            Create a secure new password for your account
          </p>
        </div>

        {isSuccess ? (
          <div className="mt-6 rounded-2xl bg-emerald-50/80 p-6 text-center border border-emerald-200">
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" />
            <h4 className="mt-2 text-sm font-bold text-emerald-950">
              Password Updated Successfully!
            </h4>
            <p className="mt-1 text-xs text-emerald-800">
              Redirecting you to login...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <Input
              label="New Password"
              type="password"
              placeholder="••••••••"
              leftIcon={<Lock className="h-4 w-4 text-[#86868b]" />}
              error={errors.password?.message}
              {...register('password')}
            />

            <Input
              label="Confirm New Password"
              type="password"
              placeholder="••••••••"
              leftIcon={<Lock className="h-4 w-4 text-[#86868b]" />}
              error={errors.confirmPassword?.message}
              {...register('confirmPassword')}
            />

            <Button type="submit" className="w-full mt-3" size="lg" isLoading={isLoading}>
              Update Password
            </Button>

            <div className="text-center pt-2">
              <Link
                to="/auth/login"
                className="text-xs font-medium text-[#6e6e73] hover:text-[#1d1d1f] transition-colors"
              >
                Cancel and back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
