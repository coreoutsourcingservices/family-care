"""Admin-authored health articles, tagged for child or women's health."""
from datetime import timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import or_, select

from core.article_schemas import HealthArticleInput, ArticleVisibilityInput
from core.database import db
from core.errors import APIError
from core.models import HealthArticle, User, WomenArticleVisibility, PregnancyCare, now, uid
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
                  category=row.category, stage_month=row.stage_month, time_label=row.time_label,
                  cover_image_url=row.cover_image_url, tags=row.tags or [],
                  status=article_status(row), published_at=row.published_at.isoformat()+'Z' if row.published_at else None,
                  created_at=row.created_at.isoformat()+'Z', updated_at=row.updated_at.isoformat()+'Z',
                  author={'id':row.author_id, 'role':author.role if author else 'ADMIN', 'full_name':author.full_name if author else 'FamilyCare Admin'})
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
    category = request.args.get('category')
    if category:
        query = query.where(HealthArticle.category == category)
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
    if value.stage_month is not None and (value.audience != 'women' or value.category != 'pregnancy'):
        raise APIError(422, 'invalid_article_stage', 'Pregnancy month requires the women pregnancy category')
    row.category = value.category
    row.stage_month = value.stage_month
    row.time_label = value.time_label.strip()
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
    audit('health_article_created', row.author_id, g.user.id)
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
    audit('health_article_updated', row.author_id, g.user.id)
    db().commit()
    return jsonify(article=data(row))


def archive_article(article_id):
    row = db().scalar(select(HealthArticle).where(HealthArticle.id == str(article_id)).with_for_update())
    if not row:
        raise APIError(404, 'health_article_not_found', 'Health article not found')
    row.status = 'ARCHIVED'
    row.updated_at = now()
    audit('health_article_archived', row.author_id, g.user.id)
    db().commit()
    return jsonify(article=data(row))


def public_list():
    audience = request.args.get('audience', '').lower()
    if audience not in AUDIENCES:
        raise APIError(422, 'invalid_audience', 'Audience is required: child or women')
    page, per_page = pagination_args()
    query = select(HealthArticle).where(HealthArticle.audience == audience,
        HealthArticle.status == 'PUBLISHED', HealthArticle.published_at <= now(),
        HealthArticle.author_id.in_(select(User.id).where(User.role == 'ADMIN')))
    term = request.args.get('q', '').strip()
    if term:
        pattern = '%'+term[:120]+'%'
        query = query.where(or_(HealthArticle.title.ilike(pattern), HealthArticle.summary.ilike(pattern), HealthArticle.content.ilike(pattern)))
    rows, total = paginate(query.order_by(HealthArticle.published_at.desc(), HealthArticle.id), page, per_page)
    return jsonify(items=[data(row) for row in rows], total=total, page=page, per_page=per_page,
                   audience=audience)


route(bp, '/health-articles', public_list)

CATEGORIES = ('cycle', 'pcos', 'pregnancy', 'fertility', 'symptoms', 'nutrition', 'screening')


def doctor_list():
    page, per_page = pagination_args()
    query = select(HealthArticle).where(HealthArticle.audience == 'women', or_(
        HealthArticle.author_id == g.user.id,
        HealthArticle.author_id.in_(select(User.id).where(User.role == 'ADMIN')) &
        (HealthArticle.status == 'PUBLISHED') & (HealthArticle.published_at <= now())))
    category = request.args.get('category')
    if category:
        query = query.where(HealthArticle.category == category)
    rows, total = paginate(query.order_by(HealthArticle.updated_at.desc(), HealthArticle.id), page, per_page)
    items = []
    for row in rows:
        item = data(row)
        override = db().get(WomenArticleVisibility, (g.user.id, row.id))
        item.update(can_edit=row.author_id == g.user.id, doctor_active=override.active if override else True)
        items.append(item)
    return jsonify(items=items, total=total, page=page, per_page=per_page)


def doctor_create():
    value = parse(HealthArticleInput)
    if value.audience != 'women' or value.category not in CATEGORIES:
        raise APIError(422, 'invalid_category', 'Choose a women health category')
    return create_article()


