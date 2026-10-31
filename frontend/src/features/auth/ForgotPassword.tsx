import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { authService } from '../../services/auth';

const schema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

type FormData = z.infer<typeof schema>;

export const ForgotPassword: React.FC = () => {
  const [isSubmitted, setIsSubmitted] = useState(false);
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
      await authService.forgotPassword(data.email);
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4 dark:bg-slate-950">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white font-black text-xl shadow-md">
            V
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Reset Password
          </h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Enter your work email address and we'll send you a password recovery link
          </p>
        </div>

        {isSubmitted ? (
          <div className="mt-6 rounded-xl bg-emerald-50 p-6 text-center dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600 dark:text-emerald-400" />
            <h4 className="mt-2 text-sm font-bold text-emerald-900 dark:text-emerald-300">
              Recovery Link Sent
            </h4>
            <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-400">
              Check your inbox for instructions to reset your password.
            </p>
            <Link to="/auth/login">
              <Button size="sm" variant="outline" className="mt-4">
                Back to Login
              </Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <Input
              label="Work Email Address"
              type="email"
              placeholder="name@company.com"
              leftIcon={<Mail className="h-4 w-4" />}
              error={errors.email?.message}
              {...register('email')}
            />

            <Button type="submit" className="w-full" size="lg" isLoading={isLoading}>
              Send Recovery Link
            </Button>

            <div className="text-center">
              <Link
                to="/auth/login"
                className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Sign In
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
