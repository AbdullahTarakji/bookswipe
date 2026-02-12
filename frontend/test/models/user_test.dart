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
  });
}
