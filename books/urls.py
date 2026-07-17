from django.urls import path
from . import views

urlspatterns = [
    path('',views.book_list, name='book_list'),
    path('book/<int:pk>/', views.book_detail,name ='book_detail'),
    path('book/add/', views.BookCreateView.as_view(), name='book_add'),
    path('book/<int:pk>/review', views.add_review, name ='add_review'),
]