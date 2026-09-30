from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=80)
    code_key = models.CharField(max_length=64, unique=True, db_index=True)
    code_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.code}호실 - {self.name}'


class Post(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='posts')
    medicine = models.CharField(max_length=120)
    body = models.TextField()
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.medicine
