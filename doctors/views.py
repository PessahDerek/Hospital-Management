from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Q
from django.urls import reverse
from django.core.files.storage import default_storage

from patients.models import Appointment, Status
from .models import Blogs, Comments, Category
from users.models import Doctors, Specialty

User = get_user_model()

@login_required(login_url='/login')
def doctor_dashboard(request):
  return render(request,'doctors/doctor_dashboard.html')

@login_required(login_url='/login')
def profile(request):
    specialities = Specialty.objects.all()
    updated_profile_successfully  = False
    updated_password_successfully = False
    base_template = 'patients/base.html'
    if request.user.is_doctor:
      base_template = 'doctors/base.html'
    
    if request.method == 'POST':
      if 'update_profile' in request.POST:
        user = request.user
        user.first_name = request.POST.get('user_firstname')
        user.last_name = request.POST.get('user_lastname')
        user.gender = request.POST.get('user_gender')
        user.birthday = request.POST.get('birthday')
        user.id_address.address_line = request.POST.get('address_line')
        user.id_address.region = request.POST.get('region')
        user.id_address.city = request.POST.get('city')
        user.id_address.code_postal = request.POST.get('code_postal')
        
        if(user.is_doctor):
          specialty = request.POST.get('Speciality')
          specialty_name = Specialty.objects.get(name=specialty)

          doctor_profile = user.doctors
          doctor_profile.specialty = specialty_name
          doctor_profile.bio = request.POST.get('bio')
          doctor_profile.save()
        else:
          patient_profile = user.patients
          patient_profile.insurance = request.POST.get('insurance')
          patient_profile.save()



        if 'profile_pic' in request.FILES:
          user.profile_avatar = request.FILES['profile_pic']

        user.save()
        updated_profile_successfully  = True
        
      elif 'update_password' in request.POST:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        if not request.user.check_password(current_password):
          messages.error(request, 'Incorrect password. Please try again.')
        elif new_password != confirm_new_password:
          messages.error(request, 'New passwords do not match. Please try again.')
        elif len(new_password) < 6:
          messages.error(request, 'New password must be at least 6 characters long.')
        else:
          request.user.set_password(new_password)
          request.user.save()
          update_session_auth_hash(request, request.user) 
          updated_password_successfully = True

    curruser = request.user.username
    data = User.objects.get(username=curruser)
    return render(request, 'doctors/profile.html', context={
            "basicdata": data,
            "updated_profile_successfully": updated_profile_successfully,
            "updated_password_successfully": updated_password_successfully,
            'base_template': base_template,
            "specialities":specialities
        })
    

@login_required(login_url='/login')
def doctor_blogs(request): 
  base_template = 'patients/base.html'
  if request.user.is_doctor:
    base_template = 'doctors/base.html'   
    
  blogs = Blogs.objects.filter(is_published=True).order_by('-posted_at')
  categories = Category.objects.all()

  paginator = Paginator(blogs, 5)
  page = request.GET.get('page')
  blogs_page = paginator.get_page(page)

  context = {
      'blogs': blogs_page,
      'categories': categories,
      'base_template': base_template,
  }

  return render(request, 'doctors/doctor_blogs.html', context)

@login_required(login_url='/login')
def search_blogs(request):
  base_template = 'patients/base.html'
  if request.user.is_doctor:
    base_template = 'doctors/base.html'
    
  if request.method == 'GET':
    keyword = request.GET.get('keyword')
    
    blogs = Blogs.objects.filter(title__icontains=keyword, is_published=True).order_by('-posted_at')
    categories = Category.objects.all()

    paginator = Paginator(blogs, 5)
    page = request.GET.get('page')
    blogs_page = paginator.get_page(page)

    context = {
        'blogs': blogs_page,
        'categories': categories,
        'searching': 1,
        'keyword': keyword,
        'base_template': base_template,
    }

    return render(request, 'doctors/doctor_blogs.html', context)


def blogs_category(request, cat):
  base_template = 'patients/base.html'
  if request.user.is_doctor:
    base_template = 'doctors/base.html'
    
  category = Category.objects.get(name=cat)

  blogs = Blogs.objects.filter(id_category=category, is_published=True).order_by('-posted_at')
  categories = Category.objects.all()

  paginator = Paginator(blogs, 5)
  page = request.GET.get('page')
  blogs_page = paginator.get_page(page)

  context = {
      'blogs': blogs_page,
      'categories': categories,
      'base_template': base_template,
  }

  return render(request, 'doctors/doctor_blogs.html', context)


