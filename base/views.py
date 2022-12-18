from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from .models import Room, Topic, Message
from .form import RoomForm


# Create your views here.
def loginPage(request):
    # trying to login twice
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'user does not exist')
            return render(request, 'base/login_register.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'password is not correct')

    page = 'login'
    return render(request, 'base/login_register.html', {'page': page})


def registerPage(request):
    page = 'register'
    form = UserCreationForm()

    # can not register in case logged in
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Registeration')

    context = {'page': page, 'form': form}
    return render(request, 'base/login_register.html', context)


def logoutPage(request):
    logout(request)
    return redirect('home')


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(host__username__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    total_messages = Message.objects.filter(Q(body__icontains=q) | Q(
        user__username__icontains=q) | Q(room__name__icontains=q))
    topics = Topic.objects.all()

    context = {'rooms': rooms, 'topics': topics,
               'rooms_count': rooms.count, 'total_messages': total_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    # get all children models(message) of model # see the relation
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body'),
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = Room.objects.filter(host__username=user.username)
    total_messages = Message.objects.filter(user__username=user.username)
    topics = Topic.objects.all()

    context = {'rooms': rooms, 'topics': topics,
               'total_messages': total_messages, 'user': user}
    return render(request, 'base/user_profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')

    form = RoomForm()
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)

    # host is the only one can update the room
    if request.user != room.host:
        return HttpResponse('You have not a permission')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')

    form = RoomForm(instance=room)
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    # host is the only one can delete the room
    if request.user != room.host:
        return HttpResponse('You have not a permission')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    context = {'obj': room}
    return render(request, 'base/delete.html', context)


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    # host is the only one can delete the room
    if request.user != message.user:
        return HttpResponse('You have not a permission')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=message.room.id)

    context = {'obj': message}
    return render(request, 'base/delete.html', context)
