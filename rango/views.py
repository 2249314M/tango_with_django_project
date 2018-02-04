from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from rango.models import Category,Page
from rango.forms import CategoryForm, PageForm, UserProfileForm, UserForm
from datetime import datetime

def index(request):
    # Query database for a list of ALL categories currently stored
    # Order by number of likes in DESCENDING order
    # Retrieve top 5, and place list in context_dict dictionary
    category_list = Category.objects.order_by("-likes")[:5]
    page_list = Page.objects.order_by("-views")[:5]
    context_dict = {"categories": category_list,
                    "pages": page_list}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    response = render(request, 'rango/index.html', context_dict)

    return response

def about(request):

    if request.session.test_cookie_worked():
        print('TEST COOKIE WORKED!')
        request.session.delete_test_cookie()

    visitor_cookie_handler(request)
    context_dict = {'visits':request.session['visits']}

    # Print if the method is GET or post
    print(request.method)
    # Print user name (if no one logged in prints AnonymousUser)
    print(request.user)
    return render(request, 'rango/about.html',context_dict)

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

def register(request):
    # Boolean to tell template if registration was successful
    registered = False

    # If HTTP POST, process form data
    if request.method == 'POST':
        # Grab info from raw form information
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If both forms are valid
        if user_form.is_valid() and profile_form.is_valid():
            # Save user's form data to database
            user = user_form.save()

            # Hash password then update user object
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            # If user provided profile picture, retrieve it from input form
            # and put in UserProfile model
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Save UserProfile instance
            profile.save()

            # Update variable to indicate successful registration
            registered = True
        else:
            # Either or both forms are invalid
            print(user_form.errors, profile_form.errors)

    else:
        # Not a HTTP POST so render form using two blank ModelForm instances
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Return template depending on context
    return render(request,
                    'rango/register.html',
                    {'user_form': user_form,
                    'profile_form': profile_form,
                    'registered': registered})

def user_login(request):

    # If HTTP POST, pull out relevant information
    if request.method == 'POST':
        # Get username and password
        username = request.POST.get('username')
        password = request.POST.get('password')

        # If username/password combo is correct, return a User object
        user = authenticate(username=username,password=password)

        # If we have User object, details are correct. If not, no user
        # with matching credentials was found
        if user:
            if user.is_active:
                # If user is valid and active, log in and send back to homepage
                login(request,user)
                return HttpResponseRedirect(reverse('index'))
            else:
                # Inactive account was used so don't log in
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details so don't log in
            print("Invalid login details: {0}, {1}".format(username,password))
            return render(request, 'rango/login.html', {'message': "Invalid login details supplied."})

    # If not HTTP POST display login form
    else:
        return render(request, 'rango/login.html', {})

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

@login_required
def user_logout(request):
    # Use login_requred to ensure user can only log out if logged in
    logout(request)
    return HttpResponseRedirect(reverse('index'))

# Helper method for visitor_cookie_handler
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    # Get number of visits to site. If cookie exists, cast return values
    # to an integer. If not, then use 1
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request,'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    # If it has been more than a day since the last visit
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        request.session['last_visit'] = str(datetime.now())
    else:
        visits = 1
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits
