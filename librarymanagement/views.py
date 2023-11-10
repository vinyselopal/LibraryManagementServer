from io import BytesIO
from django.http import HttpResponse, JsonResponse
from .models import Member, Transaction, Book
from requests.models import PreparedRequest

from django.db.models import F, ExpressionWrapper, fields, Case, When
from django.utils import timezone
from django.db.models import Sum
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import Cast

import json
import requests


def index(request):
    return HttpResponse("Hello, world. Welcome to My Library.")


@csrf_exempt
def books_index(request):
    if request.method == "GET":
        title = request.GET.get("title")
        author = request.GET.get("author")

        books = Book.objects.all()

        if title:
            books = books.filter(title=title)
        if author:
            books = books.filter(authors__contains=author)

        if books:
            return JsonResponse({"message": list(books.values()), "status": 200})
        else:
            return JsonResponse({"message": list(books.values()), "status": 404})

    if request.method == "POST":
        request_body = json.loads(request.body.decode("utf-8"))

        books = request_body.get("books")

        try:
            for book in books:
                b = Book.objects.get_or_create(**book)
                if b[1] == False:
                    b[0].quantity = 1 + b[0].quantity
                    b[0].save()
            return JsonResponse({"message": "books added successfully", "status": 201})
        except:
            return JsonResponse({"message": "failed to add books", "status": 409})


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
        outstanding_debt = request.GET.get("outstanding_debt")

        members = Member.objects.all()

        if outstanding_debt == "true":
            transaction_fee_queryset = (
                Transaction.objects.filter(payment_done=False)
                .annotate(
                    days_difference=Case(
                        When(
                            return_date__isnull=False,
                            then=Cast(
                                F("return_date") - F("issue_date"),
                                fields.IntegerField(),
                            ),
                        ),
                        default=Cast(
                            timezone.now().date() - F("issue_date"),
                            fields.IntegerField(),
                        ),
                        output_field=fields.IntegerField(),
                    )
                )
                .annotate(
                    transaction_fee=ExpressionWrapper(
                        F("days_difference") * F("book__rent"),
                        output_field=fields.DecimalField(),
                    )
                )
            )
            outstanding_debt_queryset = (
                transaction_fee_queryset.select_related("member")
                .values("member_id")
                .annotate(debt=Sum("transaction_fee"))
            )

            members = outstanding_debt_queryset.filter(debt__gt=500)

        if members:
            return JsonResponse({"message": list(members.values()), "status": 200})
        else:
            return JsonResponse({"message": list(members.values()), "status": 404})

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
        member = Member.objects.filter(id=member_id)

        if member:
            return JsonResponse({"message": list(member.values()), "status": 200})
        else:
            return JsonResponse({"message": list(member.values()), "status": 404})

    if request.method == "PUT":
        request_body = json.loads(request.body.decode("utf-8"))

        updated_fields = request_body.get("updated_fields")
        response = Member.objects.filter(id=member_id).update(**updated_fields)
        return JsonResponse({"message": response, "status": 204})

    if request.method == "DELETE":
        response = Member.objects.get(id=member_id).delete()
        return JsonResponse({"message": response, "status": 204})


@csrf_exempt
def get_transactions(request):
    book_title = request.GET.get("book_title")
    book_author = request.GET.get("book_author")
    issue_date = request.GET.get("issue_date")
    return_date = request.GET.get("return_date")
    member_email = request.GET.get("member_email")

    transactions = Transaction.objects.all()

    if member_email:
        transactions = transactions.filter(member__email=member_email)
    if return_date:
        transactions = transactions.filter(return_date=return_date)
    if issue_date:
        transactions = transactions.filter(issue_date=issue_date)
    if book_title:
        transactions = transactions.filter(book__title=book_title)
    if book_author:
        transactions = transactions.filter(book__authors__contains=book_author)

    return JsonResponse({"message": list(transactions.values()), "status": 200})


