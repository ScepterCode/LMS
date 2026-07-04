import os
import sys
from pathlib import Path

# Load .env manually
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with env_file.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

print('Loaded environment variables from .env')

results = {}

# Supabase
try:
    from supabase import create_client
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not supabase_url or not supabase_key:
        raise ValueError('SUPABASE_URL or SUPABASE_SERVICE_KEY missing')
    client = create_client(supabase_url, supabase_key)
    response = client.table('users').select('id').limit(1).execute()
    results['supabase'] = {'ok': True, 'data': response.data[:1] if hasattr(response, 'data') else None}
except Exception as e:
    results['supabase'] = {'ok': False, 'error': str(e)}

# PostgreSQL
try:
    import importlib.util
    if importlib.util.find_spec('psycopg'):
        import psycopg
        conn = psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=10)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        results['postgres'] = {'ok': True, 'value': cur.fetchone()}
        cur.close(); conn.close()
    elif importlib.util.find_spec('psycopg2'):
        import psycopg2
        conn = psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=10)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        results['postgres'] = {'ok': True, 'value': cur.fetchone()}
        cur.close(); conn.close()
    else:
        results['postgres'] = {'ok': False, 'error': 'No psycopg driver installed'}
except Exception as e:
    results['postgres'] = {'ok': False, 'error': str(e)}

# Redis
try:
    import redis
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        raise ValueError('REDIS_URL missing')
    r = redis.from_url(redis_url, socket_timeout=10)
    pong = r.ping()
    results['redis'] = {'ok': True, 'pong': pong}
except Exception as e:
    results['redis'] = {'ok': False, 'error': str(e)}

# Termii
try:
    import requests
    termii_key = os.environ.get('TERMII_API_KEY')
    termii_sender = os.environ.get('TERMII_SENDER_ID')
    if not termii_key or not termii_sender:
        raise ValueError('TERMII_API_KEY or TERMII_SENDER_ID missing')
    url = 'https://api.termii.com/api/sms/send'
    payload = {
        'to': '2348000000000',
        'from': termii_sender,
        'sms': 'Test message',
        'type': 'plain',
        'channel': 'dnd'
    }
    headers = {'Authorization': termii_key}
    termii_resp = requests.post(url, json=payload, headers=headers, timeout=10)
    results['termii'] = {'ok': termii_resp.status_code == 200, 'status_code': termii_resp.status_code, 'text': termii_resp.text}
except Exception as e:
    results['termii'] = {'ok': False, 'error': str(e)}

# Paystack
try:
    import requests
    paystack_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not paystack_key:
        raise ValueError('PAYSTACK_SECRET_KEY missing')
    headers = {'Authorization': f'Bearer {paystack_key}' }
    paystack_resp = requests.get('https://api.paystack.co/transaction/verify/0', headers=headers, timeout=10)
    results['paystack'] = {'ok': paystack_resp.status_code == 400 or paystack_resp.status_code == 401 or paystack_resp.status_code == 404, 'status_code': paystack_resp.status_code, 'text': paystack_resp.text}
except Exception as e:
    results['paystack'] = {'ok': False, 'error': str(e)}

# Hugging Face
try:
    import requests
    hf_token = os.environ.get('HF_API_TOKEN')
    if not hf_token:
        raise ValueError('HF_API_TOKEN missing')
    headers = {'Authorization': f'Bearer {hf_token}' }
    hf_resp = requests.get('https://api-inference.huggingface.co/models/gpt2', headers=headers, timeout=10)
    results['huggingface'] = {'ok': hf_resp.status_code == 200 or hf_resp.status_code == 401, 'status_code': hf_resp.status_code, 'text': hf_resp.text[:400]}
except Exception as e:
    results['huggingface'] = {'ok': False, 'error': str(e)}

print(results)
