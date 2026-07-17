from apps.content.models import MaterialFile, MaterialGroup


class MaterialCatalogService:
    @staticmethod
    def refresh_group_file_count(group: MaterialGroup) -> MaterialGroup:
        group.file_count = MaterialFile.objects.filter(group=group).count()
        group.save(update_fields=["file_count", "updated_at"])
        return group
