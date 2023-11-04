from django.shortcuts import render
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from .models import Member, Transaction, Book

from django.db.models import F, ExpressionWrapper, fields
from django.utils import timezone
from django.db.models import Sum
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import copy


def index(request):
    return HttpResponse("Hello, world. Welcome to My Library.")


@csrf_exempt
def books_index(request):
    if request.method == "GET":
        request_body = json.loads(request.body.decode("utf-8"))
        title = request_body.get("title")
        author = request_body.get("author")

        books = Book.objects.all()

        if title:
            books = books.filter(title=title)
        if author:
            books = books.filter(authors__contains=author)
        return JsonResponse({"message": list(books.values()), "status": 200})

    if request.method == "POST":
        request_body = json.loads(request.body.decode("utf-8"))

        title = request_body.get("title")
        authors = request_body.get("authors")
        quantity = request_body.get("quantity")
        rent = request_body.get("rent")

        response = Book.objects.create(
            title=title, authors=authors, quantity=quantity, rent=rent
        )
        return JsonResponse(
            {"message": serializers.serialize("json", [response]), "status": 201}
        )


@csrf_exempt
def crud_book(request, book_id=None):
    if request.method == "GET":
        book = Book.objects.filter(id=book_id)
        return JsonResponse(
            {"message": serializers.serialize("json", book), "status": 200}
        )

    if request.method == "PUT":
        request_body = json.loads(request.body.decode("utf-8"))

        updated_fields = request_body.get("updated_fields")
        response = Book.objects.filter(id=book_id).update(**updated_fields)

        return JsonResponse({"message": response, "status": 204})

    if request.method == "DELETE":
        response = Book.objects.get(id=book_id).delete()
        return JsonResponse({"message": response, "status": 204})


@csrf_exempt
def members_index(request):
    if request.method == "GET":
        members = Member.objects.all()
        return JsonResponse({"message": list(members.values()), "status": 200})

    if request.method == "POST":
        request_body = json.loads(request.body.decode("utf-8"))

        email = request_body.get("email")
        response = Member.objects.create(email=email)
        return JsonResponse(
            {"message": serializers.serialize("json", [response]), "status": 201}
        )


@csrf_exempt
def crud_members(request, member_id=None):
    if request.method == "GET":
        member = Member.objects.get(id=member_id)
        return JsonResponse(
            {"message": serializers.serialize("json", [member]), "status": 200}
        )

    if request.method == "PUT":
        request_body = json.loads(request.body.decode("utf-8"))

        updated_fields = request_body.get("updated_fields")
        response = Member.objects.filter(id=member_id).update(**updated_fields)
        return JsonResponse({"message": response, "status": 204})

    if request.method == "DELETE":
        response = Member.objects.get(id=member_id).delete()
        return JsonResponse({"message": response, "status": 204})


@csrf_exempt
def get_outstanding_transactions(request, member_id):
    response = Transaction.objects.filter(member_id=member_id, return_date=None)
    return JsonResponse(
        {"message": serializers.serialize("json", response), "status": 200}
    )


@csrf_exempt
def issue_book(request, member_id):
    request_body = json.loads(request.body.decode("utf-8"))

    book_id = request_body.get("book_id")
    issue_date = request_body.get("issue_date")

    transaction_fee_queryset = Transaction.objects.filter(
        member_id=member_id, payment_done=False
    ).annotate(
        transaction_fee=ExpressionWrapper(
            (F("return_date") - F("issue_date")) * F("book__rent"),
            output_field=fields.DecimalField(),
        )
        if F("return_date") != None
        else ExpressionWrapper(
            (timezone.now() - F("issue_date")) * F("book__rent"),
            output_field=fields.DecimalField(),
        )
    )
    outstanding_debt = transaction_fee_queryset.aggregate(debt=Sum("transaction_fee"))[
        "debt"
    ]

    if outstanding_debt > 500:
        return JsonResponse({"message": "Outstanding debt overflow", "status": 409})

    else:
        response = Transaction.objects.create(
            member_id=member_id, book_id=book_id, issue_date=issue_date
        )
        return JsonResponse(
            {"message": serializers.serialize("json", response), "status": 201}
        )


@csrf_exempt
def return_book(request, member_id):
    request_body = json.loads(request.body.decode("utf-8"))

    book_id = request_body.get("book_id")
    return_date = request_body.get("return_date")

    response = Transaction.objects.filter(member_id=member_id, book_id=book_id).update(
        return_date=return_date
    )
    return JsonResponse(
        {"message": serializers.serialize("json", response), "status": 204}
    )


@csrf_exempt
def charge_fee(request, member_id):
    request_body = json.loads(request.body.decode("utf-8"))

    book_id = request_body.get("book_id")

    response = Transaction.objects.filter(member_id=member_id, book_id=book_id).update(
        payment_done=True
    )

    return JsonResponse(
        {"message": serializers.serialize("json", response), "status": 204}
    )


@csrf_exempt
def import_books(request):
    if request.method == "POST":
        request_body = json.loads(request.body.decode("utf-8"))
        title = request_body.get("title")
        authors = request_body.get("authors")
        isbn = request_body.get("isbn")
        publisher = request_body.get("publisher")
        page = request_body.get("page")

        api_url = "https://frappe.io/api/method/frappe-library?"
        if title:
            api_url = api_url + f"title={title}"
        if authors:
            api_url = api_url + f"authors={authors}"
        if isbn:
            api_url = api_url + f"isbn={isbn}"
        if publisher:
            api_url = api_url + f"publisher={publisher}"
        if page:
            api_url = api_url + f"page={page}"

        response = requests.get(api_url)
        print(response.content)
        data = BytesIO(response.content)
        deserialized_data = json.load(data)
        books = deserialized_data['message']

        cleaned_books = []
        keys_mapping = {'  num_pages': 'num_pages', 'bookID': 'id'}
        for book in books:
            cleaned_book = {keys_mapping.get(key, key): value for key, value in book.items()}
            cleaned_books.append(cleaned_book)

        book_objects = [Book(**book) for book in cleaned_books]


        Book.objects.bulk_create(book_objects)


# Create your views here.
