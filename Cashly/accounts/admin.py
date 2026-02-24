from django.contrib import admin
from .models import UserProfile, Expense, Income, Budget, FinancialGoal


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'category', 'amount', 'date')
    list_filter = ('category', 'date', 'user')
    search_fields = ('description', 'user__username')
    ordering = ('-date',)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'source', 'amount', 'date')
    list_filter = ('source', 'date', 'user')
    search_fields = ('description', 'user__username')
    ordering = ('-date',)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'limit', 'month')
    list_filter = ('category', 'month', 'user')
    search_fields = ('user__username',)


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'target', 'saved', 'percent')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at',)

