from django.db import models
from django.utils import timezone


class Book(models.Model):
    title = models.CharField(max_length=500, null=False)
    authors = models.CharField(max_length=500, null=True)
    quantity = models.IntegerField(default=1)
    rent = models.DecimalField(max_digits=100, decimal_places=2, default=50)
    average_rating = models.CharField(max_length=500, null=True)
    isbn = models.CharField(max_length=500, null=True)
    isbn13 = models.CharField(max_length=500, null=True)
    language_code = models.CharField(max_length=500, null=True)
    num_pages = models.CharField(max_length=500, null=True)
    text_reviews_count = models.CharField(max_length=500, null=True)
    ratings_count = models.CharField(max_length=500, null=True)
    publication_date = models.CharField(max_length=500, null=True)
    publisher = models.CharField(max_length=500, null=True)
    average_rating = models.CharField(max_length=500, null=True)

    class Meta:
        unique_together = ("title", "authors")

    def __str__(self):
        return f"{self.quantity} {self.title} by {self.authors} id {self.id}"


class Member(models.Model):
    email = models.EmailField(max_length=500, null=True, unique=True)

    def __str__(self):
        return self.email


class Transaction(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    issue_date = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True)
    payment_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} to {self.member.email} issued on {self.issue_date}, return on {self.return_date}, payment {self.payment_done}"
