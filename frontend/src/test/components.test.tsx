import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { StatCard } from '../components/common/StatCard';
import { Layers } from 'lucide-react';

describe('Common UI Components', () => {
  it('renders Button with variants and loading state', () => {
    const { rerender } = render(<Button variant="primary">Proceed</Button>);
    expect(screen.getByRole('button', { name: /proceed/i })).toBeInTheDocument();

    rerender(<Button isLoading>Proceed</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders Badge with custom status colors', () => {
    render(<Badge variant="success">Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders StatCard with title, value, and change trend indicator', () => {
    render(
      <StatCard
        title="MRR Growth"
        value="$284,500"
        change={18.2}
        icon={<Layers data-testid="icon" />}
      />
    );

    expect(screen.getByText('MRR Growth')).toBeInTheDocument();
    expect(screen.getByText('$284,500')).toBeInTheDocument();
    expect(screen.getByText('+18.2%')).toBeInTheDocument();
  });
});
