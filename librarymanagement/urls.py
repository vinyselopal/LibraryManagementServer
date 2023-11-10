from django.urls import path

from . import views

urlpatterns = [
    path("members", views.members_index, name="index"),
    path("members/<int:member_id>", views.crud_members),
    path("members/issue_book", views.issue_book),
    path("transactions/<int:transaction_id>/return_book", views.return_book),
    path("transactions/<int:transaction_id>/charge_fee", views.charge_fee),
    path("books", views.books_index),
    path("books/<int:book_id>", views.crud_book),
    path("books/import_books", views.import_books),
    path("transactions", views.get_transactions),
]
