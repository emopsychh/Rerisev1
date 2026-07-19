from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.academy.models import Lesson


class Command(BaseCommand):
    help = (
        "Убирает битые video_url вида /media/... без файла на диске "
        "(старый сид создавал такие пути без загрузки)."
    )

    def handle(self, *args, **options):
        cleared = 0
        kept_file = 0
        for lesson in Lesson.objects.all().iterator():
            url = (lesson.video_url or "").strip()
            if lesson.video_file and lesson.video_file.name:
                # Синхронизируем отображаемую ссылку с реальным файлом.
                public = lesson.resolved_video_url
                if public and lesson.video_url != public:
                    Lesson.objects.filter(pk=lesson.pk).update(video_url=public)
                    kept_file += 1
                continue

            if not url.startswith("/media/"):
                continue

            relative = url[len("/media/") :].lstrip("/")
            full = Path(settings.MEDIA_ROOT) / relative
            if full.is_file():
                continue

            Lesson.objects.filter(pk=lesson.pk).update(video_url="")
            cleared += 1
            self.stdout.write(f"cleared lesson #{lesson.pk}: {url}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Cleared broken urls: {cleared}. Synced from files: {kept_file}."
            )
        )