@csrf_exempt
def issue_book(request):
    request_body = json.loads(request.body.decode("utf-8"))

    book_title = request_body.get("book_title")
    book_author = request_body.get("book_author")
    issue_date = request_body.get("issue_date")
    member_email = request_body.get("member_email")

    member_id = Member.objects.get(email=member_email).id
    book_id = Book.objects.get(title=book_title, authors__contains=book_author).id

    transaction_fee_queryset = Transaction.objects.filter(
        member_id=member_id, payment_done=False
    ).annotate(
        transaction_fee=ExpressionWrapper(
            Case(
                When(
                    return_date__isnull=False, then=(F("return_date") - F("issue_date"))
                ),
                default=(timezone.now().date() - F("issue_date")),
                output_field=fields.DurationField(),
            )
            * F("book__rent"),
            output_field=fields.DecimalField(),
        )
    )

    outstanding_debt = transaction_fee_queryset.aggregate(debt=Sum("transaction_fee"))[
        "debt"
    ]

    book_quantity = Book.objects.get(id=book_id).quantity
    books_issued = Transaction.objects.filter(book_id=book_id, return_date=None).count()
    books_unissued = book_quantity - books_issued

    if transaction_fee_queryset and outstanding_debt > 500:
        return JsonResponse({"message": "Outstanding debt overflow", "status": 409})

    if books_unissued == 0:
        return JsonResponse({"message": "Book not available", "status": 409})

    else:
        response = Transaction.objects.create(
            member_id=member_id, book_id=book_id, issue_date=issue_date
        )
        if isinstance(response, Transaction):
            return JsonResponse({"message": "new transaction created", "status": 201})


@csrf_exempt
def return_book(request, transaction_id):
    return_date = timezone.now().date()

    transaction = Transaction.objects.get(id=transaction_id)
    if transaction.return_date == None:
        response = Transaction.objects.filter(id=transaction_id).update(
            return_date=return_date
        )
        if isinstance(response, int):
            return JsonResponse({"message": "return issued", "status": 204})
    else:
        return JsonResponse({"message": "already returned", "status": 400})


@csrf_exempt
def charge_fee(request, transaction_id):
    response = Transaction.objects.filter(id=transaction_id).update(payment_done=True)

    if isinstance(response, int):
        return JsonResponse({"message": "charged fee", "status": 204})


def deduplicate_books(books):
    seen_ids = set()
    unique_books = []
    for book in books:
        if not book["isbn"] in seen_ids:
            unique_books.append(book)
            seen_ids.add(book["isbn"])
    return unique_books


def append_page_to_url(api_url, key, value):
    req = PreparedRequest()
    req.prepare_url(api_url, {key: value})
    return req.url


@csrf_exempt
def import_books(request):
    if request.method == "GET":
        title = request.GET.get("title")
        author = request.GET.get("author")
        quantity = int(request.GET.get("quantity"))

        api_url = "https://frappe.io/api/method/frappe-library?"

        if title:
            api_url = append_page_to_url(api_url, "title", title)
        if author:
            api_url = append_page_to_url(api_url, "authors", author)

        books = []

        page = 1
        while len(books) < quantity:
            request_url = append_page_to_url(api_url, "page", page)
            print(request_url)
            response = requests.get(request_url)
            data = BytesIO(response.content)
            deserialized_data = json.load(data)
            next_batch = deserialized_data["message"]
            if not len(next_batch):
                break
            books.extend(deserialized_data["message"])
            books = deduplicate_books(books)
            page = page + 1

        books = books[0:quantity]

        cleaned_books = []

        keys_mapping = {"  num_pages": "num_pages", "bookID": "id"}
        for book in books:
            cleaned_book = {
                keys_mapping.get(key, key): value for key, value in book.items()
            }
            cleaned_book["rent"] = 50
            cleaned_books.append(cleaned_book)

        return JsonResponse({"message": cleaned_books, "status": 201})


# Create your views here.
