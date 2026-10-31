"""Pydantic schemas for the Finance Dashboard."""

from typing import List
from pydantic import BaseModel
from decimal import Decimal


class MonthlyRevenuePoint(BaseModel):
    month: str
    revenue: float
    target: float


class SubscriptionGrowthPoint(BaseModel):
    month: str
    active: int
    new: int
    churned: int


class PaymentTrendPoint(BaseModel):
    date: str
    volume: float
    count: int


class InvoiceDistributionPoint(BaseModel):
    name: str
    value: float
    color: str


class DashboardMetricsResponse(BaseModel):
    active_subscriptions: int
    active_subscriptions_change: float = 12.5
    revenue_received: float
    revenue_change: float = 14.2
    outstanding_amount: float
    outstanding_change: float = -3.8
    overdue_invoices: int
    total_customers: int
    total_customers_change: float = 8.1
    upcoming_renewals: int
    monthly_revenue: List[MonthlyRevenuePoint] = []
    subscription_growth: List[SubscriptionGrowthPoint] = []
    payment_trends: List[PaymentTrendPoint] = []
    invoice_distribution: List[InvoiceDistributionPoint] = []
