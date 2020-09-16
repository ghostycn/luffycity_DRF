#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.urls import path
from .views import ShoppingCartView
from .settlement_view import SettlementView
from .payment_view import PaymentView
urlpatterns = [
    path('shopping_cart',ShoppingCartView.as_view()),
    path('settlement',SettlementView.as_view()),
    path('payment',PaymentView.as_view())
]