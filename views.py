import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import Patient, Post


def _json(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _key(name, code):
    raw = f'{name}\0{code}'.encode('utf-8')
    return hmac.new(settings.SECRET_KEY.encode('utf-8'), raw, hashlib.sha256).hexdigest()


def _patient(request):
    pid = request.session.get('patient_id')
    if not pid:
        return None
    try:
        return Patient.objects.get(pk=pid)
    except Patient.DoesNotExist:
        request.session.flush()
        return None


def _post_json(post, include_private=True):
    data = {
        'id': post.id,
        'medicine': post.medicine,
        'body': post.body,
        'private': post.is_private,
        'createdAt': post.created_at.isoformat(),
        'updatedAt': post.updated_at.isoformat(),
    }
    if not include_private:
        data.pop('private', None)
    return data


@ensure_csrf_cookie
def index(request):
    return render(request, 'ward/index.html')


@require_http_methods(['GET'])
def me(request):
    p = _patient(request)
    if not p:
        return JsonResponse({'loggedIn': False})
    return JsonResponse({
        'loggedIn': True,
        'profile': {
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'posts': [_post_json(x) for x in p.posts.all()],
        },
    })


@require_http_methods(['POST'])
def login_patient(request):
    data = _json(request)
    name = str(data.get('name', '')).strip()
    code = str(data.get('code', '')).strip()
    if not name or not code:
        return JsonResponse({'error': '이름과 코드를 모두 입력해주세요.'}, status=400)
    if len(name) > 80 or len(code) > 80:
        return JsonResponse({'error': '이름 또는 코드가 너무 깁니다.'}, status=400)

    key = _key(name, code)
    patient = Patient.objects.filter(code_key=key).first()
    if patient:
        if patient.name != name or not check_password(code, patient.code_hash):
            return JsonResponse({'error': '입원 정보를 확인해주세요.'}, status=401)
    else:
        try:
            with transaction.atomic():
                patient = Patient.objects.create(
                    name=name,
                    code=code,
                    code_key=key,
                    code_hash=make_password(code),
                )
        except IntegrityError:
            patient = Patient.objects.get(code_key=key)

    request.session.cycle_key()
    request.session['patient_id'] = patient.id
    return JsonResponse({'ok': True, 'profile': {
        'id': patient.id,
        'name': patient.name,
        'code': patient.code,
        'posts': [_post_json(x) for x in patient.posts.all()],
    }})


@require_http_methods(['POST'])
def logout_patient(request):
    request.session.flush()
    return JsonResponse({'ok': True})


@require_http_methods(['DELETE'])
def delete_profile(request):
    patient = _patient(request)
    if not patient:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    patient.delete()
    request.session.flush()
    return JsonResponse({'ok': True})


@require_http_methods(['POST'])
def posts(request):
    patient = _patient(request)
    if not patient:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    data = _json(request)
    medicine = str(data.get('medicine', '')).strip()
    body = str(data.get('body', '')).strip()
    is_private = bool(data.get('private', False))
    if not medicine or not body:
        return JsonResponse({'error': '약 이름과 글 내용을 모두 입력해주세요.'}, status=400)
    if len(medicine) > 120:
        return JsonResponse({'error': '약 이름이 너무 깁니다.'}, status=400)
    post = Post.objects.create(patient=patient, medicine=medicine, body=body, is_private=is_private)
    return JsonResponse({'ok': True, 'post': _post_json(post)})


@require_http_methods(['PUT', 'DELETE'])
def post_detail(request, post_id):
    patient = _patient(request)
    if not patient:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    try:
        post = Post.objects.get(pk=post_id, patient=patient)
    except Post.DoesNotExist:
        return JsonResponse({'error': '내 처방만 수정하거나 삭제할 수 있습니다.'}, status=403)

    if request.method == 'DELETE':
        post.delete()
        return JsonResponse({'ok': True})

    data = _json(request)
    medicine = str(data.get('medicine', '')).strip()
    body = str(data.get('body', '')).strip()
    if not medicine or not body:
        return JsonResponse({'error': '약 이름과 글 내용을 모두 입력해주세요.'}, status=400)
    post.medicine = medicine
    post.body = body
    post.is_private = bool(data.get('private', False))
    post.save()
    return JsonResponse({'ok': True, 'post': _post_json(post)})


@require_http_methods(['GET'])
def rooms(request):
    patient = _patient(request)
    qs = Patient.objects.all().order_by('code', 'name')
    result = []
    for p in qs:
        public_count = p.posts.filter(is_private=False).count()
        result.append({
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'publicCount': public_count,
            'isMe': bool(patient and patient.id == p.id),
        })
    return JsonResponse({'rooms': result})


@require_http_methods(['GET'])
def room_detail(request, patient_id):
    p = Patient.objects.filter(pk=patient_id).first()
    if not p:
        return JsonResponse({'error': '호실을 찾을 수 없습니다.'}, status=404)
    public_posts = p.posts.filter(is_private=False)
    return JsonResponse({
        'room': {
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'posts': [_post_json(x, include_private=False) for x in public_posts],
        }
    })
