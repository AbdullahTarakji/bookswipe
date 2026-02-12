import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/user.dart';

void main() {
  group('User', () {
    test('fromJson parses auth token response', () {
      final json = {
        'access_token': 'test-token',
        'refresh_token': 'test-refresh',
        'token_type': 'bearer',
      };

      final user = User.fromJson(json);

      expect(user.token, 'test-token');
      expect(user.refreshToken, 'test-refresh');
    });

    test('fromJson handles integer id from profile', () {
      final json = {
        'id': 42,
        'email': 'test@example.com',
        'token': 'abc',
        'refresh_token': 'def',
      };

      final user = User.fromJson(json);

      expect(user.id, '42');
      expect(user.email, 'test@example.com');
      expect(user.token, 'abc');
      expect(user.refreshToken, 'def');
    });

    test('toJson includes refresh token', () {
      const user = User(
        id: '1',
        email: 'test@example.com',
        token: 'access',
        refreshToken: 'refresh',
      );

      final json = user.toJson();

      expect(json['id'], '1');
      expect(json['email'], 'test@example.com');
      expect(json['token'], 'access');
      expect(json['refresh_token'], 'refresh');
    });

    test('copyWithTokens updates tokens only', () {
      const user = User(
        id: '1',
        email: 'test@example.com',
        token: 'old-token',
        refreshToken: 'old-refresh',
      );

      final updated = user.copyWithTokens(
        token: 'new-token',
        refreshToken: 'new-refresh',
      );

      expect(updated.id, '1');
      expect(updated.email, 'test@example.com');
      expect(updated.token, 'new-token');
      expect(updated.refreshToken, 'new-refresh');
    });

    test('fromJson defaults refreshToken to empty string', () {
      final json = {
        'access_token': 'token-only',
      };

      final user = User.fromJson(json);

      expect(user.token, 'token-only');
      expect(user.refreshToken, '');
    });

    test('fromJson parses subscription fields', () {
      final json = {
        'id': 1,
        'email': 'test@example.com',
        'token': 'abc',
        'subscription_status': 'active',
        'subscription_plan': 'premium',
        'subscription_end_date': '2025-12-31T00:00:00',
      };

      final user = User.fromJson(json);

      expect(user.subscriptionStatus, 'active');
      expect(user.subscriptionPlan, 'premium');
      expect(user.subscriptionEndDate, '2025-12-31T00:00:00');
      expect(user.isPremium, isTrue);
    });

    test('isPremium is false for free users', () {
      const user = User(
        id: '1',
        email: 'test@example.com',
        token: 'abc',
        subscriptionStatus: 'free',
        subscriptionPlan: 'free',
      );

      expect(user.isPremium, isFalse);
    });

    test('isPremium is false when status is cancelled', () {
      const user = User(
        id: '1',
        email: 'test@example.com',
        token: 'abc',
        subscriptionStatus: 'cancelled',
        subscriptionPlan: 'premium',
      );

      expect(user.isPremium, isFalse);
    });

    test('copyWithSubscription updates subscription only', () {
      const user = User(
        id: '1',
        email: 'test@example.com',
        token: 'abc',
        refreshToken: 'def',
      );

      final updated = user.copyWithSubscription(
        subscriptionStatus: 'active',
        subscriptionPlan: 'premium',
      );

      expect(updated.id, '1');
      expect(updated.email, 'test@example.com');
      expect(updated.token, 'abc');
      expect(updated.subscriptionStatus, 'active');
      expect(updated.subscriptionPlan, 'premium');
      expect(updated.isPremium, isTrue);
    });

    test('toJson includes subscription fields', () {
      const user = User(
        id: '1',
        email: 'test@example.com',
        token: 'access',
        refreshToken: 'refresh',
        subscriptionStatus: 'active',
        subscriptionPlan: 'premium',
        subscriptionEndDate: '2025-12-31T00:00:00',
      );

      final json = user.toJson();

      expect(json['subscription_status'], 'active');
      expect(json['subscription_plan'], 'premium');
      expect(json['subscription_end_date'], '2025-12-31T00:00:00');
    });

    test('fromJson defaults subscription to free', () {
      final json = {
        'access_token': 'token',
      };

      final user = User.fromJson(json);

      expect(user.subscriptionStatus, 'free');
      expect(user.subscriptionPlan, 'free');
      expect(user.subscriptionEndDate, isNull);
      expect(user.isPremium, isFalse);
    });
  });
}
