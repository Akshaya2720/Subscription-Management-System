import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { CustomerLayout } from '../components/layout/CustomerLayout';
import { Login } from '../features/auth/Login';
import { RegisterOrg } from '../features/auth/RegisterOrg';
import { ForgotPassword } from '../features/auth/ForgotPassword';
import { ResetPassword } from '../features/auth/ResetPassword';
import { UserProfile } from '../features/auth/UserProfile';
import { Dashboard } from '../features/dashboard/Dashboard';
import { CustomerList } from '../features/customers/CustomerList';
import { ProductList } from '../features/products/ProductList';
import { PlanList } from '../features/plans/PlanList';
import { QuotationList } from '../features/quotations/QuotationList';
import { SubscriptionList } from '../features/subscriptions/SubscriptionList';
import { BillingRuns } from '../features/billing/BillingRuns';
import { InvoiceList } from '../features/invoices/InvoiceList';
import { PaymentList } from '../features/payments/PaymentList';
import { DiscountList } from '../features/discounts/DiscountList';
import { VerificationList } from '../features/verification/VerificationList';
import { AIInsightsDashboard } from '../features/ai-insights/AIInsightsDashboard';
import { AuditTrail } from '../features/audit/AuditTrail';
import { ReportsView } from '../features/reports/ReportsView';
import { SettingsView } from '../features/settings/SettingsView';

import { CustomerDashboard } from '../features/customer-portal/CustomerDashboard';
import { CustomerSubscriptions } from '../features/customer-portal/CustomerSubscriptions';
import { CustomerInvoices } from '../features/customer-portal/CustomerInvoices';
import { CustomerPayments } from '../features/customer-portal/CustomerPayments';
import { CustomerServices } from '../features/customer-portal/CustomerServices';
import { CustomerDisputes } from '../features/customer-portal/CustomerDisputes';
import { CustomerHelp } from '../features/customer-portal/CustomerHelp';
import { CustomerProfile } from '../features/customer-portal/CustomerProfile';
import { authService } from '../services/auth';

const RootRedirect = () => {
  const user = authService.getCurrentUser();
  if (!user) return <Navigate to="/auth/login" replace />;
  if (user.role === 'customer') return <Navigate to="/portal/dashboard" replace />;
  return <Navigate to="/admin/overview" replace />;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootRedirect />,
  },
  // Auth Routes
  {
    path: '/auth/login',
    element: <Login />,
  },
  {
    path: '/auth/register-org',
    element: <RegisterOrg />,
  },
  {
    path: '/auth/forgot-password',
    element: <ForgotPassword />,
  },
  {
    path: '/auth/reset-password',
    element: <ResetPassword />,
  },

  // Admin & Staff Workspace Routes
  {
    path: '/admin',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/admin/overview" replace /> },
      { path: 'overview', element: <Dashboard /> },
      { path: 'customers', element: <CustomerList /> },
      { path: 'products', element: <ProductList /> },
      { path: 'plans', element: <PlanList /> },
      { path: 'quotations', element: <QuotationList /> },
      { path: 'subscriptions', element: <SubscriptionList /> },
      { path: 'billing', element: <BillingRuns /> },
      { path: 'invoices', element: <InvoiceList /> },
      { path: 'payments', element: <PaymentList /> },
      { path: 'discounts', element: <DiscountList /> },
      { path: 'verification', element: <VerificationList /> },
      { path: 'ai-insights', element: <AIInsightsDashboard /> },
      { path: 'audit', element: <AuditTrail /> },
      { path: 'reports', element: <ReportsView /> },
      { path: 'settings', element: <SettingsView /> },
      { path: 'profile', element: <UserProfile /> },
    ],
  },

  // Customer Self-Service Portal Routes
  {
    path: '/portal',
    element: <CustomerLayout />,
    children: [
      { index: true, element: <Navigate to="/portal/dashboard" replace /> },
      { path: 'dashboard', element: <CustomerDashboard /> },
      { path: 'subscriptions', element: <CustomerSubscriptions /> },
      { path: 'invoices', element: <CustomerInvoices /> },
      { path: 'payments', element: <CustomerPayments /> },
      { path: 'services', element: <CustomerServices /> },
      { path: 'disputes', element: <CustomerDisputes /> },
      { path: 'help', element: <CustomerHelp /> },
      { path: 'profile', element: <CustomerProfile /> },
    ],
  },

  // Catch-all
  {
    path: '*',
    element: <RootRedirect />,
  },
]);
