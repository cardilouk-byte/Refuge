from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.views import role_required, staff_required

from .forms import DepartmentForm, StaffPositionForm
from .models import Department, StaffPosition


def _tree():
    departments = list(
        Department.objects.filter(is_active=True).prefetch_related("positions__user", "positions__teacher")
    )
    nodes = {d.pk: {"dept": d, "children": []} for d in departments}
    roots = []
    for d in departments:
        if d.parent_id and d.parent_id in nodes:
            nodes[d.parent_id]["children"].append(nodes[d.pk])
        else:
            roots.append(nodes[d.pk])
    return roots


@staff_required
def tree_view(request):
    return render(request, "departments/tree.html", {"roots": _tree()})


@role_required("SUPERADMIN", "DIRECTION")
def department_create(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Depatman an kreye.")
            return redirect("departments:tree")
    else:
        form = DepartmentForm()
    return render(request, "departments/department_form.html", {"form": form})


@role_required("SUPERADMIN", "DIRECTION")
def department_update(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, "Chanjman yo anrejistre.")
            return redirect("departments:tree")
    else:
        form = DepartmentForm(instance=dept)
    positions = dept.positions.select_related("user", "teacher")
    return render(
        request, "departments/department_form.html",
        {"form": form, "obj": dept, "positions": positions,
         "position_form": StaffPositionForm(initial={"department": dept})},
    )


@role_required("SUPERADMIN", "DIRECTION")
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        child_count = Department.objects.filter(parent=dept).count()
        if child_count:
            messages.error(request, f"Depatman an gen {child_count} sous-depatman. Deplase yo anvan.")
        else:
            dept.delete()
            messages.success(request, "Depatman an efase.")
    return redirect("departments:tree")


@role_required("SUPERADMIN", "DIRECTION")
def position_create(request):
    if request.method == "POST":
        form = StaffPositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Post la ajoute.")
            return redirect("departments:department_update", pk=form.instance.department_id)
    return redirect("departments:tree")


@role_required("SUPERADMIN", "DIRECTION")
def position_delete(request, pk):
    position = get_object_or_404(StaffPosition, pk=pk)
    dept_pk = position.department_id
    if request.method == "POST":
        position.delete()
        messages.success(request, "Post la retire.")
    return redirect("departments:department_update", pk=dept_pk)
