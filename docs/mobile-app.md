# Mobile & web app (Flutter)

The Flutter app in `apps/mobile` targets Android, iOS, tablet, and web from a single codebase.

## Architecture

```
lib/
├── main.dart                  # App entry, ProviderScope, MaterialApp.router
├── core/
│   ├── config.dart            # API base URL (--dart-define)
│   ├── theme.dart             # Material 3 light/dark themes
│   ├── models.dart            # Data models matching API schemas
│   ├── api_client.dart        # Dio client, JWT header, auto-refresh on 401
│   ├── auth_controller.dart   # Auth state (Riverpod), secure token storage
│   ├── data_providers.dart    # Riverpod providers for API data
│   └── router.dart            # go_router with auth-gated redirects
└── features/
    ├── auth/                  # login_screen, register_screen
    ├── dashboard/             # dashboard_screen (summary, charts)
    └── expenses/              # expense_list_screen, expense_form
```

## Key design decisions

- **State management:** Riverpod (`StateNotifier` for auth, `FutureProvider` for data).
- **Routing:** `go_router` with a redirect that gates routes on authentication state.
- **Token storage:** `flutter_secure_storage` (Keychain on iOS, Keystore on Android, encrypted web storage). Only the refresh token is persisted; the access token lives in memory.
- **Auto-refresh:** the Dio interceptor retries a request once after a 401 by refreshing the token pair.
- **Responsive:** the dashboard uses `LayoutBuilder` — side-by-side charts on wide screens (tablet/web), stacked on phones.
- **Charts:** `fl_chart` (pie for category breakdown, bar for trends).

## Running

```powershell
# Web (Chrome) against the local API
.\scripts\dev-app.ps1

# Android emulator (reaches host API via 10.0.2.2)
.\scripts\dev-app.ps1 -Device android

# Or directly
cd apps\mobile
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

The API base URL is injected at build/run time via `--dart-define=API_BASE_URL=...` (see [config.dart](../apps/mobile/lib/core/config.dart)). Default is `http://localhost:8000`; the Android emulator uses `http://10.0.2.2:8000`.

## Testing

```powershell
cd apps\mobile
flutter analyze   # static analysis
flutter test      # unit/widget tests
```

## Building

```powershell
flutter build web --release          # web → build/web
flutter build apk --release          # Android (requires Android SDK)
flutter build appbundle --release    # Play Store
flutter build ios --release          # iOS (requires macOS/Xcode)
```

## Store distribution

- **Android:** `flutter build appbundle`, sign with an upload key, upload to Play Console.
- **iOS:** `flutter build ipa` on macOS, upload via Xcode/App Store Connect.
- Signing configuration and store metadata are set up in a later phase before release.
