import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Search,
  Plus,
  Mail,
  Edit2,
  Eye,
  Filter,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { customerService } from '../../services/customerService';
import { Customer } from '../../types';
import { formatCurrency, formatDate } from '../../utils';

const customerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Valid business email is required'),
  phone: z.string().optional(),
  company_name: z.string().min(2, 'Company name is required'),
  tax_number: z.string().optional(),
  address_line1: z.string().optional(),
  city: z.string().optional(),
  country: z.string().min(2, 'Country is required'),
  status: z.enum(['active', 'inactive', 'archived']),
  currency: z.string().min(1, 'Currency is required'),
});

type CustomerFormData = z.infer<typeof customerSchema>;

export const CustomerList: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [viewingCustomer, setViewingCustomer] = useState<Customer | null>(null);

  // Queries
  const { data: customers = [], isLoading } = useQuery({
    queryKey: ['customers', search, statusFilter],
    queryFn: () => customerService.getCustomers(search, statusFilter),
  });

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (data: CustomerFormData) => customerService.createCustomer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      setIsCreateOpen(false);
      reset();
    },
  });

  // Edit Mutation
  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Customer> }) =>
      customerService.updateCustomer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      setEditingCustomer(null);
    },
  });

  // Form for creation
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CustomerFormData>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      status: 'active',
      currency: 'USD',
      country: 'United States',
    },
  });

  const onSubmitCreate = (data: CustomerFormData) => {
    createMutation.mutate(data);
  };

  const handleOpenEdit = (customer: Customer) => {
    setEditingCustomer(customer);
  };

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Subscriptions', path: '/admin/subscriptions' },
          { label: 'Quotations & Pricing', path: '/admin/quotations' },
          { label: 'Product Catalog & Plans', path: '/admin/plans' },
          { label: 'Customers', path: '/admin/customers', badge: `${customers.length}` },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Customer Directory
          </h1>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Manage client accounts, contracts, tax IDs, and billing communication records
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="h-3.5 w-3.5" />}>
          Add Customer
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#86868b]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by customer name, company, or email..."
            className="w-full rounded-full border border-[#d2d2d7] bg-white pl-10 pr-4 py-2 text-xs text-[#1d1d1f] placeholder-[#86868b] focus:border-[#0071e3] focus:outline-none focus:ring-2 focus:ring-[#0071e3]/20 shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="h-4 w-4 text-[#86868b] shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-full border border-[#d2d2d7] bg-white px-4 py-2 text-xs font-medium text-[#1d1d1f] outline-none focus:border-[#0071e3] shadow-2xs w-full sm:w-auto cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Customers Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Customer / Company</TableHead>
            <TableHead>Contact Email</TableHead>
            <TableHead>Tax Number</TableHead>
            <TableHead>Location</TableHead>
            <TableHead>Total Spend</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={4} />
        ) : customers.length === 0 ? (
          <TableEmpty
            title="No customers found"
            description="Create your first customer to begin establishing contracts and subscriptions."
            actionText="Add New Customer"
            onAction={() => setIsCreateOpen(true)}
            colSpan={7}
          />
        ) : (
          <TableBody>
            {customers.map((c) => (
              <TableRow key={c.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-100 font-bold text-xs text-[#1d1d1f] shadow-2xs">
                      {c.name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-semibold text-xs text-[#1d1d1f]">{c.name}</p>
                      <p className="text-[11px] text-[#6e6e73]">{c.company_name || 'Individual'}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-xs text-[#1d1d1f]">
                  <div className="flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-[#86868b]" />
                    {c.email}
                  </div>
                </TableCell>
                <TableCell className="text-xs font-mono text-[#6e6e73]">
                  {c.tax_number || '—'}
                </TableCell>
                <TableCell className="text-xs text-[#6e6e73]">
                  {[c.city, c.country].filter(Boolean).join(', ') || 'Global'}
                </TableCell>
                <TableCell className="text-xs font-semibold text-[#1d1d1f]">
                  {formatCurrency(c.total_spend, c.currency)}
                </TableCell>
                <TableCell>
                  <Badge variant={c.status === 'active' ? 'success' : 'default'} size="sm">
                    {c.status.toUpperCase()}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => setViewingCustomer(c)}
                      className="rounded-full p-2 text-[#6e6e73] hover:bg-black/[0.05] hover:text-[#1d1d1f] transition-colors"
                      title="View Details & History"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleOpenEdit(c)}
                      className="rounded-full p-2 text-[#6e6e73] hover:bg-black/[0.05] hover:text-[#1d1d1f] transition-colors"
                      title="Edit Customer"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>

      {/* Create Customer Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add New Customer"
        description="Register a new client entity for billing and SLA tracking"
        maxWidth="lg"
      >
        <form onSubmit={handleSubmit(onSubmitCreate)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Contact Person Name"
              placeholder="e.g. Sarah Jenkins"
              error={errors.name?.message}
              {...register('name')}
            />
            <Input
              label="Company Name"
              placeholder="e.g. Acme Cloud Corp"
              error={errors.company_name?.message}
              {...register('company_name')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Billing Email"
              type="email"
              placeholder="billing@acme.com"
              error={errors.email?.message}
              {...register('email')}
            />
            <Input
              label="Phone Number"
              placeholder="+1 (555) 000-0000"
              {...register('phone')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Tax Identification / VAT #"
              placeholder="US-123456789"
              {...register('tax_number')}
            />
            <Select
              label="Billing Currency"
              options={[
                { label: 'USD ($)', value: 'USD' },
                { label: 'EUR (€)', value: 'EUR' },
                { label: 'GBP (£)', value: 'GBP' },
              ]}
              {...register('currency')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Address Line"
              placeholder="123 Market St"
              className="sm:col-span-2"
              {...register('address_line1')}
            />
            <Input label="City" placeholder="San Francisco" {...register('city')} />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-black/[0.06]">
            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Customer
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Customer Modal */}
      {editingCustomer && (
        <Modal
          isOpen={!!editingCustomer}
          onClose={() => setEditingCustomer(null)}
          title={`Edit ${editingCustomer.name}`}
          maxWidth="md"
        >
          <div className="space-y-4">
            <Input
              label="Contact Name"
              defaultValue={editingCustomer.name}
              id="edit-name"
            />
            <Input
              label="Company"
              defaultValue={editingCustomer.company_name}
              id="edit-company"
            />
            <Input
              label="Email"
              defaultValue={editingCustomer.email}
              id="edit-email"
            />
            <Select
              label="Account Status"
              defaultValue={editingCustomer.status}
              options={[
                { label: 'Active', value: 'active' },
                { label: 'Inactive', value: 'inactive' },
                { label: 'Archived', value: 'archived' },
              ]}
              id="edit-status"
            />
            <div className="flex justify-end gap-3 pt-4 border-t border-black/[0.06]">
              <Button variant="outline" onClick={() => setEditingCustomer(null)}>
                Cancel
              </Button>
              <Button
                onClick={() => {
                  const name = (document.getElementById('edit-name') as HTMLInputElement)?.value;
                  const company_name = (document.getElementById('edit-company') as HTMLInputElement)?.value;
                  const email = (document.getElementById('edit-email') as HTMLInputElement)?.value;
                  const status = (document.getElementById('edit-status') as HTMLSelectElement)?.value as any;
                  editMutation.mutate({
                    id: editingCustomer.id,
                    data: { name, company_name, email, status },
                  });
                }}
                isLoading={editMutation.isPending}
              >
                Save Changes
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Customer Details & History Modal */}
      {viewingCustomer && (
        <Modal
          isOpen={!!viewingCustomer}
          onClose={() => setViewingCustomer(null)}
          title={`Customer Profile: ${viewingCustomer.company_name || viewingCustomer.name}`}
          description={`Customer ID: ${viewingCustomer.id} • Registered: ${formatDate(viewingCustomer.created_at)}`}
          maxWidth="2xl"
        >
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-2xl bg-[#f5f5f7] border border-black/[0.06] p-4">
                <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Total Spend</span>
                <p className="text-xl font-bold text-[#1d1d1f] mt-1">
                  {formatCurrency(viewingCustomer.total_spend, viewingCustomer.currency)}
                </p>
              </div>
              <div className="rounded-2xl bg-[#f5f5f7] border border-black/[0.06] p-4">
                <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Active Subscriptions</span>
                <p className="text-xl font-bold text-[#1d1d1f] mt-1">
                  {viewingCustomer.active_subscriptions_count || 1}
                </p>
              </div>
              <div className="rounded-2xl bg-[#f5f5f7] border border-black/[0.06] p-4">
                <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Account Status</span>
                <div className="mt-1">
                  <Badge variant={viewingCustomer.status === 'active' ? 'success' : 'default'}>
                    {viewingCustomer.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="rounded-2xl border border-black/[0.08] p-4 bg-[#fbfbfd] space-y-2">
              <h4 className="text-xs font-bold text-[#1d1d1f] uppercase tracking-wider">
                Billing & Entity Details
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[#6e6e73]">Contact: </span>
                  <span className="font-semibold text-[#1d1d1f]">{viewingCustomer.name}</span>
                </div>
                <div>
                  <span className="text-[#6e6e73]">Email: </span>
                  <span className="font-semibold text-[#1d1d1f]">{viewingCustomer.email}</span>
                </div>
                <div>
                  <span className="text-[#6e6e73]">Tax / VAT ID: </span>
                  <span className="font-mono text-[#1d1d1f]">{viewingCustomer.tax_number || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-[#6e6e73]">Billing Address: </span>
                  <span className="text-[#1d1d1f]">
                    {[viewingCustomer.address_line1, viewingCustomer.city, viewingCustomer.country].filter(Boolean).join(', ') || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
