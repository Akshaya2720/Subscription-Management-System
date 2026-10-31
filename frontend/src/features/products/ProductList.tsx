import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Plus, Package, Edit2, Power, Layers } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { productService } from '../../services/productService';
import { Product } from '../../types';
import { formatCurrency, formatDate } from '../../utils';

const productSchema = z.object({
  name: z.string().min(2, 'Product name is required'),
  code: z.string().min(2, 'Product code is required'),
  description: z.string().min(5, 'Description is required'),
  category: z.string().optional(),
  base_price: z.coerce.number().min(0, 'Base price must be >= 0'),
  currency: z.string().min(1, 'Currency is required'),
});

type ProductFormData = z.infer<typeof productSchema>;

export const ProductList: React.FC = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  const { data: products = [], isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: () => productService.getProducts(),
  });

  const createMutation = useMutation({
    mutationFn: (data: ProductFormData) =>
      productService.createProduct({
        ...data,
        is_active: true,
        variants: [],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setIsCreateOpen(false);
      reset();
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => productService.toggleProductStatus(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      currency: 'USD',
      base_price: 999,
    },
  });

  const onSubmitCreate = (data: ProductFormData) => {
    createMutation.mutate(data);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Products & Service Catalog
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure enterprise software, hardware tiers, and billable service deliverables
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
          Add Product
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Product</TableHead>
            <TableHead>Code / SKU</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Variants</TableHead>
            <TableHead>Base Price</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={3} />
        ) : products.length === 0 ? (
          <TableEmpty
            title="No products"
            description="Add products to your catalog to link with subscription plans."
            actionText="Create Product"
            onAction={() => setIsCreateOpen(true)}
            colSpan={7}
          />
        ) : (
          <TableBody>
            {products.map((p) => (
              <TableRow key={p.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400">
                      <Package className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-xs text-slate-900 dark:text-white">{p.name}</p>
                      <p className="text-[11px] text-slate-500 max-w-xs truncate">{p.description}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="font-mono text-xs text-slate-600 dark:text-slate-300">
                  {p.code}
                </TableCell>
                <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                  {p.category || 'General'}
                </TableCell>
                <TableCell className="text-xs">
                  {p.variants && p.variants.length > 0 ? (
                    <span className="inline-flex items-center gap-1 font-semibold text-brand-600">
                      <Layers className="h-3.5 w-3.5" />
                      {p.variants.length} variant(s)
                    </span>
                  ) : (
                    <span className="text-slate-400">Standard Tier</span>
                  )}
                </TableCell>
                <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                  {formatCurrency(p.base_price, p.currency)}
                </TableCell>
                <TableCell>
                  <Badge variant={p.is_active ? 'success' : 'default'} size="sm">
                    {p.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => toggleMutation.mutate(p.id)}
                      className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800"
                      title={p.is_active ? 'Deactivate' : 'Activate'}
                    >
                      <Power className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setEditingProduct(p)}
                      className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800"
                      title="Edit Product"
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

      {/* Create Product Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Catalog Product"
        description="Define a new sellable product or service item"
        maxWidth="lg"
      >
        <form onSubmit={handleSubmit(onSubmitCreate)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Product Name"
              placeholder="e.g. Dedicated GPU Cluster"
              error={errors.name?.message}
              {...register('name')}
            />
            <Input
              label="Product Code / SKU"
              placeholder="e.g. PROD-GPU-8X"
              error={errors.code?.message}
              {...register('code')}
            />
          </div>

          <Input
            label="Category"
            placeholder="e.g. Infrastructure / Support / SaaS"
            {...register('category')}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Base Price"
              type="number"
              step="0.01"
              placeholder="1200.00"
              error={errors.base_price?.message}
              {...register('base_price')}
            />
            <Input
              label="Currency"
              defaultValue="USD"
              error={errors.currency?.message}
              {...register('currency')}
            />
          </div>

          <Input
            label="Description"
            placeholder="High-performance compute node with 99.9% uptime SLA"
            error={errors.description?.message}
            {...register('description')}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Product
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
