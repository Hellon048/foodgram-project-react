from django.contrib.auth.models import AbstractUser
from django.db.models import (CharField, CheckConstraint, EmailField,
                              ManyToManyField, Q)
from django.db.models.functions import Length
from django.utils.translation import gettext_lazy as _

from api import conf

from .validators import username_validation

CharField.register_lookup(Length)


class MyUser(AbstractUser):
    email = EmailField(
        verbose_name='Адрес электронной почты',
        max_length=conf.MAX_LEN_EMAIL_FIELD,
        unique=True,
        help_text=conf.USERS_HELP_EMAIL
    )

    username = CharField(
        verbose_name='Пользователь',
        max_length=conf.MAX_LEN_USERS_CHARFIELD,
        unique=True,
        help_text=(conf.USERS_HELP_UNAME),
        validators=(username_validation(),
                    ),
    )
    first_name = CharField(
        verbose_name='Имя',
        max_length=conf.MAX_LEN_USERS_CHARFIELD,
        help_text=conf.USERS_HELP_FNAME
    )
    last_name = CharField(
        verbose_name='Фамилия',
        max_length=conf.MAX_LEN_USERS_CHARFIELD,
        help_text=conf.USERS_HELP_FNAME
    )
    password = CharField(
        verbose_name=_('Пароль'),
        max_length=conf.MAX_LEN_USERS_CHARFIELD,
        help_text=conf.USERS_HELP_FNAME
    )
    subscribe = ManyToManyField(
        verbose_name='Подписка',
        related_name='subscribers',
        to='self',
        symmetrical=False,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = (
            CheckConstraint(
                check=Q(username__length__gte=conf.MIN_USERNAME_LENGTH),
                name='\nusername too short\n',
            ),
        )

    def __str__(self):
        return f'{self.username}: {self.email}'
