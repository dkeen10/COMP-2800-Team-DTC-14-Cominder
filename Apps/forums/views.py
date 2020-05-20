from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from Apps.users.models import *
from datetime import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import FormMixin
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .forms import *
try:
    from django.utils import simplejson as json
except ImportError:
    import json

# Create your views here.


def forums(request):
    # posts = Post.objects.all()
    preferences = Profile.objects.get(user=request.user)
    forums = SubForum.objects.filter(category__profile__user=request.user)
    posts = Post.objects.filter(sub_forum__in=forums)

    context = {
        'forums': forums,
        'posts': posts,
        'preferences': preferences,
    }
    return render(request, 'forums/main.html', context)


@require_POST
def like(request):
    post, message = '', ''
    if request.method == 'POST':
        user = request.user
        slug = request.POST.get('slug', None)
        post = get_object_or_404(Post, pk=slug)

        if post.likes.filter(id=user.id).exists():
            post.likes.remove(user)
        else:
            post.likes.add(user)
    context = {
        'likes': post.total_likes(),
    }
    return HttpResponse(json.dumps(context), content_type='application/json')


@require_POST
def comment_like(request):
    comment, message = '', ''
    if request.method == 'POST':
        user = request.user
        slug = request.POST.get('slug', None)
        comment = get_object_or_404(Comment, pk=slug)

        if comment.likes.filter(id=user.id).exists():
            comment.likes.remove(user)
            message = "Like"
        else:
            comment.likes.add(user)
            message = "Dislike"
    context = {
        'likes': comment.total_likes(),
        'message': message,
    }
    return HttpResponse(json.dumps(context), content_type='application/json')


class PostList(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'forums/main.html'


class SubforumPostsList(ListView):
    model = Post
    paginate_by = 10
    context_object_name = 'posts'
    template_name = 'forums/subforum_main.html'

    def get_queryset(self, *args, **kwargs):
        return Post.objects.filter(Q(sub_forum__pk=self.kwargs['pk']))


def create_comment_object(request, cleaned_response, post_pk):
    comment_created = Comment.objects.create(posted_by=request.user, message=cleaned_response['message'], on_post_id=post_pk)
    comment_created.save()
    return comment_created


def post_detail_view(request, pk):      # post pk
    comment_created = None
    post_instance = Post.objects.get(pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form = form.cleaned_data
            comment_created = create_comment_object(request, form, pk)
    form = CommentForm()
    comment_instances = Comment.objects.filter(on_post_id=pk)
    return_list = []
    for comment in comment_instances:

        return_list.append((comment, comment.likes.filter(id=request.user.id).exists()))
    context = {
        'form': form,
        'comments': return_list,
        'object': post_instance,
        'user': request.user
    }
    return render(request, 'forums/post_detail.html', context)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    success_url = '/task-tracker/home'
    fields = ['title', 'description', 'sub_forum']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return True


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/forums/'

    def test_func(self):
        return True
