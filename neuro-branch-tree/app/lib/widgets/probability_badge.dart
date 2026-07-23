/// Confidence percentage badge with deliberate visual treatment.
///
/// Design principle: low percentages (≤5%) are the guardrail working correctly
/// — they should look MUTED and informational, NOT alarming or red. A 5% result
/// means "vague symptoms, correctly low confidence" — that's the system
/// functioning as designed, not an error state.
///
/// Visual tiers:
///   ≤5%   → small, gray, muted (guardrail working correctly)
///   6-49% → medium, amber-toned (moderate evidence)
///   ≥50%  → prominent, teal/green (strong match)

import 'package:flutter/material.dart';

class ProbabilityBadge extends StatelessWidget {
  final int confidencePct;

  const ProbabilityBadge({super.key, required this.confidencePct});

  _BadgeStyle get _style {
    if (confidencePct <= 5) {
      return _BadgeStyle(
        bgColor: Colors.grey.shade200,
        textColor: Colors.grey.shade600,
        fontSize: 12.0,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        borderRadius: 10.0,
      );
    } else if (confidencePct < 50) {
      return _BadgeStyle(
        bgColor: Colors.amber.shade100,
        textColor: Colors.amber.shade800,
        fontSize: 13.0,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        borderRadius: 12.0,
      );
    } else {
      return _BadgeStyle(
        bgColor: const Color(0xFF0D9488), // teal-600
        textColor: Colors.white,
        fontSize: 15.0,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
        borderRadius: 14.0,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = _style;
    return Container(
      key: const Key('probability_badge'),
      padding: s.padding,
      decoration: BoxDecoration(
        color: s.bgColor,
        borderRadius: BorderRadius.circular(s.borderRadius),
      ),
      child: Text(
        '$confidencePct%',
        style: TextStyle(
          fontSize: s.fontSize,
          fontWeight: FontWeight.w600,
          color: s.textColor,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}

class _BadgeStyle {
  final Color bgColor;
  final Color textColor;
  final double fontSize;
  final EdgeInsets padding;
  final double borderRadius;

  const _BadgeStyle({
    required this.bgColor,
    required this.textColor,
    required this.fontSize,
    required this.padding,
    required this.borderRadius,
  });
}
