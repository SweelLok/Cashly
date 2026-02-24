from django.urls import path
from .views import (
    activate_email, 
    register_view, 
    login_view, 
    logout_view, 
    dashboard_view,
    profile_view,
    edit_profile_view,
    add_expense_view,
    add_income_view,
    delete_expense_view,
    delete_income_view,
    investments_goals_view,
    update_budgets_view,
    add_goal_view,
    edit_goal_view,
    delete_goal_view
)


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('profile/add-expense/', add_expense_view, name='add_expense'),
    path('profile/add-income/', add_income_view, name='add_income'),
    path('profile/delete-expense/<int:expense_id>/', delete_expense_view, name='delete_expense'),
    path('profile/delete-income/<int:income_id>/', delete_income_view, name='delete_income'),
    path('explore/', investments_goals_view, name='investments_goals'),
    path('explore/add-goal/', add_goal_view, name='add_goal'),
    path('explore/edit-goal/<int:goal_id>/', edit_goal_view, name='edit_goal'),
    path('explore/delete-goal/<int:goal_id>/', delete_goal_view, name='delete_goal'),
    path('profile/update-budgets/', update_budgets_view, name='update_budgets'),
    path('activate/<uidb64>/<token>/', activate_email, name='activate'),
]
