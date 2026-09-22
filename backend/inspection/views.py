from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from inspection.models import Inspection, WaterwaySection
from inspection.rules import judge


def _can_write(user) -> bool:
    return user.groups.filter(name="inspector").exists()


def health(_request):
    from django.http import JsonResponse

    return JsonResponse({"status": "ok", "service": "nav-aid-inspection"})


@require_http_methods(["GET", "POST"])
def login_view(request):
    from django.contrib.auth import authenticate, login

    error = ""
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", ""),
        )
        if user is None:
            error = "用户名或密码错误"
        else:
            login(request, user)
            return redirect("list")
    return render(request, "login.html", {"error": error})


def logout_view(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect("login")


@login_required
def list_view(request):
    rows = Inspection.objects.all()
    sections = WaterwaySection.objects.all()
    current = request.GET.get("section", "").strip()
    active = ""
    if current == "untagged":
        rows = rows.filter(section__isnull=True)
        active = "untagged"
    elif current:
        try:
            section_id = int(current)
        except ValueError:
            section_id = None
        if section_id is not None:
            rows = rows.filter(section_id=section_id)
            active = str(section_id)
    return render(
        request,
        "list.html",
        {
            "rows": rows,
            "sections": sections,
            "active": active,
            "can_write": _can_write(request.user),
        },
    )


@login_required
def detail_view(request, pk):
    row = get_object_or_404(Inspection, pk=pk)
    return render(
        request,
        "detail.html",
        {"row": row, "sections": WaterwaySection.objects.all(), "error": ""},
    )


@login_required
@require_http_methods(["GET", "POST"])
def sections_view(request):
    error = ""
    if request.method == "POST":
        if not _can_write(request.user):
            return HttpResponseForbidden("仅持灯账号可维护水道区段")
        name = request.POST.get("name", "").strip()
        try:
            min_cd = float(request.POST.get("min_cd", ""))
        except (TypeError, ValueError):
            min_cd = None
        if not name or min_cd is None:
            error = "请填区段名称和标称亮度下限"
        elif WaterwaySection.objects.filter(name=name).exists():
            error = "区段名称已存在"
        else:
            WaterwaySection.objects.create(
                name=name, min_cd=min_cd, created_by=request.user.username
            )
            return redirect("sections")
    return render(
        request,
        "sections.html",
        {"sections": WaterwaySection.objects.all(), "error": error},
    )


@login_required
@require_http_methods(["POST"])
def tag_section_view(request, pk):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅持灯账号可贴水道区段")
    row = get_object_or_404(Inspection, pk=pk)
    sections = WaterwaySection.objects.all()
    try:
        section = sections.get(pk=int(request.POST.get("section_id", "")))
    except (TypeError, ValueError, WaterwaySection.DoesNotExist):
        return render(
            request,
            "detail.html",
            {"row": row, "sections": sections, "error": "请选择有效的区段"},
            status=400,
        )
    if row.measured_cd < section.min_cd:
        error = (
            f"实测光强 {row.measured_cd:g} 低于区段「{section.name}」的"
            f"标称亮度下限 {section.min_cd:g}，已拒绝贴标"
        )
        return render(
            request,
            "detail.html",
            {"row": row, "sections": sections, "error": error},
            status=400,
        )
    row.section = section
    row.save(update_fields=["section"])
    return redirect("detail", pk=row.pk)


@login_required
@require_http_methods(["GET", "POST"])
def create_view(request):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅巡检员可登记灯光巡检")
    error = ""
    if request.method == "POST":
        try:
            measured = float(request.POST["measured_cd"])
            required = float(request.POST["required_cd"])
            bearing = float(request.POST["bearing_error_deg"])
            code = request.POST["aid_code"].strip()
            if not code:
                raise ValueError("empty")
        except (KeyError, ValueError):
            error = "请填编号和三项数值"
        else:
            verdict, note = judge(measured, required, bearing)
            row = Inspection.objects.create(
                aid_code=code,
                measured_cd=measured,
                required_cd=required,
                bearing_error_deg=bearing,
                verdict=verdict,
                note=note,
                created_by=request.user.username,
            )
            return redirect("detail", pk=row.pk)
    return render(request, "form.html", {"error": error})
