from django.contrib import messages
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.views import teaching_staff_required as staff_required

from .models import MediaFile
from .services import IMAGE_FORMATS, compress_image, image_dimensions


@staff_required
def index(request):
    category = request.GET.get("categorie", "")
    files = MediaFile.objects.all()
    if category:
        files = files.filter(category=category)
    return render(request, "media_library/index.html", {
        "files": files,
        "categories": MediaFile.Category.choices,
        "current_category": category,
    })


@staff_required
def upload(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        category = request.POST.get("category", MediaFile.Category.AUTRES)
        count = 0
        for uploaded in request.FILES.getlist("files"):
            extension = uploaded.name.rsplit(".", 1)[-1].lower()
            content = uploaded.read()
            size = len(content)
            width, height = 0, 0
            if extension in IMAGE_FORMATS:
                uploaded.seek(0)
                try:
                    buffer, size = compress_image(uploaded)
                    extension = "jpg"
                    buffer.seek(0)
                    width, height = image_dimensions(buffer)
                    buffer.seek(0)
                except Exception:
                    uploaded.seek(0)
                    buffer = uploaded
            else:
                from io import BytesIO
                buffer = BytesIO(content)
            name = uploaded.name.rsplit(".", 1)[0] + ".jpg" if extension in IMAGE_FORMATS else uploaded.name
            media = MediaFile(
                original_name=uploaded.name, category=category,
                width=width, height=height, size_bytes=size, uploaded_by=request.user,
            )
            media.file.save(name, ContentFile(buffer.read()), save=True)
            count += 1
        messages.success(request, f"{count} fichier(s) ajouté(s) à la bibliothèque.")
    return redirect("media_library:index")


@staff_required
@require_POST
def delete(request, pk):
    media = get_object_or_404(MediaFile, pk=pk)
    media.file.delete(save=False)
    media.delete()
    messages.success(request, "Fichier supprimé.")
    return redirect("media_library:index")
