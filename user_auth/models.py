from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    username = models.BinaryField(
        _("username"),
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.BinaryField(_("first name"), blank=True)
    last_name = models.BinaryField(_("last name"), blank=True)
    email = models.BinaryField(_("email address"), blank=True)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = False
