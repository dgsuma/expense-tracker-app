/// API configuration. Override at build/run time with --dart-define.
class AppConfig {
  /// Base URL of the backend API.
  ///
  /// Empty string (the default for web builds) means "same origin": the app
  /// calls /api/... relative to whatever host/port served it, and nginx proxies
  /// those requests to the API container. This makes the web build work from
  /// any address (localhost, LAN IP, domain) with no rebuild and no CORS.
  ///
  /// Native builds still need an absolute URL:
  /// - Android emulator: http://10.0.2.2:8000
  /// - Physical device:  http://PC-LAN-IP:8000
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );
}
