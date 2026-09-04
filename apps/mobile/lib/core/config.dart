/// API configuration. Override at build/run time with --dart-define.
class AppConfig {
  /// Base URL of the backend API.
  /// - Android emulator: http://10.0.2.2:8000
  /// - iOS simulator / web / desktop: http://localhost:8000
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
}
