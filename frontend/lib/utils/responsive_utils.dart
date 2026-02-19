import 'package:flutter/material.dart';
import 'package:responsive_framework/responsive_framework.dart';

bool isMobile(BuildContext context) =>
    ResponsiveBreakpoints.of(context).isMobile;

bool isTablet(BuildContext context) =>
    ResponsiveBreakpoints.of(context).isTablet;

bool isDesktop(BuildContext context) =>
    ResponsiveBreakpoints.of(context).isDesktop;

double maxContentWidth(BuildContext context) {
  if (isDesktop(context)) return 1200;
  if (isTablet(context)) return 900;
  return 600;
}

int gridColumns(BuildContext context) {
  if (isDesktop(context)) return 4;
  if (isTablet(context)) return 3;
  return 2;
}

double horizontalPadding(BuildContext context) {
  if (isDesktop(context)) return 48;
  if (isTablet(context)) return 32;
  return 16;
}
