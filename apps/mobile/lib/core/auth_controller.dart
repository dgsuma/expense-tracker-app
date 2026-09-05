import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';
import 'models.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(apiClientProvider));
});

class AuthState {
  final User? user;
  final bool isLoading;
  final String? error;

  const AuthState({this.user, this.isLoading = false, this.error});

  bool get isAuthenticated => user != null;

  AuthState copyWith(
      {User? user, bool? isLoading, String? error, bool clearUser = false}) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  final ApiClient _api;
  final _storage = const FlutterSecureStorage();
  String? _refreshToken;

  /// Completes when the initial session restore (or login) finishes and the
  /// access token is set. Data providers await this before making requests.
  Future<void> get ready => _readyCompleter.future;
  final _readyCompleter = Completer<void>();

  AuthController(this._api) : super(const AuthState(isLoading: true)) {
    _api.setRefreshHandler(_refresh);
    _restoreSession();
  }

  Future<void> _restoreSession() async {
    try {
      _refreshToken = await _storage.read(key: 'refresh_token');
      if (_refreshToken == null) {
        state = const AuthState();
        return;
      }
      final refreshed = await _refresh();
      if (refreshed) {
        await _loadUser();
      } else {
        state = const AuthState();
      }
    } catch (_) {
      state = const AuthState();
    } finally {
      if (!_readyCompleter.isCompleted) _readyCompleter.complete();
    }
  }

  Future<bool> _refresh() async {
    if (_refreshToken == null) return false;
    try {
      final response = await _api.dio.post(
        '/api/v1/auth/refresh',
        data: {'refresh_token': _refreshToken},
      );
      _api.setAccessToken(response.data['access_token'] as String);
      _refreshToken = response.data['refresh_token'] as String;
      await _storage.write(key: 'refresh_token', value: _refreshToken);
      return true;
    } catch (_) {
      await _clearTokens();
      return false;
    }
  }

  Future<void> _loadUser() async {
    final response = await _api.dio.get('/api/v1/users/me');
    state =
        AuthState(user: User.fromJson(response.data as Map<String, dynamic>));
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true);
    try {
      final response = await _api.dio.post(
        '/api/v1/auth/login',
        data: {'email': email, 'password': password},
      );
      _api.setAccessToken(response.data['access_token'] as String);
      _refreshToken = response.data['refresh_token'] as String;
      await _storage.write(key: 'refresh_token', value: _refreshToken);
      await _loadUser();
      if (!_readyCompleter.isCompleted) _readyCompleter.complete();
      return true;
    } catch (e) {
      state =
          state.copyWith(isLoading: false, error: 'Invalid email or password');
      return false;
    }
  }

  Future<bool> register(String email, String password, String displayName,
      String currency) async {
    state = state.copyWith(isLoading: true);
    try {
      await _api.dio.post('/api/v1/auth/register', data: {
        'email': email,
        'password': password,
        'display_name': displayName,
        'default_currency': currency,
      });
      return login(email, password);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Registration failed');
      return false;
    }
  }

  Future<void> logout() async {
    if (_refreshToken != null) {
      try {
        await _api.dio.post('/api/v1/auth/logout',
            data: {'refresh_token': _refreshToken});
      } catch (_) {}
    }
    await _clearTokens();
    state = const AuthState();
  }

  Future<void> _clearTokens() async {
    _api.setAccessToken(null);
    _refreshToken = null;
    await _storage.delete(key: 'refresh_token');
  }
}
