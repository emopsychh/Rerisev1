from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.views import APIView

from apps.content.access import is_safe_download_redirect
from apps.content.constants import CATEGORY_ALL, CATEGORY_FILTER_CHOICES
from apps.content.models import MaterialGroup
from apps.content.selectors import (
    build_chats_payload,
    build_home_payload,
    build_materials_catalog,
    get_material_file_for_user,
    get_material_group_for_user,
    serialize_material_group_detail,
)
from core.responses import error_response, success_response


class HomeView(APIView):
    def get(self, request):
        return success_response(build_home_payload(request.user))


class MaterialsCatalogView(APIView):
    def get(self, request):
        category = request.query_params.get("category", CATEGORY_ALL)
        if category not in CATEGORY_FILTER_CHOICES:
            category = CATEGORY_ALL
        search = request.query_params.get("search")
        return success_response(build_materials_catalog(request.user, category, search))


class MaterialGroupDetailView(APIView):
    def get(self, request, group_id: int):
        group = get_material_group_for_user(group_id, request.user)
        if group is None:
            exists = MaterialGroup.objects.filter(pk=group_id).exists()
            if exists:
                return error_response(
                    "FORBIDDEN",
                    "Нет доступа к этой группе материалов",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            return error_response(
                "NOT_FOUND",
                "Группа материалов не найдена",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(serialize_material_group_detail(group))


class MaterialFileDownloadView(APIView):
    def get(self, request, file_id: int):
        material_file = get_material_file_for_user(file_id, request.user)
        if material_file is None:
            from apps.content.models import MaterialFile

            exists = MaterialFile.objects.filter(pk=file_id).exists()
            if exists:
                return error_response(
                    "FORBIDDEN",
                    "Нет доступа к этому файлу",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            return error_response(
                "NOT_FOUND",
                "Файл не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not is_safe_download_redirect(material_file.file_url):
            return error_response(
                "INVALID_FILE_URL",
                "Некорректный URL файла",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return HttpResponseRedirect(material_file.file_url)


class ChatsView(APIView):
    def get(self, request):
        return success_response(build_chats_payload(request.user))
