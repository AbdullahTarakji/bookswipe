import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/user.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/login_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/services/auth_service.dart';
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

class MockAuthService extends Mock implements AuthService {}

/// Helper to pump the LoginScreen with overridden providers.
Widget buildLoginScreen({
  required MockApiService api,
  required MockAuthService auth,
  AsyncValue<User?>? authState,
}) {
  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      authServiceProvider.overrideWithValue(auth),
      if (authState != null)
        authStateProvider.overrideWith(
          (ref) => _FakeAuthNotifier(ref.read(apiServiceProvider),
              ref.read(authServiceProvider), authState),
        ),
    ],
    child: const MaterialApp(home: LoginScreen()),
  );
}

class _FakeAuthNotifier extends AuthNotifier {
  final AsyncValue<User?> _initial;

  _FakeAuthNotifier(super.api, super.auth, this._initial);

  @override
  // ignore: must_call_super
  AsyncValue<User?> get state => _initial;

  @override
  set state(AsyncValue<User?> value) {
    // no-op for fake
  }
}

void main() {
  late MockApiService mockApi;
  late MockAuthService mockAuth;

  setUp(() {
    mockApi = MockApiService();
    mockAuth = MockAuthService();
    when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);
  });

  group('LoginScreen', () {
    testWidgets('renders all login form elements', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.text('BookSwipe'), findsOneWidget);
      expect(find.text('Discover your next read'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Log In'), findsOneWidget);
      expect(find.text("Don't have an account? Sign up"), findsOneWidget);
    });

    testWidgets('shows email validation error', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // Enter invalid email
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Email'), 'not-an-email');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Password'), 'password');

      // Tap Log In
      await tester.tap(find.text('Log In'));
      await tester.pumpAndSettle();

      expect(find.textContaining('valid email'), findsOneWidget);
    });

    testWidgets('shows password required error', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // Enter valid email but leave password empty
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Email'), 'test@example.com');

      await tester.tap(find.text('Log In'));
      await tester.pumpAndSettle();

      expect(find.textContaining('password'), findsWidgets);
    });

    testWidgets('password visibility toggle works', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // Initially password is obscured (visibility_off icon shown)
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);

      // Tap to toggle
      await tester.tap(find.byIcon(Icons.visibility_off));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.visibility), findsOneWidget);
    });

    testWidgets('shows loading state', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.loading(),
      ));
      await tester.pump();

      // The button should show a CircularProgressIndicator when loading
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows error message on auth failure', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState:
            AsyncValue.error('Invalid email or password', StackTrace.current),
      ));
      await tester.pumpAndSettle();

      expect(find.textContaining('Invalid email or password'), findsOneWidget);
    });

    testWidgets('has or divider and social login section', (tester) async {
      await tester.pumpWidget(buildLoginScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.text('or'), findsOneWidget);
    });
  });
}
