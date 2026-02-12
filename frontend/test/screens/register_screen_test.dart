import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/user.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/register_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/services/auth_service.dart';
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

class MockAuthService extends Mock implements AuthService {}

class _FakeAuthNotifier extends AuthNotifier {
  final AsyncValue<User?> _initial;

  _FakeAuthNotifier(super.api, super.auth, this._initial);

  @override
  // ignore: must_call_super
  AsyncValue<User?> get state => _initial;

  @override
  set state(AsyncValue<User?> value) {}
}

Widget buildRegisterScreen({
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
          (ref) => _FakeAuthNotifier(
              ref.read(apiServiceProvider),
              ref.read(authServiceProvider),
              authState),
        ),
    ],
    child: const MaterialApp(home: RegisterScreen()),
  );
}

void main() {
  late MockApiService mockApi;
  late MockAuthService mockAuth;

  setUp(() {
    mockApi = MockApiService();
    mockAuth = MockAuthService();
    when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);
  });

  group('RegisterScreen', () {
    testWidgets('renders all registration form elements', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.text('Create Account'), findsNWidgets(2)); // headline + button
      expect(find.text('Join BookSwipe today'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Confirm Password'), findsOneWidget);
      expect(find.widgetWithText(FilledButton, 'Create Account'), findsOneWidget);
      expect(find.text('Already have an account? Log in'), findsOneWidget);
    });

    testWidgets('validates email format', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      await tester.enterText(
          find.widgetWithText(TextFormField, 'Email'), 'bad-email');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Password'), 'TestPass123');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Confirm Password'), 'TestPass123');

      await tester.tap(find.widgetWithText(FilledButton, 'Create Account'));
      await tester.pumpAndSettle();

      expect(find.textContaining('valid email'), findsOneWidget);
    });

    testWidgets('validates password strength', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      await tester.enterText(
          find.widgetWithText(TextFormField, 'Email'), 'test@example.com');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Password'), 'weak');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Confirm Password'), 'weak');

      await tester.tap(find.widgetWithText(FilledButton, 'Create Account'));
      await tester.pumpAndSettle();

      // Should show password validation error
      expect(find.textContaining('8 characters'), findsOneWidget);
    });

    testWidgets('validates password match', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      await tester.enterText(
          find.widgetWithText(TextFormField, 'Email'), 'test@example.com');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Password'), 'TestPass123');
      await tester.enterText(
          find.widgetWithText(TextFormField, 'Confirm Password'), 'DifferentPass123');

      await tester.tap(find.widgetWithText(FilledButton, 'Create Account'));
      await tester.pumpAndSettle();

      expect(find.textContaining('match'), findsOneWidget);
    });

    testWidgets('shows loading state', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.loading(),
      ));
      await tester.pump();

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows error message on registration failure', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: AsyncValue.error(
            'Email already registered', StackTrace.current),
      ));
      await tester.pumpAndSettle();

      expect(find.textContaining('Email already registered'), findsOneWidget);
    });

    testWidgets('password visibility toggle works', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.visibility_off), findsOneWidget);

      await tester.tap(find.byIcon(Icons.visibility_off));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.visibility), findsOneWidget);
    });

    testWidgets('has or divider and social login section', (tester) async {
      await tester.pumpWidget(buildRegisterScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.text('or'), findsOneWidget);
    });
  });
}
