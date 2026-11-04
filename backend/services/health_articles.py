"""Admin-authored health articles, tagged for child or women's health."""
from datetime import timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import or_, select

from core.article_schemas import HealthArticleInput
from core.database import db
from core.errors import APIError
from core.models import HealthArticle, User, now, uid
from core.routing import route
from core.schemas import parse
from services.approvals import paginate
from services.repository import audit

bp = Blueprint('health_articles', __name__, url_prefix='/api/v1')
AUDIENCES = ('child', 'women')
STATUSES = ('DRAFT', 'PUBLISHED', 'SCHEDULED', 'ARCHIVED')


def article_status(row, at=None):
    if row.status != 'PUBLISHED':
        return row.status
    at = at or now()
    if row.published_at and row.published_at > at:
        return 'SCHEDULED'
    return 'PUBLISHED'


def data(row, include_content=True):
    author = db().get(User, row.author_id)
    result = dict(id=row.id, title=row.title, audience=row.audience, summary=row.summary,
                  cover_image_url=row.cover_image_url, tags=row.tags or [],
                  status=article_status(row), published_at=row.published_at.isoformat()+'Z' if row.published_at else None,
                  created_at=row.created_at.isoformat()+'Z', updated_at=row.updated_at.isoformat()+'Z',
                  author={'id':row.author_id, 'full_name':author.full_name if author else 'FamilyCare Admin'})
    if include_content:
        result['content'] = row.content
    return result


def pagination_args():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
    except (ValueError, TypeError):
        raise APIError(422, 'invalid_pagination', 'Use integer page and per_page')
    if page < 1 or not 1 <= per_page <= 100:
        raise APIError(422, 'invalid_pagination', 'Page must be positive and per_page must be 1 to 100')
    return page, per_page


def admin_list():
    page, per_page = pagination_args()
    query = select(HealthArticle)
    audience = request.args.get('audience')
    status = request.args.get('status', '').upper()
    term = request.args.get('q', '').strip()
    if audience:
        if audience not in AUDIENCES:
            raise APIError(422, 'invalid_audience', 'Audience must be child or women')
        query = query.where(HealthArticle.audience == audience)
    if status:
        if status not in STATUSES:
            raise APIError(422, 'invalid_status', 'Choose draft, published, scheduled or archived')
        at = now()
        if status == 'SCHEDULED':
            query = query.where(HealthArticle.status == 'PUBLISHED', HealthArticle.published_at > at)
        elif status == 'PUBLISHED':
            query = query.where(HealthArticle.status == 'PUBLISHED',
                                or_(HealthArticle.published_at.is_(None), HealthArticle.published_at <= at))
        else:
            query = query.where(HealthArticle.status == status)
    if term:
        pattern = '%'+term[:120]+'%'
        query = query.where(or_(HealthArticle.title.ilike(pattern), HealthArticle.summary.ilike(pattern)))
    rows, total = paginate(query.order_by(HealthArticle.updated_at.desc(), HealthArticle.id), page, per_page)
    return jsonify(items=[data(row, include_content=False) for row in rows], total=total, page=page, per_page=per_page)


def admin_detail(article_id):
    row = db().get(HealthArticle, str(article_id))
    if not row:
        raise APIError(404, 'health_article_not_found', 'Health article not found')
    return jsonify(article=data(row))


def _publication(value):
    if value.status == 'DRAFT':
        return None
    if value.published_at is None:
        return now()
    return value.published_at.astimezone(timezone.utc).replace(tzinfo=None)


def _apply(row, value):
    row.title = value.title
    row.audience = value.audience
    row.summary = value.summary
    row.content = value.content
    row.cover_image_url = value.cover_image_url
    row.tags = value.tags
    row.status = value.status
    row.published_at = _publication(value)
    row.updated_at = now()


def create_article():
    value = parse(HealthArticleInput)
    row = HealthArticle(id=uid(), author_id=g.user.id, status='DRAFT', title='', audience='child', content='')
    _apply(row, value)
    db().add(row)
    audit('health_article_created', row.id, g.user.id)
    db().commit()
    return jsonify(article=data(row)), 201


def update_article(article_id):
    row = db().scalar(select(HealthArticle).where(HealthArticle.id == str(article_id)).with_for_update())
    if not row:
        raise APIError(404, 'health_article_not_found', 'Health article not found')
    if row.status == 'ARCHIVED':
        raise APIError(409, 'health_article_archived', 'Archived articles cannot be edited')
    value = parse(HealthArticleInput)
    _apply(row, value)
    audit('health_article_updated', row.id, g.user.id)
    db().commit()
    return jsonify(article=data(row))


def archive_article(article_id):
    row = db().scalar(select(HealthArticle).where(HealthArticle.id == str(article_id)).with_for_update())
    if not row:
        raise APIError(404, 'health_article_not_found', 'Health article not found')
    row.status = 'ARCHIVED'
    row.updated_at = now()
    audit('health_article_archived', row.id, g.user.id)
    db().commit()
    return jsonify(article=data(row))


def public_list():
    audience = request.args.get('audience', '').lower()
    if audience not in AUDIENCES:
        raise APIError(422, 'invalid_audience', 'Audience is required: child or women')
    page, per_page = pagination_args()
    query = select(HealthArticle).where(HealthArticle.audience == audience,
        HealthArticle.status == 'PUBLISHED', HealthArticle.published_at <= now())
    term = request.args.get('q', '').strip()
    if term:
        pattern = '%'+term[:120]+'%'
        query = query.where(or_(HealthArticle.title.ilike(pattern), HealthArticle.summary.ilike(pattern), HealthArticle.content.ilike(pattern)))
    rows, total = paginate(query.order_by(HealthArticle.published_at.desc(), HealthArticle.id), page, per_page)
    return jsonify(items=[data(row) for row in rows], total=total, page=page, per_page=per_page,
                   audience=audience)


route(bp, '/health-articles', public_list)
