import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/login_screen.dart';
import '../features/auth/register_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/expenses/expense_list_screen.dart';
import 'auth_controller.dart';

/// Converts a Riverpod provider into a [Listenable] so go_router can re-run its
/// redirect whenever the auth state changes — without recreating the router.
class _AuthRefreshListener extends ChangeNotifier {
  _AuthRefreshListener(Ref ref) {
    _sub = ref.listen<AuthState>(
      authControllerProvider,
      (_, __) => notifyListeners(),
    );
  }

  late final ProviderSubscription<AuthState> _sub;

  @override
  void dispose() {
    _sub.close();
    super.dispose();
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final refreshListener = _AuthRefreshListener(ref);
  ref.onDispose(refreshListener.dispose);

  return GoRouter(
    initialLocation: '/dashboard',
    refreshListenable: refreshListener,
    redirect: (context, state) {
      // Read the latest auth state at redirect time (not a captured value).
      final authState = ref.read(authControllerProvider);
      final isAuthenticated = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';

      if (authState.isLoading) return null; // wait for session restore
      if (!isAuthenticated && !isAuthRoute) return '/login';
      if (isAuthenticated && isAuthRoute) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
          path: '/register',
          builder: (context, state) => const RegisterScreen()),
      GoRoute(
          path: '/dashboard',
          builder: (context, state) => const DashboardScreen()),
      GoRoute(
          path: '/expenses',
          builder: (context, state) => const ExpenseListScreen()),
    ],
  );
});
