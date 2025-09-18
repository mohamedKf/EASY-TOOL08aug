from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views, admin_views, api_views
from . import supplier_views

urlpatterns = [
    path('home/', views.home_page, name='home'),
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("reset-password/", views.reset_password, name="reset_password"),

    path('contractor/', views.contractor_page, name='contractor_page'),
    path('contractor/project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('worker/', views.worker_page, name='worker_page'),


    path('clock-in/', views.clock_in_view, name='clock_in'),
    path('clock-out/', views.clock_out_view, name='clock_out'),

    path('send-message/', views.send_message_view, name='send_message'),
    path('inbox/', views.inbox_view, name='inbox'),

    path('inbox/', views.inbox_view, name='inbox'),
    path('send/', views.send_message_view, name='send_message'),
    path('reply/<int:message_id>/', views.reply_message_view, name='reply_message'),
    path('delete/<int:message_id>/', views.delete_message_view, name='delete_message'),

    path('messages/sent/', views.sent_messages_view, name='sent_messages'),

    path('contractor/create_project/', views.create_project_view, name='create_project'),

    path('contractor/', views.contractor_page, name='contractor_page'),
    path('contractor/project/<int:project_id>/', views.project_detail, name='project_detail'),

    path('projects/<int:project_id>/add-aluminum/', views.add_aluminum_item, name='add_aluminum_item'),

    path('pricing/', views.pricing_view, name='pricing'),

    path('create-company/', views.create_company_view, name='create_company'),

    # urls.py
    path('superadmin/companies/', admin_views.company_list_view, name='admin_company_list'),
    path('superadmin/companies/delete/<int:company_id>/', admin_views.delete_company, name='delete_company'),

    path('my-reports/', views.my_reports_view, name='my_reports'),

    path('contractor/worker-log/', views.contractor_worker_log_view, name='contractor_worker_log'),

    path('worker/company/', views.worker_company_view, name='worker_company'),
    path('contractor/company/', views.contractor_company_view, name='contractor_company'),

    path('projects/', views.project_list_view, name='project_list_view'),

    path('projects/<int:project_id>/add-drywall-room/', views.add_drywall_room, name='add_drywall_room'),
    path('materials/', views.materials_page, name='materials_page'),
    path('projects/all/', views.project_list_view, name='all_projects_nested'),

    path('worker/work/', views.worker_work_page, name='worker_work_page'),
    path('export/drywall/<int:project_id>/', views.export_drywall_materials_pdf, name='export_drywall_materials_pdf'),
    path('export/aluminum/<int:project_id>/', views.export_aluminum_materials_pdf, name='export_aluminum_materials_pdf'),
    path('export/glass/<int:project_id>/', views.export_glass_materials_pdf, name='export_glass_materials_pdf'),
    path('export/worker-log/<int:worker_id>/', views.export_worker_log_pdf, name='export_worker_log_pdf'),
    path('contractor/worker/<int:worker_id>/update-wage/', views.update_worker_wage, name='update_worker_wage'),
    path('supplier/add-screw/', views.add_screw, name='add_screw'),
    path('supplier/add-profile-set/', views.add_profile_set, name='add_profile_set'),
    path('supplier/add-metal-profile/', views.add_metal_profile, name='add_metal_profile'),
    path('supplier/add-drywall-board/', views.add_drywall_board, name='add_drywall_board'),

    path('supplier/add-items/', views.supplier_add_items, name='supplier_add_items'),
    path('supplier/', views.supplier_home_view, name='supplier_home'),
# Screw
    path('supplier/screw/edit/<int:pk>/', views.edit_screw, name='edit_screw'),
    path('supplier/screw/delete/<int:pk>/', views.delete_screw, name='delete_screw'),

    # Profile Set
    path('supplier/profile/edit/<int:pk>/', views.edit_profile_set, name='edit_profile_set'),
    path('supplier/profile/delete/<int:pk>/', views.delete_profile_set, name='delete_profile_set'),

    # Metal
    path('supplier/metal/edit/<int:pk>/', views.edit_metal_profile, name='edit_metal_profile'),
    path('supplier/metal/delete/<int:pk>/', views.delete_metal_profile, name='delete_metal_profile'),

    # Drywall
    path('supplier/board/edit/<int:pk>/', views.edit_drywall_board, name='edit_drywall_board'),
    path('supplier/board/delete/<int:pk>/', views.delete_drywall_board, name='delete_drywall_board'),

    # Contractor supplier material view
    path('contractor/suppliers/', views.supplier_list_view, name='supplier_list'),
    path('contractor/supplier/<int:supplier_id>/inventory/', views.supplier_inventory_view, name='supplier_inventory'),


    path('supplier/orders/', views.supplier_orders_view, name='supplier_orders'),
    path('supplier/update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('contractor/orders/', views.contractor_orders_view, name='contractor_orders'),

    path('contractor/export-orders-pdf/', views.export_order_pdf_view, name='export_orders_pdf'),
    path('contractor/export-orders-pdf/<int:order_id>/', views.export_order_pdf_view, name='export_orders_pdf'),


    #api urls*****

    path('api/worker-signup/', api_views.worker_signup_api, name='worker_signup_api'),
    path('api/worker-login/', api_views.worker_login_api, name='worker_login_api'),
    path('api/worker-logout/', api_views.worker_logout_api, name='worker_logout_api'),
    path('api/worker-clock-in/', api_views.clock_in_api, name='worker_clock_in_api'),
    path('api/worker-clock-out/', api_views.clock_out_api, name='worker_clock_out_api'),
    path('api/messages/send/', api_views.send_message_api, name='send_message_api'),
    path('api/messages/inbox/', api_views.inbox_api, name='inbox_api'),
    path('api/messages/<int:message_id>/reply/', api_views.reply_message_api, name='reply_message_api'),
    path('api/messages/<int:message_id>/delete/', api_views.delete_message_api, name='delete_message_api'),
    path('api/messages/sent/', api_views.sent_messages_api, name='sent_messages_api'),
    path('api/worker/work-page/', api_views.worker_work_page_api, name='worker_work_page_api'),
    path('api/worker-home/', api_views.worker_home_api, name='worker_home_api'),

    #supplier api urls*****
    path('api/supplier/login/',supplier_views.api_supplier_login, name='api_supplier_login'),
    path('api/supplier/add-screw/',supplier_views.api_add_screw, name='api_add_screw'),
    path('api/supplier/add-metal-profile/', supplier_views.api_add_metal_profile, name='api_add_metal_profile'),
    path('api/supplier/add-drywall-board/', supplier_views.api_add_drywall_board, name='api_add_drywall_board'),
    path('api/supplier/add-profile-set/', supplier_views.api_add_profile_set, name='api_add_profile_set'),

    path('api/supplier/profile-set/<int:pk>/edit/', supplier_views.api_edit_profile_set, name='api_edit_profile_set'),
    path('api/supplier/profile-set/<int:pk>/delete/', supplier_views.api_delete_profile_set,name='api_delete_profile_set'),

    path('api/supplier/metal-profile/<int:pk>/edit/', supplier_views.api_edit_metal_profile,name='api_edit_metal_profile'),
    path('api/supplier/metal-profile/<int:pk>/delete/', supplier_views.api_delete_metal_profile,name='api_delete_metal_profile'),

    path('api/supplier/drywall-board/<int:pk>/edit/', supplier_views.api_edit_drywall_board, name='api_edit_drywall_board'),
    path('api/supplier/drywall-board/<int:pk>/delete/', supplier_views.api_delete_drywall_board, name='api_delete_drywall_board'),

    path('api/supplier/inventory/', supplier_views.api_supplier_inventory, name='api_supplier_inventory'),
    path('api/supplier/add-item/', supplier_views.api_supplier_add_item, name='api_supplier_add_item'),

    path('api/supplier/orders/', supplier_views.api_supplier_orders, name='api_supplier_orders'),
    path('api/supplier/orders/<int:order_id>/update/', supplier_views.api_update_supplier_order, name='api_update_supplier_order'),
    path('api/supplier/orders/', supplier_views.api_supplier_orders, name='api_supplier_orders'),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/supplier/token-login/", supplier_views.api_supplier_token_login, name="api_supplier_token_login"),
    path("api/supplier/token-logout/", supplier_views.api_supplier_token_logout, name="api_supplier_token_logout"),

    # Inventory – ADD
    path("api/supplier/inventory/screws/add/",          supplier_views.api_add_screw, name="api_add_screw"),
    path("api/supplier/inventory/profile-sets/add/",    supplier_views.api_add_profile_set, name="api_add_profile_set"),
    path("api/supplier/inventory/metal-profiles/add/",  supplier_views.api_add_metal_profile, name="api_add_metal_profile"),
    path("api/supplier/inventory/drywall-boards/add/",  supplier_views.api_add_drywall_board, name="api_add_drywall_board"),

    # Inventory – EDIT
    path("api/supplier/inventory/screws/<int:pk>/edit/",         supplier_views.api_edit_screw,name="api_edit_screw"),
    path("api/supplier/inventory/profile-sets/<int:pk>/edit/",   supplier_views.api_edit_profile_set, name="api_edit_profile_set"),
    path("api/supplier/inventory/metal-profiles/<int:pk>/edit/", supplier_views.api_edit_metal_profile,name="api_edit_metal_profile"),
    path("api/supplier/inventory/drywall-boards/<int:pk>/edit/", supplier_views.api_edit_drywall_board,name="api_edit_drywall_board"),

    # Inventory – DELETE
    path("api/supplier/inventory/screws/<int:pk>/delete/",         supplier_views.api_delete_screw, name="api_delete_screw"),
    path("api/supplier/inventory/profile-sets/<int:pk>/delete/",   supplier_views.api_delete_profile_set, name="api_delete_profile_set"),
    path("api/supplier/inventory/metal-profiles/<int:pk>/delete/", supplier_views.api_delete_metal_profile,name="api_delete_metal_profile"),
    path("api/supplier/inventory/drywall-boards/<int:pk>/delete/", supplier_views.api_delete_drywall_board,name="api_delete_drywall_board"),



    # Your existing export URLs (keep these as they are)
    path('project/<int:project_id>/export-aluminum/', views.export_aluminum_materials_pdf,
         name='export_aluminum_materials_pdf'),
    path('project/<int:project_id>/export-glass/', views.export_glass_materials_pdf, name='export_glass_materials_pdf'),
    path('project/<int:project_id>/export-drywall/', views.export_drywall_materials_pdf,
         name='export_drywall_materials_pdf'),
]


