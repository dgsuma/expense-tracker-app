import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/auth_controller.dart';
import 'core/data_providers.dart';
import 'core/router.dart';
import 'core/theme.dart';

void main() {
  runApp(const ProviderScope(child: ExpenseTrackerApp()));
}

class ExpenseTrackerApp extends ConsumerWidget {
  const ExpenseTrackerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Whenever the authenticated user changes (login, logout, or registering a
    // new account over an existing session), drop all cached user data so the
    // dashboard and lists reload fresh for the new user instead of showing the
    // previous user's metrics.
    ref.listen<String?>(
      authControllerProvider.select((s) => s.user?.id),
      (previous, next) {
        if (previous != next) {
          ref.invalidate(categoriesProvider);
          ref.invalidate(paymentMethodsProvider);
          ref.invalidate(expensesProvider);
          ref.invalidate(summaryProvider);
          ref.invalidate(categoryTotalsProvider);
          ref.invalidate(trendsProvider);
        }
      },
    );

    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Expense Tracker',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
