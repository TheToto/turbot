from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone

from slackblocks import (
    Button,
    SectionBlock,
    Confirm,
    DividerBlock,
    ActionsBlock,
    ContextBlock,
)
from workspaces.models import User, Channel
from workspaces.utils import int_to_emoji


class Poll(models.Model):
    name = models.CharField(max_length=256)
    creator = models.ForeignKey(
        User, related_name="created_polls", on_delete=models.CASCADE
    )
    channel = models.ForeignKey(Channel, related_name="polls", on_delete=models.CASCADE)
    unique_choice = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)
    open_choice = models.BooleanField(default=False)
    visible_results = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def slack_blocks(self):
        total_votes = UserChoice.objects.filter(choice__poll__id=self.id).count()

        blocks = [
            SectionBlock(
                f"*{self.name}*\n\nTotal votes: `{total_votes}`",
                accessory=Button(
                    "Delete Poll",
                    action_id="polls.delete",
                    value=f"{self.id}",
                    confirm=Confirm(
                        "Delete Poll", text="Are you sure you want to delete this poll?"
                    ),
                ),
            ),
            DividerBlock(),
            *map(
                lambda c: c.get_slack_block(self.visible_results, self.anonymous),
                self.choices.order_by("index").prefetch_related("voters").all(),
            ),
            *(
                [
                    ActionsBlock(
                        Button(
                            "Reveal results",
                            action_id="polls.reveal",
                            value=f"{self.id}",
                        )
                    )
                ]
                if not self.visible_results
                else []
            ),
            *(
                [
                    ActionsBlock(
                        Button(
                            "Add a choice",
                            action_id="polls.new_choice",
                            value=f"{self.id}",
                        )
                    )
                ]
                if self.open_choice
                else []
            ),
            ContextBlock(f"*Created By:* {self.creator.slack_username}"),
            ContextBlock(f'{timezone.now().strftime("Last updated: %x at %H:%M")}'),
        ]

        return repr(blocks)

    def __str__(self):
        return (
            f"Poll {self.name} created by: {self.creator.name} in {self.channel.name}"
        )


class Choice(models.Model):
    index = models.PositiveSmallIntegerField()
    text = models.CharField(max_length=256)
    poll = models.ForeignKey(Poll, related_name="choices", on_delete=models.CASCADE)
    voters = models.ManyToManyField(
        User,
        through="UserChoice",
        through_fields=("choice", "user"),
        related_name="poll_choices",
    )

    class Meta:
        unique_together = ("index", "poll")

    @property
    def slack_text(self):
        return f"{int_to_emoji(self.index)} {self.text}"

    @property
    def slack_voters(self):
        return " ".join(map(lambda u: u.slack_username, self.voters.all()))

    def get_slack_block(self, show_results=True, anonymous=False):
        voter_count = ""
        if show_results:
            voter_count = f"\t`{self.voters.count()}`"

        voters = ""
        if not anonymous:
            voters = f"\n{self.slack_voters}"

        return SectionBlock(
            f"{self.slack_text}{voter_count}{voters}",
            accessory=Button(text="Vote", action_id="polls.vote", value=f"{self.id}"),
        )

    def __str__(self):
        return f'Choice "{self.text}" of poll "{self.poll.name}" ({self.poll.id})'


class UserChoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "choice")
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.user} : {self.choice}"
