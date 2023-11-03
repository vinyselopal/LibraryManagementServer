from django.urls import path

from . import views

urlpatterns = [
    path("members", views.members_index, name="index"),
    path("members/<int:member_id>", views.crud_members),
    path(
        "members/<int:member_id>/outstanding_transactions",
        views.get_outstanding_transactions,
    ),
    path("members/<int:member_id>/issue_book", views.issue_book),
    path("members/<int:member_id>/return_book", views.return_book),
    path("members/<int:member_id>/charge_fee", views.charge_fee),
    path("books", views.books_index),
    path("books/<int:book_id>", views.crud_book),
]
