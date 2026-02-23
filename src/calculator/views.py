from django.shortcuts import render

def calculator(request):
    return render(request, 'calculator/calculator.html')

def result(request):
    return render(request, 'result.html')
