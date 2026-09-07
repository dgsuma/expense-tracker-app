import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_controller.dart';
import 'models.dart';

/// Waits until the user is authenticated (access token set on the API client)
/// before letting a data provider fire. Prevents unauthenticated requests during
/// the login/session-restore race.
///
/// The [AuthController.ready] completer only completes once (after the initial
/// session restore), so it is not sufficient on its own: after it completes
/// unauthenticated, a later login must still be awaited. We therefore poll the
/// auth state until a user is present (or the provider is disposed).
Future<void> _ensureAuthenticated(Ref ref) async {
  // Fast path: already authenticated.
  if (ref.read(authControllerProvider).isAuthenticated) return;

  // Wait for the initial session restore / login to finish.
  await ref.read(authControllerProvider.notifier).ready;

  // After the first restore completes we may still be unauthenticated (e.g. the
  // dashboard mounted in the same frame as a fresh login). Keep waiting until a
  // user is actually present so requests always carry a token.
  final completer = Completer<void>();
  if (ref.read(authControllerProvider).isAuthenticated) return;
  final sub = ref.listen<AuthState>(authControllerProvider, (prev, next) {
    if (next.isAuthenticated && !completer.isCompleted) completer.complete();
  });
  // Safety timeout so a provider never hangs forever if login is aborted.
  final timer = Timer(const Duration(seconds: 10), () {
    if (!completer.isCompleted) completer.complete();
  });
  try {
    await completer.future;
  } finally {
    timer.cancel();
    sub.close();
  }
}

final categoriesProvider = FutureProvider<List<Category>>((ref) async {
  await _ensureAuthenticated(ref);
  final api = ref.watch(apiClientProvider);
  final response = await api.dio.get('/api/v1/categories');
  return (response.data as List<dynamic>)
      .map((c) => Category.fromJson(c as Map<String, dynamic>))
      .toList();
});

final paymentMethodsProvider = FutureProvider<List<PaymentMethod>>((ref) async {
  await _ensureAuthenticated(ref);
  final api = ref.watch(apiClientProvider);
  final response = await api.dio.get('/api/v1/payment-methods');
  return (response.data as List<dynamic>)
      .map((p) => PaymentMethod.fromJson(p as Map<String, dynamic>))
      .toList();
});

final expensesProvider = FutureProvider<ExpensePage>((ref) async {
  await _ensureAuthenticated(ref);
  final api = ref.watch(apiClientProvider);
  final response = await api.dio.get('/api/v1/expenses');
  return ExpensePage.fromJson(response.data as Map<String, dynamic>);
});

final summaryProvider = FutureProvider<Summary>((ref) async {
  await _ensureAuthenticated(ref);
  final api = ref.watch(apiClientProvider);
  final response =
      await api.dio.get('/api/v1/analytics/summary?period=monthly');
  return Summary.fromJson(response.data as Map<String, dynamic>);
});

final categoryTotalsProvider = FutureProvider<List<CategoryTotal>>((ref) async {
  await _ensureAuthenticated(ref);
  final api = ref.watch(apiClientProvider);
  final response = await api.dio.get('/api/v1/analytics/by-category');
  return (response.data['items'] as List<dynamic>)
      .map((c) => CategoryTotal.fromJson(c as Map<String, dynamic>))
      .toList();
});

final trendsProvider = FutureProvider<List<TrendPoint>>((ref) async {
  await _ensureAuthenticated(ref);
  final api = ref.watch(apiClientProvider);
  final response =
      await api.dio.get('/api/v1/analytics/trends?granularity=day');
  return (response.data['points'] as List<dynamic>)
      .map((p) => TrendPoint.fromJson(p as Map<String, dynamic>))
      .toList();
});
