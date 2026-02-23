from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def education(request):
    return render(request, 'education.html')

def result(request):
    return render(request, 'results.html')
