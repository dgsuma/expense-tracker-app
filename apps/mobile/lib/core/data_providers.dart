import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_controller.dart';
import 'models.dart';

/// Waits until the user is authenticated (access token set on the API client)
/// before letting a data provider fire. Prevents unauthenticated requests during
/// the login/session-restore race.
Future<void> _ensureAuthenticated(Ref ref) async {
  if (ref.read(authControllerProvider).isAuthenticated) return;
  await ref.read(authControllerProvider.notifier).ready;
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
