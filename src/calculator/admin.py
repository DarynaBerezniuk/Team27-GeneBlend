from django.contrib import admin
from .models import EducationCard, FunFact

@admin.register(EducationCard)
class EducationCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'row', 'col')
    search_fields = ('title', 'summary_text')

@admin.register(FunFact)
class FunFactAdmin(admin.ModelAdmin):
    id_display = 'id'
    text_display = 'fact'
