from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import Company, CustomUser

@staff_member_required
def company_list_view(request):
    companies = Company.objects.all().select_related('contractor')

    data = []
    for company in companies:
        workers = CustomUser.objects.filter(company=company, user_type='worker')
        data.append({
            'id': company.id,
            'name': company.name,
            'contractor': company.contractor,
            'code': company.code,
            'workers': workers
        })

    return render(request, 'admin/company_list.html', {'companies_data': data})

@staff_member_required
def delete_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company.delete()
    return redirect('admin_company_list')  # this should match your URL name
