import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _onboardingCompleteKey = 'onboarding_complete';
const _tutorialShownKey = 'swipe_tutorial_shown';

/// Whether the user has completed onboarding.
final onboardingCompleteProvider =
    StateNotifierProvider<OnboardingNotifier, bool>((ref) {
  return OnboardingNotifier();
});

/// Whether the swipe tutorial overlay has been shown.
final tutorialShownProvider =
    StateNotifierProvider<TutorialShownNotifier, bool>((ref) {
  return TutorialShownNotifier();
});

class OnboardingNotifier extends StateNotifier<bool> {
  OnboardingNotifier() : super(true) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool(_onboardingCompleteKey) ?? false;
  }

  Future<void> complete() async {
    state = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_onboardingCompleteKey, true);
  }
}

class TutorialShownNotifier extends StateNotifier<bool> {
  TutorialShownNotifier() : super(true) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool(_tutorialShownKey) ?? false;
  }

  Future<void> markShown() async {
    state = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_tutorialShownKey, true);
  }
}
