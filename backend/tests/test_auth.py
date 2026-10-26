import os
import unittest
from unittest.mock import Mock, patch

from app import create_app


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_ANON_KEY': 'test-key'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = create_app().test_client()

    def response(self, data, status=200):
        return Mock(ok=status < 400, status_code=status, content=b'json', json=lambda: data)

    def test_health(self):
        self.assertEqual(self.client.get('/health').status_code, 200)

    @patch('app.requests.request')
    def test_public_signup_rejects_admin_without_network(self, http):
        for role in ('admin', 'super_admin'):
            result = self.client.post('/api/auth/signup', json={
                'email': 'a@example.com', 'password': 'long-password-123',
                'full_name': 'A', 'role': role})
            self.assertEqual(result.status_code, 400)
        http.assert_not_called()

    @patch('app.requests.request')
    def test_doctor_patient_signup(self, http):
        http.return_value = self.response({'id': 'user-id'})
        for role in ('doctor', 'patient'):
            result = self.client.post('/api/auth/signup', json={
                'email': 'a@example.com', 'password': 'long-password-123',
                'full_name': 'Example', 'role': role})
            self.assertEqual(result.status_code, 202)
            self.assertEqual(http.call_args.kwargs['json']['data']['role'], role)

    def test_missing_token(self):
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

    @patch('app.requests.request')
    def test_invalid_token(self, http):
        http.return_value = self.response({}, 401)
        self.assertEqual(self.client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid'}).status_code, 401)

    @patch('app.requests.request')
    def test_patient_cannot_list_users(self, http):
        http.side_effect = [self.response({'id': 'u'}),
                            self.response([{'id': 'u', 'role': 'patient'}])]
        self.assertEqual(self.client.get('/api/admin/users', headers={
            'Authorization': 'Bearer valid'}).status_code, 403)

    @patch('app.requests.request')
    def test_admin_cannot_promote(self, http):
        http.side_effect = [self.response({'id': 'u'}),
                            self.response([{'id': 'u', 'role': 'admin'}])]
        result = self.client.patch('/api/admin/users/00000000-0000-0000-0000-000000000001/role',
                                   headers={'Authorization': 'Bearer valid'}, json={'role': 'super_admin'})
        self.assertEqual(result.status_code, 403)
        self.assertEqual(http.call_count, 2)

    @patch('app.requests.request')
    def test_super_admin_promotes(self, http):
        http.side_effect = [self.response({'id': 'u'}),
                            self.response([{'id': 'u', 'role': 'super_admin'}]), self.response({})]
        result = self.client.patch('/api/admin/users/00000000-0000-0000-0000-000000000001/role',
                                   headers={'Authorization': 'Bearer valid'}, json={'role': 'admin'})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(http.call_args.args[1].endswith('/rpc/set_user_role'))

    @patch('app.requests.request')
    def test_signin_and_refresh(self, http):
        http.return_value = self.response({'access_token': 'token', 'refresh_token': 'refresh'})
        result = self.client.post('/api/auth/signin', json={'email': 'a@example.com', 'password': 'test'})
        self.assertEqual(result.json['access_token'], 'token')
        self.assertEqual(self.client.post('/api/auth/refresh', json={'refresh_token': 'refresh'}).status_code, 200)

    def test_non_object_json(self):
        self.assertEqual(self.client.post('/api/auth/signup', json=[]).status_code, 400)


if __name__ == '__main__':
    unittest.main()
