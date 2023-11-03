from django.http import HttpResponse, JsonResponse

from ..models import Book


def index(request):
    all_books = Book.objects.all()
    return HttpResponse(all_books)


def crud_book(request, book_id=None):
    if request.method == "GET":
        title = request.GET.get("title")
        author = request.GET.get("author")

        books = Book.objects.all()

        if book_id:
            books = books.filter(id=book_id)
        if title:
            books = books.filter(title=title)
        if author:
            books = books.filter(authors__contain=author)

        JsonResponse({"message": books, "status": 200})

    if request.method == "POST":
        title = request.title
        authors = request.authors
        quantity = request.quantity
        rent = request.rent
        response = Book.objects.create(
            title=title, authors=authors, quantity=quantity, rent=rent
        )
        JsonResponse({"message": response, "status": 201})

    if request.method == "PUT":
        new_book = request.new_book
        response = Book.objects.get(id=book_id).update(**new_book)
        JsonResponse({"message": response, "status": 204})

    if request.method == "DELETE":
        response = Book.objects.get(id=book_id).delete()
        JsonResponse({"message": response, "status": 204})
