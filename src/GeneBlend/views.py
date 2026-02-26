from django.shortcuts import render
from django.http import JsonResponse
from calculator.models import EducationCard, FunFact

def home(request):
    random_fact = FunFact.objects.order_by('?').first()

    return render(request, 'home.html', {'fact': random_fact})    

def education(request):
    return render(request, 'education.html')

def education_api(request):
    cards = EducationCard.objects.all()
    
    data = []
    for card in cards:
        data.append({
            "row": card.row,
            "col": card.col,
            "title": card.title,
            "text": card.text,
            "sections": card.sections,
            "tags": card.tags,
            "image": card.image_svg        })
    
    return JsonResponse(data, safe=False)

