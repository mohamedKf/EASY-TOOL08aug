from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
import json
from django.shortcuts import get_object_or_404
from accounts.forms import ScrewForm, DrywallBoardForm, MetalProfileForm, ProfileSetForm
from accounts.models import Screw, ProfileSet, MetalProfile, DrywallBoard, Order
from rest_framework.authtoken.models import Token


@csrf_exempt
def api_supplier_login(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JsonResponse({"status": "error", "message": "Username and password required"}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is not None and getattr(user, "user_type", None) == "supplier":
        login(request, user)  # ✅ set session cookie so subsequent calls are authenticated
        return JsonResponse({"status": "ok", "username": user.username, "user_type": user.user_type})
    return JsonResponse({"status": "error", "message": "Invalid credentials or not a supplier"}, status=401)
@csrf_exempt
@login_required
def api_add_screw(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        form = ScrewForm(data)
        if form.is_valid():
            screw = form.save(commit=False)
            screw.supplier = request.user
            screw.save()
            return JsonResponse({"status": "ok", "message": "Screw added successfully"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)

    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

@csrf_exempt
@login_required
def api_add_drywall_board(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        form = DrywallBoardForm(data)
        if form.is_valid():
            board = form.save(commit=False)
            board.supplier = request.user
            board.save()
            return JsonResponse({"status": "ok", "message": "Drywall board added"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

@csrf_exempt
@login_required
def api_add_metal_profile(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        form = MetalProfileForm(data)
        if form.is_valid():
            metal = form.save(commit=False)
            metal.supplier = request.user
            metal.save()
            return JsonResponse({"status": "ok", "message": "Metal profile added"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

@csrf_exempt
@login_required
def api_add_profile_set(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        form = ProfileSetForm(data)
        if form.is_valid():
            profile_set = form.save(commit=False)
            profile_set.supplier = request.user
            profile_set.save()
            return JsonResponse({"status": "ok", "message": "Profile set added"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

@csrf_exempt
@login_required
def api_edit_screw(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    screw = get_object_or_404(Screw, pk=pk, supplier=request.user)

    if request.method == "PUT":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        form = ScrewForm(data, instance=screw)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "ok", "message": "Screw updated"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)

    return JsonResponse({"status": "error", "message": "Only PUT allowed"}, status=405)


@csrf_exempt
@login_required
def api_delete_screw(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    screw = get_object_or_404(Screw, pk=pk, supplier=request.user)

    if request.method == "DELETE":
        screw.delete()
        return JsonResponse({"status": "ok", "message": "Screw deleted"})

    return JsonResponse({"status": "error", "message": "Only DELETE allowed"}, status=405)

# EDIT ProfileSet (PUT)
@csrf_exempt
@login_required
def api_edit_profile_set(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    profile = get_object_or_404(ProfileSet, pk=pk, supplier=request.user)

    if request.method != "PUT":
        return JsonResponse({"status": "error", "message": "Only PUT allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    form = ProfileSetForm(data, instance=profile)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": "ok", "message": "Profile set updated"})
    else:
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


# DELETE ProfileSet (DELETE)
@csrf_exempt
@login_required
def api_delete_profile_set(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    profile = get_object_or_404(ProfileSet, pk=pk, supplier=request.user)

    if request.method != "DELETE":
        return JsonResponse({"status": "error", "message": "Only DELETE allowed"}, status=405)

    profile.delete()
    return JsonResponse({"status": "ok", "message": "Profile set deleted"})

@csrf_exempt
@login_required
def api_edit_metal_profile(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    metal = get_object_or_404(MetalProfile, pk=pk, supplier=request.user)

    if request.method != "PUT":
        return JsonResponse({"status": "error", "message": "Only PUT allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    form = MetalProfileForm(data, instance=metal)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": "ok", "message": "Metal profile updated"})
    return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@csrf_exempt
@login_required
def api_delete_metal_profile(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    metal = get_object_or_404(MetalProfile, pk=pk, supplier=request.user)

    if request.method != "DELETE":
        return JsonResponse({"status": "error", "message": "Only DELETE allowed"}, status=405)

    metal.delete()
    return JsonResponse({"status": "ok", "message": "Metal profile deleted"})

@csrf_exempt
@login_required
def api_edit_drywall_board(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    board = get_object_or_404(DrywallBoard, pk=pk, supplier=request.user)

    if request.method != "PUT":
        return JsonResponse({"status": "error", "message": "Only PUT allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    form = DrywallBoardForm(data, instance=board)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": "ok", "message": "Drywall board updated"})
    return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@csrf_exempt
@login_required
def api_delete_drywall_board(request, pk):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    board = get_object_or_404(DrywallBoard, pk=pk, supplier=request.user)

    if request.method != "DELETE":
        return JsonResponse({"status": "error", "message": "Only DELETE allowed"}, status=405)

    board.delete()
    return JsonResponse({"status": "ok", "message": "Drywall board deleted"})

@csrf_exempt
@login_required
def api_supplier_inventory(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Only GET allowed"}, status=405)

    data = {
        "screws": list(Screw.objects.filter(supplier=request.user).values()),
        "profile_sets": list(ProfileSet.objects.filter(supplier=request.user).values()),
        "metal_profiles": list(MetalProfile.objects.filter(supplier=request.user).values()),
        "drywall_boards": list(DrywallBoard.objects.filter(supplier=request.user).values())
    }
    return JsonResponse({"status": "ok", "inventory": data})


@csrf_exempt
@login_required
def api_supplier_add_item(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    item_type = data.get("type")
    if item_type == "screw":
        form = ScrewForm(data)
    elif item_type == "profile_set":
        form = ProfileSetForm(data)
    elif item_type == "metal_profile":
        form = MetalProfileForm(data)
    elif item_type == "drywall_board":
        form = DrywallBoardForm(data)
    else:
        return JsonResponse({"status": "error", "message": "Unknown item type"}, status=400)

    if form.is_valid():
        obj = form.save(commit=False)
        obj.supplier = request.user
        obj.save()
        return JsonResponse({"status": "ok", "message": f"{item_type} added successfully"})
    else:
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)




@csrf_exempt
@login_required
def api_supplier_orders(request):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Only GET allowed"}, status=405)

    orders = Order.objects.filter(supplier=request.user).prefetch_related('items', 'company', 'contractor')

    data = []
    for order in orders:
        data.append({
            "id": order.id,
            "order_number": order.order_number,
            "contractor": order.contractor.username if order.contractor else None,
            "company": order.company.name if order.company else None,
            "status": order.status,
            "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
            "items": [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "unit_price": float(item.unit_price),
                    "quantity": item.quantity,
                    "total_price": float(item.total_price())
                }
                for item in order.items.all()
            ],
            "total_before_tax": float(order.total_before_tax()),
            "total_after_tax": float(order.total_after_tax())
        })

    return JsonResponse({"status": "ok", "orders": data})


@csrf_exempt
@login_required
def api_update_supplier_order(request, order_id):
    if request.user.user_type != 'supplier':
        return JsonResponse({"status": "error", "message": "Not authorized"}, status=403)

    order = get_object_or_404(Order, id=order_id, supplier=request.user)

    if request.method != "PUT":
        return JsonResponse({"status": "error", "message": "Only PUT allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    if "delivery_date" in data:
        order.delivery_date = data["delivery_date"]
    if "status" in data:
        order.status = data["status"]

    order.save()
    return JsonResponse({"status": "ok", "message": "Order updated"})




@csrf_exempt
def api_supplier_token_login(request):
    if request.method != "POST":
        return JsonResponse({"status":"error","message":"POST required"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status":"error","message":"Invalid JSON"}, status=400)

    user = authenticate(username=data.get("username"), password=data.get("password"))
    if not user or getattr(user, "user_type", None) != "supplier":
        return JsonResponse({"status":"error","message":"Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return JsonResponse({"status":"ok","token":token.key,"username":user.username,"user_type":"supplier"})

@csrf_exempt
def api_supplier_token_logout(request):
    if request.method != "POST":
        return JsonResponse({"status":"error","message":"POST required"}, status=405)
    try:
        token_key = json.loads(request.body.decode("utf-8")).get("token")
    except json.JSONDecodeError:
        return JsonResponse({"status":"error","message":"Invalid JSON"}, status=400)
    if not token_key:
        return JsonResponse({"status":"error","message":"Token required"}, status=400)

    from rest_framework.authtoken.models import Token
    try:
        Token.objects.get(key=token_key).delete()
        return JsonResponse({"status":"ok","message":"Logged out"})
    except Token.DoesNotExist:
        return JsonResponse({"status":"error","message":"Invalid token"}, status=401)