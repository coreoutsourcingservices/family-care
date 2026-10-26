// API integration only; add dio and flutter_secure_storage to the Flutter project.
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class FamilyCareApi {
  final Dio dio;
  final FlutterSecureStorage storage = const FlutterSecureStorage();
  Future<void>? _refreshing;

  FamilyCareApi(String baseUrl) : dio = Dio(BaseOptions(baseUrl: baseUrl)) {
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) async {
      final access = await storage.read(key: 'access_token');
      if (access != null) options.headers['Authorization'] = 'Bearer $access';
      handler.next(options);
    }, onError: (error, handler) async {
      final options = error.requestOptions;
      final data = error.response?.data;
      final code = data is Map ? data['error']?['code'] : null;
      final expiredSession = code == 'invalid_token' || code == 'session_revoked';
      if (error.response?.statusCode == 401 && expiredSession && options.extra['retried'] != true && !options.path.contains('/auth/refresh')) {
        try {
          _refreshing ??= _refresh().whenComplete(() => _refreshing = null);
          await _refreshing;
          options.extra['retried'] = true;
          final access = await storage.read(key: 'access_token');
          options.headers['Authorization'] = 'Bearer $access';
          handler.resolve(await dio.fetch(options));
          return;
        } catch (_) { await clearTokens(); }
      }
      handler.next(error);
    }));
  }

  Future<void> saveSession(Map<String, dynamic> data) async {
    if (data['access_token'] != null) {
      await storage.write(key: 'access_token', value: data['access_token']);
      await storage.write(key: 'refresh_token', value: data['refresh_token']);
    }
  }

  Future<void> _refresh() async {
    final refresh = await storage.read(key: 'refresh_token');
    if (refresh == null) throw StateError('No refresh session');
    final response = await dio.post('/api/v1/auth/refresh', data: {'refresh_token': refresh});
    await saveSession(Map<String, dynamic>.from(response.data));
  }

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> data) async {
    final response = await dio.post(path, data: data);
    final result = Map<String, dynamic>.from(response.data);
    await saveSession(result);
    return result;
  }

  Future<void> clearTokens() async {
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
  }

  Future<void> logout() async {
    try { await dio.post('/api/v1/auth/logout'); } finally { await clearTokens(); }
  }
}

// Desktop/browser local base: http://127.0.0.1:5001.
// Android emulator reaches a host-bound backend via http://10.0.2.2:5001.
// Physical phones require an explicitly bound LAN address/firewall setup; use HTTPS in production.