def doctor_owned(article_id):
    row = db().get(HealthArticle, str(article_id))
    if not row or row.author_id != g.user.id or row.audience != 'women':
        raise APIError(404, 'health_article_not_found', 'Your article was not found')
    return row


def doctor_detail(article_id):
    return jsonify(article=data(doctor_owned(article_id)))


def doctor_update(article_id):
    doctor_owned(article_id)
    value = parse(HealthArticleInput)
    if value.audience != 'women' or value.category not in CATEGORIES:
        raise APIError(422, 'invalid_category', 'Choose a women health category')
    return update_article(article_id)


def doctor_visibility(article_id):
    row = db().get(HealthArticle, str(article_id))
    author = db().get(User, row.author_id) if row else None
    if not row or row.audience != 'women' or not author or author.role != 'ADMIN' or article_status(row) != 'PUBLISHED':
        raise APIError(404, 'health_article_not_found', 'Active admin article not found')
    value = parse(ArticleVisibilityInput)
    override = db().get(WomenArticleVisibility, (g.user.id, row.id))
    if not override:
        override = WomenArticleVisibility(doctor_id=g.user.id, article_id=row.id)
        db().add(override)
    override.active = value.active
    audit('women_article_visibility_updated', row.author_id, g.user.id)
    db().commit()
    return jsonify(active=override.active)


def profile_articles(profile_id):
    from services.women_workspace import get_profile
    from services.pregnancy_guide import MONTHS, current_week
    category = request.args.get('category', '')
    if category not in CATEGORIES:
        raise APIError(422, 'invalid_category', 'Choose a women health category')
    profile, _ = get_profile(profile_id, category)
    doctor_id = profile.referred_doctor_id
    month = None
    if category == 'pregnancy':
        stage = db().get(PregnancyCare, profile.id)
        if stage and stage.active and (stage.details or {}).get('lifecycle', 'Ongoing') == 'Ongoing':
            week = current_week(stage)
            month = next((i+1 for i, (start, end) in enumerate(MONTHS) if start <= week <= end), 9 if 40 < week <= 42 else None)
    author_ids = select(User.id).where(User.role == 'ADMIN', User.account_status == 'ACTIVE')
    authors = HealthArticle.author_id.in_(author_ids)
    if doctor_id:
        authors = or_(authors, HealthArticle.author_id.in_(select(User.id).where(
            User.id == doctor_id, User.role == 'DOCTOR', User.account_status == 'ACTIVE', User.approval_status == 'APPROVED')))
    query = select(HealthArticle).where(HealthArticle.audience == 'women', HealthArticle.category == category,
        HealthArticle.status == 'PUBLISHED', HealthArticle.published_at <= now(), authors,
        or_(HealthArticle.stage_month.is_(None), HealthArticle.stage_month == month) if month else HealthArticle.stage_month.is_(None))
    if doctor_id:
        hidden = select(WomenArticleVisibility.article_id).where(WomenArticleVisibility.doctor_id == doctor_id, WomenArticleVisibility.active.is_(False))
        query = query.where(HealthArticle.id.not_in(hidden))
    page, per_page = pagination_args()
    rows, total = paginate(query.order_by(HealthArticle.published_at.desc(), HealthArticle.id), page, per_page)
    return jsonify(items=[data(row) for row in rows], total=total, page=page, per_page=per_page, stage_month=month)


route(bp, '/doctor/women-health-articles', doctor_list, roles=('DOCTOR',))
route(bp, '/doctor/women-health-articles', doctor_create, 'POST', roles=('DOCTOR',), schema=HealthArticleInput)
route(bp, '/doctor/women-health-articles/<uuid:article_id>', doctor_detail, roles=('DOCTOR',))
route(bp, '/doctor/women-health-articles/<uuid:article_id>', doctor_update, 'PUT', roles=('DOCTOR',), schema=HealthArticleInput)
route(bp, '/doctor/women-health-articles/<uuid:article_id>/visibility', doctor_visibility, 'PUT', roles=('DOCTOR',), schema=ArticleVisibilityInput)
route(bp, '/women/profiles/<uuid:profile_id>/health-articles', profile_articles, roles=('PATIENT', 'DOCTOR'))
