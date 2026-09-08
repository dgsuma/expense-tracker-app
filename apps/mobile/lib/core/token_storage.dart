import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Stores the refresh token.
///
/// On native platforms we use [FlutterSecureStorage] (Keychain / Keystore).
/// On web, `flutter_secure_storage` relies on the Web Crypto API
/// (`crypto.subtle`), which browsers only expose in *secure contexts*
/// (HTTPS or localhost). When the app is served over plain HTTP on a LAN
/// (e.g. http://192.168.1.5:8080), that API is unavailable and the storage
/// write throws — which previously caused login to fail right after a
/// successful token response. So on web we persist the token with
/// [SharedPreferences] (localStorage) instead.
///
/// Note: localStorage is readable by any script on the origin, so this is
/// acceptable only for development / trusted-LAN use. Production web should be
/// served over HTTPS, where secure storage works.
abstract class TokenStorage {
  Future<String?> read();
  Future<void> write(String value);
  Future<void> delete();
}

class _SecureTokenStorage implements TokenStorage {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const _key = 'refresh_token';

  @override
  Future<String?> read() => _storage.read(key: _key);

  @override
  Future<void> write(String value) => _storage.write(key: _key, value: value);

  @override
  Future<void> delete() => _storage.delete(key: _key);
}

class _WebTokenStorage implements TokenStorage {
  static const _key = 'refresh_token';

  @override
  Future<String?> read() async =>
      (await SharedPreferences.getInstance()).getString(_key);

  @override
  Future<void> write(String value) async =>
      (await SharedPreferences.getInstance()).setString(_key, value);

  @override
  Future<void> delete() async =>
      (await SharedPreferences.getInstance()).remove(_key);
}

/// Returns the appropriate storage for the current platform.
TokenStorage createTokenStorage() =>
    kIsWeb ? _WebTokenStorage() : _SecureTokenStorage();
