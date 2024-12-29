from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from .constants import MAX_USER_FIRST_NAME_LENGTH, MAX_USER_LAST_NAME_LENGTH
from .utils import get_avatar_path


class User(AbstractUser):
    """Custom user model with an additional avatar field."""

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(
        _('first name'), max_length=MAX_USER_FIRST_NAME_LENGTH
    )
    last_name = models.CharField(
        _('last name'), max_length=MAX_USER_LAST_NAME_LENGTH
    )
    avatar = models.ImageField(
        upload_to=get_avatar_path,
        default=None,
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username

    def __repr__(self) -> str:
        return (
            f'<User('
            f'username={self.username!r}, '
            f'email={self.email!r}, '
            f'first_name={self.first_name!r}, '
            f'last_name={self.last_name!r})>'
        )


class UserSubscriptions(models.Model):
    """Model for user subscriptions."""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Подписчик'),
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name=_('Подписки'),
    )

    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        constraints = [
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_user_subscription',
                fields=('subscriber', 'subscribed_to'),
            ),
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_prevent_self_subscribe',
                check=~Q(subscriber=F('subscribed_to')),
            ),
        ]

    def clean(self) -> None:
        """Validate subscription to prevent self-subscription."""
        if self.subscriber == self.subscribed_to:
            raise ValidationError(_('User cannot subscribe to themselves.'))

    def __str__(self) -> str:
        return f'{self.subscriber} -> {self.subscribed_to}'

    def __repr__(self) -> str:
        return (
            f'<UserSubscriptions('
            f'subscriber={self.subscriber.username!r}, '
            f'subscribed_to={self.subscribed_to.username!r})>'
        )
