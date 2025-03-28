from django.core.management.base import BaseCommand
from resources.models import ResourceCategory
from django.utils.text import slugify
import time

class Command(BaseCommand):
    help = '为没有slug的资源分类生成slug'

    def handle(self, *args, **options):
        categories = ResourceCategory.objects.all()
        updated_count = 0
        
        for category in categories:
            if not category.slug:
                base_slug = slugify(category.name)
                if base_slug == '':
                    base_slug = f"category-{category.id}"
                
                # 检查slug是否已存在
                if ResourceCategory.objects.filter(slug=base_slug).exists():
                    # 如果存在，添加时间戳确保唯一性
                    category.slug = f"{base_slug}-{int(time.time())}"
                else:
                    category.slug = base_slug
                
                category.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'已更新资源分类 "{category.name}" 的slug为: {category.slug}'))
        
        if updated_count == 0:
            self.stdout.write(self.style.SUCCESS('所有资源分类已有有效的slug，无需更新'))
        else:
            self.stdout.write(self.style.SUCCESS(f'共更新了 {updated_count} 个资源分类的slug')) 