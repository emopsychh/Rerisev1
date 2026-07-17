from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.constants import STAGE_SLUGS
from apps.crm.selectors import build_kanban, get_owned_lead, serialize_lead
from apps.crm.serializers import LeadCreateSerializer, LeadUpdateSerializer
from apps.crm.services import LeadService
from core.responses import error_response, success_response


class LeadListCreateView(APIView):
    def get(self, request):
        stage = request.query_params.get("stage")
        if stage and stage not in STAGE_SLUGS:
            stage = None
        search = request.query_params.get("search")
        return success_response(build_kanban(request.user, stage, search))

    def post(self, request):
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            lead = LeadService.create_lead(request.user, serializer.validated_data)
        except LookupError as exc:
            return error_response(
                "NOT_FOUND",
                str(exc),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(serialize_lead(lead), status_code=status.HTTP_201_CREATED)


class LeadDetailView(APIView):
    def patch(self, request, lead_id: int):
        lead = get_owned_lead(request.user, lead_id)
        if not lead:
            return error_response(
                "NOT_FOUND",
                "Лид не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeadUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            lead = LeadService.update_lead(lead, request.user, serializer.validated_data)
        except LookupError as exc:
            return error_response(
                "NOT_FOUND",
                str(exc),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(serialize_lead(lead))

    def delete(self, request, lead_id: int):
        lead = get_owned_lead(request.user, lead_id)
        if not lead:
            return error_response(
                "NOT_FOUND",
                "Лид не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        LeadService.delete_lead(lead)
        return Response(status=status.HTTP_204_NO_CONTENT)
