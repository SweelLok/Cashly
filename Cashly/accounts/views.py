from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.contrib import messages
from django.conf import settings
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging
import smtplib

from .tokens import email_verification_token
from .forms import RegisterForm, EditProfileForm
from .models import UserProfile, Expense, Income, Budget, FinancialGoal
from django.http import HttpResponse

logger = logging.getLogger(__name__)

# вход
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)  # залогиниваем
        return redirect('dashboard')

    return render(request, 'accounts/login.html', {'form': form})


# выход
def logout_view(request):
    logout(request)
    return redirect('login')


# главная страница
@login_required
def dashboard_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # последние расходы
    expense_list = Expense.objects.filter(user=request.user).order_by('-date')[:10]
    income_list = Income.objects.filter(user=request.user).order_by('-date')[:10]
    
    investments_count = FinancialGoal.objects.filter(user=request.user).count()
    
    # считаем по месяцам
    today = datetime.now().date()
    current_month_start = today.replace(day=1)
    
    monthly_budget = profile.monthly_budget or Decimal('0')
    monthly_spent = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    monthly_income = Income.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    portfolio_value = monthly_budget - monthly_spent
    
    budget_categories = []
    budgets = Budget.objects.filter(user=request.user, month__gte=current_month_start)
    
    for budget in budgets:
        spent = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        budget_categories.append({
            'name': budget.category,
            'limit': budget.limit,
            'spent': spent,
            'is_over': spent > budget.limit,
            'percent': min(int((spent / budget.limit) * 100) if budget.limit > 0 else 0, 100)
        })
    
    total_expenses = sum(Decimal(str(exp.amount)) for exp in expense_list)
    total_income = sum(Decimal(str(inc.amount)) for inc in income_list)
    
    context = {
        'investments_count': investments_count,
        'portfolio_value': portfolio_value,
        'expense_list': expense_list,
        'income_list': income_list,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'monthly_income': monthly_income,
        'budget_categories': budget_categories,
    }
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    expense_list = Expense.objects.filter(user=request.user).order_by('-date')[:10]
    income_list = Income.objects.filter(user=request.user).order_by('-date')[:10]
    
    investments_count = FinancialGoal.objects.filter(user=request.user).count()
    
    portfolio_value = FinancialGoal.objects.filter(user=request.user).aggregate(
        total=Sum('saved')
    )['total'] or 0
    
    today = datetime.now().date()
    current_month_start = today.replace(day=1)
    
    budget_categories = []
    budgets = Budget.objects.filter(user=request.user, month__gte=current_month_start)
    
    for budget in budgets:
        spent = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        budget_categories.append({
            'name': budget.category,
            'limit': budget.limit,
            'spent': spent,
            'is_over': spent > budget.limit,
            'percent': min(int((spent / budget.limit) * 100) if budget.limit > 0 else 0, 100)
        })
    
    total_budget = budgets.aggregate(total=Sum('limit'))['total'] or Decimal('0')
    spent_total = sum(Decimal(str(cat['spent'])) for cat in budget_categories)
    remaining_total = total_budget - spent_total
    total_budget_percent = int((spent_total / total_budget) * 100) if total_budget > 0 else 0
    
    goals = FinancialGoal.objects.filter(user=request.user)
    
    monthly_budget = profile.monthly_budget or Decimal('0')
    lifetime_budget = profile.lifetime_budget or Decimal('0')

    monthly_spent = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    monthly_income = Income.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    lifetime_spent = Expense.objects.filter(
        user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    lifetime_income = Income.objects.filter(
        user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    monthly_percent = int((monthly_spent / monthly_budget) * 100) if monthly_budget > 0 else 0
    lifetime_percent = int((lifetime_spent / lifetime_budget) * 100) if lifetime_budget > 0 else 0

    monthly_remaining = monthly_budget - monthly_spent + monthly_income
    lifetime_remaining = lifetime_budget - lifetime_spent + lifetime_income
    
    monthly_net = monthly_income - monthly_spent
    
    context = {
        'investments_count': investments_count,
        'portfolio_value': portfolio_value,
        'expense_list': expense_list,
        'income_list': income_list,
        'budget_categories': budget_categories,
        'total_budget': total_budget,
        'spent_total': spent_total,
        'remaining_total': remaining_total,
        'total_budget_percent': total_budget_percent,
        'goals': goals,
        'monthly_budget': monthly_budget,
        'monthly_spent': monthly_spent,
        'monthly_income': monthly_income,
        'monthly_net': monthly_net,
        'monthly_percent': monthly_percent,
        'monthly_remaining': monthly_remaining,
        'lifetime_budget': lifetime_budget,
        'lifetime_spent': lifetime_spent,
        'lifetime_income': lifetime_income,
        'lifetime_percent': lifetime_percent,
        'lifetime_remaining': lifetime_remaining,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def investments_goals_view(request):
    goals = FinancialGoal.objects.filter(user=request.user)
    
    today = datetime.now().date()
    current_month_start = today.replace(day=1)
    
    monthly_income = Income.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    monthly_spent = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    monthly_net = monthly_income - monthly_spent
    
    context = {
        'goals': goals,
        'monthly_net': monthly_net,
    }
    
    return render(request, 'accounts/investments_goals.html', context)


def terms_view(request):
    return render(request, 'accounts/terms.html')


@login_required
def update_budgets_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        try:
            mb = request.POST.get('monthly_budget', '')
            lb = request.POST.get('lifetime_budget', '')
            if mb != '':
                profile.monthly_budget = Decimal(mb)
            if lb != '':
                profile.lifetime_budget = Decimal(lb)
            profile.save()
            messages.success(request, 'Budgets updated successfully')
        except Exception:
            messages.error(request, 'Failed to update budgets')
    return redirect('profile')


@login_required
def edit_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = EditProfileForm(instance=profile, user=request.user)
        form.fields['username'].initial = request.user.username
        form.fields['email'].initial = request.user.email
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


# добавить расход
@login_required
def add_expense_view(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        category = request.POST.get('category')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        
        if description and category and amount and date:
            try:
                amt = Decimal(amount)
            except InvalidOperation:
                messages.error(request, 'Некорректная сумма')
                return render(request, 'accounts/add_expense.html', {
                    'categories': Expense.CATEGORIES
                })

            if amt < 0:
                messages.error(request, 'Сумма не может быть отрицательной')
                return render(request, 'accounts/add_expense.html', {
                    'categories': Expense.CATEGORIES
                })

            Expense.objects.create(
                user=request.user,
                description=description,
                category=category,
                amount=amt,
                date=date
            )
            messages.success(request, 'Expense added successfully!')
            return redirect('profile')
    
    return render(request, 'accounts/add_expense.html', {
        'categories': Expense.CATEGORIES
    })


# добавить доход
@login_required
def add_income_view(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        source = request.POST.get('source')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        
        if description and source and amount and date:
            try:
                amt = Decimal(amount)
            except InvalidOperation:
                messages.error(request, 'Incorrect amount')
                return render(request, 'accounts/add_income.html', {
                    'sources': Income.SOURCES
                })

            if amt < 0:
                messages.error(request, 'Amount cannot be negative')
                return render(request, 'accounts/add_income.html', {
                    'sources': Income.SOURCES
                })

            Income.objects.create(
                user=request.user,
                description=description,
                source=source,
                amount=amt,
                date=date
            )
            messages.success(request, 'Income added successfully!')
            return redirect('profile')
    
    return render(request, 'accounts/add_income.html', {
        'sources': Income.SOURCES
    })


# удалить расход
@login_required
def delete_expense_view(request, expense_id):
    expense = Expense.objects.filter(user=request.user, id=expense_id).first()
    
    if not expense:
        messages.error(request, 'Expense not found')
        return redirect('profile')
    
    expense.delete()
    messages.success(request, 'Expense deleted successfully!')
    return redirect('profile')


# удалить доход
@login_required
def delete_income_view(request, income_id):
    income = Income.objects.filter(user=request.user, id=income_id).first()
    
    if not income:
        messages.error(request, 'Income not found')
        return redirect('profile')
    
    income.delete()
    messages.success(request, 'Income deleted successfully!')
    return redirect('profile')


# регистрация
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # активируем по email
            user.save()
            
            UserProfile.objects.get_or_create(user=user)

            if not settings.EMAIL_CONFIGURED:
                logger.warning("Email not configured. User created but email not sent.")
                messages.warning(
                    request,
                    'Account created! Email service is not configured. Please contact administrator to verify your email.'
                )
                return render(request, 'accounts/email_sent.html', {
                    'email_error': True,
                    'message': 'Your account has been created but email verification could not be sent due to server configuration. Please contact support.'
                })

            mail_subject = 'Подтверждение email'
            domain = request.get_host()
            message = render_to_string('accounts/email_confirm.html', {
                'user': user,
                'domain': domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': email_verification_token.make_token(user),
            })

            email = EmailMessage(
                mail_subject,
                message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            try:
                email.send(fail_silently=False)
                logger.info(f"Confirmation email sent successfully to {user.email}")
                return render(request, 'accounts/email_sent.html')
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication Error: {str(e)}")
                messages.error(request, 'Email service authentication failed. Please check server configuration.')
                return render(request, 'accounts/email_sent.html', {
                    'email_error': True,
                    'message': 'Your account has been created but email verification could not be sent. Please contact support.'
                })
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                messages.error(request, f'Failed to send confirmation email: {str(e)}')
                return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# новая цель
@login_required
def add_goal_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        target = request.POST.get('target')
        icon = request.POST.get('icon', '🎯')
        
        if name and target:
            try:
                FinancialGoal.objects.create(
                    user=request.user,
                    name=name,
                    target=Decimal(target),
                    icon=icon
                )
                messages.success(request, 'Goal added successfully!')
            except Exception as e:
                messages.error(request, f'Failed to add goal: {str(e)}')
        return redirect('investments_goals')
    
    return render(request, 'accounts/add_goal.html')


# редактировать цель
@login_required
def edit_goal_view(request, goal_id):
    goal = FinancialGoal.objects.filter(user=request.user, id=goal_id).first()
    
    if not goal:
        messages.error(request, 'Goal not found')
        return redirect('investments_goals')
    
    if request.method == 'POST':
        goal.name = request.POST.get('name', goal.name)
        goal.target = Decimal(request.POST.get('target', goal.target))
        goal.saved = Decimal(request.POST.get('saved', goal.saved))
        goal.icon = request.POST.get('icon', goal.icon)
        goal.save()
        messages.success(request, 'Goal updated successfully!')
        return redirect('investments_goals')
    
    return render(request, 'accounts/edit_goal.html', {'goal': goal})


# удалить цель
@login_required
def delete_goal_view(request, goal_id):
    goal = FinancialGoal.objects.filter(user=request.user, id=goal_id).first()
    
    if not goal:
        messages.error(request, 'Goal not found')
        return redirect('investments_goals')
    
    goal.delete()
    messages.success(request, 'Goal deleted successfully!')
    return redirect('investments_goals')


def activate_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'accounts/email_confirmed.html')
    else:
        return HttpResponse('Invalid activation link')
    