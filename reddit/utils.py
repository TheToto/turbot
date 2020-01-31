from typing import Optional
import datetime

from slackblocks import SectionBlock, ImageBlock, ContextBlock

import praw
from django.conf import settings
from . import models

reddit = praw.Reddit(
    client_id=settings.PRAW_CLIENT_ID,
    client_secret=settings.PRAW_CLIENT_SECRET,
    user_agent=settings.PRAW_USER_AGENT,
)


def has_valid_extension(url):
    return any(ext in url for ext in settings.REDDIT_VALID_EXTENSION)


def get_submission(channel: models.Channel) -> Optional[models.Submission]:
    subreddits = "+".join(
        (
            models.Subscription.objects.filter(channel=channel).values_list(
                "subreddit", flat=True
            )
        )
    )

    posts = reddit.subreddit(subreddits).hot()
    posts = filter(lambda p: has_valid_extension(p.url), posts)

    for post in posts:
        if models.Submission.objects.filter(
            channel_id=channel.id, post_id=post.id
        ).exists():
            continue
        return models.Submission.objects.create(
            channel=channel,
            post_id=post.id,
            title=post.title,
            url=post.url,
            subreddit=post.subreddit,
        )


def send_submission(submission: models.Submission):
    perma_link = (
        f"https://reddit.com/r/{submission.subreddit}/comments/{submission.post_id}/"
    )

    blocks = [SectionBlock(f"*<{perma_link}|{submission.title}>*")]

    if has_valid_extension(submission.url):
        blocks.append(ImageBlock(image_url=submission.url, alt_text=submission.url))

    blocks.append(
        ContextBlock(
            f"<https://reddit.com/r/{submission.subreddit}|/r/{submission.subreddit}>"
        )
    )

    settings.SLACK_CLIENT.chat_postMessage(
        channel=submission.channel.id,
        text=f"New submission: {submission.title}",
        blocks=blocks,
    )


def trigger_queryset(queryset):
    for channel_id in queryset.values_list("channel", flat=True).distinct():
        channel = models.Channel.objects.get(pk=channel_id)
        submission = get_submission(channel)
        if submission:
            send_submission(submission)


def trigger_submissions(*channels, respect_datetime=True):
    now = datetime.datetime.now().time()
    is_nightime = settings.NIGHT_START < now or now < settings.NIGHT_END

    if respect_datetime and is_nightime:
        return
    queryset = models.Subscription.objects
    if channels:
        queryset = queryset.filter(channel_id__in=channels)

    trigger_queryset(queryset)
