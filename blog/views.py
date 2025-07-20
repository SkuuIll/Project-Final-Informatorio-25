from django.shortcuts import render

def custom_404(request, exception):
    return render(request, "404.html", status=404)

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")

def collaborate(request):
    return render(request, "collaborate.html")

def privacy(request):
    return render(request, "privacy.html")

def terms(request):
    return render(request, "terms.html")

def cookies(request):
    return render(request, "cookies.html")
