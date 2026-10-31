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
    <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7] p-6 selection:bg-[#0071e3] selection:text-white">
      <div className="w-full max-w-md rounded-3xl border border-black/[0.08] bg-white p-8 shadow-apple-card sm:p-10">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1d1d1f] text-white font-black text-2xl shadow-sm tracking-tight">
            V
          </div>
          <h2 className="mt-5 text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Reset Password
          </h2>
          <p className="mt-1.5 text-xs text-[#6e6e73]">
            Enter your work email address and we'll send you a password recovery link
          </p>
        </div>

        {isSubmitted ? (
          <div className="mt-6 rounded-2xl bg-emerald-50/80 p-6 text-center border border-emerald-200">
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" />
            <h4 className="mt-2 text-sm font-bold text-emerald-950">
              Recovery Link Sent
            </h4>
            <p className="mt-1 text-xs text-emerald-800">
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
              leftIcon={<Mail className="h-4 w-4 text-[#86868b]" />}
              error={errors.email?.message}
              {...register('email')}
            />

            <Button type="submit" className="w-full mt-2" size="lg" isLoading={isLoading}>
              Send Recovery Link
            </Button>

            <div className="text-center pt-2">
              <Link
                to="/auth/login"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6e6e73] hover:text-[#1d1d1f] transition-colors"
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
