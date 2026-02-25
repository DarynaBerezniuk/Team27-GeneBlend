from django.shortcuts import render, redirect
from .genetics_calculator import GeneticCalculator

def calculator(request):
    return render(request, 'calculator/calculator.html')

def results(request):
    if request.method == 'POST':
        calc = GeneticCalculator()
        raw_results = calc.calculate(request.POST)
        
        labels = {
            "eye_color": "Колір очей", "hair_color": "Колір волосся",
            "hair_type": "Тип волосся", "blood": "Група крові",
            "rh": "Резус-фактор", "height": "Ріст",
            "dimples": "Ямочки", "freckles": "Веснянки"
        }

        translations = {
            "brown": "Карі", "blue": "Блакитні", "green": "Зелені",
            "dark": "Темне", "blonde": "Світле", "red": "Руде",
            "curly": "Кучеряве", "wavy": "Хвилясте", "straight": "Пряме",
            "pos": "Rh+", "neg": "Rh-",
            "tall": "Високий (180+)", "medium": "Середній (165-179)", "short": "Низький (до 164)",
            "yes": "Є", "no": "Немає"
        }
        
        formatted_results = []
        for key, phenotypes in raw_results.items():
            p_list = [
                {
                    'name': translations.get(p_name, p_name),
                    'probability': float(p_val)
                } for p_name, p_val in phenotypes.items()
            ]
            
            # ONLY add to the list if the user actually provided data for this trait
            if len(p_list) > 0:
                formatted_results.append({
                    'title': labels.get(key, key),
                    'phenotypes': p_list,
                    'is_skipped': False
                })

        # If the user sent a completely empty form, formatted_results will be []
        # We store it anyway; the template will handle the empty list.
        request.session['genetics_results'] = formatted_results
        return redirect('results')

    results_to_display = request.session.pop('genetics_results', None)
    return render(request, 'calculator/results.html', {'results': results_to_display})
