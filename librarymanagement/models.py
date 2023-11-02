from django.db import models
from django.utils import timezone

class Book(models.Model):
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500, null=True)
    quantity = models.IntegerField(null=True)
    rent = models.DecimalField(max_digits=100, decimal_places=2, null=True)
    def __str__(self):
        return self.title

class Member(models.Model):
    email = models.EmailField(max_length=500, null=True)
    def __str__(self):
        return self.name

class Transaction(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True)
    payment_done = models.BooleanField(default=False)

    def __str__(self):
        return self.book
