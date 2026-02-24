from django.contrib import admin
from .models import EducationCard

@admin.register(EducationCard)
class EducationCardAdmin(admin.ModelAdmin):
    # This controls which columns show up in the list view
    list_display = ('title', 'row', 'col')
    # This adds a search bar to the admin
    search_fields = ('title', 'summary_text')
