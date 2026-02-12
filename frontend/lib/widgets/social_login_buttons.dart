import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../providers/providers.dart';

class SocialLoginButtons extends ConsumerWidget {
  const SocialLoginButtons({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final isLoading = authState.isLoading;

    return Column(
      children: [
        // Google Sign-In button (brand guidelines: white bg, Google colors)
        SizedBox(
          width: double.infinity,
          height: 48,
          child: OutlinedButton.icon(
            onPressed: isLoading ? null : () => _signInWithGoogle(context, ref),
            icon: Image.asset(
              'assets/google_logo.png',
              height: 20,
              width: 20,
              errorBuilder: (context, error, stackTrace) => const Icon(Icons.g_mobiledata, size: 24),
            ),
            label: const Text('Sign in with Google'),
            style: OutlinedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: const Color(0xFF1F1F1F),
              side: const BorderSide(color: Color(0xFFDADCE0)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              textStyle: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        // Apple Sign-In button (brand guidelines: black bg, white text)
        if (Platform.isIOS || Platform.isMacOS)
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: isLoading ? null : () => _signInWithApple(context, ref),
              icon: const Icon(Icons.apple, size: 24),
              label: const Text('Sign in with Apple'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                textStyle: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _signInWithGoogle(BuildContext context, WidgetRef ref) async {
    try {
      final googleSignIn = GoogleSignIn(scopes: ['email']);
      final account = await googleSignIn.signIn();
      if (account == null) return; // User cancelled

      final auth = await account.authentication;
      final idToken = auth.idToken;
      if (idToken == null) {
        if (context.mounted) _showError(context, 'Failed to get Google ID token');
        return;
      }

      await ref.read(authStateProvider.notifier).signInWithGoogle(idToken);
    } catch (e) {
      if (context.mounted) {
        _showError(context, 'Google sign-in failed. Please try again.');
      }
    }
  }

  Future<void> _signInWithApple(BuildContext context, WidgetRef ref) async {
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      final authCode = credential.authorizationCode;
      final identityToken = credential.identityToken;
      if (identityToken == null) {
        if (context.mounted) _showError(context, 'Failed to get Apple identity token');
        return;
      }

      await ref.read(authStateProvider.notifier).signInWithApple(
        authorizationCode: authCode,
        identityToken: identityToken,
      );
    } catch (e) {
      if (context.mounted) {
        _showError(context, 'Apple sign-in failed. Please try again.');
      }
    }
  }

  void _showError(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}