@login_required(login_url='/login')
def upload_blog(request, blog_id=None):
    if blog_id:
        blog = get_object_or_404(Blogs, pk=blog_id)
    else:
        blog = Blogs()

    if request.method == 'POST':
        title = request.POST.get('assign_title') 
        category_name = request.POST.get('assign_class')
        category = Category.objects.get(name=category_name)
        new_image = request.FILES.get('assignupload')
        description = request.POST.get('assign_desc')
        summary = request.POST.get('assign_des')

        is_published = request.POST.get('upload_blog') == 'Submit'

        user = request.user 
        author = get_object_or_404(Doctors, user=user)

        if new_image:
          if blog.thumbnail:
              default_storage.delete(blog.thumbnail.name)
          
          blog.thumbnail = new_image

        blog.title = title
        blog.doctor = author
        blog.id_category = category
        blog.description = description
        blog.summary = summary
        blog.is_published = is_published
        blog.posted_at = datetime.now()

        blog.save()

        if is_published:
            messages.success(request, 'Blog successfully published!')
        else:
            messages.success(request, 'Blog saved as draft.')

        return redirect('upload_blog') 

    total_categories = Category.objects.all()

    context = {
        'user_name': request.user.username,
        'total_categories': total_categories,
        'blog': blog,
    }

    return render(request, 'doctors/upload_blog.html', context)


@login_required(login_url='/login')
def view_blog(request, blog_id):
    base_template = 'patients/base.html'
    if request.user.is_doctor:
      base_template = 'doctors/base.html'
    
    blog = get_object_or_404(Blogs, blog_id=blog_id)

    related_blogs = Blogs.objects.filter(id_category=blog.id_category, is_published=True).exclude(blog_id=blog_id).order_by('-posted_at')[:3]
    recent_blogs = Blogs.objects.filter(~Q(blog_id=blog_id), is_published=True).order_by('-posted_at')[:5]
    categories = Category.objects.all()
    comments = Comments.objects.filter(blog=blog)

    context = {
        'related_blogs': related_blogs,
        'recent_blogs': recent_blogs,
        'blog': blog,
        'categories': categories,
        'comments': comments,
        'base_template': base_template,
    }

    return render(request, 'doctors/view_blog.html', context)

@login_required(login_url='/login')
def post_comment(request):
  if request.method == 'POST':
    comment_content = request.POST.get('comment')
    blog_id = request.POST.get('id')
    blog = Blogs.objects.get(blog_id=blog_id)
    user = request.user

    comment = Comments(content=comment_content, commented_at=datetime.now(), user=user, blog=blog)
    comment.save()

    return redirect(reverse('blog', args=[int(blog_id)]))


@login_required(login_url='/login')
def doctor_myblogs(request):

  user = request.user
  author = get_object_or_404(Doctors, user=user)
  
  blogs = Blogs.objects.filter(doctor=author).order_by('-posted_at')
  categories = Category.objects.all()

  paginator = Paginator(blogs, 5)
  page = request.GET.get('page')
  blogs_page = paginator.get_page(page)

  context = {
      'blogs': blogs_page,
      'categories': categories,
      'base_template': 'doctors/base.html'
  }

  return render(request, 'doctors/doctor_blogs.html', context)


@login_required(login_url='/login')
def doctor_drafts(request):
    user = request.user
    author = get_object_or_404(Doctors, user=user)

    drafts = Blogs.objects.filter(doctor=author, is_published=False).order_by('-posted_at')
    categories = Category.objects.all()

    paginator = Paginator(drafts, 5)
    page = request.GET.get('page')
    drafts_page = paginator.get_page(page)

    context = {
        'drafts': drafts_page,
        'categories': categories,
    }

    return render(request, 'doctors/doctor_drafts.html', context)


@login_required(login_url='/login')
def view_appointments(request):
  if request.method == 'POST':
    status = request.POST.get("status")
    app_id = request.POST.get("app")
    
    print("status:"+status)    
    print("app_id:"+app_id)   
    
    app = Appointment.objects.get(id=app_id)
    status_id = Status.objects.get(status=status)
    app.status = status_id

    app.save()
  app = Appointment.objects.filter(doctor__user = request.user)
  return render(request,"doctors/viewappointments.html",{'appointments':app})
    

