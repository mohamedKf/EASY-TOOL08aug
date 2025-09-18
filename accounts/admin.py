from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import Company, CustomUser

@staff_member_required
def admin_companies_view(request):
    companies = Company.objects.all().select_related('contractor').prefetch_related('contractor__owned_company', 'customuser_set')

    context = {
        'companies': companies
    }
    return render(request, 'admin/company_list.html', context)
