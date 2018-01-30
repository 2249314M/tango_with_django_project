from django.shortcuts import render
from django.http import HttpResponse
#Import Category view
from rango.models import Category,Page
from rango.forms import CategoryForm, PageForm

def index(request):
    # Query database for a list of ALL categories currently stored
    # Order by number of likes in DESCENDING order
    # Retrieve top 5, and place list in context_dict dictionary

    category_list = Category.objects.order_by("-likes")[:5]
    page_list = Page.objects.order_by("-views")[:5]
    context_dict = {"categories": category_list,
                    "pages": page_list}

    # Render response and send it back
    return render(request, 'rango/index.html', context_dict)

def about(request):
    # Print if the method is GET or post
    print(request.method)
    # Print user name (if no one logged in prints AnonymousUser)
    print(request.user)
    return render(request, 'rango/about.html',{})

def show_category(request,category_name_slug):
    context_dict = {}

    try:
        # Use try-except, as .get() may raise DoesNotExist exception
        category = Category.objects.get(slug=category_name_slug)

        # Get associated pages. filter() returns a list of Page objects, or an empty list
        pages = Page.objects.filter(category=category)

        # Add results to context_dict under name pages
        context_dict["pages"] = pages

        # Add Category object from database to context_dict
        # This is to verify that the category exists
        context_dict["category"] = category

    except Category.DoesNotExist:
        # Don't do anything - template will display "no category" message
        context_dict["category"] = None
        context_dict["pages"] = None

    # Render and return response
    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form':form})

def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return show_category(request, category_name_slug)

        else:
            print(form.errors)

    context_dict = {'form':form, 'category':category}
    return render(request, 'rango/add_page.html', context_dict)
