from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils import get_avatar_path
from users.constants import SUBSCRIBERS, SUBSCRIPTIONS


class User(AbstractUser):
    """Custom user model with an additional avatar field."""

    email = models.EmailField(_('email address'), blank=True, unique=True)
    avatar = models.ImageField(
        upload_to=get_avatar_path,
        default=None,
        blank=True,
        null=True,
    )

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        indexes = [
            models.Index(fields=('username',), name='user_username_idx'),
            models.Index(fields=('email',), name='user_email_idx'),
        ]

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
        related_name=SUBSCRIPTIONS,
        verbose_name=_('Подписчик'),
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name=SUBSCRIBERS,
        verbose_name=_('Подписки'),
    )

    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        constraints = [
            models.UniqueConstraint(
                fields=('subscriber', 'subscribed_to'),
                name='unique_user_subscription',
            )
        ]

    def clean(self) -> None:
        """Validate subscription to prevent self-subscription."""
        if self.subscriber == self.subscribed_to:
            raise ValidationError(_('User cannot subscribe to themselves.'))

    @staticmethod
    def subscribe(subscriber, subscribed_to) -> 'UserSubscriptions':
        """Create a subscription between two users."""
        if subscriber == subscribed_to:
            raise ValueError('User cannot subscribe to themselves.')
        return UserSubscriptions.objects.create(
            subscriber=subscriber, subscribed_to=subscribed_to
        )

    @staticmethod
    def unsubscribe(subscriber, subscribed_to) -> None:
        """Remove a subscription between two users."""
        subscriber.filter(subscribed_to=subscribed_to).delete()

    @staticmethod
    def is_subscribed(subscriber, subscribed_to) -> bool:
        """Check if a subscription exists between two users."""
        return subscriber.filter(subscribed_to=subscribed_to).exists()

    def __str__(self) -> str:
        return f'{self.subscriber} -> {self.subscribed_to}'

    def __repr__(self) -> str:
        return (
            f'<UserSubscriptions('
            f'subscriber={self.subscriber.username!r}, '
            f'subscribed_to={self.subscribed_to.username!r})>'
        )
