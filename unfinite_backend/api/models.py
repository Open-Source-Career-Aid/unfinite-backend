from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Create your models here.

class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):

        if not email or not password:
            raise ValueError('No email/password provided.')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_learner', True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_learner', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class UnfiniteUser(AbstractUser):
    is_staff = models.BooleanField(default=False)
    is_learner = models.BooleanField(default=False)
    is_beta = models.BooleanField(default=False)
    register_date = models.DateField(auto_now=True)

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

# class Learner(models.Model):
#     user = models.OneToOneField(UnfiniteUser, on_delete=models.CASCADE, primary_key=True)

class BetaKey(models.Model):

    user_email = models.EmailField(_('email address'), unique=True)
    key = models.CharField(max_length=64)

    def validate_key(self, candidate_key):
        return self.key == candidate_key

class Query(models.Model):
    user = models.OneToOneField(UnfiniteUser, on_delete=models.PROTECT, primary_key=False)
    query_text = models.TextField()
    skeleton = models.TextField()
    num_tokens = models.IntegerField()
    num_searched = models.IntegerField(default=1)
    
    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Query, self).save(*args, **kwargs)

class Feedback(models.Model):
    user = models.OneToOneField(UnfiniteUser, on_delete=models.PROTECT, primary_key=False)
    query = models.ForeignKey(Query, on_delete=models.PROTECT)
    text = models.TextField()

    THUMBUP = 'TU'
    THUMBDOWN = 'TD'
    THUMBNEUTRAL = 'TN'
    THUMB_CHOICES = [(THUMBUP, 'Thumbs-up'), (THUMBDOWN, 'Thumbds-down'), (THUMBNEUTRAL, 'Neutral')]

    rating = models.CharField(max_length=2, choices=THUMB_CHOICES, default=THUMBNEUTRAL)

    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Feedback, self).save(*args, **kwargs)

class SERP(models.Model):
    search_string = models.TextField()
    queries = models.ManyToManyField(Query)
    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(SERP, self).save(*args, **kwargs)

class SERPItem(models.Model):
    serp = models.ForeignKey(SERP, on_delete=models.CASCADE)
    title = models.TextField()
    url = models.URLField()
    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(SERPItem, self).save(*args, **kwargs) 