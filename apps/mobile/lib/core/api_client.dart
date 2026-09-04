import 'package:dio/dio.dart';

import 'config.dart';

/// HTTP client with JWT auth and automatic token refresh on 401.
class ApiClient {
  final Dio _dio;
  String? _accessToken;
  Future<bool> Function()? _onRefresh;

  ApiClient()
      : _dio = Dio(BaseOptions(
          baseUrl: AppConfig.apiBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 15),
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // On 401, try a single token refresh then retry the request once.
        if (error.response?.statusCode == 401 && _onRefresh != null) {
          final refreshed = await _onRefresh!();
          if (refreshed) {
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer $_accessToken';
            try {
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            } catch (_) {
              return handler.next(error);
            }
          }
        }
        handler.next(error);
      },
    ));
  }

  void setAccessToken(String? token) => _accessToken = token;
  void setRefreshHandler(Future<bool> Function() handler) =>
      _onRefresh = handler;

  Dio get dio => _dio;
}
