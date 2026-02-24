from django.shortcuts import render

def calculator(request):
    return render(request, 'calculator/calculator.html')

def results(request):
    return render(request, 'calculator/results.html')
