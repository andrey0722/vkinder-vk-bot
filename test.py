import base64
import hashlib
import secrets
from typing import Literal, NotRequired, TypedDict
from urllib.parse import quote
from urllib.parse import quote_plus
from urllib.parse import urlencode

from flask import Flask
from flask import jsonify
from flask import request
from flask import session
import pkce
import requests

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


CLIENT_ID = 54226387
REDIRECT_URI = 'https://5423d660-d1e8-4433-aca6-b394fbd5041d.tunnel4.com/callback'
SCOPES = 'photos'

# REDIRECT_URI = quote_plus(REDIRECT_URI)
REDIRECT_URI = quote(REDIRECT_URI, safe=":/?#[]@!$&'()*+,;=")


class Pkce:
    __slots__ = ('verifier', 'challenge')

    def __init__(self, size: int = 32) -> None:
        self.verifier = self._encode(secrets.token_bytes(size))
        digest = hashlib.sha256(self.verifier.encode('utf-8')).digest()
        self.challenge = self._encode(digest)

    @staticmethod
    def _encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

type AuthResponseType = Literal['code']

type CodeChallengeMethodType = Literal['S256']


class AuthUrlParams(TypedDict):
    """All parameters for authorization URL."""

    client_id: int
    response_type: AuthResponseType
    redirect_uri: str
    state: NotRequired[str]
    scope: NotRequired[str]
    code_challenge: NotRequired[str]
    code_challenge_method: NotRequired[CodeChallengeMethodType]


@app.route('/')
def home():
    code_verifier, code_challenge = pkce.generate_pkce_pair()
    session['code_verifier'] = code_verifier  # Сохраняем для обмена

    params = AuthUrlParams(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        response_type='code',
        scope=SCOPES,
        code_challenge=code_challenge,
        code_challenge_method='S256',
    )
    query = urlencode(
        params,
        encoding='utf-8',
        errors='surrogatepass',
        quote_via=quote,
    )
    auth_url = f'https://id.vk.ru/authorize?{query}'
    return f'<a href="{auth_url}">Авторизоваться в VK</a>'


@app.route('/callback')
def callback():
    code = request.args.get('code')
    device_id = request.args.get('device_id')

    if not code:
        return 'Ошибка: нет кода'
    if not device_id:
        return 'Ошибка: нет device_id в редиректе'

    code_verifier = session.get('code_verifier')
    if not code_verifier:
        return 'Ошибка: нет verifier (PKCE)'

    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier,
        'device_id': device_id,
    }

    response = requests.post('https://id.vk.ru/oauth2/auth', data=token_data)

    if response.status_code == 200:
        token_info = response.json()
        # Очищаем сессию: session.clear()
        return jsonify(token_info)
    return f'Ошибка обмена: {response.status_code} - {response.text}'


def app_main():
    # app.run(debug=True, host='127.0.0.1', port=5000)
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    app_main()
