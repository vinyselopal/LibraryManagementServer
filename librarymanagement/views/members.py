from django.http import HttpResponse, JsonResponse
from ..models import Member, Transaction

from django.db.models import F, ExpressionWrapper, fields
from django.utils import timezone
from django.db.models import Sum


def index(request):
    members = Member.objects.all()
    JsonResponse({"message": members, "status": 200})


def crud_members(request, member_id=None):
    if request.method == "GET":
        member = Member.objects.filter(id=member_id)
        JsonResponse({"message": member, "status": 200})

    if request.method == "POST":
        email = request.email
        response = Member.objects.create(email=email)
        JsonResponse({"message": response, "status": 201})

    if request.method == "PUT":
        new_member = request.new_member
        response = Member.objects.get(id=member_id).update(email=new_member.email)
        JsonResponse({"message": response, "status": 204})

    if request.method == "DELETE":
        response = Member.objects.get(id=member_id).delete()
        JsonResponse({"message": response, "status": 204})


def get_outstanding_transactions(request, member_id):
    response = Transaction.objects.filter(member_id=member_id, return_date=None)
    JsonResponse({"message": response, "status": 200})


def issue_book(request, member_id):
    book_id = request.book_id
    issue_date = request.issue_date

    outstanding_debt = (
        Transaction.objects.filter(member_id=member_id, payment_done=False)
        .annotate(
            transaction_fee=ExpressionWrapper(
                (F("return_date") - F("issue_date")) * F("book__rent")
            )
            if F("return_date") != None
            else ExpressionWrapper((timezone.now() - F("issue_date")) * F("book__rent"))
        )
        .aggregate(debt=Sum("transaction_fee"))["debt"]
    )

    if outstanding_debt > 500:
        JsonResponse({"message": "Outstanding debt overflow", "status": 409})

    else:
        response = Transaction.objects.create(
            member_id=member_id, book_id=book_id, issue_date=issue_date
        )
        JsonResponse({"message": response, "status": 201})


def return_book(request, member_id):
    book_id = request.book_id
    return_date = request.return_date

    response = Transaction.objects.filter(member_id=member_id, book_id=book_id).update(
        return_date=return_date
    )
    JsonResponse({"message": response, "status": 204})


def charge_fee(request, member_id):
    book_id = request.book_id

    response = Transaction.objects.filter(member_id=member_id, book_id=book_id).update(
        payment_done=True
    )

    JsonResponse({"message": response, "status": 204})
