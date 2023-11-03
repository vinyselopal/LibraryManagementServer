from django.urls import path

from .views import books
from .views import members

urlpatterns = [
    path("members", members.index, name="index"),
    path("members/<int:member_id>", members.crud_members),
    path(
        "members/<int:member_id>/outstanding_transactions",
        members.get_outstanding_transactions,
    ),
    path("members/<int:member_id>/issue_book", members.issue_book),
    path("members/<int:member_id>/return_book", members.return_book),
    path("members/<int:member_id>/charge_fee", members.charge_fee),
    path("books", books.index),
    path("books/<int:book_id>", books.crud_book),
]
