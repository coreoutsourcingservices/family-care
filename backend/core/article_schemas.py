from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator

from core.schemas import Schema


class ArticleVisibilityInput(Schema):
    active: bool = Field(strict=True)


class HealthArticleInput(Schema):
    category: Literal['cycle', 'pcos', 'pregnancy', 'fertility', 'symptoms', 'nutrition', 'screening'] | None = None
    stage_month: int | None = Field(default=None, ge=1, le=9, strict=True)
    time_label: str = Field(default='', max_length=100)
    title: str = Field(min_length=3, max_length=180)
    audience: Literal['child', 'women']
    summary: str = Field(default='', max_length=600)
    content: str = Field(min_length=20, max_length=30000)
    cover_image_url: str | None = Field(default=None, max_length=1000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    status: Literal['DRAFT', 'PUBLISHED'] = 'DRAFT'
    published_at: datetime | None = None

    @field_validator('title', 'content')
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('This field must not be blank')
        return value

    @field_validator('summary')
    @classmethod
    def clean_summary(cls, value):
        return value.strip()

    @field_validator('cover_image_url')
    @classmethod
    def valid_image_url(cls, value):
        if value is None or not value.strip():
            return None
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError('Use a complete http or https image URL')
        return value

    @field_validator('tags')
    @classmethod
    def clean_tags(cls, value):
        tags = []
        seen = set()
        for tag in value:
            tag = tag.strip()
            if not tag or len(tag) > 32:
                raise ValueError('Each tag must contain 1 to 32 characters')
            key = tag.casefold()
            if key not in seen:
                seen.add(key)
                tags.append(tag)
        return tags

    @field_validator('published_at')
    @classmethod
    def timezone_required(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError('Include a timezone in the publication date and time')
        return value
