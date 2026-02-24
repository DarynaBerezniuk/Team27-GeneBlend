from django.shortcuts import render
from django.http import JsonResponse
from calculator.models import EducationCard

def home(request):
    return render(request, 'home.html')

def education(request):
    return render(request, 'education.html')

def education_api(request):
    # Fetch all records from the database
    cards = EducationCard.objects.all()
    
    data = []
    for card in cards:
        data.append({
            "row": card.row,
            "col": card.col,
            "title": card.title,
            "text": card.text,  # This matches the 'text' key in your JS
            "sections": card.sections,  # JSONField is automatically handled
            "tags": card.tags,          # JSONField is automatically handled
            "image": card.image_svg     # This matches the 'image' key in your JS
        })
    
    # Return the data as JSON so education.js can read it
    return JsonResponse(data, safe=False)

def result(request):
    return render(request, 'results.html')
