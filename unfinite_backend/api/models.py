from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import secrets

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

    USERNAME_FIELD = 'email' # users are identified by unique emails, not usernames
    REQUIRED_FIELDS = []

    objects = UserManager()

# class Learner(models.Model):
#     user = models.OneToOneField(UnfiniteUser, on_delete=models.CASCADE, primary_key=True)

def get_key():
    return secrets.token_urlsafe(32)

class BetaKey(models.Model):

    # this object links a to-be-registered user with a one-time-use key
    # such that only users with a key can register. The BetaKey object linking
    # a user (email) and a key is deleted after the user registers.

    user_email = models.EmailField(_('email address'), unique=True)
    key = models.CharField(max_length=64, default=get_key)

    def validate_key(self, candidate_key):
        return self.key == candidate_key

class Query(models.Model):

    # Every time a user makes a unique query, a new Query object is created
    # The object stores the query text, the skeleton returned from an LLM,
    # the number of tokens used (for cost tracking purposes), and the number
    # of times the query was searched.

    user = models.ForeignKey(UnfiniteUser, on_delete=models.SET_NULL, null=True)
    query_text = models.TextField()
    skeleton = models.TextField()
    num_tokens = models.IntegerField()
    num_searched = models.IntegerField(default=1)
    
    created = models.DateField()
    updated = models.DateField()

    def searched(self):
        self.num_searched += 1
        return super(Query, self).save()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Query, self).save(*args, **kwargs)

class SERP(models.Model):

    # Stores search results related to a search string. Relates to queries that 
    # triggered the search. entries contains a JSON encoding of a list of 
    # url-title pairs of search results

    search_string = models.TextField()
    queries = models.ManyToManyField(Query)
    entries = models.TextField()
    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(SERP, self).save(*args, **kwargs)

class SERPFeedback(models.Model):
    user = models.ForeignKey(UnfiniteUser, on_delete=models.SET_NULL, primary_key=False, null=True)
    query = models.ForeignKey(Query, on_delete=models.SET_NULL, null=True)
    serp = models.ForeignKey(SERP, on_delete=models.SET_NULL, null=True)
    resource = models.TextField()

    THUMBUP = 'TU'
    THUMBDOWN = 'TD'
    THUMBNEUTRAL = 'TN'
    THUMB_CHOICES = [(THUMBUP, 'Thumbs-up'), (THUMBDOWN, 'Thumbs-down'), (THUMBNEUTRAL, 'Neutral')]

    rating = models.CharField(max_length=2, choices=THUMB_CHOICES, default=THUMBNEUTRAL)

    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(SERPFeedback, self).save(*args, **kwargs)

class Feedback(models.Model):
    user = models.ForeignKey(UnfiniteUser, on_delete=models.SET_NULL, primary_key=False, null=True)
    query = models.ForeignKey(Query, on_delete=models.SET_NULL, null=True)
    text = models.TextField()

    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Feedback, self).save(*args, **kwargs)

class SERPItem(models.Model):

    # No longer used, TODO: Delete

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

class Completion(models.Model):

    user = models.ForeignKey(UnfiniteUser, on_delete=models.SET_NULL, null=True)
    query = models.ForeignKey(Query, on_delete=models.SET_NULL, null=True)

    completion = models.TextField()

    created = models.DateField()
    updated = models.DateField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(Completion, self).save(*args, **kwargs) 

class EventLog(models.Model):

    user = models.ForeignKey(UnfiniteUser, on_delete=models.SET_NULL, null=True)
    query = models.ForeignKey(Query, on_delete=models.SET_NULL, null=True)
    serp = models.ForeignKey(SERP, on_delete=models.SET_NULL, null=True)
    completion = models.ForeignKey(Completion, on_delete=models.SET_NULL, null=True)

    query_was_new = models.BooleanField(null=True)
    serp_was_new = models.BooleanField(null=True)
    completion_idx = models.IntegerField(blank=True, null=True)
    desc = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
